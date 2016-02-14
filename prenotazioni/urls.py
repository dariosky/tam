# coding=utf-8
from django.conf.urls import url

from .views.main import prenota, cronologia, attachments_list

urlpatterns = [
    url(r'^$', prenota, name="tamPrenotazioni"),
    url(r'^edit/(?P<id_prenotazione>\d+)/$', prenota, name="tamPrenotazioni-edit"),

    url(r'^storico/$', cronologia, name="tamCronoPrenotazioni"),
    url(r'^attachments/$', attachments_list, name="tamPrenotazioni-attachment-list")
]
