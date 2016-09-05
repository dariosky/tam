# coding=utf-8
from django.db import models
from django.contrib.auth.models import User
from future.utils import python_2_unicode_compatible


@python_2_unicode_compatible
class CodaPresenze(models.Model):
    data_accodamento = models.DateTimeField(auto_now_add=True, editable=True)
    utente = models.ForeignKey(User)
    luogo = models.TextField(max_length=30)

    class Meta:
        verbose_name_plural = "Coda Presenze"
        ordering = ["data_accodamento"]
        permissions = (
            ('view', 'Visualizzazione coda'),
            ('editall', 'Coda di tutti'),
        )

    def __str__(self):
        return "%s %s a %s" % (
        self.data_accodamento.strftime("%d/%m/%Y %H:%M"), self.utente, self.luogo)

# l'utente potente potrà rimettere in fondo alla coda e cancellare
