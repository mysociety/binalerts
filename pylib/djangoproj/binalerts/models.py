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

    # Convert from day of week string e.g. Sunday, to number, e.g. 0
    def day_of_week_string_to_number(self, day_of_week):
        for row in DAY_OF_WEEK_CHOICES:
            if row[1] == day_of_week:
                return row[0]
        raise Exception("Unknown day of week string '%s'" % day_of_week)

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

    # Works out what a row in the table is, and yields each one. A row is
    # just items which are lined up vertically.
    def _yield_rows_from_pdf(self, doc):
        items = []
        last_top = None
        for node in doc.getElementsByTagName('text'):
            top = int(node.getAttribute('top'))

            if top != last_top and items != []:
                yield items
                items = []

            text = self._get_text_from_node(node.childNodes).strip()
            items.append(text)
            last_top = top
        if items != []:
            yield items

    # loads http://www.barnet.gov.uk/garden-and-kitchen-waste-collection-streets.pdf
    # after it has been converted with "pdftohtml -xml"
    def load_from_pdf_xml(self, xml_file_name):
        doc = xml.dom.minidom.parse(xml_file_name)

        rows = self._yield_rows_from_pdf(doc)
        started = False
        for row in rows:
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
                for column in row:
                    print column + ",",
                print
                (street_name_1, street_name_2, partial_postcode, day_of_week) = row
                slug = (street_name_1 + " " + street_name_2 + " " + partial_postcode).replace(' ', '_').lower()
                bin_collection = BinCollection(
                        street_name = street_name_1 + ' ' + street_name_2,
                        street_url_name = slug, 
                        street_partial_postcode = partial_postcode,
                        collection_day = self.day_of_week_string_to_number(day_of_week)
                )
                bin_collection.save()



class BinCollection(models.Model):
    street_name = models.CharField(max_length=200)
    street_url_name = models.SlugField(max_length=50)
    street_partial_postcode = models.CharField(max_length=5) # e.g. NW4

    collection_day = models.IntegerField(choices = DAY_OF_WEEK_CHOICES)
    collection_type = models.CharField(max_length = 10, choices = COLLECTION_TYPE_CHOICES)

    objects = BinCollectionManager()

    def __unicode__(self):
        return "%s %s (%s)" % (self.street_name, self.street_partial_postcode, self.get_collection_day_display())


