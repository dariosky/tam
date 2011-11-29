#coding: utf8
from django.db import models
from tam.models import Viaggio, Conducente, Cliente, Passeggero
from decimal import Decimal

nomi_fatture = {'1': "Fattura consorzio", '2': "Fattura conducente", '3': "Ricevuta"}
nomi_plurale = {'1': "fatture consorzio", '2': "fatture conducente", '3': "ricevute"}

class Fattura(models.Model):
	emessa_da = models.TextField()	# anagrafica emittente
	emessa_a = models.TextField()	# anagrafica cliente
	# cliente e passeggero sono prepopolati in automatico (uno dei 2) ma non sono obbligatori.
	# servono solo per avere un'associazione, emessa_a fa fede
	cliente = models.ForeignKey(Cliente, null=True, blank=True, related_name="fatture", on_delete=models.SET_NULL)
	passeggero = models.ForeignKey(Passeggero, null=True, blank=True, related_name="fatture", on_delete=models.SET_NULL)
	
	note = models.TextField(blank=True)	# note in testata

	tipo = models.CharField(max_length=1, db_index=True) # tipo fattura: 1.Consorzio (a cliente), 2.Conducente (a consorzio), 3.Ricevuta (a cliente)

	data = models.DateField(db_index=True)
	anno = models.IntegerField()
	progressivo = models.IntegerField()

	archiviata = models.BooleanField(default=False) # se true la fattura non è più modificabile

	class Meta:
		verbose_name_plural = "Fatture"
		ordering = ("anno", "progressivo")
		permissions = ( ('generate', 'Genera le fatture'),
						('view', 'Visualizzazione fatture'))
	def __unicode__(self):
		anno = self.anno or "-"
		progressivo = self.progressivo or "-"
		if not self.data: return "fattura-senza-data"
		return u"%s %s/%s del %s emessa a %s. %d righe" % (nomi_fatture[self.tipo], anno, progressivo,
															self.data.strftime("%d/%m/%Y %H:%M"),
															self.destinatario(),
															self.righe.count()
														  )
		
	def destinatario(self):
		return self.emessa_a.replace('\r', '').split('\n')[0]
	
	def imponibile(self):
		return sum([(riga.prezzo or 0) for riga in self.righe.all()])
	def iva(self):
		return sum([(riga.prezzo or 0)*(riga.iva/Decimal(100)) for riga in self.righe.all()])
	
	def lordo_totale(self):
		return sum([(riga.prezzo or 0)*(1+riga.iva/Decimal(100)) for riga in self.righe.all()])


class RigaFattura(models.Model):
	fattura = models.ForeignKey(Fattura, related_name="righe")
	riga = models.IntegerField()

	descrizione = models.TextField()
	note = models.TextField()

	qta = models.IntegerField()
	prezzo = models.DecimalField(max_digits=9, decimal_places=2, null=True)	#fissa in euro
	iva = models.IntegerField()	# iva in percentuale

	viaggio = models.OneToOneField(Viaggio, null=True, related_name="riga_fattura", on_delete=models.SET_NULL)
	conducente = models.ForeignKey(Conducente, null=True, related_name="fatture", on_delete=models.SET_NULL)
	riga_fattura_consorzio = models.OneToOneField("RigaFattura", null=True, related_name="fattura_conducente_collegata")
	
	def totale(self):
		return self.prezzo*self.qta*(100+self.iva)/100

	class Meta:
		verbose_name_plural = "Righe Fattura"
		ordering = ("fattura", "riga")
	def __unicode__(self):
		return u"riga %d. %.2f." % (self.riga, self.prezzo or 0)
