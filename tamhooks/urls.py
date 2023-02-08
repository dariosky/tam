# coding=utf-8
from django.conf.urls import re_path
from .views import mail_report

urlpatterns = [
    re_path(r"^email/$", mail_report, name="tamWebhookEmail"),
]
