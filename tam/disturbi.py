#coding: utf-8

import datetime
from math import ceil, floor

def fascia_uno_o_due_disturbi(fascia_start, fascia_end, date_start, date_end,
							 punti_fascia, tipo, results={}):
	intersection_start = max(fascia_start, date_start)
	intersection_end = min(fascia_end, date_end)
	if intersection_start <= intersection_end:
		#print "Tocco la fascia %s-%s" % (fascia_start, fascia_end)
		results[tipo] = max(results.get(tipo, 0), punti_fascia) # massimo due punti


def fascia_quarti_lineari(fascia_start, fascia_end, date_start, date_end,
				    minuti_per_quarto, tipo, results={}):
	""" Aggiungo a result il codice della fascia (night o morning) con i punti corrispondenti
		nel solo giorno indicato (in trovaDisturbi itero tra giorni e fasce)
		
		la corsa tra date_start e date_end tocca nel giorno indicato da dayMarker tra le ore h_start:m_start e h_end:m_end
		Controllo se date_start cade nella fascia per contarlo
		o se date_end è nella fascia
		o se date_start è prima della fascia e date_end è dopo
	"""
	intersection_start = max(fascia_start, date_start)
	intersection_end = min(fascia_end, date_end)
	if intersection_start <= intersection_end:
#		print "Disturbo dalle %s alle %s ogni %d minuti" % (intersection_start, intersection_end, minuti_per_quarto)
		intersezione = (intersection_end - intersection_start)
		minuti = intersezione.days * (24 * 60 * 60) + (intersezione.seconds / 60) # calcolo la durata in minuti dell'intersezione
		if minuti < 1: return
		quarti = ceil(float(minuti) / minuti_per_quarto)
		#if quarti == 0: quarti = 1.0	# minimo un quarto
#		print "%d minuti. Quarti: %d." % (minuti, quarti)
		results[tipo] = results.get(tipo, 0.0) + quarti / 4


def fascia_semilineari(fascia_start, fascia_end, date_start, date_end,
				    minuti_per_quarto, tipo, punti_partenza=0, results={}):
	""" Aggiungo a result il codice della fascia (night o morning) con i punti corrispondenti
		nel solo giorno indicato (in trovaDisturbi itero tra giorni e fasce)
		
		la corsa tra date_start e date_end tocca nel giorno indicato da dayMarker tra le ore h_start:m_start e h_end:m_end
		Controllo se date_start cade nella fascia per contarlo
		o se date_end è nella fascia
		o se date_start è prima della fascia e date_end è dopo
	"""
	intersection_start = max(fascia_start, date_start)
	intersection_end = min(fascia_end, date_end)
#	print date_start, date_end, fascia_start, fascia_end
	if intersection_start <= intersection_end:
		if minuti_per_quarto > 0:
			intersezione = (intersection_end - fascia_start)
		else:
			intersezione = (intersection_start - fascia_start)
		minuti = intersezione.days * (24 * 60 * 60) + (intersezione.seconds / 60) # calcolo la durata in minuti dell'intersezione
#		print "Disturbo dalle %s alle %s - %d minuti" % (intersection_start, intersection_end, minuti)
		#if minuti < 1: return
		quarti = floor(float(minuti) / abs(minuti_per_quarto))

		if punti_partenza:
			if minuti_per_quarto > 0:
#				print "    ho %d quarti ma ci aggiungo %.2f da mezzanotte" % (quarti, punti_partenza)
				quarti = quarti + punti_partenza * 4
			else:
#				print "    ho %d quarti, li perdo rispetto ai punti di partenza: %.2f" % (quarti, punti_partenza)
				quarti = punti_partenza * 4 - quarti
		else:
			quarti += 1 #se non ho dei punti di partenza, comincio da un quarto
#			print "   non avendo un minimo parto da 1 quarto supplementare"

		#if quarti == 0: quarti = 1.0	# minimo un quarto
#		print "    %d minuti. Quarti: %d. Punti: %.2f" % (minuti, quarti, quarti / 4)
		results[tipo] = max(results.get(tipo, 0.0), quarti / 4)

# *****************************************

def fasce_uno_due(dayMarker, data_inizio, data_fine, results):
	fascia_uno_o_due_disturbi(dayMarker.replace(hour=0, minute=0), dayMarker.replace(hour=4, minute=1),
					data_inizio, data_fine,
					punti_fascia=2.0, tipo='night', results=results)
	fascia_uno_o_due_disturbi(dayMarker.replace(hour=4, minute=1), dayMarker.replace(hour=6, minute=1),
					data_inizio, data_fine,
					punti_fascia=2.0, tipo='morning', results=results)
	fascia_uno_o_due_disturbi(dayMarker.replace(hour=6, minute=1), dayMarker.replace(hour=7, minute=46),
					data_inizio, data_fine,
					punti_fascia=1, tipo='morning', results=results)

	if dayMarker.isoweekday() in (6, 7):	   # saturday and sunday, normal worktime is less
		fascia_uno_o_due_disturbi(dayMarker.replace(hour=20, minute=0), dayMarker.replace(hour=22, minute=31),
						data_inizio, data_fine,
						punti_fascia=1, tipo='night', results=results)
	else:
		fascia_uno_o_due_disturbi(dayMarker.replace(hour=20, minute=30), dayMarker.replace(hour=22, minute=31),
						data_inizio, data_fine,
						punti_fascia=1, tipo='night', results=results)

	fascia_uno_o_due_disturbi(dayMarker.replace(hour=22, minute=31), dayMarker.replace(hour=23, minute=59),
						data_inizio, data_fine,
						punti_fascia=2, tipo='night', results=results)


def fasce_lineari(dayMarker, data_inizio, data_fine, results):
	fascia_quarti_lineari(dayMarker.replace(hour=0, minute=0), dayMarker.replace(hour=4, minute=0),
					data_inizio, data_fine,
					minuti_per_quarto=15, tipo='night', results=results)
	fascia_quarti_lineari(dayMarker.replace(hour=4, minute=0), dayMarker.replace(hour=6, minute=0),
					data_inizio, data_fine,
					minuti_per_quarto=15, tipo='morning', results=results)
	fascia_quarti_lineari(dayMarker.replace(hour=6, minute=0), dayMarker.replace(hour=7, minute=45),
					data_inizio, data_fine,
					minuti_per_quarto=30, tipo='morning', results=results)

	if dayMarker.isoweekday() in (6, 7):	   # saturday and sunday, normal worktime is less
		fascia_quarti_lineari(dayMarker.replace(hour=20, minute=0), dayMarker.replace(hour=22, minute=30),
						data_inizio, data_fine,
						minuti_per_quarto=30, tipo='night', results=results)
	else:
		fascia_quarti_lineari(dayMarker.replace(hour=20, minute=30), dayMarker.replace(hour=22, minute=30),
						data_inizio, data_fine,
						minuti_per_quarto=30, tipo='night', results=results)

	fascia_quarti_lineari(dayMarker.replace(hour=22, minute=30), dayMarker.replace(hour=23, minute=59),
						data_inizio, data_fine,
						minuti_per_quarto=15, tipo='night', results=results)


def fasce_semilineari(dayMarker, data_inizio, data_fine, results):
	giornoPrima = dayMarker - datetime.timedelta(days= 1)
	if giornoPrima.isoweekday() in (6, 7):	# il giorno prima era festivo, a mezzanotte sono arrivato a 2.25 punti
		fascia_semilineari(dayMarker.replace(hour=0, minute=0), dayMarker.replace(hour=3, minute=29),
						   data_inizio, data_fine,
						   minuti_per_quarto=30, tipo='night', punti_partenza=2.25, results=results)
	else:
		fascia_semilineari(dayMarker.replace(hour=0, minute=0), dayMarker.replace(hour=3, minute=29),
						   data_inizio, data_fine,
						   minuti_per_quarto=30, tipo='night', punti_partenza=2.0, results=results)

	fascia_semilineari(dayMarker.replace(hour=3, minute=30), dayMarker.replace(hour=7, minute=45), # la mattina scendo
						  data_inizio, data_fine,
						  minuti_per_quarto= -30, punti_partenza=2.25, tipo='morning', results=results)

	if dayMarker.isoweekday() in (6, 7):	   # saturday and sunday, normal worktime is less
		fascia_semilineari(dayMarker.replace(hour=20, minute=0), dayMarker.replace(hour=23, minute=59),
						data_inizio, data_fine,
						minuti_per_quarto=30, tipo='night', results=results)
	else:
		fascia_semilineari(dayMarker.replace(hour=20, minute=30), dayMarker.replace(hour=23, minute=59),
						data_inizio, data_fine,
						minuti_per_quarto=30, tipo='night', results=results)
	# qui ho i risultati delle fasce diurine e notturne.
	# restituisco però solo la fascia con il massimo
	if results:
		max_val = max(results.values())
		for k in results.keys():
			if results[k] < max_val:
				#print "cancello", k
				del(results[k])

# ***************************************************************************************

def trovaDisturbi(data_inizio, data_fine, metodo=fasce_lineari):
	""" Itero tra giorni e fasce chiamando il metodo di calcolo dei punti supplementari	"""
#	print "da", data_inizio, "a", data_fine
	results = {}
	giorno_fine = data_fine.date()
	dayMarker = data_inizio.replace(hour=0, minute=0)
	while dayMarker.date() <= giorno_fine:
#		print 'aggiungo le fasce del ', dayMarker
		metodo(dayMarker, data_inizio, data_fine, results)
		dayMarker += datetime.timedelta(days=1)
#	print results
	return results
