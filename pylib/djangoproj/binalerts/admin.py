# admin.py:
# Administration pages for Bin Alerts.
#
# Copyright (c) 2011 UK Citizens Online Democracy. All rights reserved.
# Email: duncan@mysociety.org; WWW: http://www.mysociety.org/

from django.contrib import admin
from django.contrib.contenttypes.generic import GenericTabularInline

from binalerts.models import BinCollection, BinCollectionType, Street, CollectionAlert, DataImport
from emailconfirmation.models import EmailConfirmation

class BinCollectionAdmin(admin.ModelAdmin):
    readonly_fields = ('last_updated',)
    list_display = ('street', 'collection_day', 'collection_type', 'last_updated')
    list_editable = ('collection_day',)
    list_display_links = ('street',)
    list_filter = ('collection_day', 'collection_type')
    search_fields = ('street__name',)
        
class StreetAdmin(admin.ModelAdmin):
    search_fields = ('name', 'partial_postcode')
    fields = ('name', 'partial_postcode', 'url_name')
    list_display = ('name', 'partial_postcode', 'url_name')
    prepopulated_fields = {"url_name": ("name","partial_postcode")} # gah! django uses - not _ for slugs

    def save_model(self, request, street, form, change):
        street.url_name = street.url_name.replace("-", "_") # fix hyphens from django slug magic
        street.save() # TODO: really URL name should be unique as a db constraint, no?

        
class DataImportAdmin(admin.ModelAdmin):
    actions = ('execute_import_data',)
    list_display = ('upload_file', 'timestamp', 'implicit_collection_type', 'guess_postcodes')

    # for historic (Barnet) reasons, hardwire implicit collection types for now: use can always override
    # and these really ought to be coming out of config
    # But it's best to do it here, not in the model, so the implicit type is shown clearly in the admin listing
    # If the incoming files contain clear collection types then it would be OK for implicit_collection_type to stay as None
    def save_model(self, request, obj, form, change):
        if not obj.implicit_collection_type:
            default_type_id = None
            if obj.upload_file.name.endswith('.csv'):
                default_type_id = 'D'
            elif obj.upload_file.name.endswith('.xml'):
                default_type_id = 'G'
            if default_type_id:
                obj.implicit_collection_type = BinCollectionType.objects.get(friendly_id=default_type_id)
                self.message_user(request, "*%s file automatically assumed to be for %s" % (obj.upload_file.name[-4:], obj.implicit_collection_type))
        obj.save()
         
    def execute_import_data(self, request, queryset):
        for di in queryset:
            report_lines = di.import_data() 
            self.message_user(request, "Imported data")
            for rl in report_lines:
                self.message_user(request, rl)
    execute_import_data.short_description = "Import data from file"

class EmailConfirmationInline(GenericTabularInline):
    model = EmailConfirmation
    extra = 1
    max_num = 1
    can_delete = False
    fields = ('confirmed',)

class CollectionAlertAdmin(admin.ModelAdmin):
    inlines = (EmailConfirmationInline,)
    list_display = ('email', 'street', 'is_confirmed')
    search_fields = ('email', 'street__name')
    readonly_fields = ('last_checked_date', 'last_sent_date')

class CollectionTypeAdmin(admin.ModelAdmin):
    list_display = ('description', 'friendly_id', 'detail_text')

admin.site.register(CollectionAlert, CollectionAlertAdmin)
admin.site.register(BinCollection, BinCollectionAdmin)
admin.site.register(BinCollectionType, CollectionTypeAdmin)
admin.site.register(Street, StreetAdmin)
admin.site.register(DataImport, DataImportAdmin)

