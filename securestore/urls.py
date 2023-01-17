# coding=utf-8
from django.conf.urls import url
from .views import notfound, serve_secure_file

urlpatterns = [
    url(r"^notfound/$", notfound, name="secure-404"),
    url(r"(?P<path>.*)", serve_secure_file, name="sercurestore_download"),
]
