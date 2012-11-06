from django.shortcuts import render_to_response
from django.template.context import RequestContext
from markViews import prenotazioni
from django import forms
from prenotazioni.models import Prenotazione

class FormPrenotazioni(forms.Form):
	class Meta:
		model = Prenotazione
	

@prenotazioni
def prenota(request, template_name='prenotazioni/main.html'):
	
	utentePrenotazioni = request.user.prenotazioni
	form =FormPrenotazioni(request.POST or None)
	if form.is_valid():
		print "Via con la prenotazione"
	
	return render_to_response(
							template_name,
							{
								"utentePrenotazioni":utentePrenotazioni,
								"form":form,
							},
							context_instance=RequestContext(request))
