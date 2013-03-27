#coding: utf-8
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.contrib.auth.models import User


fs = FileSystemStorage(location=settings.SECURE_STORE_LOCATION,
                       base_url=settings.SECURE_URL)


class BoardMessage(models.Model):
	date = models.DateTimeField('Data di inserimento', null=False)
	author = models.ForeignKey(User)
	message = models.TextField('Messaggio', blank=True, null=True)
	attachment = models.FileField(storage=fs,
	                              upload_to='board/attachments/%Y/%m',
	                              null=True, blank=True)
	active = models.BooleanField('Messaggio visibile', default=True)

	def attachment_name(self):
		if self.attachment:
			return os.path.split(self.attachment.name)[1]

	def __unicode__(self):
		result = ""
		if self.attachment: result += "* "
		result += "%s: %s" % (self.author.username, self.message)
		if self.attachment:
			path, filename = os.path.split(self.attachment.file.name)
			result += " [%s]" % filename
		return result

	class Meta:
		ordering = ["-date"]
