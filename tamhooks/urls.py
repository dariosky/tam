# coding=utf-8
from django.conf.urls import url
from .views import mail_report

urlpatterns = [
    url(r'^email/$', mail_report, name='tamWebhookEmail'),
]
