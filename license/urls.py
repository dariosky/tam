# coding=utf-8
from django.conf.urls import url
from django.shortcuts import render

urlpatterns = [
    url(r'^license/$', render, {'template_name': 'license.html'}, name="tam_license"),
    # url(r'^licenza/$', 'notLicensed', name="tamLicense" ),
    # url(r"^activation/$", "activation", name="tamActivation"),
]
