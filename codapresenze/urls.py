# coding=utf-8
from django.conf.urls import re_path

from .views import coda, FerieView

urlpatterns = [
    re_path(r"^$", coda, name="codapresenze-home"),
    re_path(r"^codaferie/", FerieView.as_view(), name="codapresenze-ferie"),
]
