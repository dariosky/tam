# coding=utf-8
from django.db import models
from django.contrib.auth.models import User


class CodaPresenze(models.Model):
	data_accodamento = models.DateTimeField(auto_now_add=True, editable=True)
	utente = models.ForeignKey(User)
	luogo = models.TextField(max_length=30)

	class Meta:
		verbose_name_plural = "Coda Presenze"
		ordering = ["data_accodamento"]
		permissions = (('view', 'Visualizzazione coda'),)

	def __unicode__(self):
		return "%s %s a %s" % (self.data_accodamento.strftime("%d/%m/%Y %H:%M"), self.utente, self.luogo)

# l'utente potente potrà rimettere in fondo alla coda e cancellare
