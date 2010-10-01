# models.py:
# Models for Bin Alerts.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

from django.db import models

class BinCollectionManager(models.Manager):
    def find_by_street_name(self, street_name):
        return self.filter(street_name__icontains=street_name)

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

class BinCollection(models.Model):
    street_name = models.CharField(max_length=200)
    street_url_name = models.CharField(max_length=200)

    collection_day = models.IntegerField(choices = DAY_OF_WEEK_CHOICES)
    collection_type = models.CharField(max_length = 10, choices = COLLECTION_TYPE_CHOICES)

    objects = BinCollectionManager()

    def __unicode__(self):
        return "%s (%s)" % (self.street_name, self.get_collection_day_display())


