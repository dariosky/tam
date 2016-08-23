from settings import *

SECRET_KEY = "TestTestTestTest"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

from tam.views.classifiche_taxiabano import *
