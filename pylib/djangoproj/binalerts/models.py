# models.py:
# Models for Bin Alerts.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

from django.db import models

class BinCollectionManager(models.Manager):
    def find_by_street_name(self, street_name):
        return self.filter(street_name__icontains=street_name)

class BinCollection(models.Model):
    street_name = models.CharField(max_length=200)
    street_url_name = models.CharField(max_length=200)

    objects = BinCollectionManager()

    def __unicode__(self):
        return self.street_name


