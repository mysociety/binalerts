
from south.db import db
from django.db import models
from djangoproj.binalerts.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'BinCollection.street_partial_postcode'
        db.add_column('binalerts_bincollection', 'street_partial_postcode', models.fields.CharField(max_length=5, default='XX0'),keep_default=False)
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'BinCollection.street_partial_postcode'
        db.delete_column('binalerts_bincollection', 'street_partial_postcode')
        
    
    
    models = {
        'binalerts.bincollection': {
            'collection_day': ('django.db.models.fields.IntegerField', [], {}),
            'collection_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'street_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'street_partial_postcode': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'street_url_name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }
    
    complete_apps = ['binalerts']
