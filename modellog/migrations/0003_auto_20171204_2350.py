# Generated by Django 2.0 on 2017-12-04 22:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modellog', '0002_auto_20160831_0011'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='action_type',
            field=models.CharField(choices=[('A', 'Creazione'), ('M', 'Modifica'), ('D', 'Cancellazione'), ('B', 'Backup'), ('G', 'Backup scaricato'), ('K', 'Archiviazione'), ('F', 'Appianamento'), ('L', 'Login'), ('O', 'Logout'), ('X', 'Export Excel'), ('C', 'Fatturazione'), ('Q', 'Presenze')], max_length=1),
        ),
    ]