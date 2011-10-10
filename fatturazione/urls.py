'''
Created on 11/set/2011

@author: Dario Varotto
'''
from django.conf.urls.defaults import * #@UnusedWildImport
from fatturazione.views.generazione import filtro_consorzio, filtro_ricevute, \
	filtro_conducente

urlpatterns = patterns ('fatturazione.views',
    url(r'^$', 'lista_fatture', name="tamGenerazioneFatture"),

    url(r'^genera/consorzio/$', 'genera_fatture', {'filtro':filtro_consorzio, "tipo":"1"},
	   		 name="tamFattureGeneraConsorzio"),

    url(r'^genera/conducente/$', 'genera_conducente',
	   		 name="tamFattureGeneraConducente"),

	url(r'^genera/ricevute/$', 'genera_fatture', {'filtro':filtro_ricevute, "tipo":"3",
												  "keys":["conducente", "cliente"],
												  "template_name":"2.fatturazione_ricevute.djhtml"},
	   		name="tamFattureGeneraRicevute"),
)
