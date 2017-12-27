# coding=utf-8
from django.conf.urls import url

from .views import coda, ferie

urlpatterns = [
    url(r'^$', coda, name='codapresenze-home'),
    url(r'^codaferie/', ferie, name='codapresenze-ferie'),
]
