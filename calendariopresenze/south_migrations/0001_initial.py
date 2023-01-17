# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding model 'Calendar'
        db.create_table(
            "calendariopresenze_calendar",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "conducente",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["tam.Conducente"]
                    ),
                ),
                ("date_start", self.gf("django.db.models.fields.DateTimeField")()),
                ("date_end", self.gf("django.db.models.fields.DateTimeField")()),
                ("hours", self.gf("django.db.models.fields.IntegerField")()),
                ("type", self.gf("django.db.models.fields.IntegerField")()),
                (
                    "available",
                    self.gf("django.db.models.fields.BooleanField")(default=False),
                ),
            ),
        )
        db.send_create_signal("calendariopresenze", ["Calendar"])

    def backwards(self, orm):
        # Deleting model 'Calendar'
        db.delete_table("calendariopresenze_calendar")

    models = {
        "calendariopresenze.calendar": {
            "Meta": {"object_name": "Calendar"},
            "available": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "conducente": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Conducente']"},
            ),
            "date_end": ("django.db.models.fields.DateTimeField", [], {}),
            "date_start": ("django.db.models.fields.DateTimeField", [], {}),
            "hours": ("django.db.models.fields.IntegerField", [], {}),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "type": ("django.db.models.fields.IntegerField", [], {}),
        },
        "tam.conducente": {
            "Meta": {
                "ordering": "['-attivo', 'nick', 'nome']",
                "object_name": "Conducente",
            },
            "assente": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "attivo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "db_index": "True"},
            ),
            "classifica_iniziale_diurni": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "12", "decimal_places": "2"},
            ),
            "classifica_iniziale_doppiPadova": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "12", "decimal_places": "2"},
            ),
            "classifica_iniziale_long": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "12", "decimal_places": "2"},
            ),
            "classifica_iniziale_medium": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "12", "decimal_places": "2"},
            ),
            "classifica_iniziale_notturni": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "12", "decimal_places": "2"},
            ),
            "classifica_iniziale_prezzoDoppiVenezia": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "12", "decimal_places": "2"},
            ),
            "classifica_iniziale_puntiDoppiVenezia": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "dati": (
                "django.db.models.fields.TextField",
                [],
                {"null": "True", "blank": "True"},
            ),
            "emette_ricevute": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
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
    }

    complete_apps = ["calendariopresenze"]
