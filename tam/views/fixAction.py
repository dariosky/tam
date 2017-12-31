# coding: utf-8
from django import db
from django.contrib.auth.decorators import user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission, User
from modellog.models import ActionLog
from prenotazioni.models import Prenotazione
from tam import tamdates
from tam.models import Viaggio, Luogo, Conducente
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from django.shortcuts import render
from tam.disturbi import trovaDisturbi, fasce_semilineari
from django.contrib import messages


@user_passes_test(lambda user: user.is_superuser)
def fixAction(request, template_name="utils/fixAction.html"):
    if not request.user.is_superuser:
        messages.error(request, "Devi avere i superpoteri per eseguire le azioni correttive.")
        return HttpResponseRedirect(reverse("tamUtil"))

    messageLines = []
    error = ""
    if request.POST.get('associate-drivers'):
        unassociated_drivers = Conducente.objects.filter(user__isnull=True, attivo=True)
        messageLines.append(
            'We have %d unassociated drivers' % len(unassociated_drivers)
        )
        available_users = User.objects.filter(is_active=True,
                                              prenotazioni__isnull=True)
        for driver in unassociated_drivers:
            maybe_users = available_users.filter(username__in=["socio%s" % driver.nick])
            if maybe_users:
                if len(maybe_users) == 1:
                    user = maybe_users[0]
                    driver.user = user
                    driver.save()
                    messageLines.append(f"Associated {driver} with user {user}")
                else:
                    messageLines.append(f"Multiple possible associations with {driver}")

    #	messageLines.append("Nessuna azione correttiva impostata. Meglio tenere tutto fermo di default.")
    if request.POST.get('toV2'):
        # ===========================================================================
        # Azione di aggiornamento alla 2.0
        # Aggiungo lo speciale ai luoghi in base al nome
        # Effettuo il vacuum del DB
        from tamArchive.tasks import vacuum_db

        messageLines.append('Imposto gli speciali sui luoghi con stazione/aer* nel nome.')
        stazioni = Luogo.objects.filter(nome__icontains='stazione').exclude(speciale='S')
        if len(stazioni):
            messageLines.append('%d stazioni trovate:' % len(stazioni))
        for stazione in stazioni:
            stazione.speciale = 'S'
            stazione.save()
            messageLines.append(stazione.nome)
        aeroporti = Luogo.objects.filter(nome__icontains=' aer').exclude(speciale='A')
        if len(aeroporti):
            messageLines.append('%d aeroporti trovati:' % len(aeroporti))
        for aeroporto in aeroporti:
            aeroporto.speciale = 'A'
            aeroporto.save()
            messageLines.append(aeroporto.nome)

        gruppo_potenti = Group.objects.get(name='Potente')
        permessiDaAggiungere = ('get_backup', 'can_backup', 'archive', 'flat')
        for nomePermesso in permessiDaAggiungere:
            p = Permission.objects.get(codename=nomePermesso)
            gruppo_potenti.permissions.add(p)
            messageLines.append('Do agli utenti potenti: %s' % nomePermesso)
        messageLines.append('Vacuum DB.')
        vacuum_db()
        # ===========================================================================

    if "Aggiorno i prezzi di Padova e Venezia delle corse degli ultimi 2 mesi" == False:
        corseCambiate = corse = 0

        corseDaSistemare = Viaggio.objects.filter(
            data__gt=datetime.date.today() - datetime.timedelta(days=60),
            padre__isnull=True)
        # corseDaSistemare = Viaggio.objects.filter(pk=44068, padre__isnull=True)
        for corsa in corseDaSistemare:
            oldDPadova = corsa.prezzoDoppioPadova
            oldVenezia = corsa.prezzoVenezia
            corsa.updatePrecomp(forceDontSave=True)
            if oldDPadova != corsa.prezzoDoppioPadova or oldVenezia != corsa.prezzoVenezia:
                messageLines.append("%s\n   DPD: %d->%d VE: %d->%d" % (
                    corsa, oldDPadova, corsa.prezzoDoppioPadova, oldVenezia, corsa.prezzoVenezia))
                corseCambiate += 1
            corse += 1
        messageLines.append("Corse aggiornate %d/%d" % (corseCambiate, corse))

    if False:
        messageLines.append("Conguaglio completamente la corsa 35562")
        messageLines.append("e tolgo il conguaglio alle 38740 e 38887")

        def status():
            corsa = Viaggio.objects.filter(pk=35562)[0]
            messageLines.append("la prima del %s è conguagliata di %d km su %d punti. Andrebbe 360."
                                % (corsa.date_start, corsa.km_conguagliati, corsa.punti_abbinata))

            corsa = Viaggio.objects.filter(pk=38740)[0]
            messageLines.append("la seconda del %s è conguagliata di %d km su %d punti. Andrebbe 0."
                                % (corsa.date_start, corsa.km_conguagliati, corsa.punti_abbinata))

            corsa = Viaggio.objects.filter(pk=38887)[0]
            messageLines.append("la terza del %s è conguagliata di %d km su %d punti. Andrebbe 0."
                                % (corsa.date_start, corsa.km_conguagliati, corsa.punti_abbinata))

        status()

        messageLines.append("EFFETTUO LE AZIONI!")
        corsa = Viaggio.objects.filter(pk=35562)[0]
        corsa.km_conguagliati = 360
        corsa.save()
        corsa.updatePrecomp()  # salvo perché mi toglierà i punti

        corsa = Viaggio.objects.filter(pk=38740)[0]
        corsa.km_conguagliati = 0
        corsa.save()
        corsa.updatePrecomp()  # salvo perché mi toglierà i punti

        corsa = Viaggio.objects.filter(pk=38887)[0]
        corsa.km_conguagliati = 0
        corsa.save()
        corsa.updatePrecomp()  # salvo perché mi toglierà i punti

        status()

    if request.POST.get('fixDisturbi'):
        # Per le corse abbinate, dove l'ultimo fratello è un aereoporto ricalcolo i distrubi
        print("Refixo")
        viaggi = Viaggio.objects.filter(is_abbinata__in=('P', 'S'),
                                        date_start__gt=datetime.datetime(2012, 3, 1),
                                        padre=None)
        sistemati = 0
        for viaggio in viaggi:
            ultimaCorsa = viaggio.lastfratello()
            if ultimaCorsa.da.speciale == 'A':

                disturbiGiusti = trovaDisturbi(viaggio.date_start,
                                               viaggio.get_date_end(recurse=True),
                                               metodo=fasce_semilineari)
                notturniGiusti = disturbiGiusti.get('night', 0)
                diurniGiusti = disturbiGiusti.get('morning', 0)
                if diurniGiusti != viaggio.punti_diurni or notturniGiusti != viaggio.punti_notturni:
                    messageLines.append(viaggio)
                    messageLines.append(ultimaCorsa)
                    messageLines.append(
                        "prima %s/%s" % (viaggio.punti_diurni, viaggio.punti_notturni))
                    messageLines.append("dopo %s/%s" % (diurniGiusti, notturniGiusti))
                    messageLines.append(" ")
                    viaggio.punti_diurni = diurniGiusti
                    viaggio.punti_notturni = notturniGiusti
                    viaggio.save()
                    sistemati += 1

        messageLines.append("Errati (e corretti) %d/%d" % (sistemati, len(viaggi)))
    if request.POST.get("spostaILog"):
        from tam.tasks import moveLogs

        moveLogs()
        messages.info(request, "Spostamento dei log iniziato.")

    if request.POST.get("permessiStandard"):
        import tam.views.actions.set_default_permissions as setperm

        setperm.delete_all_permissions()
        setperm.create_missing_permissions()
        setperm.create_missing_groups()
        setperm.set_default_permissions()

    if request.POST.get("deleteAllCorse"):
        messageLines.append("CANCELLO TUTTE LE PRENOTAZIONI e le CORSE")
        Prenotazione.objects.all().delete()
        Viaggio.objects.all().delete()

    if request.POST.get("renewTragitto"):
        messageLines.append("Aggiorno il tragitto precalcolato, senza toccare nient'altro.")
        # passaggio da mediagenerator a django-pipeline...
        #  gli asset precalcolati li lascio senza timestamp
        query_asset_sub = r"""
        -- night
                            UPDATE tam_viaggio
                            SET html_tragitto = regexp_replace(html_tragitto, '/static/img/(night[\d]*)\.[a-z0-9]*\.png', '/static/img/\1.png', 'g')
                            WHERE html_tragitto LIKE '%/static/img%' AND html_tragitto LIKE '%night%';

                            UPDATE tam_viaggio
                            SET html_tragitto = regexp_replace(html_tragitto, '/media/(night[\d]*)\.png', '/static/img/\1.png', 'g')
                            WHERE html_tragitto LIKE '%/media/%' AND html_tragitto LIKE '%night%';

                            UPDATE tam_viaggio
                            SET html_tragitto = regexp_replace(html_tragitto, '/mediaprod/(night[\d]*)-[a-z0-9]*\.png', '/static/img/\1.png', 'g')
                            WHERE html_tragitto LIKE '%/mediaprod/%' AND html_tragitto LIKE '%night%';
        -- morning
                            UPDATE tam_viaggio
                            SET html_tragitto = regexp_replace(html_tragitto, '/static/img/(morning[\d]*)\.[a-z0-9]*\.png', '/static/img/\1.png', 'g')
                            WHERE html_tragitto LIKE '%/static/img%' AND html_tragitto LIKE '%morning%';

                            UPDATE tam_viaggio
                            SET html_tragitto = regexp_replace(html_tragitto, '/media/(morning[\d]*)\.png', '/static/img/\1.png', 'g')
                            WHERE html_tragitto LIKE '%/media/%' AND html_tragitto LIKE '%morning%';

                            UPDATE tam_viaggio
                            SET html_tragitto = regexp_replace(html_tragitto, '/mediaprod/(morning[\d]*)-[a-z0-9]*\.png', '/static/img/\1.png', 'g')
                            WHERE html_tragitto LIKE '%/mediaprod/%' AND html_tragitto LIKE '%morning%';
        --arrow
                            UPDATE tam_viaggio
                            SET html_tragitto = regexp_replace(html_tragitto, '/static/img/(arrow_right)\.[a-z0-9]*\.png', '/static/img/\1.png', 'g')
                            WHERE html_tragitto LIKE '%/static/img%' AND html_tragitto LIKE '%arrow_right%';

                            UPDATE tam_viaggio
                            SET html_tragitto = regexp_replace(html_tragitto, '/media/(arrow_right[\d]*)\.png', '/static/img/\1.png', 'g')
                            WHERE html_tragitto LIKE '%/media/%' AND html_tragitto LIKE '%arrow_right%';

                            UPDATE tam_viaggio
                            SET html_tragitto = regexp_replace(html_tragitto, '/mediaprod/(arrow_right[\d]*)\.png', '/static/img/\1.png', 'g')
                            WHERE html_tragitto LIKE '%/mediaprod/%' AND html_tragitto LIKE '%arrow_right%';

                            UPDATE tam_viaggio
                            SET html_tragitto = regexp_replace(html_tragitto, '/mediaprod/(arrow_right[\d]*)-[a-z0-9]*\.png', '/static/img/\1.png', 'g')
                            WHERE html_tragitto LIKE '%/mediaprod/%' AND html_tragitto LIKE '%arrow_right%';
        --airport
                            UPDATE tam_viaggio
                            SET html_tragitto = regexp_replace(html_tragitto, '/static/(flag/luogo-airport)\.[a-z0-9]*\.png', '/static/\1.png', 'g')
                            WHERE html_tragitto LIKE '%/static/%' AND html_tragitto LIKE '%flag/luogo-airport%';

                            UPDATE tam_viaggio
                            SET html_tragitto = regexp_replace(html_tragitto, '/mediaprod/(flag/luogo-airport[\d]*)-[a-z0-9]*\.png', '/static/\1.png', 'g')
                            WHERE html_tragitto LIKE '%/mediaprod/flag/%' AND html_tragitto LIKE '%luogo-airport%';

                          """.replace("%", "%%")
        from django.db import connection

        cursor = connection.cursor()
        cursor.execute(query_asset_sub)
        connection.commit()
        prossimiviaggi = Viaggio.objects.filter(
            data__gt=tamdates.ita_today() - datetime.timedelta(days=15))
        messageLines.append("Ricalcolo completamente i prossimi viaggi: %s." % len(prossimiviaggi))
        for viaggio in prossimiviaggi:
            viaggio.html_tragitto = viaggio.get_html_tragitto()
            viaggio.save()

    if request.POST.get("setEndDates"):
        # add end dates to latest viaggio (I suppose we don't need it the old ones)
        viaggi = Viaggio.objects.filter(date_end=None, padre_id=None,
                                        data__gt=tamdates.ita_today() - datetime.timedelta(days=15))
        messageLines.append("Imposto la data di fine a %d corse." % len(viaggi))
        for viaggio in viaggi:
            viaggio.date_end = viaggio.get_date_end(recurse=True)
            viaggio.save(updateViaggi=False)

    if request.POST.get('setCustomPermissions'):
        stats_non_model, created = ContentType.objects.get_or_create(
            app_label='stats', model='unused'
        )

        can_see_stats, created = Permission.objects.get_or_create(
            name='can see stats', content_type=stats_non_model,
            codename='can_see_stats')
        messageLines.append(
            "Stats permissions where already there" if not created else "Stats permissions created")

    if request.POST.get('consolidateLog'):
        messageLines.append("Starting moving log files from SQLITE to the default connection")
        sourceLogs = ActionLog.objects.using('modellog').all()
        if len(sourceLogs) > 0:
            existing = ActionLog.objects.all()
            messageLines.append("Deleting the existing logs form the default: %d" % len(existing))
            existing.delete()
            messageLines.append("%d log records to move" % len(sourceLogs))
            ActionLog.objects.bulk_create(sourceLogs, batch_size=1000)
            sourceLogs.delete()
        else:
            messageLines.append("No records to move in SQLITE")
        cursor = db.connection.cursor()
        messageLines.append("Resetting log sequence")
        cursor.execute("""
        BEGIN;
          SELECT setval(pg_get_serial_sequence('"modellog_actionlog"','id'), coalesce(max("id"), 1), max("id") IS NOT NULL) FROM "modellog_actionlog";
        COMMIT;
        """)

    return render(request, template_name, {"messageLines": messageLines, "error": error})
