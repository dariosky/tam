# coding=utf-8
import copy
import datetime
from django.conf import settings
from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect, HttpResponse
from django.template import Context
from django.template.loader import get_template
from django.views.generic.base import TemplateView
from calendariopresenze.models import Calendar
from modellog.actions import logAction
from tam import tamdates
from tam.models import Conducente
from tam.tamdates import ita_today, appendTimeToDate, appendTimeFromRegex


class CalendarForm(forms.Form):
	type = forms.IntegerField()
	conducente = forms.IntegerField()
	time_from = forms.CharField(max_length=5)
	time_to = forms.CharField(max_length=5)

	def clean_time_from(self):
		data = self.cleaned_data['time_from']
		return tamdates.normalizeTimeString(data)

	def clean_time_to(self):
		data = self.cleaned_data['time_to']
		return tamdates.normalizeTimeString(data)


class CalendarManage(TemplateView):
	template_name = 'calendar/cal_manage.html'

	def get_context_data(self, **kwargs):
		context = super(CalendarManage, self).get_context_data(**kwargs)
		day_string = self.request.GET.get('day', None)
		day = tamdates.parseDateString(day_string, default=ita_today())
		# this filter is valid until the next day
		nextday = day + datetime.timedelta(days=1)
		context['nextday'] = nextday  # I'll use this to check if the range goes ahead on days
		context['day'] = day
		context['selected_day'] = day.strftime('%d/%m/%Y')
		calendars = copy.copy(settings.CALENDAR_DESC)
		# I don't use the date-interval cross detection anymore... let's see only the event's starting in the day
		calendars_in_the_day = Calendar.objects.filter(
			date_start__range=(day, nextday),
		)
		# one query to get the calendars, then regrouped
		for caltype, calDesc in calendars.items():
			calDesc['elements'] = [c for c in calendars_in_the_day if c.type == caltype]

		context['calendars'] = calendars
		context['conducenti'] = Conducente.objects.filter(attivo=True)
		context.update({"mediabundleJS": ('tamUI',),  # I need the datepicker
		                "mediabundleCSS": ('tamUI',),
		})
		context['form'] = CalendarForm(self.request.POST if self.request.method == 'POST' else None)
		context['dontHilightFirst'] = True
		return context

	def post(self, request, *args, **kwargs):
		print "POST", request.POST
		context = self.get_context_data()
		form = context['form']
		action = request.POST.get('action', 'new')
		if action == 'delete':
			if not request.user.has_perm('calendariopresenze.delete_calendar'):
				if request.is_ajax():
					return HttpResponse("Non hai permessi per cancellare le presenze.", status=401)
				else:
					messages.error(request, "Non hai permessi per cancellare le presenze.")
					return HttpResponseRedirect(reverse('calendariopresenze-manage'))
			calendar = Calendar.objects.get(id=request.POST['calendar_id'])
			caldesc = settings.CALENDAR_DESC[calendar.type]
			logAction('P',
			          instance=calendar,
			          description=u"Presenze: cancellato {name} {calendar}".format(
				          name=caldesc['name'],
				          calendar=calendar
			          )
			)
			calendar.delete()
			return HttpResponse("ok", status=200)
		if action == 'new':
			if not request.user.has_perm('calendariopresenze.add_calendar'):
				if request.is_ajax():
					return HttpResponse("Non hai permessi per modificare le presenze.", status=401)
				else:
					messages.error(request, "Non hai permessi per modificare le presenze.")
					return HttpResponseRedirect(reverse('calendariopresenze-manage'))
			cal_fixed_start = None
			cal_fixed_end = None
			subname = None
			caldesc = None
			if 'type' in request.POST:
				try:
					caldesc = settings.CALENDAR_DESC[int(request.POST['type'])]

					if "subname" in request.POST:
						subname = request.POST['subname']
						for subcal in caldesc['display_as']:
							if subcal['name'] == subname:
								cal_fixed_start = subcal['date_start']
								cal_fixed_end = subcal['date_end']
								break
				except ValueError:
					pass

			day = context['day']

			conducente_id = int(request.POST['conducente'])
			conducente = Conducente.objects.get(id=conducente_id)
			calendar_type = int(request.POST['type'])

			if 'time_from' in request.POST:
				string_from = request.POST['time_from']
				date_start = appendTimeToDate(day, string_from)
			else:
				assert cal_fixed_start
				date_start = appendTimeFromRegex(day, cal_fixed_start)
			if 'time_to' in request.POST:
				string_to = request.POST['time_to']
				date_end = appendTimeToDate(day, string_to)
			else:
				assert cal_fixed_end
				date_end = appendTimeFromRegex(day, cal_fixed_end)

			calendar = Calendar(
				conducente=conducente, type=calendar_type,
				date_start=date_start,
				date_end=date_end,
			)
			calendar.save()
			logAction('P',
			          instance=calendar,
			          description=u"Presenze: aggiunto {name} {calendar}".format(
				          name=subname or caldesc['name'],
				          calendar=calendar
			          )
			)
			if request.is_ajax():
				row_template = get_template('calendar/cal_row.html')
				context = Context(dict(
					element=calendar,
					calDesc=settings.CALENDAR_DESC[calendar.type]
				))
				return HttpResponse(row_template.render(context), status=201)
			else:
				return HttpResponseRedirect(
					reverse('calendariopresenze-manage') + '?day=' + context['selected_day']
				)


if __name__ == '__main__':
	today = datetime.date.today()
	# testing conversions
	print "3:30", appendTimeToDate(today, "3:30")
	print "3h30m", appendTimeFromRegex(today, "3h30m")
	assert appendTimeToDate(today, "3:30") == appendTimeFromRegex(today, "3h30m")
	print "1d3h30m", appendTimeFromRegex(today, "1d3h30m")
	print "1d", appendTimeFromRegex(today, "1d")

	print "\nNow try with timezone-aware dates"
	print ita_today()
	print "3:30", appendTimeToDate(ita_today(), "3:30")
	print "3h30m", appendTimeFromRegex(ita_today(), "3h30m")
