# coding=utf-8
from django.conf.urls import re_path
from calendariopresenze.views import CalendarManage, CalendarRank, CalendarByConducente

urlpatterns = [
    re_path(r"set/", CalendarManage.as_view(), name="calendariopresenze-manage"),
    re_path(
        r"rank/(?P<year>\d{4})/", CalendarRank.as_view(), name="calendariopresenze-rank"
    ),
    re_path(r"rank/", CalendarRank.as_view(), name="calendariopresenze-rank"),
    re_path(
        r"view/(?P<year>\d{4})/(?P<conducente_id>\d+)/(?P<caltype>\d+)/",
        CalendarByConducente.as_view(),
        name="calendariopresenze-view",
    ),
]
