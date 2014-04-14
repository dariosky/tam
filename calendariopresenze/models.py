# coding=utf-8
from django.conf import settings
from django.db import models
from django.db.models.deletion import CASCADE
# from tam.models import Conducente
from tam.tamdates import tz_italy


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
	value = models.IntegerField()  # value is the minutes of duration or other kind of score

	class Meta:
		ordering = ['date_start', 'conducente']

	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		delta = (self.date_end - self.date_start)
		self.minutes = (delta.days * 60 * 24) + delta.seconds / 60
		caldesc = settings.CALENDAR_DESC[self.type]
		if 'get_value' in caldesc:
			self.value = caldesc['get_value'](self)
		else:
			self.value = self.minutes  # time based calendar
		super(Calendar, self).save(force_insert, force_update, using, update_fields)

	def display(self):
		"""
		Return the display string to be shown
		@return: string
		"""
		caldesc = settings.CALENDAR_DESC[self.type]
		if "display" in caldesc:
			return caldesc['display'](self)
		else:
			return self.pretty_duration()

	def __unicode__(self):
		caldesc = settings.CALENDAR_DESC[self.type]
		result = u"{conducente}. {date_start} ".format(conducente=self.conducente,
		                                               date_start=(self.date_start.astimezone(tz_italy)).strftime("%d/%m/%Y %H:%M"))
		if "display_as" in caldesc:
			result += self.display()
		else:
			result += "{duration} [tipo {type}]".format(
				duration=self.pretty_duration(),
				type=self.type
			)
		return result + (u" but available" if self.available else u"")

	def pretty_duration(self):
		return pretty_duration(self.minutes)

	@property
	def name(self):
		return settings.CALENDAR_DESC[self.type]['name']

	@property
	def tags(self):
		return settings.CALENDAR_DESC[self.type]['tags']
