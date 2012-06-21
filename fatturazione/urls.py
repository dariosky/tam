'''
Created on 11/set/2011

@author: Dario Varotto
'''
from django.conf.urls.defaults import * #@UnusedWildImport

urlpatterns = patterns ('fatturazione.views',
    url(r'^$', 'lista_fatture_generabili', name="tamGenerazioneFatture"),

#    url(r'^genera/consorzio/$', 'genera_fatture', { 'filtro':filtro_consorzio,
#													"tipo":"1",
#													"keys":["cliente"],
#													"template_name":"2-1.fatturazione_consorzio.djhtml",
#													"order_by":["cliente", "data"],
#												},
#	   		 name="tamFattureGeneraConsorzio"),

#    url(r'^genera/conducente/$', 'genera_fatture', {'filtro':filtro_conducente, "tipo":"2",
#												  "keys":["conducente"],
#												  "template_name":"2-2.fatturazione_conducente.djhtml",
#												  "manager":RigaFattura.objects,
#												  "order_by":["conducente", "viaggio__cliente", "fattura__data"],
#												  },
#	   		 name="tamFattureGeneraConducente"),

#	url(r'^genera/ricevute/$', 'genera_fatture', {'filtro':filtro_ricevute, "tipo":"3",
#												  "keys":["cliente", "passeggero"],
#												  "template_name":"2-3.fatturazione_ricevute.djhtml"},
#	   		name="tamFattureGeneraRicevute"),

#	url(r'^genera/consorzio/manuale/$', 'nuova_fattura', {"tipo":"1"}, name="tam-nuova-fattura-consorzio"),
#	url(r'^genera/conducente/manuale/$', 'nuova_fattura', {"tipo":"2"}, name="tam-nuova-fattura-conducente"),
#	url(r'^genera/ricevuta/manuale/$', 'nuova_fattura', {"tipo":"3"}, name="tam-nuova-fattura-ricevuta"),

	url(r'^archivio/$', 'view_fatture', name="tamVisualizzazioneFatture"),

	url(r'archivio/(?P<id_fattura>\d*)/$', 'fattura', name='tamFatturaId'),

	url(r'archivio/export/(?P<id_fattura>\d*)/(?P<export_type>pdf|html)/$', 'exportfattura', name='tamExportFattura'),

)

from fatturazione.views.generazione import DEFINIZIONE_FATTURE
for fatturazione in DEFINIZIONE_FATTURE:
	urlpatterns += patterns ('fatturazione.views',
		url(fatturazione.url_generazione,
			'genera_fatture',
			{ "fatturazione":fatturazione },
			name="tamGenerazione%s" % fatturazione.codice
		),
		url(fatturazione.url_generazione.replace("$", "manuale/$"),
			'nuova_fattura', {"tipo":fatturazione.codice}, name=fatturazione.url_name()
		),
	)
