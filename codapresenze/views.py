# Create your views here.
import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core import serializers
import json
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from codapresenze.models import CodaPresenze
from modellog.actions import logAction
from tam import tamdates
from tam.tamdates import tz_italy


def coda(request, template_name='codapresenze/coda.html'):
	if not request.user.has_perm('codapresenze.view'):
		messages.error(request, 'Non hai accesso alla coda presenze.')
		return HttpResponseRedirect(reverse('tamCorse'))

	if request.method == 'POST':
		posizioneCorrente = CodaPresenze.objects.filter(utente=request.user)
		message = ""
		if 'dequeue' in request.POST or 'place' in request.POST:
			# mi disaccodo
			if posizioneCorrente:
				posizioneCorrente = posizioneCorrente[0]
				message += " si disaccoda da %s" % posizioneCorrente.luogo
				posizioneCorrente.delete()


		if 'place' in request.POST:
			# mi riaccodo
			nuovaPosizione = CodaPresenze(
				utente=request.user,
				luogo=request.POST.get('place'),
			)
			message += " e si accoda a %s" % nuovaPosizione.luogo
			nuovaPosizione.save()

		if message:
			logAction('Q', description=message, user=request.user)

	coda = CodaPresenze.objects.all().values('id', 'utente__username', 'luogo', 'data_accodamento')
	dthandler = lambda obj: obj.astimezone(tz_italy).isoformat() if isinstance(obj, datetime.datetime) else None
	coda = [{"luogo": u["luogo"],
	         "utente": u["utente__username"],
	         "data": u['data_accodamento'],
	         "id": u['id']
	        } for u in coda]
	codajson = json.dumps(coda, default=dthandler)

	if request.is_ajax():
		return HttpResponse(codajson, mimetype="application/json")

	piazze = getattr(settings, "CODA_PIAZZE", ['Abano', 'Montegrotto'])

	return render(
		request,
		template_name,
		{'coda': coda,
		 'codajson': codajson,
		 "piazze": piazze,
		},
	)
