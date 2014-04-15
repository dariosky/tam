#coding: utf-8
""" Definizione delle CLASSIFICHE
È una lista ordinata di dizionari
nome
descrizione (facoltativa)
mapping field (per indicare da che campo (dei viaggi) viene popolata la classifica
function (si usa per popolare i valori nel record del viaggio in modifica)
type (predefinito è 'prezzo', potrebbe essere anche 'punti' o 'supplementari')

verranno aggiungi in visualizzazione:
			 'dati': con una lista ordinata per mapping_field di (chiave, conducente.nick, classifica)
			   dove classifica tiene tutti i dati classifica del conducente (presi da SQL),
			 	un campo 'conducente'
			 	se è una classifica a punti tiene anche altri 3 campi:
			 		abbinate: con tutti i viaggi del conducente ancora non completamente conguagliati
			 		celle abbinate: una lista di punti del tipo {valore: x, data: x}
			 'min', 'max': con i valori chiave massimi e minimi

"""
import pytz

CLASSIFICHE = [
	{"nome": "Venezia",
	 "descrizione": ">=60km",
	 "mapping_field": "prezzoVenezia",
	 'viaggio_field': 'prezzoVenezia',
	 'ignore_if_field': 'punti_abbinata',  # ignoro questa classifica se ho dei punti abbinata
	},
	{"nome": "Supplementari mattutini",
	 "mapping_field": "puntiDiurni",
	 'type': 'supplementari',
	 'image': "img/morning.png",
	 'viaggio_field': 'punti_diurni',
	},
	{"nome": "Supplementari serali",
	 "mapping_field": "puntiNotturni",
	 'type': 'supplementari',
	 'image': "img/night.png",
	 'viaggio_field': 'punti_notturni',
	},
	{"nome": "Doppi Venezia",
	 'type': 'punti',
	 "mapping_field": "punti_abbinata",
	 "viaggio_field": "punti_abbinata",
	},
	{"nome": "Doppi Padova",
	 "mapping_field": "prezzoDoppioPadova",
	 'viaggio_field': 'prezzoDoppioPadova',
	},
	{"nome": "Padova",
	 "descrizione": ">16€, <60km",
	 "mapping_field": "prezzoPadova",
	 'viaggio_field': 'prezzoPadova',
	},
]
NOMI_CAMPI_CONDUCENTE = {}  # tutto dai modelli

from decimal import Decimal

kmPuntoAbbinate = Decimal(120)


def process_classifiche(viaggio, force_numDoppi=None):
	if viaggio.is_abbinata and viaggio.padre is None:  # per i padri abbinati
		da = dettagliAbbinamento(viaggio, force_numDoppi=force_numDoppi)  # trovo i dettagli
		#print("Sono il padre di un abbinata da %s chilometri. Pricy: %s.\n%s"%(da["kmTotali"], da["pricy"], da) )
		if da["puntiAbbinamento"] > 0:
			viaggio.punti_abbinata = da["puntiAbbinamento"]
			viaggio.prezzoPunti = da["valorePunti"]
			viaggio.prezzoVenezia = da["rimanenteInLunghe"]
		else:  # le corse abbinate senza punti si comportano come le singole
			if da["pricy"]:
				viaggio.prezzoDoppioPadova = da["rimanenteInLunghe"]
			else:
				prezzoNetto = da["rimanenteInLunghe"]
				if da["kmTotali"] >= getattr(settings, 'KM_PER_LUNGHE', 50):
					viaggio.prezzoVenezia = prezzoNetto
				elif 25 <= da["kmTotali"] < getattr(settings, 'KM_PER_LUNGHE', 50):
					viaggio.prezzoPadova = prezzoNetto
	elif viaggio.padre_id is None:  # corse non abbinate, o abbinate che non fanno alcun punto
		if viaggio.is_long():
			viaggio.prezzoVenezia = viaggio.prezzo_finale
		elif viaggio.is_medium():
			viaggio.prezzoPadova = viaggio.prezzo_finale
		# i figli non prendono nulla

	if viaggio.padre_id is None:  # padri e singoli possono avere i supplementi
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
	for cursore in [viaggio] + list(viaggio.viaggio_set.all()):
		bacino = cursore.da
		if cursore.da.bacino: bacino = cursore.da.bacino
		if not bacino in baciniDiPartenza:
			baciniDiPartenza.append(bacino)
		#logging.debug("Bacini di partenza: %d"%len(baciniDiPartenza))
	if len(baciniDiPartenza) > 1:  # se partono tutti dalla stessa zona, non la considero un'abbinata
		partiAbbinamento = kmTotali / kmPuntoAbbinate  # è un Decimal
		puntiAbbinamento = int(partiAbbinamento)
	#logging.debug("Casette abbinamento %d, sarebbero %s" % (puntiAbbinamento, partiAbbinamento))

	if (force_numDoppi is not None) and (force_numDoppi != puntiAbbinamento):
		#logging.debug("Forzo il numero di doppi a %d." % force_numDoppi)
		puntiAbbinamento = min(force_numDoppi, puntiAbbinamento)  # forzo di punti doppio, max quello calcolato

	kmRimanenti = kmTotali - (puntiAbbinamento * kmPuntoAbbinate)  # il resto della divisione per 120

	if puntiAbbinamento:
		rimanenteInLunghe = kmRimanenti * Decimal("0.65")  # gli eccedenti li metto nei venezia a 0.65€/km
		#logging.debug("Dei %skm totali, %s sono fuori abbinta a 0.65 vengono %s "%(kmTotali, kmRimanenti, rimanenteInLunghe) )
		valorePunti = (valoreTotale - rimanenteInLunghe) / puntiAbbinamento
		#valorePunti = int(valoreDaConguagliare/partiAbbinamento)	# vecchio modo: valore punti in proporzioned
		valoreAbbinate = puntiAbbinamento * valorePunti
		pricy = False
	else:
		rimanenteInLunghe = Decimal(
			str(int(valoreTotale - valoreAbbinate)))  # vecchio modo: il rimanente è il rimanente
		valorePunti = 0

		if kmRimanenti:
			#lordoRimanente=viaggio.get_lordotot()* (kmNonConguagliati) / kmTotali
			lordoRimanente = viaggio.get_lordotot()
			#logging.error("Mi rimangono euro %s in %s chilometri"%(lordoRimanente, kmTotali))
			euroAlKm = lordoRimanente / kmTotali
			#logging.error("I rimanenti %.2fs km sono a %.2f euro/km" % (kmRimanenti, euroAlKm))
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
	"kmTotali": kmTotali,
	"puntiAbbinamento": puntiAbbinamento,
	"valorePunti": valorePunti,
	"rimanenteInLunghe": rimanenteInLunghe,
	"pricy": pricy
	}
	return result


def get_value(viaggio, forzaSingolo=False):
	""" Return the value of this trip on the scoreboard """
	importoViaggio = viaggio.prezzo  # lordo
	forzaSingolo = False  # TMP
	singolo = forzaSingolo or (not viaggio.is_abbinata)
	if forzaSingolo:
		pass
	#			logging.debug("Forzo la corsa come fosse un singolo:%s" % singolo)

	if viaggio.commissione:  # tolgo la commissione dal lordo
		if viaggio.tipo_commissione == "P":
			importoViaggio = importoViaggio * (
			Decimal(1) - viaggio.commissione / Decimal(100))  # commissione in percentuale
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

	if (
		viaggio.pagamento_differito or viaggio.fatturazione) and settings.SCONTO_FATTURATE:  # tolgo gli abbuoni (per differito o altro)
		importoViaggio = importoViaggio * (100 - settings.SCONTO_FATTURATE) / Decimal(100)
	if viaggio.abbuono_fisso:
		importoViaggio -= viaggio.abbuono_fisso
	if viaggio.abbuono_percentuale:
		importoViaggio = importoViaggio * (
		Decimal(1) - viaggio.abbuono_percentuale / Decimal(100))  # abbuono in percentuale
	importoViaggio = importoViaggio - viaggio.costo_sosta

	if settings.SCONTO_SOSTA:
		importoViaggio += viaggio.prezzo_sosta * (
		Decimal(1) - settings.SCONTO_SOSTA / Decimal(100))  # aggiungo il prezzo della sosta scontato del 25%
	else:
		importoViaggio += viaggio.prezzo_sosta  # prezzo sosta intero
	return importoViaggio.quantize(Decimal('.01'))


GET_VALUE_FUNCTION = get_value
PROCESS_CLASSIFICHE_FUNCTION = process_classifiche
KM_PUNTO_ABBINATE = kmPuntoAbbinate

tz_italy = pytz.timezone('Europe/Rome')


def gettoneDoppioSeFeriale(calendar):
	"""
		Restituisce il valore a gettoni, doppio se il calendario è in un giorno festivo o prefestivo
	"""
	reference_date = calendar.date_start.astimezone(tz_italy)
	if reference_date.weekday() in (5, 6):
		return 2
	md = reference_date.timetuple()[1:3]
	if md in (
	(1, 1),  # Capodanno
	(1, 6),  # Epifania
	(4, 25),  # 25 aprile
	(5, 1),  # primo maggio, festa del lavoro
	(6, 2),  # 2 giugno, festa della repubblica
	(8, 15),  # ferragosto
	(11, 1),  # ognissanti
	(12, 8),  # immacolata
	(12, 25),  # Natale
	(12, 26),  # S.Stefano
	):
		return 2

	return 1


def cal_display_mattino_pomeriggio(calendar):
	reference_date = calendar.date_start.astimezone(tz_italy)
	result = u""
	if reference_date.hour <= 12:
		result += u"mattino"
	else:
		result += u"pomeriggio"
	if calendar.value > 1:
		result += u" x%d" % calendar.value
	return result


def cal_display_all_day(calendar):
	result = u"Tutto il giorno"
	if calendar.value > 1:
		result += u" x%d" % calendar.value
	return result


from django.conf import settings
