#!/usr/bin/env python
# coding=utf-8
import os
import django
from django.apps import apps
from subprocess import call
from django.conf import settings

os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
os.environ["PYTHONPATH"] = settings.PROJECT_PATH
django.setup()

configs = apps.get_app_configs()
for app in configs:
    if not app.path.startswith(settings.PROJECT_PATH):
        continue
    if not os.path.isdir(os.path.join(app.path, "locale")):
        # print "%s doesn't support locales" % app.verbose_name
        continue
    print("Building messages for %s" % app.verbose_name)
    os.chdir(app.path)
    call(["django-admin", "makemessages", "--no-wrap", "--no-obsolete"])
print("fin")
