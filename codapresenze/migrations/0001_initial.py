# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CodaPresenze',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_accodamento', models.DateTimeField(auto_now_add=True)),
                ('luogo', models.TextField(max_length=30)),
                ('utente', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT)),
            ],
            options={
                'ordering': ['data_accodamento'],
                'verbose_name_plural': 'Coda Presenze',
                'permissions': (('view', 'Visualizzazione coda'), ('editall', 'Coda di tutti')),
            },
            bases=(models.Model,),
        ),
    ]
