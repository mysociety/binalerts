# admin.py:
# Administration pages for Bin Alerts.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

from binalerts.models import BinCollection, BinCollectionType, Street, CollectionAlert
from emailconfirmation.models import EmailConfirmation

from django.contrib import admin

admin.site.register(BinCollection)
admin.site.register(BinCollectionType)
admin.site.register(CollectionAlert)
admin.site.register(EmailConfirmation)
admin.site.register(Street)


