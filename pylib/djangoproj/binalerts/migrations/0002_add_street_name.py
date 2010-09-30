
from south.db import db
from django.db import models
from djangoproj.binalerts.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'BinCollection.street_name'
        db.add_column('binalerts_bincollection', 'street_name', orm['binalerts.bincollection:street_name'])
        
        # Adding field 'BinCollection.street_url_name'
        db.add_column('binalerts_bincollection', 'street_url_name', orm['binalerts.bincollection:street_url_name'])
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'BinCollection.street_name'
        db.delete_column('binalerts_bincollection', 'street_name')
        
        # Deleting field 'BinCollection.street_url_name'
        db.delete_column('binalerts_bincollection', 'street_url_name')
        
    
    
    models = {
        'binalerts.bincollection': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'street_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'street_url_name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }
    
    complete_apps = ['binalerts']
