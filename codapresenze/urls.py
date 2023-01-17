# coding=utf-8
from django.conf.urls import url

from .views import coda, FerieView

urlpatterns = [
    url(r"^$", coda, name="codapresenze-home"),
    url(r"^codaferie/", FerieView.as_view(), name="codapresenze-ferie"),
]
