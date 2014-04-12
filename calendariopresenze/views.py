# coding=utf-8
import copy
import datetime
from django.conf import settings
from django import forms
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.base import TemplateView
from calendariopresenze.models import Calendar
from tam import tamdates
from tam.models import Conducente
from tam.tamdates import ita_today


class CalendarForm(forms.Form):
	type = forms.CharField(max_length=10)
	conducente = forms.IntegerField()
	time_from = forms.CharField(max_length=5)
	time_to = forms.CharField(max_length=5)


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
		calendars_in_the_day = Calendar.objects.filter(
			date_start__lt=nextday,  # I use the date-interval cross detection
			date_end__gt=day,
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
			calendar = Calendar.objects.get(id=request.POST['calendar_id'])
			calendar.delete()
			return HttpResponse("ok", status=200)
		if form.is_valid():
			day = context['day']
			conducente_id = form.cleaned_data['conducente']
			conducente = Conducente.objects.get(id=conducente_id)
			calendar_type = form.cleaned_data['type']
			string_from, string_to = form.cleaned_data['time_from'], form.cleaned_data['time_to']

			def appendTimeToDate(time_string):
				h_string, m_string = time_string.split(":")
				return day + datetime.timedelta(hours=int(h_string), minutes=int(m_string))

			date_start = appendTimeToDate(string_from)
			date_end = appendTimeToDate(string_to)
			calendar = Calendar(
				conducente=conducente, type=calendar_type,
				date_start=date_start,
				date_end=date_end,
			)
			calendar.save()
			return HttpResponseRedirect(reverse('calendariopresenze-manage') + '?day=' + context['selected_day'])
		return super(CalendarManage, self).get(request, *args, **kwargs)


