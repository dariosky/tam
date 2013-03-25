#coding: utf-8
from django.db import models
from django.contrib.auth.models import User

class BoardMessage(models.Model):
	date = models.DateTimeField('Data di inserimento', null=False)
	author = models.ForeignKey(User)
	message = models.TextField('Messaggio', blank=True, null=True)
	attach = models.FileField(upload_to='board/attachments/%Y/%m')
	active = models.BooleanField('Messaggio visibile', default=True)

