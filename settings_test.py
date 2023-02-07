# coding=utf-8
SECRET_KEY = "TestTestTestTest"

from settings import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

# noinspection PyUnresolvedReferences
from tam.views.classifiche_taxiabano import *
