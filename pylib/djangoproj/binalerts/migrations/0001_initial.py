# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'BinCollectionType'
        db.create_table('binalerts_bincollectiontype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('friendly_id', self.gf('django.db.models.fields.CharField')(max_length=4)),
        ))
        db.send_create_signal('binalerts', ['BinCollectionType'])

        # Adding model 'Street'
        db.create_table('binalerts_street', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('url_name', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('partial_postcode', self.gf('django.db.models.fields.CharField')(max_length=5)),
        ))
        db.send_create_signal('binalerts', ['Street'])

        # Adding model 'BinCollection'
        db.create_table('binalerts_bincollection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('street', self.gf('django.db.models.fields.related.ForeignKey')(related_name='bin_collections', to=orm['binalerts.Street'])),
            ('collection_day', self.gf('django.db.models.fields.IntegerField')()),
            ('collection_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['binalerts.BinCollectionType'])),
        ))
        db.send_create_signal('binalerts', ['BinCollection'])

        # Adding model 'CollectionAlert'
        db.create_table('binalerts_collectionalert', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('street', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['binalerts.Street'], null=True)),
            ('last_checked_date', self.gf('django.db.models.fields.DateField')(default=datetime.date(2000, 1, 1))),
        ))
        db.send_create_signal('binalerts', ['CollectionAlert'])


    def backwards(self, orm):
        
        # Deleting model 'BinCollectionType'
        db.delete_table('binalerts_bincollectiontype')

        # Deleting model 'Street'
        db.delete_table('binalerts_street')

        # Deleting model 'BinCollection'
        db.delete_table('binalerts_bincollection')

        # Deleting model 'CollectionAlert'
        db.delete_table('binalerts_collectionalert')


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
