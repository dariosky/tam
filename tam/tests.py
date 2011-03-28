'''
Created on 28/mar/2011

@author: Dario
'''
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "settings"

from tam.models import Viaggio, Tratta, Luogo
import datetime

inizio = Luogo.objects.get_or_create(nome='Inizio')[0]
inizio.save()
fine = Luogo.objects.get_or_create(nome='Fine')[0]
fine.save()

trattaMia = Tratta.objects.get_or_create(da=inizio, a=fine, minuti=390, km=695)[0]
trattaMia.save()

v = Viaggio(da=inizio, a=fine, data=datetime.datetime(2011, 03, 28, 12, 15, 00))
v.luogoDiRiferimento = inizio
v.updatePrecomp()

d = v.disturbi()
print "Disturbi: %s" % d
print sum(d.values())
trattaMia.delete()
inizio.delete()
fine.delete()
