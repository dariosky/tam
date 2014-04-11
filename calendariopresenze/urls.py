# coding=utf-8
from django.conf.urls import url, patterns
from calendariopresenze.views import CalendarManage

urlpatterns = patterns('calendariopresenze.views',
                       url(r'', CalendarManage.as_view(), name='calendariopresenze-manage'),

)
