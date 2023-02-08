# coding=utf-8
from django.urls import re_path
from .views import actionLog

urlpatterns = [
    re_path(r"^log/$", actionLog, name="actionLog"),
]
