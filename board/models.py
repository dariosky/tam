# coding: utf-8
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from future.utils import python_2_unicode_compatible

from tam.models import UnSerializableFileSystemStorage

fs = UnSerializableFileSystemStorage(
    location=settings.SECURE_STORE_LOCATION, base_url=settings.SECURE_URL
)


def get_secure_attachment_subfolder(filename, fs, timepath):
    secure_subfolder = settings.SECURE_STORE_CUSTOM_SUBFOLDER
    filename = os.path.normpath(fs.get_valid_name(os.path.basename(filename)))
    result = timezone.now().strftime(timepath) + "/" + filename
    if secure_subfolder:
        return secure_subfolder + "/" + result
    else:
        return result


def board_upload_to(instance, filename):
    return get_secure_attachment_subfolder(filename, fs, "board/%Y/%m")


@python_2_unicode_compatible
class BoardMessage(models.Model):
    date = models.DateTimeField("Data di inserimento", null=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField("Messaggio", blank=True, null=True)
    attachment = models.FileField(
        storage=fs, upload_to=board_upload_to, null=True, blank=True
    )
    active = models.BooleanField("Messaggio visibile", default=True)

    def attachment_name(self):
        if self.attachment is not None:
            return os.path.split(self.attachment.name)[1]

    def __str__(self):
        result = ""
        if self.attachment:
            result += "* "
        result += "%s: %s" % (self.author.username, self.message)
        if self.attachment:
            try:
                path, filename = os.path.split(self.attachment.file.name)
                result += " [%s]" % filename
            except IOError:
                result += " [%s]" % "invalid-file"
        return result

    class Meta:
        ordering = ["-date"]
        permissions = (("view", "Visualizzazione bacheca"),)
        app_label = "board"
