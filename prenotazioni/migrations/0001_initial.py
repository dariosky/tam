# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tam.models
import prenotazioni.models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tam', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Prenotazione',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_registrazione', models.DateTimeField(auto_now_add=True)),
                ('data_corsa', models.DateTimeField(help_text='In the departures it is the time of the hotel pickup. On the arrival it is the time at the specified place.', verbose_name='Date and time')),
                ('pax', models.IntegerField(default=1)),
                ('is_collettivo', models.BooleanField(default=None, verbose_name='Individual or collective?', choices=[(False, 'Individual'), (True, 'Collective')])),
                ('is_arrivo', models.BooleanField(default=None, verbose_name='Arrival or departure', choices=[(True, 'Arrival from...'), (False, 'Departure to...')])),
                ('pagamento', models.CharField(default=b'D', max_length=1, verbose_name='Payment mode', choices=[(b'D', 'Direct'), (b'H', 'Hotel'), (b'F', 'Invoice')])),
                ('note_camera', models.CharField(max_length=20, verbose_name='Room number', blank=True)),
                ('note_cliente', models.CharField(max_length=40, verbose_name='Client name', blank=True)),
                ('note', models.TextField(verbose_name='Notes', blank=True)),
                ('attachment', models.FileField(storage=tam.models.UnSerializableFileSystemStorage(), upload_to=prenotazioni.models.prenotazioni_upload_to, blank=True, help_text='Attach a file (not required)', null=True, verbose_name='Attachment')),
                ('had_attachment', models.BooleanField(default=False, verbose_name=b'Allegato passato', editable=False)),
                ('cliente', models.ForeignKey(to='tam.Cliente', on_delete=django.db.models.deletion.PROTECT)),
                ('luogo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Where', to='tam.Luogo')),
            ],
            options={
                'ordering': ('-data_registrazione', 'cliente', 'owner'),
                'verbose_name_plural': 'Prenotazioni',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UtentePrenotazioni',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_operatore', models.CharField(max_length=40, null=True)),
                ('email', models.EmailField(max_length=75, null=True)),
                ('clienti', models.ManyToManyField(to='tam.Cliente')),
                ('luogo', models.ForeignKey(to='tam.Luogo', on_delete=django.db.models.deletion.PROTECT)),
                ('user', models.OneToOneField(related_name='prenotazioni', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('user',),
                'verbose_name_plural': 'Utenti prenotazioni',
                'permissions': (('manage_permissions', 'Gestisci utenti prenotazioni'),),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='prenotazione',
            name='owner',
            field=models.ForeignKey(editable=False, to='prenotazioni.UtentePrenotazioni'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='prenotazione',
            name='viaggio',
            field=models.OneToOneField(null=True, editable=False, to='tam.Viaggio'),
            preserve_default=True,
        ),
    ]
