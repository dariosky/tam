# Generated by Django 2.0 on 2017-12-04 22:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("fatturazione", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rigafattura",
            name="fattura",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="righe",
                to="fatturazione.Fattura",
            ),
        ),
    ]
