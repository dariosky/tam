# coding=utf-8
from django.urls import re_path
from .archiveViews import menu, action, flat, view

urlpatterns = [
    re_path(r"^panel/$", menu, name="tamArchiveUtil"),
    re_path(r"^doArchive/$", action, name="tamArchiveAction"),
    re_path(r"^flat/$", flat, name="tamArchiveFlat"),
    re_path(r"^view/$", view, name="tamArchiveView"),
]
