# coding=utf-8
from django.conf.urls import re_path
from .views import notfound, serve_secure_file

urlpatterns = [
    re_path(r"^notfound/$", notfound, name="secure-404"),
    re_path(r"(?P<path>.*)", serve_secure_file, name="sercurestore_download"),
]
