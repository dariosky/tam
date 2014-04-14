#coding:utf8

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.shortcuts import render_to_response
from django.template.context import RequestContext
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
	utenti = User.objects.all().order_by('username')    # .exclude(is_superuser=True)
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
			messages.error(request, "Tipo di oggetto da loggare non valido %s." % filterType)

	actions = ActionLog.objects.all()
	if filterUtente:        # rendo filterUtente un intero
		try:
			filterUtente = int(filterUtente)
		except:
			messages.error(request, "Utente %s non valido." % filterUtente)
			filterUtente = ""
	if filterId and content_type:        # rendo filterUtente un intero
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
	#			select tam_actionlog.[data] as inserimento, tam_viaggio.[data] as corsa
	#			from tam_actionlog, tam_viaggio
	#			where content_type_id=13
	#			and tam_viaggio.id=tam_actionlog.object_id
	#			and tam_viaggio.[data]<tam_actionlog.[data]
	#			and action_type='A'

	# inserimento postumo se la data della corsa è precedente alla mezzanotte del giorno di inserimento
	#		actions = actions.extra(where=['tam_viaggio.id=tam_actionlog.instance_id',
	#									   'tam_viaggio.data<datetime(tam_actionlog.data,\'start of day\')'],
	#								tables=['tam_viaggio'])

	paginator = Paginator(actions, 60, orphans=3)    # pagine
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
	#		for action in actions:		# evidenzio tutti i viaggio "preInsert"
	#			if action.modelName == 'viaggio':
	#				action.preInsert = False
	#				if action.action_type in ('A', 'M'):
	#					viaggio = Viaggio.objects.get(id=action.instance_id)
	#					action.preInsert = viaggio.data < action.data.replace(hour=0, minute=0)
	except Exception:
		messages.warning(request, "La pagina %d è vuota." % page)
		thisPage = None
		actions = []

	return render_to_response(template_name,
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
							  context_instance=RequestContext(request))
