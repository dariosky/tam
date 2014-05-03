# coding=utf-8
import copy
import datetime
from django.conf import settings
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.http.response import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.template.loader import get_template
from django.views.generic.base import TemplateView
from calendariopresenze.models import Calendar, pretty_duration
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
		time_from =tamdates.normalizeTimeString(data)
		appendTimeToDate(datetime.date.today(), time_from)
		return time_from

	def clean_time_to(self):
		data = self.cleaned_data['time_to']
		time_to = tamdates.normalizeTimeString(data)
		try:
			appendTimeToDate(datetime.date.today(), time_to)
		except ValueError:
			raise ValidationError("Invalid value")
		return time_to


class AjaxableResponseMixin(TemplateView):
	def render_to_response(self, context, **response_kwargs):
		redirect_url = context.get('redirect_url')
		message = context.get('message')
		status = context.get('status')
		if self.request.is_ajax() and message and status:
			return HttpResponse(message, status=status)
		if redirect_url:
			if message and 400 <= status < 600:
				messages.error(self.request, message)
			return HttpResponseRedirect(reverse(redirect_url))
		return super(TemplateView, self).render_to_response(context, **response_kwargs)


class CalendarManage(AjaxableResponseMixin):
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
		is_old_day = day < ita_today()
		context['can_edit'] = not is_old_day or self.request.user.has_perm('calendariopresenze.change_oldcalendar')
		return context

	def post(self, request, *args, **kwargs):
		context = self.get_context_data()
		form = context['form']
		action = request.POST.get('action')
		if not context['can_edit']:
			return self.render_to_response(
				dict(message=u"Non hai permessi per modificare le presenze.",
				     status=401,
				     redirect_url='calendariopresenze-manage')
			)

		if action == 'new':
			if not request.user.has_perm('calendariopresenze.add_calendar'):
				return self.render_to_response(
					dict(message=u"Non hai permessi per modificare le presenze.",
					     status=401,
					     redirect_url='calendariopresenze-manage')
				)
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
				try:
					date_start = appendTimeToDate(day, string_from)
				except ValueError:
					return self.render_to_response(
						dict(message=u"Ora iniziale non valida.",
						     status=400,
						     redirect_url='calendariopresenze-manage')
					)
			else:
				assert cal_fixed_start
				date_start = appendTimeFromRegex(day, cal_fixed_start)

			if 'time_to' in request.POST:
				string_to = request.POST['time_to']
				try:
					date_end = appendTimeToDate(day, string_to)
				except ValueError:
					return self.render_to_response(
						dict(message=u"Ora finale non valida.",
						     status=400,
						     redirect_url='calendariopresenze-manage')
					)
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

				# I use the context view, adding the things to rendere the row
				context.update(dict(
					element=calendar,
					calDesc=settings.CALENDAR_DESC[calendar.type]
				))
				return HttpResponse(row_template.render(RequestContext(request, context)), status=201)
			else:
				return HttpResponseRedirect(
					reverse('calendariopresenze-manage') + '?day=' + context['selected_day']
				)

		elif action == 'delete':
			if not request.user.has_perm('calendariopresenze.delete_calendar'):
				return self.render_to_response(
					dict(message=u"Non hai permessi per cancellare le presenze.",
					     status=401,
					     redirect_url='calendariopresenze-manage')
				)
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

		elif action == 'toggle':
			if not request.user.has_perm('calendariopresenze.toggle_calendavalue'):
				return self.render_to_response(
					dict(message=u"Non hai permessi per modificare il valore dei calendari.",
					     status=401,
					     redirect_url='calendariopresenze-manage')
				)
			calendar = Calendar.objects.get(id=request.POST['calendar_id'])
			caldesc = settings.CALENDAR_DESC[calendar.type]
			if not 'toggle' in caldesc:
				return self.render_to_response(
					dict(message=u"Valore del calendario non modificabile.",
					     status=400,
					     redirect_url='calendariopresenze-manage')
				)
			old_value = calendar.value
			caldesc['toggle'](calendar)
			new_value = calendar.value

			logAction('P',
			          instance=calendar,
			          description=u"Presenze: variato {name} {calendar} da {old} a {new}".format(
				          name=caldesc['name'],
				          calendar=calendar,
				          old=old_value,
				          new=new_value,
			          )
			)
			if request.is_ajax():
				row_template = get_template('calendar/cal_row.html')

				# I use the context view, adding the things to rendere the row
				context.update(dict(
					element=calendar,
					calDesc=settings.CALENDAR_DESC[calendar.type]
				))
				return HttpResponse(row_template.render(RequestContext(request, context)), status=201)
			else:
				return HttpResponseRedirect(
					reverse('calendariopresenze-manage') + '?day=' + context['selected_day']
				)

		else:
			return self.render_to_response(
				dict(message=u"Azione sconosciuta.",
				     status=400,
				     redirect_url='calendariopresenze-manage')
			)


class CalendarRank(TemplateView):
	template_name = "calendar/cal_rank.html"

	def dispatch(self, request, year=None, *args, **kwargs):
		if year is None:
			return HttpResponseRedirect(reverse('calendariopresenze-rank', kwargs={'year': datetime.date.today().year}))
		return super(CalendarRank, self).dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(CalendarRank, self).get_context_data(**kwargs)
		year = int(self.kwargs['year'])
		context['year'] = year
		calendars = copy.copy(settings.CALENDAR_DESC)
		for key, caldesc in calendars.items():
			if "hide_rank" in caldesc:
				del calendars[key]
				continue
			ranks = []
			for conducente in Conducente.objects.filter(attivo=True,
			                                            presenze__date_start__year=year,
			                                            presenze__type=key) \
					.annotate(tot=Sum('presenze__value')) \
					.order_by('-tot'):
				if 'display' in caldesc:
					value = conducente.tot
					if 'rank_display' in caldesc:
						value = caldesc['rank_display'](value)
				else:
					value = pretty_duration(conducente.tot)
				ranks.append({'name': conducente.nome, 'conducente_id': conducente.id, 'value': value})
			caldesc['rank'] = ranks
		context['calendars'] = calendars
		return context


class CalendarByConducente(TemplateView):
	template_name = "calendar/cal_view.html"

	def get_context_data(self, year, conducente_id, caltype, **kwargs):
		year = int(year)
		caltype = int(caltype)
		context = super(CalendarByConducente, self).get_context_data(**kwargs)
		conducente = Conducente.objects.get(id=conducente_id)
		caldesc = settings.CALENDAR_DESC[caltype]
		context['conducente'] = conducente
		context['caldesc'] = caldesc
		calendars = Calendar.objects.filter(conducente=conducente,
		                                    date_start__year=year,
		                                    type=caltype,
		)
		context['calendars'] = calendars
		return context


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
