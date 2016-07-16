# coding:utf-8

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.shortcuts import render
from modellog.actions import logAction
from modellog.models import ActionLog
from tam.views.tamviews import SmartPager
import logging
from django.contrib.sessions.models import Session
from django.contrib import messages
from django.utils import timezone
from tam import tamdates


def getTrace():
    """ Return current traceback as a string """
    import traceback
    import StringIO

    fp = StringIO.StringIO()
    traceback.print_exc(file=fp)
    return fp.getvalue()


def logAndCleanExpiredSessions():
    """ Clear all the expired sessions and log the disconnection of the users """
    for s in Session.objects.filter(expire_date__lt=timezone.now()):
        data = s.get_decoded()
        try:
            if '_auth_user_id' in data:
                user = User.objects.get(id=data['_auth_user_id'])
                logAction('O', user=user, description='Sessione scaduta', log_date=s.expire_date)
        except:
            pass
        s.delete()


def actionLog(request, template_name="actionLog.html"):
    logAndCleanExpiredSessions()
    from_a_superuser = request.user.is_superuser
    utenti = User.objects.all().order_by('username')
    if not from_a_superuser:
        utenti = utenti.exclude(is_superuser=True)  # normal users don't see superusers
    filterUtente = request.GET.get('user', '')
    filterType = request.GET.get('type', '')
    filterId = request.GET.get('id', '')
    filterAction = request.GET.get('action', '')
    filterPreInsert = 'preInsert' in request.GET.keys()  # se ho preinsert cerco tutte le inserite postume
    content_type = None
    viaggioType = ContentType.objects.get(app_label="tam", model='viaggio')
    if filterType:
        if filterType == 'fattura':
            content_type = ContentType.objects.get(app_label="fatturazione", model='fattura')
        else:
            try:
                content_type = ContentType.objects.get(app_label="tam", model=filterType)
            except ContentType.DoesNotExist:
                messages.error(request, "Tipo di oggetto da loggare non valido %s." % filterType)

    actions = ActionLog.objects.all()
    if filterUtente:  # rendo filterUtente un intero
        try:
            filterUtente = int(filterUtente)
        except:
            messages.error(request, "Utente %s non valido." % filterUtente)
            filterUtente = ""
    if filterId and content_type:  # rendo filterUtente un intero
        try:
            filterId = int(filterId)
        except:
            messages.error(request, "ID %s non valido." % filterId)
            filterId = ""
    if filterUtente:
        logging.debug("Filtro per utente %s" % filterUtente)
        actions = actions.filter(user_id=filterUtente)
    if content_type:
        logging.debug("Filtro per tipo oggetto %s" % content_type.model)
        actions = actions.filter(modelName=content_type.model)
    if filterId:
        logging.debug("Filtro per id %s" % filterId)
        actions = actions.filter(instance_id=filterId)
    if filterAction:
        actions = actions.filter(action_type=filterAction)
    if filterPreInsert:
        actions = actions.filter(modelName='viaggio')
        actions = actions.filter(action_type__in=('A', 'M'))
        actions = actions.filter(hilight=True)
    if not from_a_superuser:
        superuser_ids = User.objects.filter(is_superuser=True).values_list('id', flat=True)
        actions = actions.exclude(user_id__in=superuser_ids)  # hide superactions to normal

    # inserimento postumo se la data della corsa è precedente alla mezzanotte del
    # giorno di inserimento

    paginator = Paginator(actions, 60, orphans=3)  # pagine
    page = request.GET.get("page", 1)
    try:
        page = int(page)
    except:
        page = 1

    s = SmartPager(page, paginator.num_pages)
    paginator.smart_page_range = s.results

    try:
        thisPage = paginator.page(page)
        actions = thisPage.object_list
    # for action in actions:		# evidenzio tutti i viaggio "preInsert"
    #			if action.modelName == 'viaggio':
    #				action.preInsert = False
    #				if action.action_type in ('A', 'M'):
    #					viaggio = Viaggio.objects.get(id=action.instance_id)
    #					action.preInsert = viaggio.data < action.data.replace(hour=0, minute=0)
    except Exception:
        messages.warning(request, "La pagina %d è vuota." % page)
        thisPage = None
        actions = []

    return render(request,
                  template_name,
                  {
                      "actions": actions,
                      "today": tamdates.ita_today(),
                      "thisPage": thisPage,
                      "paginator": paginator,
                      "utenti": utenti,
                      'filterAction': filterAction,
                      "filterUtente": filterUtente,
                      "filterPreInsert": filterPreInsert,
                      "viaggioType": viaggioType
                  },
                  )
