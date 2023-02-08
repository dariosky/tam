# coding=utf-8
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class Positions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lat = models.FloatField(_("Latitude"), blank=True, null=True)
    lon = models.FloatField(_("Longitude"), blank=True, null=True)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}@{self.lat},{self.lon} - {self.last_update}"
