from django.shortcuts import render_to_response
from django.template.context import RequestContext
from markViews import prenotazioni
from django import forms
from prenotazioni.models import Prenotazione, TIPI_PAGAMENTO
from tam.widgets import MySplitDateTimeField, MySplitDateWidget
from django.utils.translation import ugettext as _

class FormPrenotazioni(forms.ModelForm):
	is_collettivo = forms.TypedChoiceField(label="Collettivo o individuale?",
				   coerce=lambda x: True if x == 'Collettivo' else False,
				   choices=((False, 'Individuale'), (True, 'Collettivo')),
				   widget=forms.RadioSelect
				)
	is_arrivo = forms.TypedChoiceField(label="Partenza o arrivo?",
				   coerce=lambda x: True if x == 'Arrivo' else False,
				   choices=((False, 'Partenza'), (True, 'Arrivo')),
				   widget=forms.RadioSelect
				)
	pagamento = forms.ChoiceField(label="Metodo di pagamento",
								  choices=TIPI_PAGAMENTO,
								  widget=forms.RadioSelect)

	def clean_pax(self):
		"pulizia numero di pax"
		value = self.cleaned_data['pax']
		if value > 50:
			raise forms.ValidationError("Sicuro del numero di persone?")
		return value

	def __init__(self, *args, **kwargs):
		super(FormPrenotazioni, self).__init__(*args, **kwargs)
		for field_name in self.fields:
			field = self.fields.get(field_name)
			if field:
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


@prenotazioni
def prenota(request, template_name='prenotazioni/main.html'):

	utentePrenotazioni = request.user.prenotazioni
	form = FormPrenotazioni(request.POST or None)

	if form.is_valid():
		print "Via con la prenotazione"

	return render_to_response(
							template_name,
							{
								"utentePrenotazioni":utentePrenotazioni,
								"form":form,
							},
							context_instance=RequestContext(request))
