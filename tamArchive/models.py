#coding: utf-8

from django.db import models
# load models required for the tasks
from tamArchive.tasks import TaskArchive #@UnusedImport

class ViaggioArchive(models.Model):
	class Meta:
		verbose_name_plural = "Archivi"
		ordering = ["data"]
		permissions = (('flat', 'Esegue l\'appianamento'),
						('archive', 'Esegue l\'archiviazione'))

	data = models.DateTimeField("Data della corsa", db_index=True)

	da = models.CharField("Da", max_length=25)
	a = models.CharField("A", max_length=25)
	path = models.TextField("Percorso effettuato", blank=True)	# il percorso come stringa HTML con i tempi

	pax = models.IntegerField(default=1) #numero_passeggeri
	flag_esclusivo = models.BooleanField("Servizio taxi", default=True)

	# il conducente, (quelli non confermati non li archivio)
	conducente = models.CharField("Conducente", max_length=5, blank=True, null=True, db_index=True)

	flag_richiesto = models.BooleanField("Conducente richiesto", default=False)	# True quando il conducente è fissato

	cliente = models.CharField("A", max_length=40, null=True)	# cliente o passeggero, come testo - se null è un privato non specificato

	prezzo = models.DecimalField(max_digits=9, decimal_places=2, editable=False, default=0) # prezzo lordo al cliente
	prezzo_detail = models.TextField("Dettagli prezzo", blank=True)

	flag_fineMese = models.BooleanField("Conto fine mese", default=False)
	flag_fatturazione = models.BooleanField("Fatturazione richiesta", default=False)
	flag_cartaDiCredito = models.BooleanField("Pagamento con carta di credito", default=False)
	flag_pagamentoDifferito = models.BooleanField(default=False)

	numero_pratica = models.CharField(max_length=20, null=True, blank=True)

	flag_arrivo = models.BooleanField(default=True, editable=False)
	punti_abbinata = models.IntegerField(default=0, editable=False)
	note = models.TextField(blank=True)	# le note, pari pari

	padre = models.ForeignKey("ViaggioArchive", null=True, blank=True)	# il "ViaggioArchive" padre di questa corsa

	def __unicode__(self):
		return u"viaggio del %s %s" % (self.data, self.path)
