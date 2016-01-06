# coding=utf-8
from django.conf.urls import url, patterns

from stats.views import StatsView

urlpatterns = patterns(
    '',
    url(r'^$', StatsView.as_view(), name="tamStats"),
)
