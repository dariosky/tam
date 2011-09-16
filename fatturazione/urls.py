'''
Created on 11/set/2011

@author: Dario Varotto
'''
from django.conf.urls.defaults import * #@UnusedWildImport

urlpatterns = patterns ( 'fatturazione.views',
    url(r'^genera/$', 'generazione', name="tamGenerazioneFatture"),
)