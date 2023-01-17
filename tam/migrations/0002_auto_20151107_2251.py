# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ("tam", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="taskarchive",
            name="user",
        ),
        migrations.RemoveField(
            model_name="taskbackup",
            name="user",
        ),
        migrations.DeleteModel(
            name="TaskMovelog",
        ),
        migrations.AlterField(
            model_name="profiloutente",
            name="user",
            field=models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name="TaskArchive",
        ),
        migrations.DeleteModel(
            name="TaskBackup",
        ),
    ]
