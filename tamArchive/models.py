#cofing: utf-8

from django.db import models

class ViaggioArchive(models.Model):
	data = models.DateTimeField("Data della corsa", db_index=True)
	path = models.TextField("Percorso effettuato", blank=True)
	da = models.CharField("Da", max_length=25)
	a = models.CharField("A", max_length=25)
	note = models.TextField(blank=True)
	prices = models.TextField(blank=True)
	conducente = models.CharField("Conducente", max_length=5, blank=True, null=True)

	def __unicode__(self):
		return u"viaggio del %s %s" % (self.data, self.path)
