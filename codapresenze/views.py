# Create your views here.
import datetime
import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.core import serializers
import json
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from codapresenze.models import CodaPresenze
from modellog.actions import logAction
from tam.tamdates import tz_italy
from tam.views.users import get_userkeys


def coda(request, template_name='codapresenze/coda.html'):
	if not request.user.has_perm('codapresenze.view'):
		messages.error(request, 'Non hai accesso alla coda presenze.')
		return HttpResponseRedirect(reverse('tamCorse'))

	if request.method == 'POST':
		actinguser = request.user
		if request.user.has_perm('codapresenze.editall') and 'user' in request.POST:
			try:
				username = request.POST.get('user').strip()
				#print 'Changing user to %s' % username
				actinguser = User.objects.get(username=username)
			except:
				raise Exception("Error changing user")
		posizioneCorrente = CodaPresenze.objects.filter(utente=actinguser)
		messageParts = []
		if 'dequeue' in request.POST or 'place' in request.POST:
			# mi disaccodo
			if posizioneCorrente:
				posizioneCorrente = posizioneCorrente[0]
				messageParts.append("Si disaccoda da %s." % posizioneCorrente.luogo)
				posizioneCorrente.delete()

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

	coda = CodaPresenze.objects.all().values('id', 'utente__username', 'luogo', 'data_accodamento')
	dthandler = lambda obj: obj.astimezone(tz_italy).isoformat() if isinstance(obj, datetime.datetime) else None
	coda = [{"luogo": u["luogo"],
			 "utente": u["utente__username"],
			 "data": u['data_accodamento'],
			 "id": u['id']
			} for u in coda]
	codajson = json.dumps(coda, default=dthandler)

	if request.is_ajax():
		return HttpResponse(codajson, content_type="application/json")

	piazze = getattr(settings, "CODA_PIAZZE", ['Abano', 'Montegrotto'])
	utenti = User.objects.filter(prenotazioni__isnull=True)
	if not request.user.is_superuser:
		utenti = utenti.filter(is_superuser=False)	# solo i superuser vedono i superuser
	utenti = sorted(utenti, key=get_userkeys)

	return render(
		request,
		template_name,
		{
		'codajson': codajson,
		"piazze": piazze,
		'utenti': utenti,
		},
	)
