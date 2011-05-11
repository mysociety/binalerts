# admin.py:
# Administration pages for Bin Alerts.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

from binalerts.models import BinCollection, BinCollectionType, Street, CollectionAlert
from emailconfirmation.models import EmailConfirmation

from django.contrib import admin

class BinCollectionAdmin(admin.ModelAdmin):
    readonly_fields = ('last_updated',)
    list_display = ('street', 'collection_day', 'collection_type', 'last_updated')    
    list_display_links = ('street', 'collection_day', 'collection_type')
    search_fields = ['street__name']

class StreetAdmin(admin.ModelAdmin):
    search_fields = ['name']

admin.site.register(BinCollection, BinCollectionAdmin)
admin.site.register(BinCollectionType)
admin.site.register(CollectionAlert)
admin.site.register(EmailConfirmation)
admin.site.register(Street, StreetAdmin)


