from django.utils import timezone
import datetime, time
import pytz
from django.conf import settings
import logging

def parseDateString(s, default=None):
	""" Parse datestring as it was in Italy """
	try:
		logging.debug("Estraggo la data inizio da %s" % s)
		t = time.strptime(s, '%d/%m/%Y')
		r = tz_italy.localize(datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday))
		return r
	except Exception, e:
		logging.debug("Errore nel parsing della data. %s" % e)
		return default

def ita_now():
	if settings.USE_TZ:
		return timezone.now().astimezone(tz_italy)
	else:
		return timezone.now()

def get_prossime_inizio():
	""" Restituisce la data di inizio delle prossime corse """
	adesso = ita_now()
	data_ScorsaMezzanotte = adesso.replace(hour=0, minute=0)
	data_DueOreFa = adesso - datetime.timedelta(hours=2)
	return min(data_ScorsaMezzanotte, data_DueOreFa)

def date_enforce(data):
	""" Ensure the date is timezone aware """
	if not data: return
	if isinstance(data, datetime.date):
		data = datetime.datetime(*data.timetuple()[:3])	# converto da date a datetime
	if settings.USE_TZ:
		if timezone.is_naive(data):	# nella sessione ho salvato una data naive
			data = tz_italy.localize(data)
			return data
		else:
			return data.astimezone(tz_italy)
	else:
		if timezone.is_naive(data):
			return data
		else:	# strip datetime timezone
			return datetime.datetime(*data.timetuple()[:5])
		return data

if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
	# if we are on sqlite, dates on DB are expressed as CET ...
	# where they should be UTC (or tz aware), so, let's stick to UTC
	logging.debug("using UTC to show CET (a bad hack)")
	tz_italy = pytz.timezone('UTC')
else:
	# Tutto in UTC, ma reinterpreto come CET
	logging.debug("in DB everything is TZ aware")
	tz_italy = pytz.timezone('Europe/Rome')
timezone.activate(tz_italy)
