# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field clienti on 'UtentePrenotazioni'
        db.create_table('prenotazioni_utenteprenotazioni_clienti', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('utenteprenotazioni', models.ForeignKey(orm['prenotazioni.utenteprenotazioni'], null=False)),
            ('cliente', models.ForeignKey(orm['tam.cliente'], null=False))
        ))
        db.create_unique('prenotazioni_utenteprenotazioni_clienti', ['utenteprenotazioni_id', 'cliente_id'])


    def backwards(self, orm):
        # Removing M2M table for field clienti on 'UtentePrenotazioni'
        db.delete_table('prenotazioni_utenteprenotazioni_clienti')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'prenotazioni.prenotazione': {
            'Meta': {'ordering': "('cliente', '-data_corsa', 'owner')", 'object_name': 'Prenotazione'},
            'cliente': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tam.Cliente']"}),
            'data_corsa': ('django.db.models.fields.DateTimeField', [], {}),
            'data_registrazione': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_arrivo': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_collettivo': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'luogo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tam.Luogo']"}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'note_camera': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'note_cliente': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['prenotazioni.UtentePrenotazioni']"}),
            'pagamento': ('django.db.models.fields.CharField', [], {'default': "'D'", 'max_length': '1'}),
            'pax': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'viaggio': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tam.Viaggio']", 'unique': 'True', 'null': 'True'})
        },
        'prenotazioni.utenteprenotazioni': {
            'Meta': {'ordering': "('user',)", 'object_name': 'UtentePrenotazioni'},
            'cliente': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'unicoUtentePrenotazione'", 'to': "orm['tam.Cliente']"}),
            'clienti': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['tam.Cliente']", 'symmetrical': 'False'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'luogo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tam.Luogo']"}),
            'nome_operatore': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'prenotazioni'", 'unique': 'True', 'to': "orm['auth.User']"})
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
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'pagamento_differito': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tipo': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'tipo_commissione': ('django.db.models.fields.CharField', [], {'default': "'F'", 'max_length': '1'})
        },
        'tam.conducente': {
            'Meta': {'ordering': "['-attivo', 'nick', 'nome']", 'object_name': 'Conducente'},
            'assente': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'attivo': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'classifica_iniziale_diurni': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'}),
            'classifica_iniziale_doppiPadova': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'}),
            'classifica_iniziale_long': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'}),
            'classifica_iniziale_medium': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'}),
            'classifica_iniziale_notturni': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'}),
            'classifica_iniziale_prezzoDoppiVenezia': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'}),
            'classifica_iniziale_puntiDoppiVenezia': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'dati': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'emette_ricevute': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_persone': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'nick': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'})
        },
        'tam.listino': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Listino'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
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
            'dati': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
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
            'Meta': {'ordering': "('data_padre', 'id_padre', 'data', 'id')", 'object_name': 'Viaggio'},
            'a': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'a'", 'to': "orm['tam.Luogo']"}),
            'abbuono_fisso': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'abbuono_percentuale': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'annullato': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'data_padre': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'date_start': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2009, 1, 1, 0, 0)'}),
            'esclusivo': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'fatturazione': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'html_tragitto': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_padre': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'incassato_albergo': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_abbinata': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'is_prenotazione': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'passeggero': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tam.Passeggero']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'prezzo': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'prezzoDoppioPadova': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'prezzoPadova': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'prezzoPunti': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'prezzoVenezia': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'prezzo_finale': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'prezzo_sosta': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '9', 'decimal_places': '2'}),
            'punti_abbinata': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'punti_diurni': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '6', 'decimal_places': '2'}),
            'punti_notturni': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '6', 'decimal_places': '2'}),
            'tipo_commissione': ('django.db.models.fields.CharField', [], {'default': "'F'", 'max_length': '1'}),
            'tratta': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['tam.Tratta']", 'null': 'True', 'blank': 'True'}),
            'tratta_end': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'viaggio_end_set'", 'null': 'True', 'to': "orm['tam.Tratta']"}),
            'tratta_start': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'viaggio_start_set'", 'null': 'True', 'to': "orm['tam.Tratta']"})
        }
    }

    complete_apps = ['prenotazioni']