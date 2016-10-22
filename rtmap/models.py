# coding=utf-8
from django.contrib.auth.models import User
from django.db import models


class Positions(models.Model):
    user = models.ForeignKey(User)
