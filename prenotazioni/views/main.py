#coding: utf-8
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from markViews import prenotazioni
from django import forms
from prenotazioni.models import Prenotazione, TIPI_PAGAMENTO
from tam.widgets import MySplitDateTimeField, MySplitDateWidget
from django.utils.translation import ugettext as _
from django.forms.widgets import Input
import datetime
from prenotazioni.util import preavviso_ore, prenotaCorsa
from django.db import transaction

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
		if cleaned_data['data_corsa'] < oraMinima:
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
								owner=request.user.prenotazioni,
								**form.cleaned_data
								)
		
		viaggio = prenotaCorsa(prenotazione)
		prenotazione.viaggio=viaggio
		prenotazione.save()

	return render_to_response(
							template_name,
							{
								"utentePrenotazioni":utentePrenotazioni,
								"form":form,
							},
							context_instance=RequestContext(request))
