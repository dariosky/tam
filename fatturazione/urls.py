'''
Created on 11/set/2011

@author: Dario Varotto
'''
from django.conf.urls.defaults import * #@UnusedWildImport

urlpatterns = patterns ( 'fatturazione.views',
    url(r'^$', 'generazione', name="tamGenerazioneFatture"),
    url(r'^genera/consorzio/$', 'genera_consorzio', name="tamFattureGeneraConsorzio"),
)