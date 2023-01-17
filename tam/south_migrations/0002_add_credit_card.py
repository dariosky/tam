# coding: utf-8

from south.db import db
from django.db import models
from tam.models import *


class Migration:
    def forwards(self, orm):

        # Adding field 'Viaggio.cartaDiCredito'
        db.add_column(
            "tam_viaggio", "cartaDiCredito", orm["tam.viaggio:cartaDiCredito"]
        )

    def backwards(self, orm):

        # Deleting field 'Viaggio.cartaDiCredito'
        db.delete_column("tam_viaggio", "cartaDiCredito")

    models = {
        "auth.group": {
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "name": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "80"},
            ),
            "permissions": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {"to": "orm['auth.Permission']", "blank": "True"},
            ),
        },
        "auth.permission": {
            "Meta": {"unique_together": "(('content_type', 'codename'),)"},
            "codename": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "content_type": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['contenttypes.ContentType']"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "name": ("django.db.models.fields.CharField", [], {"max_length": "50"}),
        },
        "auth.user": {
            "date_joined": (
                "django.db.models.fields.DateTimeField",
                [],
                {"default": "datetime.datetime.now"},
            ),
            "email": (
                "django.db.models.fields.EmailField",
                [],
                {"max_length": "75", "blank": "True"},
            ),
            "first_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "30", "blank": "True"},
            ),
            "groups": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {"to": "orm['auth.Group']", "blank": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "is_active": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "blank": "True"},
            ),
            "is_staff": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "is_superuser": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "last_login": (
                "django.db.models.fields.DateTimeField",
                [],
                {"default": "datetime.datetime.now"},
            ),
            "last_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "30", "blank": "True"},
            ),
            "password": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "128"},
            ),
            "user_permissions": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {"to": "orm['auth.Permission']", "blank": "True"},
            ),
            "username": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "30"},
            ),
        },
        "contenttypes.contenttype": {
            "Meta": {
                "unique_together": "(('app_label', 'model'),)",
                "db_table": "'django_content_type'",
            },
            "app_label": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "model": ("django.db.models.fields.CharField", [], {"max_length": "100"}),
            "name": ("django.db.models.fields.CharField", [], {"max_length": "100"}),
        },
        "tam.actionlog": {
            "action_type": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "1"},
            ),
            "content_type": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['contenttypes.ContentType']"},
            ),
            "data": ("django.db.models.fields.DateTimeField", [], {}),
            "description": ("django.db.models.fields.TextField", [], {"blank": "True"}),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "object_id": ("django.db.models.fields.PositiveIntegerField", [], {}),
            "user": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['auth.User']"},
            ),
        },
        "tam.bacino": {
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "nome": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "20"},
            ),
        },
        "tam.cliente": {
            "attivo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "blank": "True"},
            ),
            "commissione": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "dati": (
                "django.db.models.fields.TextField",
                [],
                {"null": "True", "blank": "True"},
            ),
            "fatturazione": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "incassato_albergo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "listino": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Listino']", "null": "True", "blank": "True"},
            ),
            "nome": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "40"},
            ),
            "pagamento_differito": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "tipo": ("django.db.models.fields.CharField", [], {"max_length": "1"}),
            "tipo_commissione": (
                "django.db.models.fields.CharField",
                [],
                {"default": "'F'", "max_length": "1"},
            ),
        },
        "tam.conducente": {
            "assente": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "attivo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "blank": "True"},
            ),
            "classifica_iniziale_diurni": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "classifica_iniziale_doppiPadova": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "classifica_iniziale_long": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "classifica_iniziale_medium": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "classifica_iniziale_notturni": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "classifica_iniziale_prezzoDoppiVenezia": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "classifica_iniziale_puntiDoppiVenezia": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "max_persone": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "4"},
            ),
            "nick": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "5", "null": "True", "blank": "True"},
            ),
            "nome": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "40"},
            ),
        },
        "tam.conguaglio": {
            "conducente": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Conducente']"},
            ),
            "dare": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "10", "max_digits": "9", "decimal_places": "2"},
            ),
            "data": (
                "django.db.models.fields.DateTimeField",
                [],
                {"auto_now": "True", "blank": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
        },
        "tam.ferie": {
            "conducente": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Conducente']"},
            ),
            "data_fine": ("django.db.models.fields.DateTimeField", [], {}),
            "data_inizio": ("django.db.models.fields.DateTimeField", [], {}),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
        },
        "tam.listino": {
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "nome": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "20"},
            ),
        },
        "tam.luogo": {
            "bacino": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Bacino']", "null": "True", "blank": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "nome": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "25"},
            ),
        },
        "tam.passeggero": {
            "dati": ("django.db.models.fields.TextField", [], {"null": "True"}),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "nome": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "40"},
            ),
        },
        "tam.prezzolistino": {
            "Meta": {
                "unique_together": "(('listino', 'tratta', 'tipo_servizio', 'max_pax'),)"
            },
            "commissione": (
                "django.db.models.fields.DecimalField",
                [],
                {
                    "default": "0",
                    "null": "True",
                    "max_digits": "9",
                    "decimal_places": "2",
                },
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "listino": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Listino']"},
            ),
            "max_pax": ("django.db.models.fields.IntegerField", [], {"default": "4"}),
            "prezzo_diurno": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "10", "max_digits": "9", "decimal_places": "2"},
            ),
            "prezzo_notturno": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "10", "max_digits": "9", "decimal_places": "2"},
            ),
            "tipo_commissione": (
                "django.db.models.fields.CharField",
                [],
                {"default": "'F'", "max_length": "1"},
            ),
            "tipo_servizio": (
                "django.db.models.fields.CharField",
                [],
                {"default": "'T'", "max_length": "1"},
            ),
            "tratta": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Tratta']"},
            ),
            "ultima_modifica": (
                "django.db.models.fields.DateField",
                [],
                {"auto_now": "True", "blank": "True"},
            ),
        },
        "tam.profiloutente": {
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "luogo": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Luogo']", "null": "True", "blank": "True"},
            ),
            "user": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['auth.User']", "unique": "True"},
            ),
        },
        "tam.tamlicense": {
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "license": ("django.db.models.fields.TextField", [], {}),
        },
        "tam.tratta": {
            "Meta": {"unique_together": "(('da', 'a'),)"},
            "a": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"related_name": "'tempo_a'", "to": "orm['tam.Luogo']"},
            ),
            "costo_autostrada": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "da": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"related_name": "'tempo_da'", "to": "orm['tam.Luogo']"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "km": ("django.db.models.fields.IntegerField", [], {"default": "0"}),
            "minuti": ("django.db.models.fields.IntegerField", [], {"default": "0"}),
        },
        "tam.viaggio": {
            "a": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"related_name": "'a'", "to": "orm['tam.Luogo']"},
            ),
            "abbuono_fisso": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "abbuono_percentuale": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "arrivo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "blank": "True"},
            ),
            "cartaDiCredito": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "cliente": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Cliente']", "null": "True", "blank": "True"},
            ),
            "commissione": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "conducente": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Conducente']", "null": "True", "blank": "True"},
            ),
            "conducente_confermato": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "conducente_richiesto": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "costo_autostrada": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "costo_sosta": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "da": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"related_name": "'da'", "to": "orm['tam.Luogo']"},
            ),
            "data": ("django.db.models.fields.DateTimeField", [], {}),
            "date_start": (
                "django.db.models.fields.DateTimeField",
                [],
                {"default": "datetime.datetime(2009, 1, 1, 0, 0)"},
            ),
            "esclusivo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "blank": "True"},
            ),
            "fatturazione": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "html_tragitto": (
                "django.db.models.fields.TextField",
                [],
                {"blank": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "incassato_albergo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "is_abbinata": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "1", "null": "True", "blank": "True"},
            ),
            "is_valid": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "blank": "True"},
            ),
            "km": ("django.db.models.fields.IntegerField", [], {"default": "0"}),
            "km_conguagliati": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0", "null": "True", "blank": "True"},
            ),
            "luogoDiRiferimento": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "related_name": "'riferimento'",
                    "null": "True",
                    "to": "orm['tam.Luogo']",
                },
            ),
            "note": ("django.db.models.fields.TextField", [], {"blank": "True"}),
            "numero_passeggeri": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "1"},
            ),
            "numero_pratica": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "20", "null": "True", "blank": "True"},
            ),
            "padre": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Viaggio']", "null": "True", "blank": "True"},
            ),
            "pagamento_differito": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "pagato": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "passeggero": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Passeggero']", "null": "True", "blank": "True"},
            ),
            "prezzo": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "prezzoDoppioPadova": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "prezzoPadova": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "prezzoPunti": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "prezzoVenezia": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "prezzo_finale": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "prezzo_sosta": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "punti_abbinata": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "punti_diurni": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "punti_notturni": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "tipo_commissione": (
                "django.db.models.fields.CharField",
                [],
                {"default": "'F'", "max_length": "1"},
            ),
            "tratta": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "default": "None",
                    "to": "orm['tam.Tratta']",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "tratta_end": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "blank": "True",
                    "related_name": "'viaggio_end_set'",
                    "null": "True",
                    "to": "orm['tam.Tratta']",
                },
            ),
            "tratta_start": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "blank": "True",
                    "related_name": "'viaggio_start_set'",
                    "null": "True",
                    "to": "orm['tam.Tratta']",
                },
            ),
        },
    }

    complete_apps = ["tam"]
