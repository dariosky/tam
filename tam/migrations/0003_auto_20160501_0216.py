# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-01 00:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tam", "0002_auto_20151107_2251"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="profiloutente",
            options={
                "permissions": (
                    ("can_backup", "Richiede un backup"),
                    ("get_backup", "Scarica un backup"),
                    ("reset_sessions", "Can reset session"),
                ),
                "verbose_name_plural": "Profili utente",
            },
        ),
    ]
