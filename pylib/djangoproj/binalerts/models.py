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

from djangoproj.settings import BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK

from django.db import models
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
    
class Street(models.Model):
    name = models.CharField(max_length=200)
    url_name = models.SlugField(max_length=50)
    partial_postcode = models.CharField(max_length=5) # e.g. NW4

    def add_collection(self, collection_type, collection_day):
        if not BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK:
            # delete all other collections (of this type), on all days, then create a new one
            for bc in self.bin_collections.filter(collection_type=collection_type):
                bc.delete()
        # find the single bin collection of this type on this day, and mark it as modified
        bin_collection, was_created = BinCollection.objects.get_or_create(street=self, collection_type=collection_type, collection_day=collection_day )
        if not was_created:
            bin_collection.last_update = datetime.datetime.now()
        bin_collection.save()

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

    def get_collection_day_name(self):
        return DAY_OF_WEEK_CHOICES[self.collection_day][1]

    def get_collection_type_display(self):
        return self.collection_type.description
            
    def __unicode__(self):
        return "%s: %s (%s)" % (self.street, DAY_OF_WEEK_CHOICES[self.collection_day][1], self.collection_type)

    # Convert from day of week string e.g. Sunday, to number, e.g. 0
    @staticmethod
    def day_of_week_string_to_number(day_of_week):
        for row in DAY_OF_WEEK_CHOICES:
            if row[1] == day_of_week:
                return row[0]
        return None

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

        for collection_alert in CollectionAlert.objects.filter(confirmed__confirmed=True).filter(last_checked_date__lt=today):
            bin_collection = collection_alert.street.bin_collections.all()[0]
            # print "day of week compare", bin_collection.collection_day, tomorrow_day_of_week
            if bin_collection.collection_day == tomorrow_day_of_week:
                send_email(None, 'Bin collection tomorrow, %s! (%s)' % (bin_collection.get_collection_day_display(), bin_collection.get_collection_type_display()),
                    'email-alert.txt', {
                        'bin_collection': bin_collection,
                        'collection_alert': collection_alert,
                        'unsubscribe_url': "http://NOT_YET_IMPLEMENTED"
                    }, collection_alert.email
                )

            collection_alert.last_checked_date = today
            collection_alert.save()

class CollectionAlert(models.Model):
    email = models.EmailField()
    street = models.ForeignKey(Street, null=True)
    
    confirmed = generic.GenericRelation(EmailConfirmation)
    last_checked_date = models.DateField(default=datetime.date(2000, 01, 01)) # always long in the past

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

    def __unicode__(self):
        return '%s: %s' % (self.timestamp, self.upload_file.name)
    
    def import_data(self):       
        if self.upload_file:
            if self.upload_file.name.endswith('.csv'):
                csv_file = self.upload_file
                report_lines = DataImport.load_from_csv_file(csv_file, want_onscreen_log=True)
            else:
                if self.upload_file.name.endswith('.xml'):
                    report_lines = DataImport.load_from_pdf_xml(self.upload_file.path, want_onscreen_log=True)
            self.upload_file.delete()
            self.delete()
            return report_lines

    # load_from_csv currently expects CSV file with:
    #     data before "Monday,Tuesday.Wednesday,Thursday,Friday" ignored
    #     thereafter, five street names per line (may be blank)
    # arg: csv_file maybe from: open(csv_file_name, 'r')
    @staticmethod
    def load_from_csv_file(csv_file, collection_type_id='D', want_onscreen_log=False):
        log_lines = []
        this_type = this_type = BinCollectionType.objects.get(friendly_id=collection_type_id)
        reader=csv.reader(csv_file, delimiter=',', quotechar='"')
        regexp_alpha_check = re.compile('\w')
        found_data = False
        day_number_offset = 0
        n_collections = 0
        n_new_streets = 0
        n_lines = 0
        for row in reader: 
            n_lines += 1
            if found_data:
                for day in range(len(row)): #   for this_day in 0..4 (actually monday-friday)
                    # note: here we are making these assumptions, based on current provided data:
                    #       index position is day
                    #       there is NO postcode
                    # Ought to dump all failures into a log for review, and manual input, later TODO
                    this_day = day + day_number_offset
                    this_day_name = DAY_OF_WEEK_CHOICES[this_day][1]
                    raw_street_name = ' '.join(row[day].strip().split())
                    if not regexp_alpha_check.match(raw_street_name): # common: an empty entry in the row, nothing more to do
                        continue
                    candidate_streets = Street.objects.filter(name__iexact=raw_street_name)
                    if len(candidate_streets) > 1:
                        msg = "line %s: found multiple matches for %s in the following streets, so did not update: %s\n" % (n_lines, raw_street_name, " & ".join(s.__unicode__() for s in candidate_streets))
                        log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
                    else:
                        if not candidate_streets:
                            # create a new street: TODO normalise this 
                            msg = "line %s: making a new street '%s': %s\n" % (n_lines, raw_street_name, this_day_name)
                            log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
                            slug = raw_street_name.replace(' ', '_').lower() # for now: no postcode
                            this_street = Street(name = raw_street_name, url_name = slug )
                            this_street.save()
                            n_new_streets += 1
                        else:
                            this_street = candidate_streets[0]
                            current_days = ", ".join("%s on %s" % (bc.collection_type.friendly_id, bc.get_collection_day_name()) for bc in candidate_streets[0].bin_collections.all())
                            if this_day_name != current_days: # only report updates if they changed they day
                                msg = "line %s: updated street '%s': %s on %s (was: %s)\n" % (n_lines, candidate_streets[0].url_name, this_type.friendly_id, this_day_name, current_days)
                                log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
                        this_street.add_collection(this_type, this_day)
                        n_collections += 1
            else:
                # lazy for now: the title line is "Monday,Tuesday,...,Friday"
                if len(row)>=5:
                    found_data = (row[0] == 'Monday' and row[4] == 'Friday')
                    day_number_offset = 1 # because row 0 is Monday, which is 1
        if not found_data:
            msg = "found no data in '%s'. Is there a title line with Monday,Tuesday,Wednesday... in it?\n" % csv_file_name
            log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
        else:
            msg = "lines read: %s\n" % n_lines
            log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
            msg = "bin collections loaded: %s\n" % n_collections
            log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
            msg = "new streets created: %s\n" % n_new_streets
            log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
        return log_lines

    # loads http://www.barnet.gov.uk/garden-and-kitchen-waste-collection-streets.pdf
    # after it has been converted with "pdftohtml -xml"
    @staticmethod
    def load_from_pdf_xml(xml_file_name, collection_type_id='G', want_onscreen_log=False):
        log_lines = []
        n_collections = 0
        n_new_streets = 0
        this_type = BinCollectionType.objects.get(friendly_id=collection_type_id)
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
                slug = (street_name_1 + " " + street_name_2 + " " + partial_postcode).replace(' ', '_').lower()
                day_of_week_as_number = BinCollection.day_of_week_string_to_number(day_of_week)
                checked_partial_postcode = Street.partial_postcode_parse(partial_postcode)

                if not day_of_week_as_number:
                    msg = "Can't parse day of week '%s', ignoring row '%s'\n" % (day_of_week, row)
                    log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
                elif not checked_partial_postcode:
                    msg = "Can't parse partial postcode '%s', ignoring row '%s'\n" % (partial_postcode, row)
                    log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)                    
                else:
                    # need to check for *similar* streets here: without postcode? etc.
                    (street, was_created) = Street.objects.get_or_create(
                        name = street_name_1 + ' ' + street_name_2,
                        url_name = slug,
                        partial_postcode = checked_partial_postcode,
                        )
                    if was_created:
                        n_new_streets += 1
                    # if there isn't a partial postcode... add it: don't make it a condition of the find because we don't always have one
                    street.add_collection(this_type, day_of_week_as_number)
                    n_collections += 1
        msg = "bin collections loaded: %s\n" % n_collections
        log_lines = DataImport._add_to_log_lines(log_lines, msg, want_onscreen_log)
        msg = "new streets created: %s\n" % n_new_streets
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
            sys.stderr.write(msg)
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