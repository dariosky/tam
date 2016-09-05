# coding=utf-8
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import models
from django.utils.translation import ugettext_lazy as _
from future.utils import python_2_unicode_compatible

LOG_ACTION_TYPE = [
    ("A", "Creazione"), ("M", "Modifica"), ("D", "Cancellazione"),
    ('L', "Login"), ("O", "Logout"),
    ("K", "Archiviazione"), ("F", "Appianamento"),
    ('X', "Export Excel"),
]


@python_2_unicode_compatible
class ActionLog(models.Model):
    data = models.DateTimeField(db_index=True)
    user_id = models.IntegerField(null=True, blank=True, default=None)
    # user = models.ForeignKey(User, null=True, blank=True, default=None)
    action_type = models.CharField(max_length=1, choices=LOG_ACTION_TYPE)

    modelName = models.CharField(max_length=20, null=True, blank=True,
                                 default=None)
    instance_id = models.IntegerField(null=True, blank=True, default=None)

    # why the hell I stopped using contentTypes?
    # content_type = models.ForeignKey(ContentType)
    # object_id = models.PositiveIntegerField()
    # content_object = generic.GenericForeignKey('content_type', 'object_id')

    description = models.TextField(blank=True)
    hilight = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = _("Azioni")
        ordering = ["-data"]

    def __str__(self):
        longName = {"A": "Creazione", "M": "Modifica", "D": "Cancellazione"}[
            self.action_type]
        return "%s di un %s - %s.\n  %s" % (
            longName, self.content_type, self.user, self.description)

    def user(self):
        """ The user who made the action """
        if self.user_id:
            return User.objects.get(id=self.user_id)

    def obj(self):
        """ Return the related object from tam.models """
        import tam.models as tamModels

        guessed_modelname = self.modelName
        if not guessed_modelname:
            return None
        guessed_modelname = guessed_modelname[0].upper() + guessed_modelname[
                                                           1:]
        result = None
        try:
            class_name = getattr(tamModels, guessed_modelname)
            result = class_name.objects.get(id=self.instance_id)
        except:
            try:
                import fatturazione.models as fatModels

                class_name = getattr(fatModels, guessed_modelname)
                result = class_name.objects.get(id=self.instance_id)
            except:
                pass
        return result

    def icon(self):
        """ Ritorno l'icona associata al tipo cliente """
        return staticfiles_storage.url('actionIcons/%s.png' % self.action_type)
