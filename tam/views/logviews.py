#coding:utf8

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from tam.models import ActionLog, logAction
from tam.views.tamviews import SmartPager
import datetime
import logging
from django.contrib.sessions.models import Session

def logAndCleanExpiredSessions():
    """ Clear all the expired sessions and log the disconnection of the users """
    for s in Session.objects.filter(expire_date__lt=datetime.datetime.now()):
        data = s.get_decoded()
        if data.has_key('_auth_user_id'):
            user = User.objects.get(id=data['_auth_user_id'])
            logAction('O', user, 'Sessione scaduta', user, log_date=s.expire_date)
        s.delete()

def actionLog(request, template_name="utils/actionLog.html"):
    user = request.user
    logAndCleanExpiredSessions()
    utenti = User.objects.all() #exclude(is_superuser=True)
    filterUtente = request.GET.get('user', '')
    filterType = request.GET.get('type', '')
    filterId = request.GET.get('id', '')
    filterAction = request.GET.get('action', '')
    filterPreInsert = 'preInsert' in request.GET.keys()    # se ho preinsert cerco tutte le inserite postume
    content_type = None
    viaggioType = ContentType.objects.get(app_label="tam", model='viaggio')
    if filterType:
        try:
            content_type = ContentType.objects.get(app_label="tam", model=filterType)
        except:
            user.message_set.create(message=u"Tipo di oggetto non valido %s." % filterType)

    actions = ActionLog.objects.all()
    if filterUtente:        # rendo filterUtente un intero
        try:
            filterUtente = int(filterUtente)
        except:
            user.message_set.create(message=u"Utente %s non valido." % filterUtente)
            filterUtente = ""
    if filterId and content_type:        # rendo filterUtente un intero
        try:
            filterId = int(filterId)
        except:
            user.message_set.create(message=u"ID %s non valido." % filterId)
            filterId = ""


    if filterUtente:
        logging.debug("Filtro per utente %s" % filterUtente)
        actions = actions.filter(user__id=filterUtente)
    if content_type:
        logging.debug("Filtro per tipo oggetto %s" % content_type)
        actions = actions.filter(content_type=content_type)
    if filterId:
        logging.debug("Filtro per id %s" % filterId)
        actions = actions.filter(object_id=filterId)
    if filterAction:
        actions = actions.filter(action_type=filterAction)
    if filterPreInsert:
        actions = actions.filter(content_type=viaggioType)
        actions = actions.filter(action_type__in=('A', 'M'))
#            select tam_actionlog.[data] as inserimento, tam_viaggio.[data] as corsa
#            from tam_actionlog, tam_viaggio
#            where content_type_id=13
#            and tam_viaggio.id=tam_actionlog.object_id
#            and tam_viaggio.[data]<tam_actionlog.[data]
#            and action_type='A'

        # inserimento postumo se la data della corsa è precedente alla mezzanotte del giorno di inserimento
        actions = actions.extra(where=['tam_viaggio.id=tam_actionlog.object_id', 'tam_viaggio.data<datetime(tam_actionlog.data,\'start of day\')'], tables=['tam_viaggio'])

    paginator = Paginator(actions, 60, orphans=3)    # pagine
    page = request.GET.get("page", 1)
    try: page = int(page)
    except: page = 1

    s = SmartPager(page, paginator.num_pages)
    paginator.smart_page_range = s.results

    try:
        thisPage = paginator.page(page)
        actions = thisPage.object_list
        for action in actions:
            if action.content_type == viaggioType:
                action.preInsert = (action.action_type in ('A', 'M')
                                    and action.content_object
                                    and action.content_object.data < action.data.replace(hour=0, minute=0))
    except Exception:
        user.message_set.create(message=u"La pagina %d è vuota." % page)
        thisPage = None
        actions = []

    return render_to_response(template_name,
                              {
                                "actions":actions,
                                "today": datetime.date.today(),
                                "thisPage":thisPage,
                                "paginator":paginator,
                                "utenti":utenti,
                                'filterAction':filterAction,
                                "filterUtente":filterUtente,
                                "filterPreInsert":filterPreInsert,
                                "viaggioType":viaggioType
                              },
                              context_instance=RequestContext(request))