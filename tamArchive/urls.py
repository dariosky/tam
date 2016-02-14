# coding=utf-8
from django.conf.urls import url
from .archiveViews import menu, action, flat, view

urlpatterns = [
    url(r'^panel/$', menu, name='tamArchiveUtil'),
    url(r'^doArchive/$', action, name='tamArchiveAction'),
    url(r'^flat/$', flat, name='tamArchiveFlat'),
    url(r'^view/$', view, name='tamArchiveView'),
]
