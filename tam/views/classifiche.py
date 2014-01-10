#coding: utf-8
import copy
from tam.models import get_classifiche, Conducente, Conguaglio, ProfiloUtente
from django.shortcuts import render_to_response
from django.template.context import RequestContext	 # Context with steroid
from decimal import Decimal
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
import logging
from django.utils.safestring import mark_safe
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

def conguaglia(classifica_definita):
	kmPuntoAbbinate = settings.KM_PUNTO_ABBINATE
	# todo: la classifica dovrebbe definire i due campi del conducente da cui prendere i valoro iniziali
#	viaggiSalvati = 0
	for key, nick, classifica in classifica_definita['dati']: #@UnusedVariable
		conducente = classifica["conducente"]
		puntiDaTogliere = classifica_definita['min']
		if conducente.classifica_iniziale_puntiDoppiVenezia: # il conducente ha punti iniziali tolgo quelli
			prezzoPuntiIniziali = conducente.classifica_iniziale_prezzoDoppiVenezia / conducente.classifica_iniziale_puntiDoppiVenezia
			puntiInizialiTolti = min(puntiDaTogliere, conducente.classifica_iniziale_puntiDoppiVenezia)
			logging.debug("Tolgo %s punti iniziali da %s a %s." % (puntiInizialiTolti, prezzoPuntiIniziali, conducente.nick))
			conducente.classifica_iniziale_puntiDoppiVenezia -= puntiInizialiTolti
			conducente.classifica_iniziale_prezzoDoppiVenezia -= prezzoPuntiIniziali
			puntiDaTogliere -= puntiInizialiTolti
			conducente.save()

		while puntiDaTogliere > 0:
			for viaggio in classifica["abbinate"]:
				puntiDaTogliereAlViaggio = min(puntiDaTogliere, viaggio.punti_abbinata)
				if puntiDaTogliereAlViaggio == 0: continue
#				logging.debug("Tolgo %d punti al viaggio %s"%(puntiDaTogliereAlViaggio, viaggio.id))

				puntiDaTogliere -= puntiDaTogliereAlViaggio
#				print "Non salvo %s,%s - %d" % (conducente, viaggio.id, puntiDaTogliereAlViaggio)
#				viaggiSalvati += 1
#				continue
				viaggio.km_conguagliati += kmPuntoAbbinate * puntiDaTogliereAlViaggio
				viaggio.save()
				viaggio.updatePrecomp() # salvo perché mi toglierà i punti

		conguaglio = Conguaglio(conducente=conducente, dare=classifica["debitoAbbinate"])
		conguaglio.save()
#	print 'avrei modificato %d viaggi' % viaggiSalvati


def classificheconducenti(request, template_name="classifiche/classifiche-conducenti.html", confirmConguaglio=False):
	user = request.user
	profilo, created = ProfiloUtente.objects.get_or_create(user=user) #@UnusedVariable
	mediabundleJS = ('tamUI',)
	mediabundleCSS = ('tamUI',)

	if not profilo.luogo:
		messages.error(request, "Devi inserire il luogo preferito per poter calcolare i disturbi.")
		return HttpResponseRedirect('/')

	if confirmConguaglio and not user.has_perm('tam.add_conguaglio'):
		messages.error(request, "Non hai il permesso di effettuare conguagli.")
		return HttpResponseRedirect(reverse("tamConducenti"))


	classificheViaggi = get_classifiche()
	# alle classifiche estratte da SQL, aggiungo:
	#	il conducente
	#	la lista di punti-valore abbinate

	conducenti = Conducente.objects.filter(attivo=True)
	conducente_byId = {}	# dizionario id->conducente
	for conducente in conducenti: conducente_byId[conducente.id] = conducente

	classifiche_definite = copy.deepcopy(settings.CLASSIFICHE)

	# prendo le classifiche definite e le mappo per ID
	classifiche_definite_byId = {}
	for classifica_definita in classifiche_definite:
		classifiche_definite_byId[classifica_definita.get('mapping_field')] = classifica_definita
		classifica_definita['dati'] = []

	if confirmConguaglio:	# se sto confermando tolgo tutte le classifiche tranne quella punti_abbinata
		classifiche_definite = [classifiche_definite_byId['punti_abbinata']]

	for classifica in classificheViaggi:	# creo le classifiche un po' estese
		conducente = conducente_byId[classifica["conducente_id"]] # prendo il conducente
		classifica["conducente"] = conducente   # aggiungo alle classifiche il campo conducente

		for key in ('puntiDiurni', 'puntiNotturni',
					'punti_abbinata',
					'prezzoPadova', 'prezzoVenezia', 'prezzoDoppioPadova'):
			# se ho una classifica con questa chiave le aggiungo i dati
			if key in classifiche_definite_byId:
				classifiche_definite_byId[key]['dati'].append((classifica[key], conducente.nick, classifica))
				if key == 'punti_abbinata':
					classifica["abbinate"] = conducente.viaggio_set.filter(punti_abbinata__gt=0)
					classifica["celle_abbinate"] = []
					if conducente.classifica_iniziale_puntiDoppiVenezia:	# aggiungo i punti iniziali
						prezzoPuntiIniziali = conducente.classifica_iniziale_prezzoDoppiVenezia / conducente.classifica_iniziale_puntiDoppiVenezia
						for punto in range(conducente.classifica_iniziale_puntiDoppiVenezia):
							classifica["celle_abbinate"].append({"valore": prezzoPuntiIniziali, "data":None})
					for viaggio in classifica["abbinate"]: # per ogni viaggio
						for punto in range(viaggio.punti_abbinata): # per ogni punto
							classifica["celle_abbinate"].append({"valore": viaggio.prezzoPunti, "data":viaggio.data})
		#classifiche.append(classifica)

	for classifica_definita in classifiche_definite:	# ordino i dati
		classifica_definita['dati'].sort()
		classifica_definita['min'] = classifica_definita["dati"][0][0]	# prendo la chiave del primo valore
		classifica_definita['max'] = classifica_definita["dati"][-1][0]	# prendo la chiave del'ultimo valore
		if classifica_definita.get("type") == "punti" and classifica_definita['min']: # abbiamo un minimo da conguagliare
			punti_assocMin = classifica_definita['min'] # punti comuni a tutti gli attivi da conguagliare
			totaleConguaglioAbbinate = 0
			for key, nick, classifica in classifica_definita['dati']:
				totaleConguaglioAbbinate += sum([punto['valore'] for punto in classifica["celle_abbinate"][:punti_assocMin]])
			mediaAbbinate = round(totaleConguaglioAbbinate / len(classifica_definita['dati']), 2)
			for key, nick, classifica  in classifica_definita['dati']:
				classifica["debitoAbbinate"] = sum([punto['valore'] for punto in classifica["celle_abbinate"][:punti_assocMin]]) - Decimal(str(mediaAbbinate))
				classifica["deveDare"] = (classifica["debitoAbbinate"] > 0)
				if classifica["deveDare"]: classifica["debitoAssoluto"] = classifica["debitoAbbinate"]
				else: classifica["debitoAssoluto"] = -classifica["debitoAbbinate"]
			classifica_definita['totaleConguaglio'] = totaleConguaglioAbbinate
			classifica_definita['mediaAbbinate'] = 	mediaAbbinate
			if confirmConguaglio and ("conguaglia" in request.POST):
				conguaglia(classifica_definita)
				messages.success(request, "Conguaglio memorizzato.")
				return HttpResponseRedirect(reverse("tamConducenti"))

	tuttiConducenti = Conducente.objects.all()
	return render_to_response(template_name,
							  {
							   'tuttiConducenti': tuttiConducenti,
							   'mediabundleJS':mediabundleJS, 'mediabundleCSS':mediabundleCSS,
							   'classifiche_definite': classifiche_definite,

							   'confirmConguaglio':confirmConguaglio,
							  },
							  context_instance=RequestContext(request))


def descrizioneDivisioneClassifiche(viaggio):
	""" A seconda dei punti nei campi del viaggio riporto la descrizione di come è stato suddiviso nelle classifiche """
	classifiche_definite = settings.CLASSIFICHE
	result = ""
	for classifica in classifiche_definite:
		tipo_classifica = classifica.get('type', 'prezzo')
		if tipo_classifica == 'prezzo':
			field = classifica.get('mapping_field')
			valore = getattr(viaggio, field, None)
			if field and valore:
				result += "%(valore)s %(prefix)s %(nome)s. " % {"valore":valore,
																"prefix":classifica.get("prefix", "nei"),
																"nome":classifica['nome']}
		elif tipo_classifica == 'punti':
			field = classifica.get('mapping_field')
			punti = getattr(viaggio, field)
			if punti > 0 :
				result += ('<img src="%s" alt="DV" />' % staticfiles_storage.url('img/casina.png')) * punti
				result += '<br/>'
				result += "%(punti)d x %(valore)s nei %(nome)s.<br/>" % {"punti":punti,
																		 "valore":viaggio.prezzoPunti,
																		 "prefix":classifica.get("prefix", "nei"),
																		 "nome":classifica["nome"]}

	result = mark_safe(result)
	return result
