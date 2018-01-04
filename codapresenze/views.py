# coding=utf-8
import datetime
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView

from codapresenze.models import CodaPresenze, StoricoPresenze
from modellog.actions import logAction
from tam.models import Conducente
from tam.tamdates import tz_italy, ita_now
from tam.views.users import get_userkeys
from utils.date_views import ThreeMonthsView

logger = logging.getLogger("tam.codapresenze")
MAX_QUEUE_TIME = 60 * 11  # max 11 hours (in minutes)


def dequeue(currentPosition: CodaPresenze):
    """ Dequeue from the current position
        We leave the queue and add to the history
    """
    currentPosition.delete()
    now = ita_now()
    start = currentPosition.data_accodamento
    seconds = (now - start).seconds
    if seconds > 60:
        # minimum 60 seconds
        minutes = seconds // 60
        if minutes > MAX_QUEUE_TIME:
            logger.warning(f'Cutting queue time to maximum: {MAX_QUEUE_TIME} instead of {minutes}')
            minutes = MAX_QUEUE_TIME
        logger.debug(f"Queue history: {currentPosition.utente}"
                     f" @{currentPosition.luogo} for {minutes} minutes")
        story = StoricoPresenze(
            start_date=start,
            user=currentPosition.utente,
            place=currentPosition.luogo,
            minutes=minutes,
        )
        story.save()
    else:
        logger.debug(f"{currentPosition.utente} was only {seconds}s@{currentPosition.luogo}")


def coda(request, template_name='codapresenze/coda.html'):
    if not request.user.has_perm('codapresenze.view'):
        messages.error(request, 'Non hai accesso alla coda presenze.')
        return HttpResponseRedirect(reverse('tamCorse'))

    if request.method == 'POST':
        actinguser = request.user
        if request.user.has_perm('codapresenze.editall') and 'user' in request.POST:
            try:
                username = request.POST.get('user').strip()
                # print 'Changing user to %s' % username
                actinguser = User.objects.get(username=username)
            except Exception:
                raise Exception("Error changing user")
        posizioneCorrente = CodaPresenze.objects.filter(utente=actinguser)
        messageParts = []
        if 'dequeue' in request.POST or 'place' in request.POST:
            # mi disaccodo
            if posizioneCorrente:
                posizioneCorrente = posizioneCorrente[0]
                messageParts.append("Si disaccoda da %s." % posizioneCorrente.luogo)
                dequeue(posizioneCorrente)

        if 'place' in request.POST:
            # mi riaccodo
            nuovaPosizione = CodaPresenze(
                utente=actinguser,
                luogo=request.POST.get('place'),
            )
            messageParts.append("Si accoda a %s." % nuovaPosizione.luogo)
            nuovaPosizione.save()

        if messageParts:
            if actinguser != request.user:
                messageParts.append('Effettuato da %s' % request.user)
            logAction('Q', description=" ".join(messageParts), user=actinguser)

    presenzedb = CodaPresenze.objects.all() \
        .values('id', 'utente__username', 'luogo', 'data_accodamento',
                'utente__conducente__nick')

    def dthandler(obj):
        if isinstance(obj, datetime.datetime):
            return obj.astimezone(tz_italy).isoformat()

    presenze = [{"luogo": u["luogo"],
                 "utente": u["utente__username"],
                 "conducente": u["utente__conducente__nick"],
                 "data": u['data_accodamento'],
                 "id": u['id']
                 } for u in presenzedb]
    codajson = json.dumps(presenze, default=dthandler)

    if request.is_ajax():
        return HttpResponse(codajson, content_type="application/json")

    utenti = User.objects.filter(prenotazioni__isnull=True, is_active=True)
    if not request.user.is_superuser:
        utenti = utenti.filter(is_superuser=False)  # solo i superuser vedono i superuser
    utenti = sorted(utenti, key=get_userkeys)

    piazze = getattr(settings, "CODA_PIAZZE", ['Abano', 'Montegrotto'])
    places = [(piazza, "other") if isinstance(piazza, str) else piazza for piazza in piazze]
    queueGroupsJson = {}
    queues = []

    for piazza in places:
        name, group = piazza
        queueGroupsJson[name] = group
        if group not in queues:
            queues.append(group)

    return render(
        request,
        template_name,
        {
            'codajson': codajson,
            'utenti': utenti,

            "places": places,  # the places
            "queues": queues,  # the groups
            'queueGroupsJson': json.dumps(queueGroupsJson),  # the associations
        },
    )


def humanizeTime(minutes):
    r = minutes
    unit = 'm'
    if minutes > 60:
        unit = 'h'
        r /= 60
    return f'{r:.1f}{unit}'


class FerieView(TemplateView, ThreeMonthsView):
    template_name = 'codapresenze/ferie.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = StoricoPresenze.objects.all()
        months = context['months']
        date_start, date_end = months.date_start, months.date_end
        # FIXME? start_date is deciding the month, should we count partially?
        qs = qs.filter(start_date__gte=date_start, start_date__lt=date_end)
        qs = qs.order_by()  # remove existing order, or they'll be used as grouper
        qs = qs.values('user').annotate(minutes=Sum('minutes'))

        users_data = {}
        for driver in Conducente.objects.filter(attivo=True):
            user = driver.user
            # we list all users_data
            users_data[user.id] = {
                'worked': humanizeTime(minutes=0),
                'userWithNoDriver': False,
                'driver': driver.nick,
                'username': user.username if user else '-'
            }

        for work_record in qs:
            user_id = work_record['user']
            if user_id not in users_data:
                users_data[user_id] = {
                    'userWithNoDriver': True,
                    'userId': user_id,
                    'username': User.objects.get(id=user_id).username,
                }
            users_data[user_id]['worked'] = humanizeTime(work_record['minutes'])

        context['data'] = users_data
        return context
