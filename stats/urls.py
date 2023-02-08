# coding=utf-8
from django.conf.urls import re_path

from stats.views import StatsView

urlpatterns = [
    re_path(r"^$", StatsView.as_view(), name="tamStats"),
]
