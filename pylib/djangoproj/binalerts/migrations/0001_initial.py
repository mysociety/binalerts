
from south.db import db
from django.db import models
from djangoproj.binalerts.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'BinCollection'
        db.create_table('binalerts_bincollection', (
            ('id', orm['binalerts.BinCollection:id']),
        ))
        db.send_create_signal('binalerts', ['BinCollection'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'BinCollection'
        db.delete_table('binalerts_bincollection')
        
    
    
    models = {
        'binalerts.bincollection': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }
    
    complete_apps = ['binalerts']
