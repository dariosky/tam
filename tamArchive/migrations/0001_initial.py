# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ViaggioArchive",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "data",
                    models.DateTimeField(
                        verbose_name=b"Data della corsa", db_index=True
                    ),
                ),
                ("da", models.CharField(max_length=25, verbose_name=b"Da")),
                ("a", models.CharField(max_length=25, verbose_name=b"A")),
                (
                    "path",
                    models.TextField(verbose_name=b"Percorso effettuato", blank=True),
                ),
                ("pax", models.IntegerField(default=1)),
                (
                    "flag_esclusivo",
                    models.BooleanField(default=True, verbose_name=b"Servizio taxi"),
                ),
                (
                    "conducente",
                    models.CharField(
                        db_index=True,
                        max_length=5,
                        null=True,
                        verbose_name=b"Conducente",
                        blank=True,
                    ),
                ),
                (
                    "flag_richiesto",
                    models.BooleanField(
                        default=False, verbose_name=b"Conducente richiesto"
                    ),
                ),
                (
                    "cliente",
                    models.CharField(max_length=40, null=True, verbose_name=b"A"),
                ),
                (
                    "prezzo",
                    models.DecimalField(
                        default=0, editable=False, max_digits=9, decimal_places=2
                    ),
                ),
                (
                    "prezzo_detail",
                    models.TextField(verbose_name=b"Dettagli prezzo", blank=True),
                ),
                (
                    "flag_fineMese",
                    models.BooleanField(default=False, verbose_name=b"Conto fine mese"),
                ),
                (
                    "flag_fatturazione",
                    models.BooleanField(
                        default=False, verbose_name=b"Fatturazione richiesta"
                    ),
                ),
                (
                    "flag_cartaDiCredito",
                    models.BooleanField(
                        default=False, verbose_name=b"Pagamento con carta di credito"
                    ),
                ),
                ("flag_pagamentoDifferito", models.BooleanField(default=False)),
                (
                    "numero_pratica",
                    models.CharField(max_length=20, null=True, blank=True),
                ),
                ("flag_arrivo", models.BooleanField(default=True, editable=False)),
                ("punti_abbinata", models.IntegerField(default=0, editable=False)),
                ("note", models.TextField(blank=True)),
                (
                    "padre",
                    models.ForeignKey(
                        blank=True, to="tamArchive.ViaggioArchive", null=True
                    ),
                ),
            ],
            options={
                "ordering": ["data"],
                "verbose_name_plural": "Archivi",
                "permissions": (
                    ("flat", "Esegue l'appianamento"),
                    ("archive", "Esegue l'archiviazione"),
                ),
            },
            bases=(models.Model,),
        ),
    ]
