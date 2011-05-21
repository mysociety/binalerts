# models.py:
# Models for Bin Alerts.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

import datetime
import sys
import xml.dom.minidom
import re
import csv
import os.path

from settings import BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK
from settings import BINS_STREETS_MUST_HAVE_POSTCODE

from django.db import models
from django.db import IntegrityError
from django.contrib.contenttypes import generic

from emailconfirmation.models import EmailConfirmation
from emailconfirmation.utils import send_email

DAY_OF_WEEK_CHOICES = (
    (0, 'Sunday'),
    (1, 'Monday'),
    (2, 'Tuesday'),
    (3, 'Wednesday'),
    (4, 'Thursday'),
    (5, 'Friday'),
    (6, 'Saturday')
)


class BinCollectionType(models.Model):
    description = models.CharField(max_length=200)
    friendly_id = models.CharField(max_length=4) # used in associated graphic filenames and javascript: rather than using a number (id)
    detail_text = models.TextField(max_length=1024, null=False, blank=True, default="") 
    # detail_text used to provide extra info on the street page (including, e.g., a link to council page)
    
    def __unicode__(self):
        return "%s" % (self.description)

class StreetManager(models.Manager):
    def find_by_name(self, name):
        return self.filter(name__icontains=name)                

    # returns list of postcodes for a given street (based on what's already in the database, of course)
    # This is used by import to guess/recommend postcodes on incoming street data lacking a postcode
    def get_postcodes_for_name(self, name):
        return self.filter(name__iexact=name).exclude(partial_postcode='').values_list('partial_postcode', flat=True)

    # add a street to the database (this is via update: a little dangerous if this isn't used in admin street creation)
    # raises IntegrityError if there's a problem (similar to get_or_create), containing useful message
    # returns street, bool was created, bool guessed_postcode
    def get_or_create_street(self, name, partial_postcode=None, guess_postcodes=False):
        if not partial_postcode:
            partial_postcode = '' # empty string since not null is enforced
        if not name:
            raise IntegrityError('street has no name')
        did_guess_postcode = False
        candidate_streets = self.filter(name__iexact=name)
        if not partial_postcode:
            postcodes = candidate_streets.exclude(partial_postcode='').values_list('partial_postcode', flat=True)
            if len(postcodes) == 1 and guess_postcodes:
                partial_postcode = postcodes[0]
                did_guess_postcode = True
            elif BINS_STREETS_MUST_HAVE_POSTCODE:
                msg = '"%s" has no postcode' % name
                if postcodes:
                    msg += ' (my guess from existing data is: %s)' % ' or '.join(postcodes)
                raise IntegrityError(msg)
        if candidate_streets.filter(partial_postcode=partial_postcode):
            return (candidate_streets[0], False, did_guess_postcode)
        elif len(candidate_streets) > 1:
            msg = '"%s"" is ambiguous, %s possibilities: %s' % (name, len(candidate_streets), " or ".join('"' + s.__unicode__() + '"' for s in candidate_streets))
            raise IntegrityError(msg)
        else:
            url_name = Street.make_url_name(name, partial_postcode)
            street = Street(name=name, url_name=url_name, partial_postcode=partial_postcode)
            street.save()
            return (street, True, did_guess_postcode) 

class Street(models.Model):
    name = models.CharField(max_length=200)
    url_name = models.SlugField(max_length=50)
    partial_postcode = models.CharField(max_length=5) # e.g. NW4

    class Meta:
        ordering = ["name", "partial_postcode"]
        
    # returns fairly specific report message (which makes this a bit fiddlier than necessary)
    # This is the routine used by data import, so it's very useful to be clear how the data change has affected collections
    def add_collection(self, collection_type, collection_day):
        msg = ""
        deleted_days = []
        collection_day_name = BinCollection.number_to_day_name(collection_day)
        if not BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK:
            # delete all other collections (of this type), on all days, then create a new one
            for bc in self.bin_collections.filter(collection_type=collection_type).order_by('collection_day'):
                if bc.collection_day != collection_day:
                    deleted_days.append(BinCollection.number_to_day_name(bc.collection_day))
                    bc.delete()
        bin_collection, was_created = BinCollection.objects.get_or_create(street=self, collection_type=collection_type, collection_day=collection_day )
        if was_created:
            if deleted_days: # only if multiple collections are forbidden
                if len(deleted_days)==1:
                    msg = "changed collection from %s to %s" % (deleted_days[0], collection_day_name) # day changed
                else:
                    msg = "repaced %s collections with one on %s" % (' and '.join(deleted_days), collection_day_name)
            else:
                msg = "added %s collection" % collection_day_name
        else:
            bin_collection.last_update = datetime.datetime.now() # mark the data as modified, since it's up-to-date as of now
            msg = "collection on %s remains unchanged" % collection_day_name
        bin_collection.save()
        return msg

    objects = StreetManager()

    def __unicode__(self):
        if (self.partial_postcode):
            return "%s, %s" % (self.name, self.partial_postcode)
        else:
            return self.name

    # Check it is a partial postcode, e.g. EN4
    @staticmethod
    def partial_postcode_parse(partial_postcode):
        if re.match("[A-Z]+[0-9]+$", partial_postcode):
            return partial_postcode
        return None

    @staticmethod
    def make_url_name(street_name, partial_postcode):
        url_name = '_'.join(street_name.strip().split())
        if partial_postcode:
            url_name += '_' + partial_postcode.strip()
        return url_name.lower()
        
        
class BinCollectionManager(models.Manager):
    def find_by_street_name(self, street_name):
        return self.filter(street__name__icontains=street_name)                    


# Represents when a type of bin is collected for a particular street.
class BinCollection(models.Model):

    street = models.ForeignKey(Street, null=False, related_name='bin_collections')
    collection_day = models.IntegerField(choices=DAY_OF_WEEK_CHOICES)
    collection_type = models.ForeignKey(BinCollectionType, null=False)
    last_updated = models.DateTimeField(auto_now=True, auto_now_add=True, null=True) # allow tracking of change data
    
    objects = BinCollectionManager()

    class Meta:
        ordering = ["street__name", "collection_day", "collection_type__friendly_id"]
        
    def get_collection_day_name(self):
        return self.number_to_day_name(self.collection_day)

    def get_collection_type_display(self):
        return self.collection_type.description
            
    def __unicode__(self):
        return "%s: %s (%s)" % (self.street, self.get_collection_day_name(), self.collection_type)

    # Convert from day of week string e.g. Sunday, to number, e.g. 0
    @staticmethod
    def day_of_week_string_to_number(day_of_week):
        for row in DAY_OF_WEEK_CHOICES:
            if row[1] == day_of_week:
                return row[0]
        return None

    # Convert from number to day of week string e.g. 0 to Sunday 
    # note: using mod 7 here, although perhaps any number > len(DAY_OF_WEEK_CHOICES) should throw an exception?
    @staticmethod
    def number_to_day_name(day_number):
        return DAY_OF_WEEK_CHOICES[day_number % 7][1]

#######################################################################################
# Email alerts for bin collections

class CollectionAlertManager(models.Manager):
    def send_pending_alerts(self, now = None):
        if now == None:
            now = datetime.datetime.now()
        today = now.date()
        # print "doing day", today

        # find day of week in same format as DAY_OF_WEEK_CHOICES
        today_day_of_week = today.isoweekday()
        assert today_day_of_week >= 1 and today_day_of_week <= 7
        tomorrow_day_of_week = (today_day_of_week + 1) % 7
        tomorrow_day_name = BinCollection.number_to_day_name(tomorrow_day_of_week)
        
        for collection_alert in CollectionAlert.objects.filter(confirmed__confirmed=True).filter(last_checked_date__lt=today):
            collections = collection_alert.street.bin_collections.filter(collection_day__exact=tomorrow_day_of_week)
            if collections:
                bin_collection_types_subject = " + ".join(bc.get_collection_type_display() for bc in collections)
                bin_collection_types_list = "\n".join("  * %s\n" % bc.get_collection_type_display() for bc in collections)
                send_email(None, 'Bin collection tomorrow, %s! (%s)' % (tomorrow_day_name, bin_collection_types_subject),
                    'email-alert.txt', {
                        'bin_collection_types_list': bin_collection_types_list,
                        'street_name': collection_alert.street.__unicode__(),
                        'tomorrow_day_name': tomorrow_day_name,
                        'collection_alert': collection_alert,
                        'unsubscribe_url': "http://NOT_YET_IMPLEMENTED"
                    }, collection_alert.email
                )
                collection_alert.last_sent_date = today
                
            collection_alert.last_checked_date = today
            collection_alert.save()

class CollectionAlert(models.Model):
    email = models.EmailField()
    street = models.ForeignKey(Street, null=True)
    
    confirmed = generic.GenericRelation(EmailConfirmation)
    last_checked_date = models.DateField(default=datetime.date(2000, 01, 01)) # always long in the past
    last_sent_date = models.DateField(default=None, blank=True, null=True) 
    
    objects = CollectionAlertManager()

    def is_confirmed(self):
        confirmeds = self.confirmed.all()
        assert len(confirmeds) == 1
        return confirmeds[0].confirmed

    class Meta:
        ordering = ('email',)
    
    def __unicode__(self):
        return 'Alert for %s, street %s, confirmed %s' % (self.email, self.street.url_name, self.is_confirmed())

class DataImport(models.Model):
    upload_file = models.FileField(upload_to='uploads')
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=True, null=True) # allow tracking of change data
    implicit_collection_type = models.ForeignKey(BinCollectionType, null=True, blank=True)
    guess_postcodes = models.BooleanField(null=False, blank=False, default=False)
    
    def __unicode__(self):
        collection_type = "auto"
        if self.implicit_collection_type:
            collection_type = self.implicit_collection_type
        guessing_postcodes = "yes" if self.guess_postcodes else "no"
        filename = os.path.split(self.upload_file.name)[1]
        return '%s: %s (guess postcodes: %s, type: %s)' % (self.timestamp, filename, guessing_postcodes, collection_type)
    
    def import_data(self):       
        if self.upload_file:
            if self.upload_file.name.endswith('.csv'):
                csv_file = self.upload_file
                report_lines = DataImport.load_from_csv_file(
                                    csv_file, 
                                    collection_type=self.implicit_collection_type, 
                                    guess_postcodes=self.guess_postcodes,
                                    want_onscreen_log=True)
            else:
                if self.upload_file.name.endswith('.xml'):
                    report_lines = DataImport.load_from_pdf_xml(
                                    self.upload_file.path, 
                                    collection_type=self.implicit_collection_type, 
                                    guess_postcodes=self.guess_postcodes,
                                    want_onscreen_log=True)
            self.upload_file.delete()
            self.delete() # deleting everything after import seems harh, but also keeps the DataImport admin clean
            return report_lines

    # load_from_csv currently expects CSV file with:
    #     data before "Monday,Tuesday.Wednesday,Thursday,Friday" ignored
    #     thereafter, five street names per line (may be blank)
    # arg: csv_file maybe from: open(csv_file_name, 'r')
    #      collection_type
    @staticmethod
    def load_from_csv_file(csv_file, collection_type=None, guess_postcodes=False, want_onscreen_log=False):
        # nb collection_type can only be optional if it's explicitly stated inside the file (currently we don't look for this)
        default_collection_type = collection_type
        auto_postcode = "will" if guess_postcodes else "will not"
        filename = os.path.split(csv_file.name)[1]
        msg = "importing from CSV file: %s (as %s unless explicitly specified), %s guess missing postcodes" % (filename, default_collection_type, auto_postcode)
        log_lines = DataImport._add_to_log_lines([], msg, want_onscreen_log)
        reader=csv.reader(csv_file, delimiter=',', quotechar='"')
        regexp_alpha_check = re.compile('\w')
        found_data = None
        day_number_offset = 0
        n_collections = 0
        n_new_streets = 0
        n_lines = 0
        for row in reader: 
            n_lines += 1
            if found_data == 'native':
                street_name = row[0]
                partial_postcode = row[1]
                try:
                    collection_type = BinCollectionType.objects.get(friendly_id=row[2])
                except ObjectDoesNotExist:
                    collection_type = default_collection_type # default
                this_day = BinCollection.day_of_week_string_to_number(row[3])
                try:
                    street, was_created, did_guess_postcode = Street.objects.get_or_create_street(street_name, partial_postcode, guess_postcodes=guess_postcodes)
                except IntegrityError, e: # e.g., ambiguous postcode: exception may contain suggested value
                    msg = "line %s: did not update street: %s" % (n_lines, e)
                    log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
                    continue
                if did_guess_postcode:
                    did_guess_postcode = "(guessed postcode %s)" % street.partial_postcode
                else:
                    did_guess_postcode = ""
                if was_created:
                    msg = 'line %s: made a new street "%s" %s' % (n_lines, street, did_guess_postcode)
                    log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
                    n_new_streets += 1
                collection_change_msg = street.add_collection(collection_type, this_day)
                msg = 'line %s: street %s: %s %s' % (n_lines, street, collection_change_msg, did_guess_postcode)
                log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log) 
                n_collections += 1 
            elif found_data == 'barnet':
                for day in range(len(row)): #   for this_day in 0..4 (actually monday-friday)
                    # note: here we are making these assumptions, based on current provided data:
                    #       index position is day (i.e., col 0 is on Monday)
                    #       there is NO postcode
                    # Ought to dump all failures into a log for review, and manual input, later TODO
                    this_day = day + day_number_offset
                    this_day_name = BinCollection.number_to_day_name(this_day)
                    street_name = ' '.join(row[day].strip().split())
                    partial_postcode = None # for now: absolutely anticipate finding one in future data
                    if not regexp_alpha_check.match(street_name): # common: an empty entry in the row, nothing more to do
                        continue
                    try:
                        street, was_created, did_guess_postcode = Street.objects.get_or_create_street(street_name, partial_postcode, guess_postcodes=guess_postcodes)
                    except IntegrityError, e: # e.g., ambiguous postcode: exception may contain suggested value
                        msg = "line %s: did not update street: %s" % (n_lines, e)
                        log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
                        continue
                    if did_guess_postcode:
                        did_guess_postcode = "(guessed postcode %s)" % street.partial_postcode
                    else:
                        did_guess_postcode = ""
                    if was_created:
                        msg = 'line %s: made a new street "%s" %s' % (n_lines, street, did_guess_postcode)
                        log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
                        n_new_streets += 1
                    collection_change_msg = street.add_collection(collection_type, this_day)
                    msg = 'line %s: street %s: %s %s' % (n_lines, street, collection_change_msg, did_guess_postcode)
                    log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log) 
                    n_collections += 1
            else:
                # lazy for now: the title line is "Monday,Tuesday,...,Friday"
                if len(row)==4 and row[0]=='street' and row[1]=='postcode' and row[2]=='type' and row[3]=='days':
                    found_data = 'native'
                elif len(row)>=5 and row[0] == 'Monday' and row[4] == 'Friday':
                    found_data = 'barnet'
                    day_number_offset = 1 # because row 0 is Monday, which is 1
        if not found_data:
            msg = 'found no data in "%s". Check that the file has the right title line in it.' % filename
            log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
        else:
            msg = "lines read from import file: %s" % n_lines
            log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
            msg = "bin collections loaded: %s" % n_collections
            log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
            msg = "new streets created: %s" % n_new_streets
            log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
        return log_lines

    # loads http://www.barnet.gov.uk/garden-and-kitchen-waste-collection-streets.pdf
    # after it has been converted with "pdftohtml -xml"
    @staticmethod
    def load_from_pdf_xml(xml_file_name, collection_type=None, guess_postcodes=False, want_onscreen_log=False):
        # nb collection_type can only be optional if it's explicitly stated inside the file (currently we don't look for this)
        auto_postcode = "will" if guess_postcodes else "will not"
        filename = os.path.split(xml_file_name)[1]
        msg = "importing from XML file: %s (as %s unless explicitly specified), %s guess missing postcodes" % (filename, collection_type, auto_postcode)
        log_lines = DataImport._add_to_log_lines([], msg, want_onscreen_log)
        n_collections = 0
        n_new_streets = 0
        doc = xml.dom.minidom.parse(xml_file_name)
        rows = DataImport._yield_rows_from_pdf(doc)
        started = False
        for row in rows:
            #print row
            # find header letters, e.g. A, B, C
            if len(row) == 1:
                letter = row[0]
                if len(letter) != 1:
                    # we loop until the first header letter
                    if not started:
                        continue
                    # this is a heuristic for the end
                    if started and letter == '':
                        n = rows.next()
                        assert n == [""]
                        n = rows.next()
                        assert n == ["April 2006"] # XXX generalise this to any date?
                        break
                    raise Exception("unexpected single item '" + letter + "' when expected a letter")
                # the letter is followed by a blank "row"
                n = rows.next()
                assert n == ["","",""]
                started = True
            elif started:
                # this is a useful row, store it
                #for column in row:
                #    print column + ",",
                #print
                (street_name_1, street_name_2, partial_postcode, day_of_week) = row
                pretty_row = ', '.join(row)
                checked_partial_postcode = Street.partial_postcode_parse(partial_postcode)
                if not checked_partial_postcode:
                    msg = 'Can\'t parse partial postcode "%s", ignoring row "%s"' % (partial_postcode, pretty_row)
                    log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)                    
                else:
                    street_name = (street_name_1 + " " + street_name_2).strip()
                    days_of_week = re.split('\W', day_of_week)
                    if len(days_of_week) > 1 and not BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK:
                        msg = 'Can\'t parse "%s" into a single day: ignoring row "%s"' % (day_of_week, row)
                        log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
                    else:
                        days_as_numbers = []
                        for day_name in days_of_week:
                            day_of_week_as_number = BinCollection.day_of_week_string_to_number(day_name)
                            if not day_of_week_as_number:
                                msg = 'Can\'t parse day of week "%s", skipping that day in row "%s"' % (day_name, row)
                                log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
                            else:
                                days_as_numbers.append(day_of_week_as_number)
                        if len(days_as_numbers) > 0:
                            try:
                                street, was_created, did_guess_postcode = Street.objects.get_or_create_street(street_name, partial_postcode, guess_postcodes=guess_postcodes)
                            except IntegrityError, e: # e.g., ambiguous postcode: exception may contain suggested value
                                msg = 'did not update street: %s in row "%s"' % (e, row)
                                log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
                                continue
                            if was_created: 
                                if did_guess_postcode:
                                    did_guess_postcode = "(guessed postcode %s)" % street.partial_postcode
                                else:
                                    did_guess_postcode = ""
                                msg = 'made a new street %s %s' % (street, did_guess_postcode)
                                log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
                                n_new_streets += 1
                            # used to report what was *new* in this update :-|
                            for day_number in days_as_numbers:
                                collection_change_msg = street.add_collection(collection_type, day_number)
                                msg = 'street %s: %s  (from row "%s")' % (street, collection_change_msg, pretty_row)
                                log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log) 
                                n_collections += 1
        msg = "bin collections loaded: %s" % n_collections
        log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
        msg = "new streets created: %s" % n_new_streets
        log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
        return log_lines

    # clumsy: either build up a list of log_lines (return the array)
    # doing this so it plays fairly nicely in the admin interface, but also 
    # runs helpfully from the command line
    @staticmethod
    def _add_to_log_lines(log_lines, msg, want_onscreen_log=False):
        if want_onscreen_log:
            log_lines.append(msg)
            return log_lines
        else:
            sys.stderr.write(msg + "\n")
            return log_lines
            
    # PDF loading, internal functions
    @staticmethod
    def _get_text_from_node(nodelist):
        rc = ""
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc = rc + node.data
            elif node.nodeType == node.ELEMENT_NODE:
                if node.nodeName == 'b':
                    rc = rc + DataImport._get_text_from_node(node.childNodes)
                else:
                    raise Exception("unfinished")
            else:
                raise Exception("unfinished")
        return rc

    # joins together items which are vertically wrapped but in the same table cell
    @staticmethod
    def _yield_cells(nodes):
        cell_text = ""
        last_top = None
        last_left = None
        for node in nodes:
            top = int(node.getAttribute('top'))
            left = int(node.getAttribute('left'))
            text = DataImport._get_text_from_node(node.childNodes).strip()

            # in vertical column exactly aligned is word wrapping in one cell
            if left == last_left:
                # so append text to current cell
                cell_text += " " + text
            else:
                yield cell_text, last_top, last_left
                cell_text = text

            last_top = top
            last_left = left

        if cell_text != "":
            yield cell_text, top, left

    # Works out what a row in the table is, and yields each one. A row is
    # just items which are lined up vertically.
    @staticmethod
    def _yield_rows_from_pdf(doc):
        items = []
        last_top = None
        last_left = None
        nodes = doc.getElementsByTagName('text').__iter__()
        for text, top, left in DataImport._yield_cells(nodes):
            if top != last_top and items != []:
                yield items
                items = []

            items.append(text)

            last_top = top
            last_left = left
        if items != []:
            yield items
