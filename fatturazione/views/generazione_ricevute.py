#coding: utf-8
"""
Ritagli estratti dalla generazione ricevute, poi soppressa
"""

# preparazione, prima di ciclare
	if tipo == "3":	# ricevuto mi preparo una lista entro la quale ciclare di conducenti che emettono ricevuti
		conducenti_ricevute = Conducente.objects.filter(emette_ricevute=True)
		if conducenti_ricevute.count() == 0:
			messages.error(request, "Nessun conducente emette ricevute. Deve essercene almeno uno.")
			return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
		dati_conducenti_ricevute = {}
		for conducente in conducenti_ricevute:
			# mi annoto il n° di fatture emesse per ogni conducente, lo cambierò sotto contando il conducente scelto come se avesse già emesso
			conducente._ricevute = len(conducente.ricevute())
			dati_conducenti_ricevute[conducente.id] = conducente	# tengo i conducenti in un dizionario
	conducenteRicevuta = None
	
# nel ciclo ad ogni cambio chiave
if tipo == '3':
				""" scelgo ruotando tra tutti i conducenti che non hanno mai emesso prima o tra quelli che hanno emesso più tempo fa
					ruoto per progressivo
				"""
				emessa_a = (elemento.cliente.dati or elemento.cliente.nome) or (elemento.passeggero.dati or elemento.passeggero.nome)
				conducenti_precedenti = conducenti_ricevute.filter(fatture__fattura__emessa_a=emessa_a, fatture__fattura__tipo='3').annotate(Max("fatture__fattura__data"))\
								.order_by("fatture__fattura__data__max")

				conducenti_estraibili = [c for c in conducenti_ricevute]
				for c in conducenti_precedenti:
					logging.debug("elimino %d che ha fatturato il %s" % (c.id, c.fatture__fattura__data__max))
					del conducenti_estraibili[conducenti_estraibili.index(c)]	# tolgo quelli che hanno già fatturato
				if conducenti_estraibili:
#					print "Ho conducenti che non hanno mai fatturato li tolgo dagli estraibili."
					pass
				else:
#					print "Tutti hanno già fatturato. Ripesco negli estraibili quelli che non hanno fatturato al cliente da più tempo."
					data_vecchia = conducenti_precedenti[0].fatture__fattura__data__max
					for c in conducenti_precedenti:
						if c.fatture__fattura__data__max > data_vecchia: break
						# c è il mio conducente in ricevute, lo cerco nella lista dei conducenti_ricevute (mi serve la conta delle ricevute)
						conducente = dati_conducenti_ricevute[c.id]
						conducenti_estraibili.append(conducente)


#					conducenti_PerNumRicevute.append( (conducente._ricevute, conducente.id) )
#					conducenti_PerNumRicevute.sort() # ordino per n° di ricevute emesse
#					print "Numero ricevute / Conducenti", conducenti_PerNumRicevute
#					for numRicevute, cond_id in conducenti_PerNumRicevute: #@UnusedVariable
#						conducenti_estraibili.append(cond_id)

				#random.shuffle(conducenti_estraibili)	# randomizzo tra gli aventi diritto

				conducenti_estraibili.sort(lambda x, y: cmp(x._ricevute, y._ricevute)) # ordino per n° di ricevute		
				#print "Parimerito:", conducenti_estraibili
				#conducente = conducenti_estraibili[progressivo % len(conducenti_estraibili)]
				conducente = conducenti_estraibili[0] # pesco il primo
				#print "Pesco il primo: %s" % (conducente)
				conducente._ricevute += 1	# conto come se l'avesse già amessa
				conducenteRicevuta = conducente
				
# per ogni elemento:
	if tipo == '3':
			elemento.conducente_ricevuta = conducenteRicevuta