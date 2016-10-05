# coding=utf-8
from django.conf.urls import url

from rtmap.views import Overview

urlpatterns = [
    url(r'^$', Overview.as_view(), name="rtmap_overview"),
]
