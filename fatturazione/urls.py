# coding=utf-8
"""
Created on 11/set/2011

@author: Dario Varotto
"""
from django.conf.urls import re_path

from fatturazione.views import (
    view_fatture,
    fattura,
    exportmultifattura,
    exportfattura,
    nuova_fattura,
    genera_fatture,
)
from fatturazione.views.generazione import (
    DEFINIZIONE_FATTURE,
    lista_fatture_generabili,
    setPagato,
)

urlpatterns = [
    re_path(r"^$", lista_fatture_generabili, name="tamGenerazioneFatture"),
    re_path(r"^archivio/$", view_fatture, name="tamVisualizzazioneFatture"),
    re_path(r"archivio/(?P<id_fattura>\d*)/$", fattura, name="tamFatturaId"),
    re_path(
        r"archivio/export/(?P<id_fattura>\d*)/(?P<export_type>pdf|html)/$",
        exportfattura,
        name="tamExportFattura",
    ),
    re_path(
        r"archivio/export/group/(?P<tipo>.*?)/(?P<export_type>pdf|html)/$",
        exportmultifattura,
        name="tamExportMultiFattura",
    ),
    re_path(r"setPagato$", setPagato, name="tamSetPagatoFattura"),
]

for fatturazione in DEFINIZIONE_FATTURE:
    if not fatturazione.generabile:
        continue
    urlpatterns += [
        re_path(
            fatturazione.url_generazione,
            genera_fatture,
            {"fatturazione": fatturazione},
            name=fatturazione.urlname_generazione(),
        ),
        re_path(
            fatturazione.url_generazione.replace("$", "manuale/$"),
            nuova_fattura,
            {"fatturazione": fatturazione},
            name=fatturazione.urlname_manuale(),
        ),
    ]
