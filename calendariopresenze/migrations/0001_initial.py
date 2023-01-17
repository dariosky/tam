# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tam", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Calendar",
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
                ("date_start", models.DateTimeField(db_index=True)),
                ("date_end", models.DateTimeField(db_index=True)),
                ("minutes", models.IntegerField(editable=False)),
                (
                    "type",
                    models.IntegerField(
                        choices=[(1, b"Ferie"), (2, b"Riposo"), (3, b"Ufficio")]
                    ),
                ),
                ("available", models.BooleanField(default=False)),
                ("value", models.IntegerField()),
                (
                    "conducente",
                    models.ForeignKey(related_name="presenze", to="tam.Conducente"),
                ),
            ],
            options={
                "ordering": ["date_start", "conducente"],
                "permissions": (
                    ("change_oldcalendar", "Imposta vecchio calendario"),
                    ("toggle_calendarvalue", "Cambia valore di un calendario"),
                ),
            },
            bases=(models.Model,),
        ),
    ]
