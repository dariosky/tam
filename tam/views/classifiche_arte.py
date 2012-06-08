#coding: utf-8

CLASSIFICHE = [
			{"nome": "Supplementari mattutini",
			 "mapping_field": "puntiDiurni",
			 'type': 'supplementari',
			 'image': "morning.png",
			},
			{"nome": "Supplementari serali",
			 "mapping_field": "puntiNotturni",
			 'type': 'supplementari',
			 'image': "night.png",
			},
			
			{"nome": "Doppi Venezia",
			 'type':'punti',
			 "mapping_field": "puntiAbbinata",
			},
			
			{"nome": "Doppi Padova",
			 "mapping_field": "prezzoDoppioPadova",
			},
			{"nome": "Venezia",
			 "descrizione": ">=50km",
			 "mapping_field": "prezzoVenezia",
			},
			{"nome": "Padova",
			 "descrizione": ">16€, <50km",
			 "mapping_field": "prezzoPadova",
			},
]

from decimal import Decimal
kmPuntoAbbinate = Decimal(120)

def process_classifiche(viaggio, force_numDoppi=None):
	if viaggio.is_abbinata and viaggio.padre is None: # per i padri abbinati
		da = dettagliAbbinamento(viaggio, force_numDoppi=force_numDoppi)	# trovo i dettagli
		#logging.debug("Sono il padre di un abbinata da %s chilometri. Pricy: %s.\n%s"%(da["kmTotali"], da["pricy"], da) )
		if da["puntiAbbinamento"] > 0:
			viaggio.punti_abbinata = da["puntiAbbinamento"]
			viaggio.prezzoPunti = da["valorePunti"]
			viaggio.prezzoVenezia = da["rimanenteInLunghe"]
		else:	# le corse abbinate senza punti si comportano come le singole
			if da["pricy"]:
				viaggio.prezzoDoppioPadova = da["rimanenteInLunghe"]
			else:
				prezzoNetto = da["rimanenteInLunghe"]
				if da["kmTotali"] >= 50:
					viaggio.prezzoVenezia = prezzoNetto
				elif 25 <= da["kmTotali"] < 50:
					viaggio.prezzoPadova = prezzoNetto
	elif viaggio.padre is None:	# corse non abbinate, o abbinate che non fanno alcun punto
		if viaggio.is_long():
			viaggio.prezzoVenezia = viaggio.prezzo_finale
		elif viaggio.is_medium():
			viaggio.prezzoPadova = viaggio.prezzo_finale
		# i figli non prendono nulla

	if viaggio.padre is None:	# padri e singoli possono avere i supplementi
		for fascia, points in viaggio.disturbi().items():
			if fascia == "night":
				viaggio.punti_notturni += points
			else:
				viaggio.punti_diurni += points


def dettagliAbbinamento(viaggio, force_numDoppi=None):
	""" Restituisce un dizionario con i dettagli dell'abbinamento
		la funzione viene usata solo nel caso la corsa sia un abbinamento (per il padre)
		Il rimanenteInLunghe va aggiunto alle Abbinate Padova se fa più di 1.25€/km alle Venezia altrimenti
	"""
	kmNonConguagliati = 0
	partiAbbinamento = 0
	valoreDaConguagliare = 0
	valorePunti = 0
	puntiAbbinamento = 0
	valoreAbbinate = 0
	rimanenteInLunghe = 0
	kmRimanenti = 0
	pricy = False

	kmTotali = viaggio.get_kmtot()
	#logging.debug("Km totali di %s: %s"%(viaggio.pk, kmTotali))

	if kmTotali == 0: return locals()

	#logging.debug("kmNonConguagliati %s"%kmNonConguagliati)

	forzaSingolo = (force_numDoppi is 0)
	valoreTotale = viaggio.get_valuetot(forzaSingolo=forzaSingolo)

	#kmNonConguagliati= kmTotali - viaggio.km_conguagliati
	#valoreDaConguagliare = viaggio.get_valuetot(forzaSingolo=forzaSingolo) * (kmNonConguagliati) / kmTotali
	#logging.debug("Valore da conguagliare %s"% valoreDaConguagliare)

	baciniDiPartenza = []
	for viaggio in [viaggio] + list(viaggio.viaggio_set.all()):
		bacino = viaggio.da
		if viaggio.da.bacino: bacino = viaggio.da.bacino
		if not bacino in baciniDiPartenza:
			baciniDiPartenza.append(bacino)
		#logging.debug("Bacini di partenza: %d"%len(baciniDiPartenza))
	if len(baciniDiPartenza) > 1:	# se partono tutti dalla stessa zona, non la considero un'abbinata
		partiAbbinamento = kmTotali / kmPuntoAbbinate	# è un Decimal
		puntiAbbinamento = int(partiAbbinamento)
		#logging.debug("Casette abbinamento %d, sarebbero %s" % (puntiAbbinamento, partiAbbinamento))

	if (force_numDoppi is not None) and (force_numDoppi != puntiAbbinamento):
		#logging.debug("Forzo il numero di doppi a %d." % force_numDoppi)
		puntiAbbinamento = min(force_numDoppi, puntiAbbinamento) # forzo di punti doppio, max quello calcolato

	kmRimanenti = kmTotali - (puntiAbbinamento * kmPuntoAbbinate)	# il resto della divisione per 120

	if puntiAbbinamento:
		rimanenteInLunghe = kmRimanenti * Decimal("0.65")  # gli eccedenti li metto nei venezia a 0.65€/km
		#logging.debug("Dei %skm totali, %s sono fuori abbinta a 0.65 vengono %s "%(kmTotali, kmRimanenti, rimanenteInLunghe) )
		valorePunti = (valoreTotale - rimanenteInLunghe) / puntiAbbinamento
		#valorePunti = int(valoreDaConguagliare/partiAbbinamento)	# vecchio modo: valore punti in proporzioned
		valoreAbbinate = puntiAbbinamento * valorePunti
		pricy = False
	else:
		rimanenteInLunghe = Decimal(str(int(valoreTotale - valoreAbbinate))) # vecchio modo: il rimanente è il rimanente
		valorePunti = 0

		if kmRimanenti:
			#lordoRimanente=viaggio.get_lordotot()* (kmNonConguagliati) / kmTotali
			lordoRimanente = viaggio.get_lordotot()
			#logging.debug("Mi rimangono euro %s in %s chilometri"%(lordoRimanente, kmTotali))
			euroAlKm = lordoRimanente / kmTotali
			#logging.debug("I rimanenti %.2fs km sono a %.2f euro/km" % (kmRimanenti, euroAlKm))
			pricy = euroAlKm > Decimal("1.25")
			#if pricy:
			#	logging.debug("Metto nei doppi Padova: %s" %rimanenteInLunghe)
			#else:
			#	logging.debug("Metto nei Venezia: %s" %rimanenteInLunghe)

	if viaggio.km_conguagliati:
		# Ho già conguagliato dei KM, converto i KM in punti (il valore è definito sopra) quei punti li tolgo ai puntiAbbinamento
		#logging.debug("La corsa ha già %d km conguagliati, tolgo %d punti ai %d che avrebbe."  % (
		#				viaggio.km_conguagliati, viaggio.km_conguagliati/kmPuntoAbbinate, puntiAbbinamento) )
		puntiAbbinamento -= (viaggio.km_conguagliati / kmPuntoAbbinate)
	result = {
			"kmTotali":kmTotali,
			"puntiAbbinamento":puntiAbbinamento,
			"valorePunti":valorePunti,
			"rimanenteInLunghe":rimanenteInLunghe,
			"pricy":pricy
		}
	return result

def get_value(viaggio, forzaSingolo=False):
	""" Return the value of this trip on the scoreboard """
	importoViaggio = viaggio.prezzo	# lordo
	forzaSingolo = False	# TMP
	singolo = forzaSingolo or (not viaggio.is_abbinata)
	if forzaSingolo:
		pass
#			logging.debug("Forzo la corsa come fosse un singolo:%s" % singolo)

	if viaggio.commissione:		# tolgo la commissione dal lordo
		if viaggio.tipo_commissione == "P":
			importoViaggio = importoViaggio * (Decimal(1) - viaggio.commissione / Decimal(100))	# commissione in percentuale
		else:
			importoViaggio = importoViaggio - viaggio.commissione

	importoViaggio = importoViaggio - viaggio.costo_autostrada

	# per le corse singole
	if singolo:
		chilometriTotali = viaggio.get_kmtot()
		if chilometriTotali:
			renditaChilometrica = importoViaggio / chilometriTotali
		else:
			renditaChilometrica = 0
		if viaggio.is_long():
			if renditaChilometrica < Decimal("0.65"):
				importoViaggio *= renditaChilometrica / Decimal("0.65")
#					logging.debug("Sconto Venezia sotto rendita: %s" % renditaChilometrica)
		elif viaggio.is_medium():
					if renditaChilometrica < Decimal("0.8"):
						importoViaggio *= renditaChilometrica / Decimal("0.8")
#							logging.debug("Sconto Padova sotto rendita: %s" % renditaChilometrica)

	if viaggio.pagamento_differito or viaggio.fatturazione:	# tolgo gli abbuoni (per differito o altro)
		importoViaggio = importoViaggio * Decimal("0.85")
#		if viaggio.tipo_abbuono=="F":
#			importoViaggio-=viaggio.abbuono
#		else:
#			importoViaggio=importoViaggio* (Decimal(1)-viaggio.abbuono/Decimal(100))	# abbuono in percentuale
	if viaggio.abbuono_percentuale:
		importoViaggio = importoViaggio * (Decimal(1) - viaggio.abbuono_percentuale / Decimal(100))	# abbuono in percentuale
	if viaggio.abbuono_fisso:
		importoViaggio -= viaggio.abbuono_fisso
	importoViaggio = importoViaggio - viaggio.costo_sosta

	importoViaggio += viaggio.prezzo_sosta * Decimal("0.75")	# aggiungo il prezzo della sosta scontato del 25%
	return importoViaggio.quantize(Decimal('.01'))