# coding=utf-8
import pytest
from django.conf import settings

from tam.models import get_classifiche, Viaggio


@pytest.fixture(scope='session')
def django_db_setup():
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory',
    }


@pytest.mark.django_db
def test_classifiche():
    classifiche = get_classifiche()
    assert classifiche == [], "No run, no classifiche"
    # viaggio = Viaggio()
