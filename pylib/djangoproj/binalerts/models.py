# models.py:
# Models for Bin Alerts.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

import datetime
import sys
import xml.dom.minidom
import re

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
        return "%s, %s" % (self.name, self.partial_postcode)

class BinCollectionManager(models.Manager):
    def find_by_street_name(self, street_name):
        return self.filter(street__name__icontains=street_name)                    
        
    # Convert from day of week string e.g. Sunday, to number, e.g. 0
    def day_of_week_string_to_number(self, day_of_week):
        for row in DAY_OF_WEEK_CHOICES:
            if row[1] == day_of_week:
                return row[0]
        return None

    # Check it is a partial postcode, e.g. EN4
    def partial_postcode_parse(self, partial_postcode):
        if re.match("[A-Z]+[0-9]+$", partial_postcode):
            return partial_postcode
        return None

    # PDF loading, internal functions

    def _get_text_from_node(self, nodelist):
        rc = ""
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc = rc + node.data
            elif node.nodeType == node.ELEMENT_NODE:
                if node.nodeName == 'b':
                    rc = rc + self._get_text_from_node(node.childNodes)
                else:
                    raise Exception("unfinished")
            else:
                raise Exception("unfinished")
        return rc

    # joins together items which are vertically wrapped but in the same table cell
    def _yield_cells(self, nodes):
        cell_text = ""
        last_top = None
        last_left = None
        for node in nodes:
            top = int(node.getAttribute('top'))
            left = int(node.getAttribute('left'))
            text = self._get_text_from_node(node.childNodes).strip()

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
    def _yield_rows_from_pdf(self, doc):
        items = []
        last_top = None
        last_left = None
        nodes = doc.getElementsByTagName('text').__iter__()
        for text, top, left in self._yield_cells(nodes):
            if top != last_top and items != []:
                yield items
                items = []

            items.append(text)

            last_top = top
            last_left = left
        if items != []:
            yield items

    # loads http://www.barnet.gov.uk/garden-and-kitchen-waste-collection-streets.pdf
    # after it has been converted with "pdftohtml -xml"
    def load_from_pdf_xml(self, xml_file_name, collection_type_id='G'):
        doc = xml.dom.minidom.parse(xml_file_name)

        this_type = BinCollectionType.objects.get(friendly_id=collection_type_id)
        
        rows = self._yield_rows_from_pdf(doc)
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
                day_of_week_as_number = self.day_of_week_string_to_number(day_of_week)
                checked_partial_postcode = self.partial_postcode_parse(partial_postcode)

                if not day_of_week_as_number:
                    sys.stderr.write("Can't parse day of week '%s', ignoring row '%s'\n" % (day_of_week, row))
                elif not checked_partial_postcode:
                    sys.stderr.write("Can't parse partial postcode '%s', ignoring row '%s'\n" % (partial_postcode, row))
                else:
                    (street, was_created) = Street.objects.get_or_create(
                        name = street_name_1 + ' ' + street_name_2,
                        url_name = slug,
                        partial_postcode = checked_partial_postcode,
                        )
                    street.add_collection(this_type, day_of_week_as_number)

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

