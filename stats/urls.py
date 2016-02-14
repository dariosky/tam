# coding=utf-8
from django.conf.urls import url

from stats.views import StatsView

urlpatterns = [
    url(r'^$', StatsView.as_view(), name="tamStats"),
]
