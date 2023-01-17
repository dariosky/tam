# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding model 'ViaggioArchive'
        db.create_table(
            "tamArchive_viaggioarchive",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "data",
                    self.gf("django.db.models.fields.DateTimeField")(db_index=True),
                ),
                ("da", self.gf("django.db.models.fields.CharField")(max_length=25)),
                ("a", self.gf("django.db.models.fields.CharField")(max_length=25)),
                ("path", self.gf("django.db.models.fields.TextField")(blank=True)),
                ("pax", self.gf("django.db.models.fields.IntegerField")(default=1)),
                (
                    "flag_esclusivo",
                    self.gf("django.db.models.fields.BooleanField")(default=True),
                ),
                (
                    "conducente",
                    self.gf("django.db.models.fields.CharField")(
                        db_index=True, max_length=5, null=True, blank=True
                    ),
                ),
                (
                    "flag_richiesto",
                    self.gf("django.db.models.fields.BooleanField")(default=False),
                ),
                (
                    "cliente",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=40, null=True
                    ),
                ),
                (
                    "prezzo",
                    self.gf("django.db.models.fields.DecimalField")(
                        default=0, max_digits=9, decimal_places=2
                    ),
                ),
                (
                    "prezzo_detail",
                    self.gf("django.db.models.fields.TextField")(blank=True),
                ),
                (
                    "flag_fineMese",
                    self.gf("django.db.models.fields.BooleanField")(default=False),
                ),
                (
                    "flag_fatturazione",
                    self.gf("django.db.models.fields.BooleanField")(default=False),
                ),
                (
                    "flag_cartaDiCredito",
                    self.gf("django.db.models.fields.BooleanField")(default=False),
                ),
                (
                    "flag_pagamentoDifferito",
                    self.gf("django.db.models.fields.BooleanField")(default=False),
                ),
                (
                    "numero_pratica",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=20, null=True, blank=True
                    ),
                ),
                (
                    "flag_arrivo",
                    self.gf("django.db.models.fields.BooleanField")(default=True),
                ),
                (
                    "punti_abbinata",
                    self.gf("django.db.models.fields.IntegerField")(default=0),
                ),
                ("note", self.gf("django.db.models.fields.TextField")(blank=True)),
                (
                    "padre",
                    self.gf("django.db.models.fields.related.ForeignKey")(
                        to=orm["tamArchive.ViaggioArchive"], null=True, blank=True
                    ),
                ),
            ),
        )
        db.send_create_signal("tamArchive", ["ViaggioArchive"])

    def backwards(self, orm):
        # Deleting model 'ViaggioArchive'
        db.delete_table("tamArchive_viaggioarchive")

    models = {
        "tamArchive.viaggioarchive": {
            "Meta": {"ordering": "['data']", "object_name": "ViaggioArchive"},
            "a": ("django.db.models.fields.CharField", [], {"max_length": "25"}),
            "cliente": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "40", "null": "True"},
            ),
            "conducente": (
                "django.db.models.fields.CharField",
                [],
                {
                    "db_index": "True",
                    "max_length": "5",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "da": ("django.db.models.fields.CharField", [], {"max_length": "25"}),
            "data": ("django.db.models.fields.DateTimeField", [], {"db_index": "True"}),
            "flag_arrivo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "flag_cartaDiCredito": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "flag_esclusivo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "flag_fatturazione": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "flag_fineMese": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "flag_pagamentoDifferito": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "flag_richiesto": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "note": ("django.db.models.fields.TextField", [], {"blank": "True"}),
            "numero_pratica": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "20", "null": "True", "blank": "True"},
            ),
            "padre": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "to": "orm['tamArchive.ViaggioArchive']",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "path": ("django.db.models.fields.TextField", [], {"blank": "True"}),
            "pax": ("django.db.models.fields.IntegerField", [], {"default": "1"}),
            "prezzo": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "9", "decimal_places": "2"},
            ),
            "prezzo_detail": (
                "django.db.models.fields.TextField",
                [],
                {"blank": "True"},
            ),
            "punti_abbinata": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
        }
    }

    complete_apps = ["tamArchive"]
