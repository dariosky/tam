# coding=utf-8
import channels
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
os.environ.setdefault("TAM_SETTINGS", "settings_local")

channel_layer = channels.asgi.get_channel_layer()
