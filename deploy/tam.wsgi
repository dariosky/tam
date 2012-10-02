import os, sys
#PARENT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

sys.path.insert(0, PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
