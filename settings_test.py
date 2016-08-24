from settings import *

SECRET_KEY = "TestTestTestTest"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

from tam.views.classifiche_taxiabano import *
