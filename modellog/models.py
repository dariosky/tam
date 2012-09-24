from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User

LOG_ACTION_TYPE = [
					("A", "Creazione"), ("M", "Modifica"), ("D", "Cancellazione"),
					('L', "Login"), ("O", "Logout"),
					("K", "Archiviazione"), ("F", "Appianamento"),
					('X', "Export Excel"),
				  ]

class ActionLog(models.Model):
	data = models.DateTimeField(db_index=True)
	user_id = models.IntegerField(null=True, blank=True, default=None)
	#user = models.ForeignKey(User, null=True, blank=True, default=None)
	action_type = models.CharField(max_length=1, choices=LOG_ACTION_TYPE)

	modelName = models.CharField(max_length='20', null=True, blank=True, default=None)
	instance_id = models.IntegerField(null=True, blank=True, default=None)
#	content_type = models.ForeignKey(ContentType)
#	object_id = models.PositiveIntegerField()
#	content_object = generic.GenericForeignKey('content_type', 'object_id')

	description = models.TextField(blank=True)
	hilight = models.BooleanField(default=False)

	class Meta:
		verbose_name_plural = _("Azioni")
		ordering = ["-data"]

	def __unicode__(self):
		longName = {"A":"Creazione", "M":"Modifica", "D":"Cancellazione"}[self.action_type]
		return "%s di un %s - %s.\n  %s" % (longName, self.content_type, self.user, self.description)

	def user(self):
		""" The user who made the action """
		if self.user_id:
			return User.objects.get(id=self.user_id)

	def obj(self):
		""" Return the related object from tam.models """
		import tam.models as tamModels
		guessed_modelname = self.modelName
		guessed_modelname = guessed_modelname[0].upper() + guessed_modelname[1:]
		try:
			class_name = getattr(tamModels, guessed_modelname)
			return class_name.objects.get(id=self.instance_id)
		except:
			return None
