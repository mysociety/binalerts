
from south.db import db
from django.db import models
from djangoproj.binalerts.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'CollectionAlert'
        db.create_table('binalerts_collectionalert', (
            ('id', orm['binalerts.collectionalert:id']),
            ('email', orm['binalerts.collectionalert:email']),
            ('street_url_name', orm['binalerts.collectionalert:street_url_name']),
            ('last_checked_date', orm['binalerts.collectionalert:last_checked_date']),
        ))
        db.send_create_signal('binalerts', ['CollectionAlert'])
        
        # Changing field 'BinCollection.street_url_name'
        # (to signature: django.db.models.fields.SlugField(max_length=50, db_index=True))
        db.alter_column('binalerts_bincollection', 'street_url_name', orm['binalerts.bincollection:street_url_name'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'CollectionAlert'
        db.delete_table('binalerts_collectionalert')
        
        # Changing field 'BinCollection.street_url_name'
        # (to signature: django.db.models.fields.CharField(max_length=200))
        db.alter_column('binalerts_bincollection', 'street_url_name', orm['binalerts.bincollection:street_url_name'])
        
    
    
    models = {
        'binalerts.bincollection': {
            'collection_day': ('django.db.models.fields.IntegerField', [], {}),
            'collection_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'street_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'street_partial_postcode': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'street_url_name': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'binalerts.collectionalert': {
            'confirmed': ('django.contrib.contenttypes.generic.GenericRelation', [], {'to': "orm['emailconfirmation.EmailConfirmation']"}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_checked_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2000, 1, 1)'}),
            'street_url_name': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'emailconfirmation.emailconfirmation': {
            'confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'page_after': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }
    
    complete_apps = ['binalerts']
