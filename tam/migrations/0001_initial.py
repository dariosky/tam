# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Bacino",
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
                ("nome", models.CharField(unique=True, max_length=20)),
            ],
            options={
                "ordering": ["nome"],
                "verbose_name_plural": "Bacini",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Cliente",
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
                (
                    "nome",
                    models.CharField(
                        unique=True, max_length=40, verbose_name=b"Nome cliente"
                    ),
                ),
                (
                    "dati",
                    models.TextField(
                        help_text=b"Stampati nelle fattura conducente",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        max_length=1,
                        verbose_name=b"Tipo cliente",
                        choices=[
                            (b"H", b"Hotel"),
                            (b"A", b"Agenzia"),
                            (b"D", b"Ditta"),
                        ],
                    ),
                ),
                (
                    "fatturazione",
                    models.BooleanField(
                        default=False, verbose_name=b"Fatturazione richiesta"
                    ),
                ),
                (
                    "pagamento_differito",
                    models.BooleanField(
                        default=False, verbose_name=b"Fatturazione esente IVA"
                    ),
                ),
                (
                    "incassato_albergo",
                    models.BooleanField(default=False, verbose_name=b"Conto fine mese"),
                ),
                (
                    "commissione",
                    models.DecimalField(
                        default=0,
                        verbose_name=b"Quota consorzio",
                        max_digits=9,
                        decimal_places=2,
                    ),
                ),
                (
                    "tipo_commissione",
                    models.CharField(
                        default=b"F",
                        max_length=1,
                        verbose_name=b"Tipo di quota",
                        choices=[(b"F", b"\xe2\x82\xac"), (b"P", b"%")],
                    ),
                ),
                ("attivo", models.BooleanField(default=True)),
                ("note", models.TextField(null=True, blank=True)),
            ],
            options={
                "ordering": ["nome"],
                "verbose_name_plural": "Clienti",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Conducente",
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
                (
                    "nome",
                    models.CharField(unique=True, max_length=40, verbose_name=b"Nome"),
                ),
                (
                    "dati",
                    models.TextField(
                        help_text=b"Stampati nelle fattura conducente",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "nick",
                    models.CharField(
                        max_length=5, null=True, verbose_name=b"Sigla", blank=True
                    ),
                ),
                ("max_persone", models.IntegerField(default=4)),
                ("attivo", models.BooleanField(default=True, db_index=True)),
                (
                    "emette_ricevute",
                    models.BooleanField(
                        default=True,
                        help_text=b"Il conducente pu\xc3\xb2 emettere fatture senza IVA?",
                        verbose_name=b"Emette senza IVA?",
                    ),
                ),
                ("assente", models.BooleanField(default=False)),
                (
                    "classifica_iniziale_diurni",
                    models.DecimalField(
                        default=0,
                        verbose_name=b"Supplementari diurni",
                        max_digits=12,
                        decimal_places=2,
                    ),
                ),
                (
                    "classifica_iniziale_notturni",
                    models.DecimalField(
                        default=0,
                        verbose_name=b"Supplementari notturni",
                        max_digits=12,
                        decimal_places=2,
                    ),
                ),
                (
                    "classifica_iniziale_puntiDoppiVenezia",
                    models.IntegerField(default=0, verbose_name=b"Punti Doppi Venezia"),
                ),
                (
                    "classifica_iniziale_prezzoDoppiVenezia",
                    models.DecimalField(
                        default=0,
                        verbose_name=b"Valore Doppi Venezia",
                        max_digits=12,
                        decimal_places=2,
                    ),
                ),
                (
                    "classifica_iniziale_doppiPadova",
                    models.DecimalField(
                        default=0,
                        verbose_name=b"Doppi Padova",
                        max_digits=12,
                        decimal_places=2,
                    ),
                ),
                (
                    "classifica_iniziale_long",
                    models.DecimalField(
                        default=0,
                        verbose_name=b"Venezia",
                        max_digits=12,
                        decimal_places=2,
                    ),
                ),
                (
                    "classifica_iniziale_medium",
                    models.DecimalField(
                        default=0,
                        verbose_name=b"Padova",
                        max_digits=12,
                        decimal_places=2,
                    ),
                ),
            ],
            options={
                "ordering": ["-attivo", "nick", "nome"],
                "verbose_name_plural": "Conducenti",
                "permissions": (
                    ("change_classifiche_iniziali", "Cambia classifiche iniziali"),
                ),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Conguaglio",
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
                ("data", models.DateTimeField(auto_now=True)),
                (
                    "dare",
                    models.DecimalField(default=10, max_digits=9, decimal_places=2),
                ),
                (
                    "conducente",
                    models.ForeignKey(to="tam.Conducente", on_delete=models.PROTECT),
                ),
            ],
            options={
                "verbose_name_plural": "Conguagli",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Listino",
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
                ("nome", models.CharField(unique=True, max_length=30)),
            ],
            options={
                "ordering": ["nome"],
                "verbose_name_plural": "Listini",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Luogo",
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
                (
                    "nome",
                    models.CharField(
                        unique=True,
                        max_length=25,
                        verbose_name=b"Localit\xc3\xa0\xc2\xa0",
                    ),
                ),
                (
                    "speciale",
                    models.CharField(
                        default=b"",
                        max_length=1,
                        verbose_name=b"Luogo particolare",
                        choices=[
                            (b"-", b"-"),
                            (b"A", b"Aeroporto"),
                            (b"S", b"Stazione"),
                        ],
                    ),
                ),
                (
                    "bacino",
                    models.ForeignKey(
                        verbose_name=b"Bacino di appartenenza",
                        blank=True,
                        to="tam.Bacino",
                        null=True,
                        on_delete=models.PROTECT,
                    ),
                ),
            ],
            options={
                "ordering": ["nome"],
                "verbose_name_plural": "Luoghi",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Passeggero",
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
                ("nome", models.CharField(unique=True, max_length=40)),
                ("dati", models.TextField(null=True, blank=True)),
            ],
            options={
                "ordering": ["nome"],
                "verbose_name_plural": "Passeggeri",
                "permissions": (
                    ("fastinsert_passenger", "Inserimento passeggero veloce"),
                ),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="PrezzoListino",
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
                (
                    "prezzo_diurno",
                    models.DecimalField(default=10, max_digits=9, decimal_places=2),
                ),
                (
                    "prezzo_notturno",
                    models.DecimalField(default=10, max_digits=9, decimal_places=2),
                ),
                (
                    "commissione",
                    models.DecimalField(
                        default=0,
                        null=True,
                        verbose_name=b"Quota consorzio",
                        max_digits=9,
                        decimal_places=2,
                    ),
                ),
                (
                    "tipo_commissione",
                    models.CharField(
                        default=b"F",
                        max_length=1,
                        verbose_name=b"Tipo di quota",
                        choices=[(b"F", b"\xe2\x82\xac"), (b"P", b"%")],
                    ),
                ),
                ("ultima_modifica", models.DateField(auto_now=True)),
                (
                    "tipo_servizio",
                    models.CharField(
                        default=b"T",
                        max_length=1,
                        choices=[(b"T", b"Taxi"), (b"C", b"Collettivo")],
                    ),
                ),
                (
                    "max_pax",
                    models.IntegerField(default=4, verbose_name=b"Pax Massimi"),
                ),
                (
                    "flag_fatturazione",
                    models.CharField(
                        default=b"-",
                        max_length=1,
                        verbose_name=b"Fatturazione forzata",
                        choices=[
                            (b"S", b"Fatturazione richiesta"),
                            (b"N", b"Fatturazione non richiesta"),
                            (b"-", b"Usa impostazioni del cliente"),
                        ],
                    ),
                ),
                (
                    "listino",
                    models.ForeignKey(to="tam.Listino", on_delete=models.PROTECT),
                ),
            ],
            options={
                "ordering": ["tipo_servizio", "max_pax"],
                "verbose_name_plural": "Prezzi Listino",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="ProfiloUtente",
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
                (
                    "luogo",
                    models.ForeignKey(
                        verbose_name=b"Luogo di partenza",
                        blank=True,
                        to="tam.Luogo",
                        null=True,
                        on_delete=models.PROTECT,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        editable=False,
                        to=settings.AUTH_USER_MODEL,
                        unique=True,
                        on_delete=models.PROTECT,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Profili utente",
                "permissions": (
                    ("can_backup", "Richiede un backup"),
                    ("get_backup", "Scarica un backup"),
                ),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TaskArchive",
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
                ("end_date", models.DateField()),
                (
                    "user",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TaskBackup",
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
                (
                    "user",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TaskMovelog",
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
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Tratta",
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
                ("minuti", models.IntegerField(default=0)),
                ("km", models.IntegerField(default=0)),
                (
                    "costo_autostrada",
                    models.DecimalField(default=0, max_digits=9, decimal_places=2),
                ),
                (
                    "a",
                    models.ForeignKey(
                        related_name="tempo_a", to="tam.Luogo", on_delete=models.PROTECT
                    ),
                ),
                (
                    "da",
                    models.ForeignKey(
                        related_name="tempo_da",
                        to="tam.Luogo",
                        on_delete=models.PROTECT,
                    ),
                ),
            ],
            options={
                "ordering": ["da", "a"],
                "verbose_name_plural": "Tratte",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Viaggio",
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
                (
                    "data",
                    models.DateTimeField(verbose_name=b"Data e ora", db_index=True),
                ),
                ("numero_passeggeri", models.IntegerField(default=1)),
                (
                    "esclusivo",
                    models.BooleanField(default=True, verbose_name=b"Servizio taxi"),
                ),
                (
                    "prezzo",
                    models.DecimalField(default=0, max_digits=9, decimal_places=2),
                ),
                (
                    "costo_autostrada",
                    models.DecimalField(default=0, max_digits=9, decimal_places=2),
                ),
                (
                    "costo_sosta",
                    models.DecimalField(default=0, max_digits=9, decimal_places=2),
                ),
                (
                    "abbuono_fisso",
                    models.DecimalField(default=0, max_digits=9, decimal_places=2),
                ),
                ("abbuono_percentuale", models.IntegerField(default=0)),
                (
                    "prezzo_sosta",
                    models.DecimalField(default=0, max_digits=9, decimal_places=2),
                ),
                (
                    "incassato_albergo",
                    models.BooleanField(default=False, verbose_name=b"Conto fine mese"),
                ),
                (
                    "fatturazione",
                    models.BooleanField(
                        default=False, verbose_name=b"Fatturazione richiesta"
                    ),
                ),
                (
                    "pagamento_differito",
                    models.BooleanField(
                        default=False, verbose_name=b"Fatturazione esente IVA"
                    ),
                ),
                (
                    "cartaDiCredito",
                    models.BooleanField(
                        default=False, verbose_name=b"Pagamento con carta di credito"
                    ),
                ),
                (
                    "commissione",
                    models.DecimalField(
                        default=0,
                        verbose_name=b"Quota consorzio",
                        max_digits=9,
                        decimal_places=2,
                    ),
                ),
                (
                    "tipo_commissione",
                    models.CharField(
                        default=b"F",
                        max_length=1,
                        verbose_name=b"Tipo di quota",
                        choices=[(b"F", b"\xe2\x82\xac"), (b"P", b"%")],
                    ),
                ),
                (
                    "numero_pratica",
                    models.CharField(max_length=20, null=True, blank=True),
                ),
                (
                    "data_padre",
                    models.DateTimeField(
                        verbose_name=b"Data e ora padre",
                        null=True,
                        editable=False,
                        db_index=True,
                    ),
                ),
                (
                    "id_padre",
                    models.PositiveIntegerField(
                        verbose_name=b"ID Gruppo",
                        null=True,
                        editable=False,
                        db_index=True,
                    ),
                ),
                (
                    "conducente_richiesto",
                    models.BooleanField(
                        default=False, verbose_name=b"Escluso dai supplementari"
                    ),
                ),
                (
                    "conducente_confermato",
                    models.BooleanField(
                        default=False, verbose_name=b"Conducente confermato"
                    ),
                ),
                ("note", models.TextField(blank=True)),
                ("pagato", models.BooleanField(default=False)),
                (
                    "km_conguagliati",
                    models.IntegerField(
                        default=0,
                        verbose_name=b"Km conguagliati",
                        null=True,
                        editable=False,
                        blank=True,
                    ),
                ),
                ("html_tragitto", models.TextField(editable=False, blank=True)),
                (
                    "is_abbinata",
                    models.CharField(
                        max_length=1, null=True, editable=False, blank=True
                    ),
                ),
                (
                    "punti_notturni",
                    models.DecimalField(
                        default=0, editable=False, max_digits=6, decimal_places=2
                    ),
                ),
                (
                    "punti_diurni",
                    models.DecimalField(
                        default=0, editable=False, max_digits=6, decimal_places=2
                    ),
                ),
                ("km", models.IntegerField(default=0, editable=False)),
                ("arrivo", models.BooleanField(default=True, editable=False)),
                ("is_valid", models.BooleanField(default=True, editable=False)),
                ("punti_abbinata", models.IntegerField(default=0, editable=False)),
                (
                    "prezzoPunti",
                    models.DecimalField(
                        default=0, editable=False, max_digits=9, decimal_places=2
                    ),
                ),
                (
                    "prezzoVenezia",
                    models.DecimalField(
                        default=0, editable=False, max_digits=9, decimal_places=2
                    ),
                ),
                (
                    "prezzoPadova",
                    models.DecimalField(
                        default=0, editable=False, max_digits=9, decimal_places=2
                    ),
                ),
                (
                    "prezzoDoppioPadova",
                    models.DecimalField(
                        default=0, editable=False, max_digits=9, decimal_places=2
                    ),
                ),
                (
                    "prezzo_finale",
                    models.DecimalField(
                        default=0, editable=False, max_digits=9, decimal_places=2
                    ),
                ),
                (
                    "date_start",
                    models.DateTimeField(
                        default=datetime.datetime(2008, 12, 31, 23, 0, tzinfo=utc),
                        editable=False,
                        db_index=True,
                    ),
                ),
                (
                    "date_end",
                    models.DateTimeField(null=True, editable=False, db_index=True),
                ),
                (
                    "annullato",
                    models.BooleanField(
                        default=False, db_index=True, verbose_name=b"Corsa annullata"
                    ),
                ),
                (
                    "is_prenotazione",
                    models.BooleanField(
                        default=False,
                        verbose_name=b"Derivato da prenotazione",
                        editable=False,
                    ),
                ),
                (
                    "a",
                    models.ForeignKey(
                        related_name="a", to="tam.Luogo", on_delete=models.PROTECT
                    ),
                ),
                (
                    "cliente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        blank=True,
                        to="tam.Cliente",
                        null=True,
                    ),
                ),
                (
                    "conducente",
                    models.ForeignKey(
                        blank=True,
                        to="tam.Conducente",
                        null=True,
                        on_delete=models.PROTECT,
                    ),
                ),
                (
                    "da",
                    models.ForeignKey(
                        related_name="da", to="tam.Luogo", on_delete=models.PROTECT
                    ),
                ),
                (
                    "luogoDiRiferimento",
                    models.ForeignKey(
                        related_name="riferimento",
                        to="tam.Luogo",
                        null=True,
                        on_delete=models.PROTECT,
                    ),
                ),
                (
                    "padre",
                    models.ForeignKey(
                        blank=True,
                        to="tam.Viaggio",
                        null=True,
                        on_delete=models.PROTECT,
                    ),
                ),
                (
                    "passeggero",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        blank=True,
                        to="tam.Passeggero",
                        null=True,
                    ),
                ),
                (
                    "tratta",
                    models.ForeignKey(
                        default=None,
                        blank=True,
                        editable=False,
                        to="tam.Tratta",
                        null=True,
                        on_delete=models.PROTECT,
                    ),
                ),
                (
                    "tratta_end",
                    models.ForeignKey(
                        related_name="viaggio_end_set",
                        blank=True,
                        editable=False,
                        to="tam.Tratta",
                        null=True,
                        on_delete=models.PROTECT,
                    ),
                ),
                (
                    "tratta_start",
                    models.ForeignKey(
                        related_name="viaggio_start_set",
                        blank=True,
                        editable=False,
                        to="tam.Tratta",
                        null=True,
                        on_delete=models.PROTECT,
                    ),
                ),
            ],
            options={
                "ordering": ("data_padre", "id_padre", "data", "id"),
                "verbose_name_plural": "Viaggi",
                "permissions": (
                    ("change_oldviaggio", "Cambia vecchio viaggio"),
                    ("change_doppi", "Cambia il numero di casette"),
                ),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name="tratta",
            unique_together={("da", "a")},
        ),
        migrations.AddField(
            model_name="prezzolistino",
            name="tratta",
            field=models.ForeignKey(to="tam.Tratta", on_delete=models.PROTECT),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name="prezzolistino",
            unique_together={("listino", "tratta", "tipo_servizio", "max_pax")},
        ),
        migrations.AddField(
            model_name="cliente",
            name="listino",
            field=models.ForeignKey(
                verbose_name=b"Listino cliente",
                blank=True,
                to="tam.Listino",
                null=True,
                on_delete=models.PROTECT,
            ),
            preserve_default=True,
        ),
    ]
