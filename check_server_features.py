# coding: utf-8

"""Controlla che le funzionalità richieste dal server siano rispettate"""

import django
from django.conf import settings

django.setup()
from django.contrib.auth.models import User


def check_db():
    User.objects.get(id=1)


# CACHE
def check_cache():
    print("%s" % settings.CACHES["default"]["BACKEND"], end=" ")
    from django.core.cache import cache

    cache.set("Test", True)
    result = cache.get("Test")
    assert result == True


# def check_celery():
# 	from time import sleep
# 	from tam.tasks import test_task
# 	result = test_task.delay("Task delayed") #@UndefinedVariable
# 	for x in range(1, 5):
# 		if result.ready():
# 			return
# 		if x > 1: print "waiting",
# 		sleep(1)
# 	assert(result.ready())


if __name__ == "__main__":
    l = globals()
    for k, fu in l.items():
        if callable(fu) and k.startswith("check_"):
            print("Checking %s" % k[6:], end=" ")
            try:
                fu()
            except Exception as e:
                print("FAIL [%s]" % e)
            else:
                print("OK")
    print("fine.")
