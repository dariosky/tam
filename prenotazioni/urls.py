# coding=utf-8
from django.conf.urls import re_path

from .views.main import prenota, cronologia, attachments_list, download_attachment

urlpatterns = [
    re_path(r"^$", prenota, name="tamPrenotazioni"),
    re_path(r"^edit/(?P<id_prenotazione>\d+)/$", prenota, name="tamPrenotazioni-edit"),
    re_path(r"^storico/$", cronologia, name="tamCronoPrenotazioni"),
    re_path(
        r"^attachment/(?P<id_prenotazione>\d+)/$",
        download_attachment,
        name="tamPrenotazioni-attachment",
    ),
    re_path(
        r"^attachments/$", attachments_list, name="tamPrenotazioni-attachment-list"
    ),
]
