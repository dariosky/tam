import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'Tam.settings'
sys.path.insert(0, '/home/dariosky/lib/')
sys.path.insert(0, '/home/dariosky/webapps/tam/')
sys.path.insert(0, '/home/dariosky/webapps/tam/Tam/')


# This has to be done here otherwise Django won't be in a directory
# that's in PYTHONPATH.
from django.core.handlers.wsgi import WSGIHandler

application = WSGIHandler()
