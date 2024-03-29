# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-05-25 17:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tam", "0006_auto_20170220_2055"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="viaggio",
            options={
                "ordering": ("data_padre", "id_padre", "data", "id"),
                "permissions": (
                    ("change_oldviaggio", "Cambia vecchio viaggio"),
                    ("change_doppi", "Cambia il numero di casette"),
                    ("disableviewprice", "Disable view of the price column"),
                ),
                "verbose_name_plural": "Viaggi",
            },
        ),
        migrations.AlterField(
            model_name="conducente",
            name="has_bus",
            field=models.BooleanField(
                default=False, editable=False, verbose_name="Ha un bus?"
            ),
        ),
    ]
