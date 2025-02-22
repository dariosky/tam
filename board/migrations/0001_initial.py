# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import tam.models
import board.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BoardMessage",
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
                ("date", models.DateTimeField(verbose_name=b"Data di inserimento")),
                (
                    "message",
                    models.TextField(null=True, verbose_name=b"Messaggio", blank=True),
                ),
                (
                    "attachment",
                    models.FileField(
                        storage=tam.models.UnSerializableFileSystemStorage(),
                        null=True,
                        upload_to=board.models.board_upload_to,
                        blank=True,
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True, verbose_name=b"Messaggio visibile"
                    ),
                ),
                ("author", models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-date"],
                "permissions": (("view", "Visualizzazione bacheca"),),
            },
            bases=(models.Model,),
        ),
    ]
