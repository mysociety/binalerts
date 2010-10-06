# models.py:
# Models for Bin Alerts.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

from django.db import models
import xml.dom.minidom

DAY_OF_WEEK_CHOICES = (
    (0, 'Sunday'),
    (1, 'Monday'),
    (2, 'Tuesday'),
    (3, 'Wednesday'),
    (4, 'Thursday'),
    (5, 'Friday'),
    (6, 'Saturday')
)

COLLECTION_TYPE_CHOICES = (
    ('G', 'Green Garden and Kitchen Waste'),
)

class BinCollectionManager(models.Manager):
    def find_by_street_name(self, street_name):
        return self.filter(street_name__icontains=street_name)

    # loads http://www.barnet.gov.uk/garden-and-kitchen-waste-collection-streets.pdf
    # after it has been converted with "pdftohtml -xml"
    def load_from_pdf_xml(self, xml_file_name):
        doc = xml.dom.minidom.parse(xml_file_name)
        for node in doc.getElementsByTagName('text'):
            top = node.getAttribute['top']
            text = " ".join([ c.data for c in text.childNodes ])
            print text

class BinCollection(models.Model):
    street_name = models.CharField(max_length=200)
    street_url_name = models.CharField(max_length=200)
    street_partial_postcode = models.CharField(max_length=5) # e.g. NW4

    collection_day = models.IntegerField(choices = DAY_OF_WEEK_CHOICES)
    collection_type = models.CharField(max_length = 10, choices = COLLECTION_TYPE_CHOICES)


    objects = BinCollectionManager()

    def __unicode__(self):
        return "%s %s (%s)" % (self.street_name, self.street_partial_postcode, self.get_collection_day_display())


