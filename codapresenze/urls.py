# coding=utf-8
from django.conf.urls import url

from .views import coda

urlpatterns = [
    url(r"", coda, name="codapresenze-home"),
    # url(r'socket\.io', 'socketio')
]
