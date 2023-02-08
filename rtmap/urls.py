# coding=utf-8
from django.urls import re_path

from rtmap.views import Overview

urlpatterns = [
    re_path(r"^$", Overview.as_view(), name="rtmap-overview"),
]
