#coding: utf8
from django.db import models
from tam.models import Viaggio

nomi_fatture = {'1': "Fattura consorzio", '2': "Fattura conducente", '3': "Ricevuta"}
class Fattura(models.Model):
	emessa_da = models.TextField()	# anagrafica emittente
	emessa_a = models.TextField()	# anagrafica cliente
	note = models.TextField(blank=True)

	tipo = models.CharField(max_length=1) # tipo fattura: 1.Consorzio (a cliente), 2.Conducente (a consorzio), 3.Ricevuta (a cliente)

	data = models.DateField()
	anno = models.IntegerField()
	progressivo = models.IntegerField()

	archiviata = models.BooleanField(default=False) # se true la fattura non è più modificabile

	class Meta:
		verbose_name_plural = "Fatture"
		ordering = ("anno", "progressivo")
	def __unicode__(self):
		destinatario = self.emessa_a.split('\n')[0]
		anno = self.anno or "-"
		progressivo = self.anno or "-"
		return u"%s %s/%s del %s emessa a %s. %d righe" % (nomi_fatture[self.tipo], anno, progressivo,
															self.data.strftime("%d/%m/%Y %H:%M"), destinatario,
															self.righe.count()
														  )


class RigaFattura(models.Model):
	fattura = models.ForeignKey(Fattura, related_name="righe")
	riga = models.IntegerField()

	descrizione = models.TextField()
	note = models.TextField()

	qta = models.IntegerField()
	prezzo = models.DecimalField(max_digits=9, decimal_places=2)	#fissa in euro
	iva = models.IntegerField()	# iva in percentuale

	viaggio = models.OneToOneField(Viaggio, null=True, related_name="riga_fattura")
	riga_fattura_conducente = models.OneToOneField("RigaFattura", null=True, related_name="fattura_conducente_collegata")

	class Meta:
		verbose_name_plural = "Righe Fattura"
		ordering = ("fattura", "riga")
	def __unicode__(self):
		return u"riga %d. %.2f." % (self.riga, self.prezzo)
