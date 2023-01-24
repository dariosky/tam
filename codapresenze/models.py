# coding=utf-8
from django.db import models
from django.contrib.auth.models import User
from six import python_2_unicode_compatible


# l'utente potente potrà rimettere in fondo alla coda e cancellare
@python_2_unicode_compatible
class CodaPresenze(models.Model):
    data_accodamento = models.DateTimeField(auto_now_add=True, editable=True)
    utente = models.ForeignKey(User, on_delete=models.CASCADE)
    luogo = models.TextField(max_length=30)

    class Meta:
        verbose_name_plural = "Coda Presenze"
        ordering = ["data_accodamento"]
        permissions = (
            ("view", "Visualizzazione coda"),
            ("editall", "Coda di tutti"),
        )

    def __str__(self):
        return "%s %s a %s" % (
            self.data_accodamento.strftime("%d/%m/%Y %H:%M"),
            self.utente,
            self.luogo,
        )


class StoricoPresenze(models.Model):
    start_date = models.DateTimeField(auto_now_add=True, editable=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place = models.TextField(max_length=30)
    minutes = models.IntegerField()

    class Meta:
        verbose_name = "Presenza"
        verbose_name_plural = "Presenze"
        ordering = ["start_date"]
        permissions = (("view", "Visualizzazione coda"),)
        indexes = [models.Index(fields=["user", "minutes"])]

    def __str__(self):
        return "{date} {user} @ {place}".format(
            date=self.start_date.strftime("%d/%m/%Y %H:%M"),
            user=self.user,
            place=self.place,
        )
