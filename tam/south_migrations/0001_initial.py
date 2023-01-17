# coding: utf-8

from south.db import db
from django.db import models
from tam.models import *


class Migration:
    def forwards(self, orm):

        # Adding model 'TamLicense'
        db.create_table(
            "tam_tamlicense",
            (
                ("id", orm["tam.TamLicense:id"]),
                ("license", orm["tam.TamLicense:license"]),
            ),
        )
        db.send_create_signal("tam", ["TamLicense"])

        # Adding model 'Cliente'
        db.create_table(
            "tam_cliente",
            (
                ("id", orm["tam.Cliente:id"]),
                ("nome", orm["tam.Cliente:nome"]),
                ("dati", orm["tam.Cliente:dati"]),
                ("tipo", orm["tam.Cliente:tipo"]),
                ("fatturazione", orm["tam.Cliente:fatturazione"]),
                ("pagamento_differito", orm["tam.Cliente:pagamento_differito"]),
                ("incassato_albergo", orm["tam.Cliente:incassato_albergo"]),
                ("listino", orm["tam.Cliente:listino"]),
                ("commissione", orm["tam.Cliente:commissione"]),
                ("tipo_commissione", orm["tam.Cliente:tipo_commissione"]),
                ("attivo", orm["tam.Cliente:attivo"]),
            ),
        )
        db.send_create_signal("tam", ["Cliente"])

        # Adding model 'Bacino'
        db.create_table(
            "tam_bacino",
            (
                ("id", orm["tam.Bacino:id"]),
                ("nome", orm["tam.Bacino:nome"]),
            ),
        )
        db.send_create_signal("tam", ["Bacino"])

        # Adding model 'Tratta'
        db.create_table(
            "tam_tratta",
            (
                ("id", orm["tam.Tratta:id"]),
                ("da", orm["tam.Tratta:da"]),
                ("a", orm["tam.Tratta:a"]),
                ("minuti", orm["tam.Tratta:minuti"]),
                ("km", orm["tam.Tratta:km"]),
                ("costo_autostrada", orm["tam.Tratta:costo_autostrada"]),
            ),
        )
        db.send_create_signal("tam", ["Tratta"])

        # Adding model 'Passeggero'
        db.create_table(
            "tam_passeggero",
            (
                ("id", orm["tam.Passeggero:id"]),
                ("nome", orm["tam.Passeggero:nome"]),
                ("dati", orm["tam.Passeggero:dati"]),
            ),
        )
        db.send_create_signal("tam", ["Passeggero"])

        # Adding model 'ActionLog'
        db.create_table(
            "tam_actionlog",
            (
                ("id", orm["tam.ActionLog:id"]),
                ("data", orm["tam.ActionLog:data"]),
                ("user", orm["tam.ActionLog:user"]),
                ("action_type", orm["tam.ActionLog:action_type"]),
                ("content_type", orm["tam.ActionLog:content_type"]),
                ("object_id", orm["tam.ActionLog:object_id"]),
                ("description", orm["tam.ActionLog:description"]),
            ),
        )
        db.send_create_signal("tam", ["ActionLog"])

        # Adding model 'Ferie'
        db.create_table(
            "tam_ferie",
            (
                ("id", orm["tam.Ferie:id"]),
                ("conducente", orm["tam.Ferie:conducente"]),
                ("data_inizio", orm["tam.Ferie:data_inizio"]),
                ("data_fine", orm["tam.Ferie:data_fine"]),
            ),
        )
        db.send_create_signal("tam", ["Ferie"])

        # Adding model 'Conducente'
        db.create_table(
            "tam_conducente",
            (
                ("id", orm["tam.Conducente:id"]),
                ("nome", orm["tam.Conducente:nome"]),
                ("nick", orm["tam.Conducente:nick"]),
                ("max_persone", orm["tam.Conducente:max_persone"]),
                ("attivo", orm["tam.Conducente:attivo"]),
                ("assente", orm["tam.Conducente:assente"]),
                (
                    "classifica_iniziale_diurni",
                    orm["tam.Conducente:classifica_iniziale_diurni"],
                ),
                (
                    "classifica_iniziale_notturni",
                    orm["tam.Conducente:classifica_iniziale_notturni"],
                ),
                (
                    "classifica_iniziale_puntiDoppiVenezia",
                    orm["tam.Conducente:classifica_iniziale_puntiDoppiVenezia"],
                ),
                (
                    "classifica_iniziale_prezzoDoppiVenezia",
                    orm["tam.Conducente:classifica_iniziale_prezzoDoppiVenezia"],
                ),
                (
                    "classifica_iniziale_doppiPadova",
                    orm["tam.Conducente:classifica_iniziale_doppiPadova"],
                ),
                (
                    "classifica_iniziale_long",
                    orm["tam.Conducente:classifica_iniziale_long"],
                ),
                (
                    "classifica_iniziale_medium",
                    orm["tam.Conducente:classifica_iniziale_medium"],
                ),
            ),
        )
        db.send_create_signal("tam", ["Conducente"])

        # Adding model 'Listino'
        db.create_table(
            "tam_listino",
            (
                ("id", orm["tam.Listino:id"]),
                ("nome", orm["tam.Listino:nome"]),
            ),
        )
        db.send_create_signal("tam", ["Listino"])

        # Adding model 'ProfiloUtente'
        db.create_table(
            "tam_profiloutente",
            (
                ("id", orm["tam.ProfiloUtente:id"]),
                ("user", orm["tam.ProfiloUtente:user"]),
                ("luogo", orm["tam.ProfiloUtente:luogo"]),
            ),
        )
        db.send_create_signal("tam", ["ProfiloUtente"])

        # Adding model 'Viaggio'
        db.create_table(
            "tam_viaggio",
            (
                ("id", orm["tam.Viaggio:id"]),
                ("data", orm["tam.Viaggio:data"]),
                ("da", orm["tam.Viaggio:da"]),
                ("a", orm["tam.Viaggio:a"]),
                ("numero_passeggeri", orm["tam.Viaggio:numero_passeggeri"]),
                ("esclusivo", orm["tam.Viaggio:esclusivo"]),
                ("cliente", orm["tam.Viaggio:cliente"]),
                ("passeggero", orm["tam.Viaggio:passeggero"]),
                ("prezzo", orm["tam.Viaggio:prezzo"]),
                ("costo_autostrada", orm["tam.Viaggio:costo_autostrada"]),
                ("costo_sosta", orm["tam.Viaggio:costo_sosta"]),
                ("abbuono_fisso", orm["tam.Viaggio:abbuono_fisso"]),
                ("abbuono_percentuale", orm["tam.Viaggio:abbuono_percentuale"]),
                ("prezzo_sosta", orm["tam.Viaggio:prezzo_sosta"]),
                ("incassato_albergo", orm["tam.Viaggio:incassato_albergo"]),
                ("fatturazione", orm["tam.Viaggio:fatturazione"]),
                ("pagamento_differito", orm["tam.Viaggio:pagamento_differito"]),
                ("commissione", orm["tam.Viaggio:commissione"]),
                ("tipo_commissione", orm["tam.Viaggio:tipo_commissione"]),
                ("numero_pratica", orm["tam.Viaggio:numero_pratica"]),
                ("padre", orm["tam.Viaggio:padre"]),
                ("conducente_richiesto", orm["tam.Viaggio:conducente_richiesto"]),
                ("conducente", orm["tam.Viaggio:conducente"]),
                ("conducente_confermato", orm["tam.Viaggio:conducente_confermato"]),
                ("note", orm["tam.Viaggio:note"]),
                ("pagato", orm["tam.Viaggio:pagato"]),
                ("luogoDiRiferimento", orm["tam.Viaggio:luogoDiRiferimento"]),
                ("km_conguagliati", orm["tam.Viaggio:km_conguagliati"]),
                ("html_tragitto", orm["tam.Viaggio:html_tragitto"]),
                ("tratta", orm["tam.Viaggio:tratta"]),
                ("tratta_start", orm["tam.Viaggio:tratta_start"]),
                ("tratta_end", orm["tam.Viaggio:tratta_end"]),
                ("is_abbinata", orm["tam.Viaggio:is_abbinata"]),
                ("punti_notturni", orm["tam.Viaggio:punti_notturni"]),
                ("punti_diurni", orm["tam.Viaggio:punti_diurni"]),
                ("km", orm["tam.Viaggio:km"]),
                ("arrivo", orm["tam.Viaggio:arrivo"]),
                ("is_valid", orm["tam.Viaggio:is_valid"]),
                ("punti_abbinata", orm["tam.Viaggio:punti_abbinata"]),
                ("prezzoPunti", orm["tam.Viaggio:prezzoPunti"]),
                ("prezzoVenezia", orm["tam.Viaggio:prezzoVenezia"]),
                ("prezzoPadova", orm["tam.Viaggio:prezzoPadova"]),
                ("prezzoDoppioPadova", orm["tam.Viaggio:prezzoDoppioPadova"]),
                ("prezzo_finale", orm["tam.Viaggio:prezzo_finale"]),
                ("date_start", orm["tam.Viaggio:date_start"]),
            ),
        )
        db.send_create_signal("tam", ["Viaggio"])

        # Adding model 'PrezzoListino'
        db.create_table(
            "tam_prezzolistino",
            (
                ("id", orm["tam.PrezzoListino:id"]),
                ("listino", orm["tam.PrezzoListino:listino"]),
                ("tratta", orm["tam.PrezzoListino:tratta"]),
                ("prezzo_diurno", orm["tam.PrezzoListino:prezzo_diurno"]),
                ("prezzo_notturno", orm["tam.PrezzoListino:prezzo_notturno"]),
                ("commissione", orm["tam.PrezzoListino:commissione"]),
                ("tipo_commissione", orm["tam.PrezzoListino:tipo_commissione"]),
                ("ultima_modifica", orm["tam.PrezzoListino:ultima_modifica"]),
                ("tipo_servizio", orm["tam.PrezzoListino:tipo_servizio"]),
                ("max_pax", orm["tam.PrezzoListino:max_pax"]),
            ),
        )
        db.send_create_signal("tam", ["PrezzoListino"])

        # Adding model 'Conguaglio'
        db.create_table(
            "tam_conguaglio",
            (
                ("id", orm["tam.Conguaglio:id"]),
                ("data", orm["tam.Conguaglio:data"]),
                ("conducente", orm["tam.Conguaglio:conducente"]),
                ("dare", orm["tam.Conguaglio:dare"]),
            ),
        )
        db.send_create_signal("tam", ["Conguaglio"])

        # Adding model 'Luogo'
        db.create_table(
            "tam_luogo",
            (
                ("id", orm["tam.Luogo:id"]),
                ("nome", orm["tam.Luogo:nome"]),
                ("bacino", orm["tam.Luogo:bacino"]),
            ),
        )
        db.send_create_signal("tam", ["Luogo"])

        # Creating unique_together for [da, a] on Tratta.
        db.create_unique("tam_tratta", ["da_id", "a_id"])

        # Creating unique_together for [listino, tratta, tipo_servizio, max_pax] on PrezzoListino.
        db.create_unique(
            "tam_prezzolistino", ["listino_id", "tratta_id", "tipo_servizio", "max_pax"]
        )

    def backwards(self, orm):

        # Deleting unique_together for [listino, tratta, tipo_servizio, max_pax] on PrezzoListino.
        db.delete_unique(
            "tam_prezzolistino", ["listino_id", "tratta_id", "tipo_servizio", "max_pax"]
        )

        # Deleting unique_together for [da, a] on Tratta.
        db.delete_unique("tam_tratta", ["da_id", "a_id"])

        # Deleting model 'TamLicense'
        db.delete_table("tam_tamlicense")

        # Deleting model 'Cliente'
        db.delete_table("tam_cliente")

        # Deleting model 'Bacino'
        db.delete_table("tam_bacino")

        # Deleting model 'Tratta'
        db.delete_table("tam_tratta")

        # Deleting model 'Passeggero'
        db.delete_table("tam_passeggero")

        # Deleting model 'ActionLog'
        db.delete_table("tam_actionlog")

        # Deleting model 'Ferie'
        db.delete_table("tam_ferie")

        # Deleting model 'Conducente'
        db.delete_table("tam_conducente")

        # Deleting model 'Listino'
        db.delete_table("tam_listino")

        # Deleting model 'ProfiloUtente'
        db.delete_table("tam_profiloutente")

        # Deleting model 'Viaggio'
        db.delete_table("tam_viaggio")

        # Deleting model 'PrezzoListino'
        db.delete_table("tam_prezzolistino")

        # Deleting model 'Conguaglio'
        db.delete_table("tam_conguaglio")

        # Deleting model 'Luogo'
        db.delete_table("tam_luogo")

    models = {
        "auth.group": {
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "name": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "80"},
            ),
            "permissions": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {"to": "orm['auth.Permission']", "blank": "True"},
            ),
        },
        "auth.permission": {
            "Meta": {"unique_together": "(('content_type', 'codename'),)"},
            "codename": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "content_type": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['contenttypes.ContentType']"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "name": ("django.db.models.fields.CharField", [], {"max_length": "50"}),
        },
        "auth.user": {
            "date_joined": (
                "django.db.models.fields.DateTimeField",
                [],
                {"default": "datetime.datetime.now"},
            ),
            "email": (
                "django.db.models.fields.EmailField",
                [],
                {"max_length": "75", "blank": "True"},
            ),
            "first_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "30", "blank": "True"},
            ),
            "groups": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {"to": "orm['auth.Group']", "blank": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "is_active": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "blank": "True"},
            ),
            "is_staff": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "is_superuser": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "last_login": (
                "django.db.models.fields.DateTimeField",
                [],
                {"default": "datetime.datetime.now"},
            ),
            "last_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "30", "blank": "True"},
            ),
            "password": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "128"},
            ),
            "user_permissions": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {"to": "orm['auth.Permission']", "blank": "True"},
            ),
            "username": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "30"},
            ),
        },
        "contenttypes.contenttype": {
            "Meta": {
                "unique_together": "(('app_label', 'model'),)",
                "db_table": "'django_content_type'",
            },
            "app_label": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "100"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "model": ("django.db.models.fields.CharField", [], {"max_length": "100"}),
            "name": ("django.db.models.fields.CharField", [], {"max_length": "100"}),
        },
        "tam.actionlog": {
            "action_type": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "1"},
            ),
            "content_type": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['contenttypes.ContentType']"},
            ),
            "data": ("django.db.models.fields.DateTimeField", [], {}),
            "description": ("django.db.models.fields.TextField", [], {"blank": "True"}),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "object_id": ("django.db.models.fields.PositiveIntegerField", [], {}),
            "user": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['auth.User']"},
            ),
        },
        "tam.bacino": {
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "nome": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "20"},
            ),
        },
        "tam.cliente": {
            "attivo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "blank": "True"},
            ),
            "commissione": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "dati": (
                "django.db.models.fields.TextField",
                [],
                {"null": "True", "blank": "True"},
            ),
            "fatturazione": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "incassato_albergo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "listino": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Listino']", "null": "True", "blank": "True"},
            ),
            "nome": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "40"},
            ),
            "pagamento_differito": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "tipo": ("django.db.models.fields.CharField", [], {"max_length": "1"}),
            "tipo_commissione": (
                "django.db.models.fields.CharField",
                [],
                {"default": "'F'", "max_length": "1"},
            ),
        },
        "tam.conducente": {
            "assente": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "attivo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "blank": "True"},
            ),
            "classifica_iniziale_diurni": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "classifica_iniziale_doppiPadova": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "classifica_iniziale_long": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "classifica_iniziale_medium": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "classifica_iniziale_notturni": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "classifica_iniziale_prezzoDoppiVenezia": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "classifica_iniziale_puntiDoppiVenezia": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "max_persone": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "4"},
            ),
            "nick": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "5", "null": "True", "blank": "True"},
            ),
            "nome": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "40"},
            ),
        },
        "tam.conguaglio": {
            "conducente": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Conducente']"},
            ),
            "dare": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "10", "max_digits": "6", "decimal_places": "2"},
            ),
            "data": (
                "django.db.models.fields.DateTimeField",
                [],
                {"auto_now": "True", "blank": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
        },
        "tam.ferie": {
            "conducente": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Conducente']"},
            ),
            "data_fine": ("django.db.models.fields.DateTimeField", [], {}),
            "data_inizio": ("django.db.models.fields.DateTimeField", [], {}),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
        },
        "tam.listino": {
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "nome": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "20"},
            ),
        },
        "tam.luogo": {
            "bacino": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Bacino']", "null": "True", "blank": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "nome": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "25"},
            ),
        },
        "tam.passeggero": {
            "dati": ("django.db.models.fields.TextField", [], {"null": "True"}),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "nome": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "40"},
            ),
        },
        "tam.prezzolistino": {
            "Meta": {
                "unique_together": "(('listino', 'tratta', 'tipo_servizio', 'max_pax'),)"
            },
            "commissione": (
                "django.db.models.fields.DecimalField",
                [],
                {
                    "default": "0",
                    "null": "True",
                    "max_digits": "6",
                    "decimal_places": "2",
                },
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "listino": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Listino']"},
            ),
            "max_pax": ("django.db.models.fields.IntegerField", [], {"default": "4"}),
            "prezzo_diurno": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "10", "max_digits": "6", "decimal_places": "2"},
            ),
            "prezzo_notturno": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "10", "max_digits": "6", "decimal_places": "2"},
            ),
            "tipo_commissione": (
                "django.db.models.fields.CharField",
                [],
                {"default": "'F'", "max_length": "1"},
            ),
            "tipo_servizio": (
                "django.db.models.fields.CharField",
                [],
                {"default": "'T'", "max_length": "1"},
            ),
            "tratta": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Tratta']"},
            ),
            "ultima_modifica": (
                "django.db.models.fields.DateField",
                [],
                {"auto_now": "True", "blank": "True"},
            ),
        },
        "tam.profiloutente": {
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "luogo": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Luogo']", "null": "True", "blank": "True"},
            ),
            "user": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['auth.User']", "unique": "True"},
            ),
        },
        "tam.tamlicense": {
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "license": ("django.db.models.fields.TextField", [], {}),
        },
        "tam.tratta": {
            "Meta": {"unique_together": "(('da', 'a'),)"},
            "a": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"related_name": "'tempo_a'", "to": "orm['tam.Luogo']"},
            ),
            "costo_autostrada": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "da": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"related_name": "'tempo_da'", "to": "orm['tam.Luogo']"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "km": ("django.db.models.fields.IntegerField", [], {"default": "0"}),
            "minuti": ("django.db.models.fields.IntegerField", [], {"default": "0"}),
        },
        "tam.viaggio": {
            "a": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"related_name": "'a'", "to": "orm['tam.Luogo']"},
            ),
            "abbuono_fisso": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "abbuono_percentuale": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "arrivo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "blank": "True"},
            ),
            "cliente": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Cliente']", "null": "True", "blank": "True"},
            ),
            "commissione": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "conducente": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Conducente']", "null": "True", "blank": "True"},
            ),
            "conducente_confermato": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "conducente_richiesto": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "costo_autostrada": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "costo_sosta": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "da": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"related_name": "'da'", "to": "orm['tam.Luogo']"},
            ),
            "data": ("django.db.models.fields.DateTimeField", [], {}),
            "date_start": (
                "django.db.models.fields.DateTimeField",
                [],
                {"default": "datetime.datetime(2009, 1, 1, 0, 0)"},
            ),
            "esclusivo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "blank": "True"},
            ),
            "fatturazione": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "html_tragitto": (
                "django.db.models.fields.TextField",
                [],
                {"blank": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "incassato_albergo": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "is_abbinata": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "1", "null": "True", "blank": "True"},
            ),
            "is_valid": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True", "blank": "True"},
            ),
            "km": ("django.db.models.fields.IntegerField", [], {"default": "0"}),
            "km_conguagliati": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0", "null": "True", "blank": "True"},
            ),
            "luogoDiRiferimento": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "related_name": "'riferimento'",
                    "null": "True",
                    "to": "orm['tam.Luogo']",
                },
            ),
            "note": ("django.db.models.fields.TextField", [], {"blank": "True"}),
            "numero_passeggeri": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "1"},
            ),
            "numero_pratica": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "20", "null": "True", "blank": "True"},
            ),
            "padre": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Viaggio']", "null": "True", "blank": "True"},
            ),
            "pagamento_differito": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "pagato": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "False", "blank": "True"},
            ),
            "passeggero": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {"to": "orm['tam.Passeggero']", "null": "True", "blank": "True"},
            ),
            "prezzo": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "prezzoDoppioPadova": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "prezzoPadova": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "prezzoPunti": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "prezzoVenezia": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "prezzo_finale": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "prezzo_sosta": (
                "django.db.models.fields.DecimalField",
                [],
                {"default": "0", "max_digits": "6", "decimal_places": "2"},
            ),
            "punti_abbinata": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "punti_diurni": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "punti_notturni": (
                "django.db.models.fields.IntegerField",
                [],
                {"default": "0"},
            ),
            "tipo_commissione": (
                "django.db.models.fields.CharField",
                [],
                {"default": "'F'", "max_length": "1"},
            ),
            "tratta": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "default": "None",
                    "to": "orm['tam.Tratta']",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "tratta_end": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "blank": "True",
                    "related_name": "'viaggio_end_set'",
                    "null": "True",
                    "to": "orm['tam.Tratta']",
                },
            ),
            "tratta_start": (
                "django.db.models.fields.related.ForeignKey",
                [],
                {
                    "blank": "True",
                    "related_name": "'viaggio_start_set'",
                    "null": "True",
                    "to": "orm['tam.Tratta']",
                },
            ),
        },
    }

    complete_apps = ["tam"]
