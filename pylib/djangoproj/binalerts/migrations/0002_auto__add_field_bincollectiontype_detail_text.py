# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'BinCollectionType.detail_text'
        db.add_column('binalerts_bincollectiontype', 'detail_text', self.gf('django.db.models.fields.TextField')(default='', max_length=1024, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'BinCollectionType.detail_text'
        db.delete_column('binalerts_bincollectiontype', 'detail_text')


    models = {
        'binalerts.bincollection': {
            'Meta': {'object_name': 'BinCollection'},
            'collection_day': ('django.db.models.fields.IntegerField', [], {}),
            'collection_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['binalerts.BinCollectionType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'street': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bin_collections'", 'to': "orm['binalerts.Street']"})
        },
        'binalerts.bincollectiontype': {
            'Meta': {'object_name': 'BinCollectionType'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'detail_text': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'friendly_id': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'binalerts.collectionalert': {
            'Meta': {'ordering': "('email',)", 'object_name': 'CollectionAlert'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_checked_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2000, 1, 1)'}),
            'street': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['binalerts.Street']", 'null': 'True'})
        },
        'binalerts.street': {
            'Meta': {'object_name': 'Street'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'partial_postcode': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'url_name': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'emailconfirmation.emailconfirmation': {
            'Meta': {'object_name': 'EmailConfirmation'},
            'confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'page_after': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['binalerts']
