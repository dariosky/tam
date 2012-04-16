#coding: utf8
from tam.models import Viaggio, Luogo
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
import datetime
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from tam.disturbi import trovaDisturbi, fasce_semilineari

def fixAction(request, template_name="utils/fixAction.html"):
	if not request.user.is_superuser:
		request.user.message_set.create(message=u"Devi avere i superpoteri per eseguire le azioni correttive.")
		return HttpResponseRedirect(reverse("tamUtil"))

	messageLines = []
	error = ""
#	messageLines.append("Nessuna azione correttiva impostata. Meglio tenere tutto fermo di default.")
	if request.POST.get('toV2'):
		#===========================================================================
		# Azione di aggiornamento alla 2.0
		# Aggiungo lo speciale ai luoghi in base al nome
		# Effettuo il vacuum del DB
		from tamArchive.archiveViews import vacuum_db
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

		from django.contrib.auth.models import Group, Permission
		gruppo_potenti = Group.objects.get(name='Potente')
		permessiDaAggiungere = ('get_backup', 'can_backup', 'archive', 'flat')
		for nomePermesso in permessiDaAggiungere:
			p = Permission.objects.get(codename=nomePermesso)
			gruppo_potenti.permissions.add(p)
			messageLines.append('Do agli utenti potenti: %s' % nomePermesso)
		messageLines.append('Vacuum DB.')
		vacuum_db()
		#===========================================================================

	if "Aggiorno i prezzi di Padova e Venezia delle corse degli ultimi 2 mesi" == False:
		corseCambiate = corse = 0

		corseDaSistemare = Viaggio.objects.filter(data__gt=datetime.date.today() - datetime.timedelta(days=60), padre__isnull=True)
	#	corseDaSistemare = Viaggio.objects.filter(pk=44068, padre__isnull=True)
		for corsa in corseDaSistemare:
			oldDPadova = corsa.prezzoDoppioPadova
			oldVenezia = corsa.prezzoVenezia
			corsa.updatePrecomp(forceDontSave=True)
			if oldDPadova <> corsa.prezzoDoppioPadova or oldVenezia <> corsa.prezzoVenezia:
				messageLines.append("%s\n   DPD: %d->%d VE: %d->%d" % (corsa, oldDPadova, corsa.prezzoDoppioPadova, oldVenezia, corsa.prezzoVenezia))
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
		corsa.updatePrecomp() # salvo perché mi toglierà i punti

		corsa = Viaggio.objects.filter(pk=38740)[0]
		corsa.km_conguagliati = 0
		corsa.save()
		corsa.updatePrecomp() # salvo perché mi toglierà i punti

		corsa = Viaggio.objects.filter(pk=38887)[0]
		corsa.km_conguagliati = 0
		corsa.save()
		corsa.updatePrecomp() # salvo perché mi toglierà i punti

		status()

	if request.POST.get('fixDisturbi'):
		""" Per le corse abbinate, dove l'ultimo fratello è un aereoporto ricalcolo i distrubi """
		print "Refixo"
		viaggi = Viaggio.objects.filter(is_abbinata__in=('P', 'S'), date_start__gt=datetime.datetime(2012, 3, 1), padre=None)
		sistemati = 0
		for viaggio in viaggi:
			ultimaCorsa = viaggio.lastfratello()
			if ultimaCorsa.da.speciale == 'A':

				disturbiGiusti = trovaDisturbi(viaggio.date_start, viaggio.date_end(recurse=True), metodo=fasce_semilineari)
				notturniGiusti = disturbiGiusti.get('night', 0)
				diurniGiusti = disturbiGiusti.get('morning', 0)
				if diurniGiusti <> viaggio.punti_diurni or notturniGiusti <> viaggio.punti_notturni:
					messageLines.append(viaggio)
					messageLines.append(ultimaCorsa)
					messageLines.append("prima %s/%s" % (viaggio.punti_diurni, viaggio.punti_notturni))
					messageLines.append("dopo %s/%s" % (diurniGiusti, notturniGiusti))
					messageLines.append(" ");
					viaggio.punti_diurni=diurniGiusti
					viaggio.punti_notturni=notturniGiusti
					viaggio.save()
					sistemati += 1

		messageLines.append("Errati (e corretti) %d/%d" % (sistemati, len(viaggi)))


	return render_to_response(template_name, {"messageLines":messageLines, "error":error},
							context_instance=RequestContext(request))
