# coding=utf-8
from django.conf import settings
from django.db import models
from django.db.models.deletion import CASCADE
# from tam.models import Conducente


def pretty_duration(minutes):
	remainder = minutes
	results = []
	a_day = 24 * 60
	if remainder >= a_day:
		results.append("%d giorni" % (remainder / a_day))
		remainder %= a_day
	an_hour = 60
	if remainder > an_hour:
		results.append("%d ore" % (remainder / an_hour))
		remainder %= an_hour
	if remainder:
		results.append("%d minuti" % remainder)
	return " ".join(results)


class Calendar(models.Model):
	conducente = models.ForeignKey('tam.Conducente', on_delete=CASCADE)
	date_start = models.DateTimeField(db_index=True)
	date_end = models.DateTimeField(db_index=True)
	minutes = models.IntegerField(editable=False)
	type = models.IntegerField(choices=[(key, c['name']) for key, c in settings.CALENDAR_DESC.items()])
	available = models.BooleanField(default=False)  # When this is True the conducente is still available

	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		delta = (self.date_end - self.date_start)
		self.minutes = (delta.days * 60 * 24) + delta.seconds / 60
		super(Calendar, self).save(force_insert, force_update, using, update_fields)

	def __unicode__(self):
		return u"{conducente}. {duration} [tipo {type}]".format(
			conducente=self.conducente,
			duration=self.pretty_duration(),
			type=self.type
		) + (u" but available" if self.available else u"")

	def pretty_duration(self):
		return pretty_duration(self.minutes)

	@property
	def name(self):
		return settings.CALENDAR_DESC[self.type]['name']

	@property
	def tags(self):
		return settings.CALENDAR_DESC[self.type]['tags']
