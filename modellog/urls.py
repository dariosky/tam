# coding=utf-8
from django.conf.urls import url
from .views import actionLog

urlpatterns = [
    url(r"^log/$", actionLog, name="actionLog"),
]
