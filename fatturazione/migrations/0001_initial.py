# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tam', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fattura',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('emessa_da', models.TextField()),
                ('emessa_a', models.TextField()),
                ('note', models.TextField(blank=True)),
                ('tipo', models.CharField(max_length=1, db_index=True)),
                ('data', models.DateField(db_index=True)),
                ('anno', models.IntegerField(null=True, db_index=True)),
                ('progressivo', models.IntegerField(null=True, db_index=True)),
                ('archiviata', models.BooleanField(default=False)),
                ('cliente', models.ForeignKey(related_name='fatture', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='tam.Cliente', null=True)),
                ('passeggero', models.ForeignKey(related_name='fatture', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='tam.Passeggero', null=True)),
            ],
            options={
                'ordering': ('anno', 'progressivo'),
                'verbose_name_plural': 'Fatture',
                'permissions': (('generate', 'Genera le fatture'), ('smalledit', 'Smalledit: alle fat.conducente'), ('view', 'Visualizzazione fatture')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RigaFattura',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('riga', models.IntegerField()),
                ('descrizione', models.TextField()),
                ('note', models.TextField()),
                ('qta', models.IntegerField()),
                ('prezzo', models.DecimalField(default=0, null=True, max_digits=9, decimal_places=2)),
                ('iva', models.IntegerField()),
                ('conducente', models.ForeignKey(related_name='fatture', on_delete=django.db.models.deletion.SET_NULL, to='tam.Conducente', null=True)),
                ('fattura', models.ForeignKey(related_name='righe', to='fatturazione.Fattura', on_delete=models.PROTECT)),
                ('riga_fattura_consorzio', models.OneToOneField(related_name='fattura_conducente_collegata', null=True, on_delete=django.db.models.deletion.SET_NULL, to='fatturazione.RigaFattura')),
                ('viaggio', models.OneToOneField(related_name='riga_fattura', null=True, on_delete=django.db.models.deletion.SET_NULL, to='tam.Viaggio')),
            ],
            options={
                'ordering': ('fattura__tipo', 'fattura', 'riga'),
                'verbose_name_plural': 'Righe Fattura',
            },
            bases=(models.Model,),
        ),
    ]
