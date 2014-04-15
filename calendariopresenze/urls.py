# coding=utf-8
from django.conf.urls import url, patterns
from calendariopresenze.views import CalendarManage, CalendarRank

urlpatterns = patterns('calendariopresenze.views',
                       url(r'set/', CalendarManage.as_view(), name='calendariopresenze-manage'),
                       url(r'rank/(?P<year>\d{4})/', CalendarRank.as_view(), name='calendariopresenze-rank'),
                       url(r'rank/', CalendarRank.as_view(), name='calendariopresenze-rank'),

)
