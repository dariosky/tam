#encoding: utf-8
'''
Created on 11/set/2011

@author: Dario
'''
import datetime
from tam.models import Viaggio, ProfiloUtente
from django import forms

"""
Generazione fatture:
Chiedo di generare le fatture
	_fino a_
	anno
	progressivo
	
Generazione Fatture consorzio (a cliente):
	progressivo annuale, ma variabile
	iva 10% sulle corse
	possibilità di inserire una riga standard
	(logo)

Generazione Fatture Conducenti (a consorzio, tutte le corse fatturabili):
	progressivo in bianco
	(senza logo)
	
Generazione Ricevute (viaggi con pagamento posticipato)


"""


from django.shortcuts import render_to_response
from django.template.context import RequestContext
from tam.views import parseDateString

def generazione(request, template_name="generazione.html"):
	class Form(forms.Form):
		class Media:
			js = (
					'js/jquery.ui/jquery-ui.custom-min.js', 'js/calendarPreferences.js', 	# calendario nel filtro avanzato
				 )

			css = {
				'all': (
						'js/jquery.ui/themes/ui-lightness/ui.all.css',
					 )	# per il calendario nel filtro date avanzato
			}
	form = Form()
	data_start = parseDateString(	# dal primo del mese scorso
									request.GET.get("data_start"),
									default=(datetime.date.today()-datetime.timedelta(days=31)).replace(day=1)
								)
	data_end = parseDateString( # all'ultimo del mese scorso
									request.GET.get("data_end"),
									default=datetime.date.today().replace(day=1)-datetime.timedelta(days=1)
								)
	# prendo i viaggi da fatturare
	da_consorzio = Viaggio.objects.filter(data__gte=data_start, data__lte=data_end, fatturazione=True, conducente__isnull=False).order_by("cliente")[:1]
	
	profile = ProfiloUtente.objects.get(user=request.user)
	luogoRiferimento = profile.luogo
	return render_to_response(template_name,
                              {
								"today": datetime.date.today(),
								"da_consorzio":da_consorzio,
								"luogoRiferimento":luogoRiferimento,
								"data_start":data_start,
								"data_end":data_end,
								"form":form,
								"dontHilightFirst":True,
                              },
                              context_instance=RequestContext(request))
