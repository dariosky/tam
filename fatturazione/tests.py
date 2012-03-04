"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.db.models.aggregates import Count, Max


from tam.models import Conducente

conducenti = Conducente.objects.filter(emette_ricevute=True)

for conducente in conducenti:
	print "%5d %30s" % (conducente.id, conducente.nome), len(conducente.ricevute())
