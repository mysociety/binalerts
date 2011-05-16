# admin.py:
# Administration pages for Bin Alerts.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

from binalerts.models import BinCollection, BinCollectionType, Street, CollectionAlert, DataImport
from emailconfirmation.models import EmailConfirmation

from django.contrib import admin

class BinCollectionAdmin(admin.ModelAdmin):
    readonly_fields = ('last_updated',)
    list_display = ('street', 'collection_day', 'collection_type', 'last_updated')    
    list_display_links = ('street', 'collection_day', 'collection_type')
    search_fields = ['street__name']

class StreetAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'partial_postcode', 'bin_collections')
    prepopulated_fields = {"url_name": ("name","partial_postcode")} # gah! django uses - not _ for slugs
    
    def save_model(self, request, street, form, change):
        street.url_name = street.url_name.replace("-", "_") # fix hyphens from django slug magic
        street.save() # TODO: really URL name should be unqiue as a db constraint, no?

        
class DataImportAdmin(admin.ModelAdmin):
    actions = ['execute_import_data']
    list_display = ('upload_file', 'timestamp', 'implicit_collection_type', 'guess_postcodes')
         
    def execute_import_data(self, request, queryset):
        for di in queryset:
            report_lines = di.import_data() 
            self.message_user(request, "Imported data")
            for rl in report_lines:
                self.message_user(request, rl)
    execute_import_data.short_description = "Import data from file"

admin.site.register(BinCollection, BinCollectionAdmin)
admin.site.register(BinCollectionType)
admin.site.register(CollectionAlert)
admin.site.register(EmailConfirmation)
admin.site.register(Street, StreetAdmin)
admin.site.register(DataImport, DataImportAdmin)

