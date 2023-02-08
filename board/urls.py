from django.conf.urls import re_path

from .views import main

urlpatterns = [
    re_path(r"", main, name="board-home"),
    # url(r'socket\.io', 'socketio')
]
