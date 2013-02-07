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
from prenotazioni.views.tam_email import notifyByMail
from django.conf import settings
#import tempfile
from email.MIMEBase import MIMEBase
from email import Encoders
import os

class NumberInput(Input):
	input_type = 'number'

def inviaMailPrenotazione(prenotazione,
						  azione,
						  attachments=[],
						  extra_context=None):
	if azione == "create":
		subject = "Conferma prenotazione TaM n° %d" % prenotazione.id
		prenotazione_suffix = "effettuata"
	elif azione == "update":
		subject = "Modifica prenotazione TaM n° %d" % prenotazione.id
		prenotazione_suffix = "modificata"
	elif azione == "delete":
		subject = "Annullamento prenotazione TaM n° %d" % prenotazione.id
		prenotazione_suffix = "cancellata"
	else:
		raise Exception ("Azione mail non valida %s" % azione)

	azione = ""
	context = { "prenotazione":prenotazione,
				"azione":prenotazione_suffix,
			  }
	if extra_context:
		context.update(extra_context)

	notifyByMail(
		to=[prenotazione.owner.email, settings.EMAIL_CONSORZIO],
		subject=subject,
		context=context,
		attachments=attachments,
		messageTxtTemplateName="prenotazioni_email/conferma.inc.txt",
		messageHtmlTemplateName="prenotazioni_email/conferma.inc.html",
	)

class FormPrenotazioni(forms.ModelForm):
	def clean_pax(self):
		"pulizia numero di pax"
		value = self.cleaned_data['pax']
		if value > 50:
			raise forms.ValidationError("Sicuro del numero di persone?")
		return value
	
	def clean_is_arrivo(self):
		value = self.cleaned_data['is_arrivo']
		if not value in (True, False):
			raise forms.ValidationError("Devi specificare se la corsa è un arrivo o una partenza.")
		return value
	
	def clean_is_collettivo(self):
		value = self.cleaned_data['is_collettivo']
		if not value in (True, False):
			raise forms.ValidationError("Questo campo è obbligatorio.")
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
		self.fields['attachment'] = forms.FileField(
												label="Allegato",
												required=False,
												help_text="Allega un file alla richiesta (opzionale)"
									)

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
def prenota(request, id_prenotazione=None, template_name='prenotazioni/main.html'):
	utentePrenotazioni = request.user.prenotazioni

	previous_values = {}
	if id_prenotazione:
		try:
			prenotazione = Prenotazione.objects.get(id=id_prenotazione)
		except Prenotazione.DoesNotExist:
			messages.error(
				request,
				"La prenotazione non esiste."
			)
			return HttpResponseRedirect(reverse('tamCronoPrenotazioni'))
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
	else:
		prenotazione = None
		editable = True

	form = FormPrenotazioni(request.POST or None, request.FILES or None, instance=prenotazione)

	# deciso se mostrare o meno la scelta dei clienti:
	clienti_attivi = utentePrenotazioni.clienti
	if clienti_attivi.count() == 0:
		messages.error(
			request,
			"Non hai alcun cliente abilitato."
		)
		return HttpResponseRedirect(reverse('login'))

	if clienti_attivi.count() > 1:
		form.fields["cliente"].editable = True
		form.fields["cliente"].queryset = utentePrenotazioni.clienti
		form.fields["cliente"].label = ''
		cliente_unico = None
	else:
		#del forms.fields['cliente']
		del form.fields['cliente']
		cliente_unico = clienti_attivi.all()[0]

	if request.method == "POST" and prenotazione:
		# salvo i valori precedenti e consento la cancellazione
		for key in form.fields:
			if key <> "attachment":
				previous_values[key] = getattr(prenotazione, key)

		if "delete" in request.POST:
			messages.success(request, "Prenotazione n°%d annullata." % prenotazione.id)
			inviaMailPrenotazione(prenotazione, "delete")
			prenotazione.delete()
			return HttpResponseRedirect(reverse('tamCronoPrenotazioni'))

	if form.is_valid() and editable:
		request_attachment = form.cleaned_data['attachment']
		attachment = None
		del form.cleaned_data['attachment']
		
		if request_attachment:
			#destination = tempfile.NamedTemporaryFile(delete=False)
			attachment = MIMEBase('application', "octet-stream")
			#print "Write to %s" % destination.name
			attachment.set_payload(request_attachment.read())
			Encoders.encode_base64(attachment)
			attachment.add_header(
					'Content-Disposition',
					'attachment; filename="%s"' % os.path.basename(request_attachment.name)
				)
			#for chunk in attachment.chunks():
			#	destination.write(chunk)
			#destination.close()

		#assert(False)
		if id_prenotazione is None:
			prenotazione = Prenotazione(
									owner=utentePrenotazioni,
									**form.cleaned_data
									)
			if clienti_attivi.count() == 1:
				prenotazione.cliente = cliente_unico

			viaggio = prenotaCorsa(prenotazione)
			prenotazione.viaggio = viaggio
			prenotazione.save()

			messages.success(
				request,
				"Prenotazione n° %d effettuata, a breve riceverai una mail di conferma." % prenotazione.id
			)
			inviaMailPrenotazione(prenotazione,
								  "create",
								  attachments=[attachment] if attachment else []
								 )
			return HttpResponseRedirect(reverse('tamPrenotazioni'))
		else:	# salvo la modifica
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
			if changes or attachment:
				stringhe_cambiamenti = []
				for key in changes:
					(label, oldValue, newValue) = changes[key]
					stringhe_cambiamenti.append("Cambiato %s da %s a %s" % (label, oldValue, newValue))

				cambiamenti = "\n".join(stringhe_cambiamenti)
				inviaMailPrenotazione(prenotazione,
									  "update",
									  attachments=[attachment] if attachment else [],
									  extra_context={"cambiamenti":cambiamenti}
									 )
				messages.success(request, "Modifica eseguita.")
				prenotazione.save()
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
								"editable":editable,
								"prenotazione":prenotazione,
								"cliente_unico":cliente_unico,
							},
							context_instance=RequestContext(request))


@prenotazioni
def cronologia(request, template_name='prenotazioni/cronologia.html'):
	utentePrenotazioni = request.user.prenotazioni
	clienti_attivi = utentePrenotazioni.clienti
	if clienti_attivi.count() == 1:
		cliente_unico = clienti_attivi.all()[0]
	else:
		cliente_unico = None

	prenotazioni = Prenotazione.objects.filter(
							cliente__in=utentePrenotazioni.clienti.all()
				   )


	return render_to_response(
							template_name,
							{
								"utentePrenotazioni":utentePrenotazioni,
								"prenotazioni":prenotazioni,
								"cliente_unico":cliente_unico,
							},
							context_instance=RequestContext(request))
