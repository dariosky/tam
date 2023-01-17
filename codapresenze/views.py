# coding=utf-8
import datetime
import json
import logging
from collections import defaultdict

from decimal import Decimal
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
from tam.models import Conducente, Viaggio
from tam.tamdates import tz_italy, ita_now
from tam.views.users import get_userkeys
from utils.date_views import ThreeMonthsView

logger = logging.getLogger("tam.codapresenze")
MAX_QUEUE_TIME = 60 * 11  # max 11 hours (in minutes)


def dequeue(currentPosition: CodaPresenze):
    """Dequeue from the current position
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
            logger.warning(
                f"Cutting queue time to maximum: {MAX_QUEUE_TIME} instead of {minutes}"
            )
            minutes = MAX_QUEUE_TIME
        logger.debug(
            f"Queue history: {currentPosition.utente}"
            f" @{currentPosition.luogo} for {minutes} minutes"
        )
        story = StoricoPresenze(
            start_date=start,
            user=currentPosition.utente,
            place=currentPosition.luogo,
            minutes=minutes,
        )
        story.save()
    else:
        logger.debug(
            f"{currentPosition.utente} was only {seconds}s@{currentPosition.luogo}"
        )


def coda(request, template_name="codapresenze/coda.html"):
    if not request.user.has_perm("codapresenze.view"):
        messages.error(request, "Non hai accesso alla coda presenze.")
        return HttpResponseRedirect(reverse("tamCorse"))

    if request.method == "POST":
        actinguser = request.user
        if request.user.has_perm("codapresenze.editall") and "user" in request.POST:
            try:
                username = request.POST.get("user").strip()
                # print 'Changing user to %s' % username
                actinguser = User.objects.get(username=username)
            except Exception:
                raise Exception("Error changing user")
        posizioneCorrente = CodaPresenze.objects.filter(utente=actinguser)
        messageParts = []
        if "dequeue" in request.POST or "place" in request.POST:
            # mi disaccodo
            if posizioneCorrente:
                posizioneCorrente = posizioneCorrente[0]
                messageParts.append("Si disaccoda da %s." % posizioneCorrente.luogo)
                dequeue(posizioneCorrente)

        if "place" in request.POST:
            # mi riaccodo
            nuovaPosizione = CodaPresenze(
                utente=actinguser,
                luogo=request.POST.get("place"),
            )
            messageParts.append("Si accoda a %s." % nuovaPosizione.luogo)
            nuovaPosizione.save()

        if messageParts:
            if actinguser != request.user:
                messageParts.append("Effettuato da %s" % request.user)
            logAction("Q", description=" ".join(messageParts), user=actinguser)

    presenzedb = CodaPresenze.objects.all().values(
        "id",
        "utente__username",
        "luogo",
        "data_accodamento",
        "utente__conducente__nick",
    )

    def dthandler(obj):
        if isinstance(obj, datetime.datetime):
            return obj.astimezone(tz_italy).isoformat()

    presenze = [
        {
            "luogo": u["luogo"],
            "utente": u["utente__username"],
            "conducente": u["utente__conducente__nick"],
            "data": u["data_accodamento"],
            "id": u["id"],
        }
        for u in presenzedb
    ]
    codajson = json.dumps(presenze, default=dthandler)

    if request.is_ajax():
        return HttpResponse(codajson, content_type="application/json")

    utenti = User.objects.filter(prenotazioni__isnull=True, is_active=True)
    if not request.user.is_superuser:
        utenti = utenti.filter(
            is_superuser=False
        )  # solo i superuser vedono i superuser
    utenti = sorted(utenti, key=get_userkeys)

    piazze = getattr(settings, "CODA_PIAZZE", ["Abano", "Montegrotto"])
    places = [
        (piazza, "other") if isinstance(piazza, str) else piazza for piazza in piazze
    ]
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
            "codajson": codajson,
            "utenti": utenti,
            "places": places,  # the places
            "queues": queues,  # the groups
            "queueGroupsJson": json.dumps(queueGroupsJson),  # the associations
        },
    )


def humanizeTime(minutes):
    r = minutes
    unit = "m"
    if minutes > 60:
        unit = "h"
        r /= 60
    return f"{r:.1f}{unit}"


class DriverMonthly:
    def __init__(self, driver: Conducente = None, user: User = None) -> None:
        self.driver = driver
        self.user = user
        self.minutes = 0
        self.userWithNoDriver = driver is None
        self.worked_counters = defaultdict(int)
        self.username = "-" if not user else user.username

    def hours(self):
        result = defaultdict(int)
        result.update(
            {t: Decimal(minutes / 60) for t, minutes in self.worked_counters.items()}
        )
        result["tot"] = Decimal(self.minutes / 60)
        result.update(
            {k: round(v, 1) for k, v in result.items()}
        )  # just a single decimal
        return result

    def pretty_worked(self):
        return humanizeTime(self.minutes)

    def add(self, minutes, worked_type):
        self.minutes += minutes
        self.worked_counters[worked_type] += minutes


class FerieView(TemplateView, ThreeMonthsView):
    template_name = "codapresenze/ferie.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queue_history = StoricoPresenze.objects.all()
        months = context["months"]
        date_start, date_end = months.date_start, months.date_end
        # FIXME? start_date is deciding the month, should we count partially?
        queue_history = queue_history.filter(
            start_date__gte=date_start, start_date__lt=date_end
        )
        queue_history = (
            queue_history.order_by()
        )  # remove existing order, or they'll be used as grouper
        queue_history = queue_history.values("user").annotate(minutes=Sum("minutes"))

        confirmed_history = Viaggio.objects.filter(
            date_start__lt=date_end, date_end__gt=date_start, conducente_confermato=True
        ).prefetch_related("conducente")

        users_data = {}
        for driver in Conducente.objects.filter(attivo=True).prefetch_related("user"):
            user = driver.user
            # we list all users_data
            users_data[user.id] = DriverMonthly(driver=driver, user=user)

        def add(user_id, worked_type, minutes):
            logger.debug(f"{user_id} add {humanizeTime(minutes)} {worked_type}")
            if user_id not in users_data:
                users_data[user_id] = DriverMonthly(
                    user=User.objects.get(id=user_id),
                )
            users_data[user_id].add(minutes, worked_type)

        for work_record in queue_history:
            add(work_record["user"], "queue", work_record["minutes"])

        for run in confirmed_history:
            user_id = run.conducente.user_id
            # get the part of the run in this slice
            run_start = max(run.date_start, date_start)
            run_end = min(run.date_end, date_end)
            minutes = (run_end - run_start).seconds / 60

            add(user_id, "run", minutes)

        context["data"] = users_data
        # for d in users_data.values():
        #     d['worked'] = humanizeTime(d['minutes'])
        return context
