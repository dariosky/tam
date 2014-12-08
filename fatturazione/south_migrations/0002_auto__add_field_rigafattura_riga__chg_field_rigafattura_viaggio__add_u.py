# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'RigaFattura.riga'
        db.add_column('fatturazione_rigafattura', 'riga', self.gf('django.db.models.fields.IntegerField')(default=1), keep_default=False)

        # Changing field 'RigaFattura.viaggio'
        db.alter_column('fatturazione_rigafattura', 'viaggio_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['tam.Viaggio']))

        # Adding unique constraint on 'RigaFattura', fields ['viaggio']
        db.create_unique('fatturazione_rigafattura', ['viaggio_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'RigaFattura', fields ['viaggio']
        db.delete_unique('fatturazione_rigafattura', ['viaggio_id'])

        # Deleting field 'RigaFattura.riga'
        db.delete_column('fatturazione_rigafattura', 'riga')

        # Changing field 'RigaFattura.viaggio'
        db.alter_column('fatturazione_rigafattura', 'viaggio_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['tam.Viaggio']))


    models = {
        'fatturazione.fattura': {
            'Meta': {'ordering': "('anno', 'progressivo')", 'object_name': 'Fattura'},
            'anno': ('django.db.models.fields.IntegerField', [], {}),
            'data': ('django.db.models.fields.DateField', [], {}),
            'emessa_a': ('django.db.models.fields.TextField', [], {}),
            'emessa_da': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {}),
            'progressivo': ('django.db.models.fields.IntegerField', [], {}),
            'tipo': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'fatturazione.rigafattura': {
            'Meta': {'ordering': "('fattura', 'riga')", 'object_name': 'RigaFattura'},
            'descrizione': ('django.db.models.fields.TextField', [], {}),
            'fattura': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'righe'", 'to': "orm['fatturazione.Fattura']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iva': ('django.db.models.fields.IntegerField', [], {}),
            'note': ('django.db.models.fields.TextField', [], {}),
            'prezzo': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'qta': ('django.db.models.fields.IntegerField', [], {}),
            'riga': ('django.db.models.fields.IntegerField', [], {}),
            'viaggio': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'riga_fattura'", 'unique': 'True', 'null': 'True', 'to': "orm['tam.Viaggio']"})
        },
        'tam.bacino': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Bacino'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'tam.cliente': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Cliente'},
            'attivo': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'commissione': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'dati': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'fatturazione': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incassato_albergo': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'listino': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tam.Listino']", 'null': 'True', 'blank': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'pagamento_differito': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tipo': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'tipo_commissione': ('django.db.models.fields.CharField', [], {'default': "'F'", 'max_length': '1'})
        },
        'tam.conducente': {
            'Meta': {'ordering': "['-attivo', 'nick', 'nome']", 'object_name': 'Conducente'},
            'assente': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'attivo': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'classifica_iniziale_diurni': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'classifica_iniziale_doppiPadova': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'classifica_iniziale_long': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'classifica_iniziale_medium': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'classifica_iniziale_notturni': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'classifica_iniziale_prezzoDoppiVenezia': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'classifica_iniziale_puntiDoppiVenezia': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_persone': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'nick': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'})
        },
        'tam.listino': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Listino'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'tam.luogo': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Luogo'},
            'bacino': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tam.Bacino']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'}),
            'speciale': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1'})
        },
        'tam.passeggero': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Passeggero'},
            'dati': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'})
        },
        'tam.tratta': {
            'Meta': {'ordering': "['da', 'a']", 'unique_together': "(('da', 'a'),)", 'object_name': 'Tratta'},
            'a': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tempo_a'", 'to': "orm['tam.Luogo']"}),
            'costo_autostrada': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'da': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tempo_da'", 'to': "orm['tam.Luogo']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'km': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'minuti': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'tam.viaggio': {
            'Meta': {'ordering': "('data',)", 'object_name': 'Viaggio'},
            'a': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'a'", 'to': "orm['tam.Luogo']"}),
            'abbuono_fisso': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'abbuono_percentuale': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'arrivo': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cartaDiCredito': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cliente': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tam.Cliente']", 'null': 'True', 'blank': 'True'}),
            'commissione': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'conducente': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tam.Conducente']", 'null': 'True', 'blank': 'True'}),
            'conducente_confermato': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'conducente_richiesto': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'costo_autostrada': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'costo_sosta': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'da': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'da'", 'to': "orm['tam.Luogo']"}),
            'data': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'date_start': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 1, 1, 0, 0)'}),
            'esclusivo': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'fatturazione': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'html_tragitto': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incassato_albergo': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_abbinata': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'is_valid': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'km': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'km_conguagliati': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'luogoDiRiferimento': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'riferimento'", 'null': 'True', 'to': "orm['tam.Luogo']"}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'numero_passeggeri': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'numero_pratica': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'padre': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tam.Viaggio']", 'null': 'True', 'blank': 'True'}),
            'pagamento_differito': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pagato': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'passeggero': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tam.Passeggero']", 'null': 'True', 'blank': 'True'}),
            'prezzo': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'prezzoDoppioPadova': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'prezzoPadova': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'prezzoPunti': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'prezzoVenezia': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'prezzo_finale': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'prezzo_sosta': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'punti_abbinata': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'punti_diurni': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'punti_notturni': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tipo_commissione': ('django.db.models.fields.CharField', [], {'default': "'F'", 'max_length': '1'}),
            'tratta': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['tam.Tratta']", 'null': 'True', 'blank': 'True'}),
            'tratta_end': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'viaggio_end_set'", 'null': 'True', 'to': "orm['tam.Tratta']"}),
            'tratta_start': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'viaggio_start_set'", 'null': 'True', 'to': "orm['tam.Tratta']"})
        }
    }

    complete_apps = ['fatturazione']
