#coding:utf-8

from django.template.context import RequestContext
from django.shortcuts import render_to_response
from fatturazione.models import Fattura
import datetime
from Tam.tam.views.tamviews import parseDateString

def view_fatture(request, template_name="5.visualizzazione.djhtml"):
	data_start = parseDateString(# dal primo del mese scorso
									request.GET.get("data_start"),
									default=datetime.date.today().replace(day=1)
								)
	data_end = parseDateString(# all'ultimo del mese scorso
									request.GET.get("data_end"),
									default=datetime.date.today()
								)
	
	lista_consorzio = Fattura.objects.filter(tipo='1', data__gte=data_start, data__lte=data_end)
#	lista_consorzio = lista_consorzio.annotate(valore=Sum(F('righe__prezzo')*(1+F('righe__iva')/100)))
	#TODO: dovrei annotare prezzo*1+iva/100, non si può fare attualmente 
	return render_to_response(template_name,
                              {
								"data_start":data_start,
								"data_end":data_end,
								"dontHilightFirst":True,
								"mediabundleJS": ('tamUI.js',),
								"mediabundleCSS": ('tamUI.css',),
								
								"lista_consorzio":lista_consorzio,
#								"lista_conducente":lista_conducente,
#								"lista_ricevute":lista_ricevute,

                              },
                              context_instance=RequestContext(request))
	
	
	
def fattura(request, id_fattura, template_name="6.fattura.djhtml"):
	fattura = Fattura.objects.get(id=id_fattura)
	emessa_da_html = fattura.emessa_da\
					.replace("www.artetaxi.it", "<a href='http://www.artetaxi.it'>www.artetaxi.it</a>")\
					.replace("info@artetaxi.it", "<a href='mailto:info@artetaxi.it'>info@artetaxi.it</a>")
	
	return render_to_response(template_name,
                              {
								"fattura":fattura,
								"emessa_da_html":emessa_da_html,

                              },
                              context_instance=RequestContext(request))