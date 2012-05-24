#coding: utf-8
from tam.models import Luogo, get_classifiche, logAction, Cliente, \
	PrezzoListino, Bacino, Tratta, Conducente, Conguaglio, kmPuntoAbbinate, Listino, \
	ProfiloUtente, Viaggio, Passeggero
from django.shortcuts import render_to_response, HttpResponse, get_object_or_404
from django.template.context import RequestContext	 # Context with steroid

def classificheconducenti(request, template_name="classifiche/classifiche-conducenti.html", confirmConguaglio=False):
	user = request.user
	profilo, created = ProfiloUtente.objects.get_or_create(user=user)
	mediabundleJS = ('tamUI.js',)
	mediabundleCSS = ('tamUI.css',)

	conducenti = Conducente.objects.filter(attivo=True)
	if not profilo.luogo:
		messages.error(request, "Devi inserire il luogo preferito per poter calcolare i disturbi.")

	classificheViaggi = get_classifiche()
	classifiche = []
	# alle classifiche estratte da SQL, aggiungo:
	#	il conducente
	#	la lista di punti-valore abbinate
	doppiVenezia = []	# lista per la visualizzazione delle classifiche doppi ordinata è (punti, conducentenick, classifica)
	puntiDiurni = []	# anche le classifiche diurne e notturne le metto in lista per ordinarle qui in vista
	puntiNotturni = []

	punti_assocMin = 0

	for classifica in classificheViaggi:	# creo le classifiche un po' estese
		for conducente in conducenti:
			if conducente.id == classifica["conducente_id"]:
				doppiVenezia.append((classifica["puntiAbbinata"], conducente.nick, classifica))
				puntiDiurni.append((classifica["puntiDiurni"], conducente.nick, classifica))
				puntiNotturni.append((classifica["puntiNotturni"], conducente.nick, classifica))
				classifica["conducente"] = conducente   # aggiungo alle classifiche il campo "conducente" con l'oggetto django del conducente
				classifica["abbinate"] = conducente.viaggio_set.filter(punti_abbinata__gt=0)
				classifica["punti_abbinate"] = []
				classifica["celle_abbinate"] = []
				if conducente.classifica_iniziale_puntiDoppiVenezia:	# aggiungo i punti iniziali
					prezzoPuntiIniziali = conducente.classifica_iniziale_prezzoDoppiVenezia / conducente.classifica_iniziale_puntiDoppiVenezia
					for punto in range(conducente.classifica_iniziale_puntiDoppiVenezia):
						classifica["punti_abbinate"].append(prezzoPuntiIniziali)
						classifica["celle_abbinate"].append({"valore": prezzoPuntiIniziali, "data":None})
				for viaggio in classifica["abbinate"]: # per ogni viaggio
					for punto in range(viaggio.punti_abbinata): # per ogni punto
						classifica["punti_abbinate"].append(viaggio.prezzoPunti)
						classifica["celle_abbinate"].append({"valore": viaggio.prezzoPunti, "data":viaggio.data})
				classifiche.append(classifica)
	doppiVenezia.sort()
	puntiDiurni.sort()
	puntiNotturni.sort()

	if classifiche:
		prezzoDoppioPadovaMax = max([c["prezzoDoppioPadova"] for c in classifiche])
		prezzoVeneziaMax = max([c["prezzoVenezia"] for c in classifiche])
		prezzoPadovaMax = max([c["prezzoPadova"] for c in classifiche])

		punti_assocMax = max([c["puntiAbbinata"] for c in classifiche])
		punti_assocMin = min([c["puntiAbbinata"] for c in classifiche])

	if punti_assocMin:
		totaleConguaglioAbbinate = 0
		for c in classifiche:
			totaleConguaglioAbbinate += sum(c["punti_abbinate"][:punti_assocMin])
		mediaAbbinate = round(totaleConguaglioAbbinate / len(classifiche), 0)
		for c in classifiche:
			c["debitoAbbinate"] = sum(c["punti_abbinate"][:punti_assocMin]) - Decimal(str(mediaAbbinate))
			c["deveDare"] = (c["debitoAbbinate"] > 0)
			if c["deveDare"]: c["debitoAssoluto"] = c["debitoAbbinate"]
			else: c["debitoAssoluto"] = -c["debitoAbbinate"]

	if confirmConguaglio and not user.has_perm('tam.add_conguaglio'):
		messages.error(request, "Non hai il permesso di effettuare conguagli.")
		return HttpResponseRedirect(reverse("tamConducenti"))

	# TMP
#	for c in classifiche:
#		conducente=c["conducente"]
#		if conducente.nick=='16':
#			for viaggio in c["abbinate"]:
#				logging.debug("Viaggio di 16. %s. " % viaggio.id+ "%d punti da %s. "%(viaggio.punti_abbinata, viaggio.prezzoPunti) + "%s/%s km" % (viaggio.km_conguagliati, viaggio.get_kmtot()) )

	if punti_assocMin and confirmConguaglio and ("conguaglia" in request.POST):	# conguaglio
		for c in classifiche:
			conducente = c["conducente"]
#			if conducente.nick!='16':	#TMP
#				logging.debug("Salto il conducente")
#				continue
			puntiDaTogliere = punti_assocMin
			if conducente.classifica_iniziale_puntiDoppiVenezia: # il conducente ha punti iniziali tolgo quelli
				prezzoPuntiIniziali = conducente.classifica_iniziale_prezzoDoppiVenezia / conducente.classifica_iniziale_puntiDoppiVenezia
				puntiInizialiTolti = min(puntiDaTogliere, conducente.classifica_iniziale_puntiDoppiVenezia)
				logging.debug("Tolgo %s punti iniziali da %s a %s." % (puntiInizialiTolti, prezzoPuntiIniziali, conducente.nick))
				conducente.classifica_iniziale_puntiDoppiVenezia -= puntiInizialiTolti
				conducente.classifica_iniziale_prezzoDoppiVenezia -= prezzoPuntiIniziali
				puntiDaTogliere -= puntiInizialiTolti
				conducente.save()

			while puntiDaTogliere > 0:
				for viaggio in c["abbinate"]:
					puntiDaTogliereAlViaggio = min(puntiDaTogliere, viaggio.punti_abbinata)
#					logging.debug("Tolgo %d punti al viaggio %s"%(puntiDaTogliereAlViaggio, viaggio.id))

					puntiDaTogliere -= puntiDaTogliereAlViaggio
#					logging.debug("Non salvo")	#TMP
#					continue
					viaggio.km_conguagliati += kmPuntoAbbinate * puntiDaTogliereAlViaggio
					viaggio.save()
					viaggio.updatePrecomp() # salvo perché mi toglierà i punti

			conguaglio = Conguaglio(conducente=conducente, dare=c["debitoAbbinate"])
			conguaglio.save()
		messages.success(request, "Conguaglio memorizzato.")
		return HttpResponseRedirect(reverse("tamConducenti"))

	tuttiConducenti = Conducente.objects.filter()
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))