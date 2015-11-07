# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models, migrations
import django.db.models.deletion
import tam.models
import prenotazioni.models


class Migration(migrations.Migration):
    dependencies = [
        ('prenotazioni', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prenotazione',
            name='attachment',
            field=models.FileField(storage=tam.models.UnSerializableFileSystemStorage(),
                                   upload_to=prenotazioni.models.prenotazioni_upload_to,
                                   blank=True,
                                   help_text='Allega un file alla richiesta (facoltativo).',
                                   null=True, verbose_name='Allegato'),
        ),
        migrations.AlterField(
            model_name='prenotazione',
            name='data_corsa',
            field=models.DateTimeField(
                help_text="Nelle partenze indica l'ora della presa in hotel. Negli arrivi indica l'ora al luogo specificato.",
                verbose_name='Data e ora'),
        ),
        migrations.AlterField(
            model_name='prenotazione',
            name='is_arrivo',
            field=models.BooleanField(default=None, verbose_name='Arrivo o partenza?',
                                      choices=[(True, 'Arrivo da...'),
                                               (False, 'Partenza per...')]),
        ),
        migrations.AlterField(
            model_name='prenotazione',
            name='is_collettivo',
            field=models.BooleanField(default=None, verbose_name='Individuale o collettivo?',
                                      choices=[(False, 'Individuale'), (True, 'Collettivo')]),
        ),
        migrations.AlterField(
            model_name='prenotazione',
            name='luogo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    verbose_name='Luogo', to='tam.Luogo'),
        ),
        migrations.AlterField(
            model_name='prenotazione',
            name='note',
            field=models.TextField(verbose_name='Note', blank=True),
        ),
        migrations.AlterField(
            model_name='prenotazione',
            name='note_camera',
            field=models.CharField(max_length=20, verbose_name='Numero di camera', blank=True),
        ),
        migrations.AlterField(
            model_name='prenotazione',
            name='note_cliente',
            field=models.CharField(max_length=40, verbose_name='Nome del cliente', blank=True),
        ),
        migrations.AlterField(
            model_name='prenotazione',
            name='pagamento',
            field=models.CharField(default=b'D', max_length=1, verbose_name='Pagamento',
                                   choices=[(b'D', 'Diretto'), (b'H', 'Hotel'),
                                            (b'F', 'Fattura')]),
        ),
        migrations.AlterField(
            model_name='utenteprenotazioni',
            name='email',
            field=models.EmailField(max_length=254, null=True),
        ),
    ]
