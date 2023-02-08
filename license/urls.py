# coding=utf-8
from django.urls import re_path
from django.shortcuts import render

urlpatterns = [
    re_path(
        r"^license/$", render, {"template_name": "license.html"}, name="tam_license"
    ),
    # url(r'^licenza/$', 'notLicensed', name="tamLicense" ),
    # url(r"^activation/$", "activation", name="tamActivation"),
]
