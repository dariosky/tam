# coding=utf-8
import copy
import datetime
from django.conf import settings
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.base import TemplateView
from calendariopresenze.models import Calendar
from tam import tamdates
from tam.tamdates import ita_today


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
		calendars = copy.copy(settings.CALENDAR_DESC)
		calendars_in_the_day = Calendar.objects.filter(
			date_start__lt=nextday,  # I use the date-interval cross detection
			date_end__gt=day,
		)
		# one query to get the calendars, then regrouped
		for caltype, calDesc in calendars.items():
			calDesc['elements'] = [c for c in calendars_in_the_day if c.type == caltype]

		context['calendars'] = calendars
		context.update({"mediabundleJS": ('tamUI',),  # I need the datepicker
		                "mediabundleCSS": ('tamUI',),
		})
		return context
