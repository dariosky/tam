#coding: utf-8
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from markViews import prenotazioni
from django import forms
from prenotazioni.models import Prenotazione
from tam.widgets import MySplitDateTimeField, MySplitDateWidget
from django.utils.translation import ugettext as _
from django.forms.widgets import Input
import datetime
from prenotazioni.util import preavviso_ore, prenotaCorsa
from django.db import transaction
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.forms.fields import TypedChoiceField

class NumberInput(Input):
	input_type = 'number'

class FormPrenotazioni(forms.ModelForm):
	def clean_pax(self):
		"pulizia numero di pax"
		value = self.cleaned_data['pax']
		if value > 50:
			raise forms.ValidationError("Sicuro del numero di persone?")
		return value

	def clean(self):
		""" Controlli di validità dell'intera form """
		cleaned_data = self.cleaned_data
		ora = datetime.datetime.now()

		oraMinima = ora + datetime.timedelta(hours=preavviso_ore) # bisogna prenotare 48 ore prima
		if 'data_corsa' in cleaned_data and cleaned_data['data_corsa'] < oraMinima:
			raise forms.ValidationError("Devi prenotare almeno %d ore prima. " % preavviso_ore)

		return cleaned_data

	def __init__(self, *args, **kwargs):
		super(FormPrenotazioni, self).__init__(*args, **kwargs)
		for field_name in self.fields:
			field = self.fields.get(field_name)
			if field:
				if field_name == 'pax':
					field.widget = NumberInput(attrs={'min':"1", 'max':"50"})
				if type(field.widget) in (forms.TextInput, forms.DateInput):
					field.widget = forms.TextInput(attrs={'placeholder': field.label})
				elif type(field.widget) in (forms.DateTimeInput,):
					data = MySplitDateTimeField(
									label="Data e ora",
									date_input_formats=[_('%d/%m/%Y')],
									time_input_formats=[_('%H:%M')],
									widget=MySplitDateWidget()
							)
					data.widget.widgets[0].format = '%d/%m/%Y'
					self.fields[field_name] = data
					field.widget = 	MySplitDateTimeField()

	class Meta:
		model = Prenotazione
		widgets = {
				'is_arrivo': forms.RadioSelect,
				'is_collettivo': forms.RadioSelect,
				'pagamento': forms.RadioSelect,
				}

@prenotazioni
@transaction.commit_on_success	# commit solo se tutto OK
def prenota(request, template_name='prenotazioni/main.html'):

	utentePrenotazioni = request.user.prenotazioni
	form = FormPrenotazioni(request.POST or None)
	if form.is_valid():
		prenotazione = Prenotazione(
								owner=utentePrenotazioni,
								cliente=utentePrenotazioni.cliente,
								**form.cleaned_data
								)

		viaggio = prenotaCorsa(prenotazione)
		prenotazione.viaggio = viaggio
		prenotazione.save()
		messages.success(
			request,
			"Prenotazione n° %d effettuata, a breve riceverai una mail di conferma." % prenotazione.id
		)
		#return HttpResponseRedirect(reverse('tamPrenotazioni')) #TMP: per prenotare a raffica

	return render_to_response(
							template_name,
							{
								"utentePrenotazioni":utentePrenotazioni,
								"form":form,
								"editable":True,
							},
							context_instance=RequestContext(request))


@prenotazioni
def cronologia(request, template_name='prenotazioni/cronologia.html'):
	utentePrenotazioni = request.user.prenotazioni

	prenotazioni = Prenotazione.objects.filter(cliente=utentePrenotazioni.cliente)


	return render_to_response(
							template_name,
							{
								"utentePrenotazioni":utentePrenotazioni,
								"prenotazioni":prenotazioni,
							},
							context_instance=RequestContext(request))


@prenotazioni
def edit(request, id_prenotazione, template_name='prenotazioni/main.html'):
	utentePrenotazioni = request.user.prenotazioni

	prenotazione = Prenotazione.objects.get(id=id_prenotazione)
	if prenotazione.owner <> utentePrenotazioni:
		messages.error(
			request,
			"La prenotazione non è stata fatta da te, non puoi accedervi."
		)
		return HttpResponseRedirect(reverse('tamCronoPrenotazioni'))
	editable = prenotazione.is_editable()
	if not editable:
		messages.warning(
			request,
			"La prenotazione non è più modificabile."
		)
		#return HttpResponseRedirect(reverse('tamCronoPrenotazioni'))

	form = FormPrenotazioni(request.POST or None, instance=prenotazione)
	previous_values = {}
	if request.method == "POST":
		for key in form.fields:
			previous_values[key] = getattr(prenotazione, key)

	if form.is_valid() and editable:
		changes = {}	# dizionario con i cambiamenti al form
		for key in form.cleaned_data:
			def humanValue(pythonValue, choices):
				for k, v in choices:
					if k == pythonValue:
						return v
			oldValue = previous_values.get(key)
			newValue = form.cleaned_data[key]

			field = form.fields[key]
			if isinstance(field, TypedChoiceField):
				oldValue = humanValue(oldValue, field.choices)
				newValue = humanValue(newValue, field.choices)

			if newValue <> oldValue:
				changes[key] = (field.label, oldValue, newValue)
#				messages.success(
#						request,
#						"Cambiato %s da %s a %s" % (form.fields[key].label,
#													oldValue,
#													newValue)
#						)
		if changes:
			messages.success(request, "Modifica eseguita.")
		prenotazione.save()	# TMP: va solo se changes	
		
		return HttpResponseRedirect(
								reverse('tamPrenotazioni-edit',
										kwargs={"id_prenotazione":prenotazione.id}
								),

							)

	return render_to_response(
							template_name,
							{
								"utentePrenotazioni":utentePrenotazioni,
								"form":form,
								"prenotazione":prenotazione,
								"editable":editable,
							},
							context_instance=RequestContext(request))

#TODO: Modifica e cancellazione (con annullamento della corsa)
#TODO: Log delle operazioni
#TODO: Email di conferma in creazione e modifica
