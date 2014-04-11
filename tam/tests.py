#coding: utf-8
'''
Created on 28/mar/2011

@author: Dario
'''
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "settings"

import unittest
import datetime
from tam.disturbi import fascia_quarti_lineari, \
	trovaDisturbi, fasce_lineari, fasce_uno_due, fascia_uno_o_due_disturbi, \
	fasce_semilineari
from tam.models import Viaggio, Tratta, Luogo
from tam.models import reallySpaceless

class TestLineari(unittest.TestCase):
	def setUp(self):
		self.giornoFeriale = datetime.datetime(2012, 2, 14, 0, 0)
		self.sabato = datetime.datetime(2012, 2, 18, 0, 0)
		self.domenica = datetime.datetime(2012, 2, 19, 0, 0)
		self.disturbi = lambda * args: trovaDisturbi(*args, metodo=fasce_lineari)

	def intervalli(self,
				   oraInizio, minutoInizio,
				   oraFine, minutoFine,
				   giorno=None):
		""" Restituisce due datetime del giorno indicato con le ore indicate, eventualmente spostando la fine al giorno seguente """
		if giorno is None:
			giorno = self.giornoFeriale
		inizio = giorno.replace(hour=oraInizio, minute=minutoInizio)
		fine = giorno.replace(hour=oraFine, minute=minutoFine)
		if fine < inizio: fine = fine + datetime.timedelta(days=1)
		return inizio, fine

	def test1AttornoAllaPrimaZonaBassa(self):
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 29)), {})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 30)), {})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 31)), {'night': 0.25})

	def test2MezzoraBassaEAdiacenti(self):
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 21, 00)), {'night':0.25})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 21, 01)), {'night':0.50}) # primo scatto serale
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 22, 30)), {'night':1.00})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 22, 31)), {'night':1.25})

	def test3UnOraDiFasciaAlta(self):
		self.assertEqual(self.disturbi(*self.intervalli(22, 30, 23, 30)), {'night':1.00})
		self.assertEqual(self.disturbi(*self.intervalli(22, 29, 23, 30)), {'night':1.25}) # ho anche un quarto in fascia bassa
		self.assertEqual(self.disturbi(*self.intervalli(22, 30, 23, 31)), {'night':1.25}) # 5 quarti in fascia alta

	def test4AroundMidnight(self):
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 45)), {'night':0.25})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 46)), {'night':0.50})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 59)), {'night':0.50})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 0)), {'night':0.50})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 1)), {'night':0.75})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 2)), {'night':0.75})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 30)), {'night':1.0})

	def test5AroundCambioGiorno(self):
		self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 0)), {'night':1.0})
		self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 1)), {'night':1.0, 'morning':0.25})
		self.assertEqual(self.disturbi(*self.intervalli(3, 59, 4, 1)), {'night':0.25, 'morning':0.25})

	def test6PrimaMattina(self):
		self.assertEqual(self.disturbi(*self.intervalli(4, 0, 6, 0)), {'morning':2.0})
		self.assertEqual(self.disturbi(*self.intervalli(4, 0, 6, 1)), {'morning':2.25})

	def test7Mattina(self):
		self.assertEqual(self.disturbi(*self.intervalli(6, 0, 7, 0)), {'morning':0.5})
		self.assertEqual(self.disturbi(*self.intervalli(7, 0, 7, 45)), {'morning':0.5})
		self.assertEqual(self.disturbi(*self.intervalli(7, 0, 8, 0)), {'morning':0.5})

	def test8Weekend(self):
		self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 15)), {}) # giorno feriale
		self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 15, giorno=self.sabato)), {'night':0.25})
		self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 30, giorno=self.domenica)), {'night':0.25})


class TestUnaDue(unittest.TestCase):
	def setUp(self):
		self.giornoFeriale = datetime.datetime(2012, 2, 14, 0, 0)
		self.sabato = datetime.datetime(2012, 2, 18, 0, 0)
		self.domenica = datetime.datetime(2012, 2, 19, 0, 0)
		self.disturbi = lambda * args: trovaDisturbi(*args, metodo=fasce_uno_due)

	def intervalli(self,
				   oraInizio, minutoInizio,
				   oraFine, minutoFine,
				   giorno=None):
		""" Restituisce due datetime del giorno indicato con le ore indicate, eventualmente spostando la fine al giorno seguente """
		if giorno is None:
			giorno = self.giornoFeriale
		inizio = giorno.replace(hour=oraInizio, minute=minutoInizio)
		fine = giorno.replace(hour=oraFine, minute=minutoFine)
		if fine < inizio: fine = fine + datetime.timedelta(days=1)
		return inizio, fine

	def test1AttornoAllaPrimaZonaBassa(self):
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 29)), {})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 30)), {'night': 1})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 31)), {'night': 1})

	def test2MezzoraBassaEAdiacenti(self):
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 21, 00)), {'night':1})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 21, 01)), {'night':1}) # primo scatto serale
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 22, 30)), {'night':1})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 22, 31)), {'night':2})

	def test3UnOraDiFasciaAlta(self):
		self.assertEqual(self.disturbi(*self.intervalli(22, 30, 23, 30)), {'night':2})
		self.assertEqual(self.disturbi(*self.intervalli(22, 29, 23, 30)), {'night':2}) # ho anche un quarto in fascia bassa
		self.assertEqual(self.disturbi(*self.intervalli(22, 30, 23, 31)), {'night':2}) # 5 quarti in fascia alta

	def test4AroundMidnight(self):
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 45)), {'night':2})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 46)), {'night':2})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 59)), {'night':2})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 0)), {'night':2})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 1)), {'night':2})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 2)), {'night':2})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 30)), {'night':2})

	def test5AroundCambioGiorno(self):
		self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 0)), {'night':2})
		self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 1)), {'night':2, 'morning':2})
		self.assertEqual(self.disturbi(*self.intervalli(3, 59, 4, 1)), {'night':2, 'morning':2})

	def test6PrimaMattina(self):
		self.assertEqual(self.disturbi(*self.intervalli(4, 0, 6, 0)), {'night':2, 'morning':2})
		self.assertEqual(self.disturbi(*self.intervalli(4, 0, 6, 1)), {'night':2, 'morning':2})

	def test7Mattina(self):
		self.assertEqual(self.disturbi(*self.intervalli(6, 0, 7, 0)), {'morning':2})
		self.assertEqual(self.disturbi(*self.intervalli(7, 0, 7, 45)), {'morning':1})
		self.assertEqual(self.disturbi(*self.intervalli(7, 0, 8, 0)), {'morning':1})

	def test8Weekend(self):
		self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 15)), {}) # giorno feriale
		self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 15, giorno=self.sabato)), {'night':1})
		self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 30, giorno=self.domenica)), {'night':1})


class TestSemiLineare(unittest.TestCase):
	def setUp(self):
		self.giornoFeriale = datetime.datetime(2012, 2, 14, 0, 0)
		self.sabato = datetime.datetime(2012, 2, 18, 0, 0)
		self.domenica = datetime.datetime(2012, 2, 19, 0, 0)
		self.disturbi = lambda * args: trovaDisturbi(*args, metodo=fasce_semilineari)

	def intervalli(self,
				   oraInizio, minutoInizio,
				   oraFine, minutoFine,
				   giorno=None):
		""" Restituisce due datetime del giorno indicato con le ore indicate, eventualmente spostando la fine al giorno seguente """
		if giorno is None:
			giorno = self.giornoFeriale
		inizio = giorno.replace(hour=oraInizio, minute=minutoInizio)
		fine = giorno.replace(hour=oraFine, minute=minutoFine)
		if fine < inizio: fine = fine + datetime.timedelta(days=1)
		return inizio, fine

	def test1AttornoAllaPrimaZonaBassa(self):
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 29)), {})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 30)), {'night': 0.25})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 31)), {'night': 0.25})

	def test2MezzoraBassaEAdiacenti(self):
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 59)), {'night':0.25})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 21, 00)), {'night':0.5})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 21, 01)), {'night':0.5}) # primo scatto serale
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 22, 30)), {'night':1.25})
		self.assertEqual(self.disturbi(*self.intervalli(20, 0, 22, 31)), {'night':1.25})

	def test3UnOraDiFasciaAlta(self):
		self.assertEqual(self.disturbi(*self.intervalli(22, 30, 23, 30)), {'night':1.75})
		self.assertEqual(self.disturbi(*self.intervalli(22, 29, 23, 30)), {'night':1.75}) # ho anche un quarto in fascia bassa
		self.assertEqual(self.disturbi(*self.intervalli(22, 30, 23, 31)), {'night':1.75}) # 5 quarti in fascia alta

	def test4AroundMidnight(self):
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 45)), {'night':1.75})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 46)), {'night':1.75})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 59)), {'night':1.75})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 0)), {'night':2.0})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 1)), {'night':2})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 2)), {'night':2})
		self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 30)), {'night':2.25})

	def test5AroundCambioGiorno(self):
		self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 0)), {'night':3.5})
		self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 1)), {'night':3.5})
		self.assertEqual(self.disturbi(*self.intervalli(3, 59, 4, 1)), {'morning':2.25})

	def test6PrimaMattina(self):
		self.assertEqual(self.disturbi(*self.intervalli(4, 0, 6, 0)), {'morning':2})
		self.assertEqual(self.disturbi(*self.intervalli(4, 0, 6, 1)), {'morning':2})

	def test7Mattina(self):
		self.assertEqual(self.disturbi(*self.intervalli(6, 0, 7, 0)), {'morning':1})
		self.assertEqual(self.disturbi(*self.intervalli(7, 0, 7, 45)), {'morning':0.5})
		self.assertEqual(self.disturbi(*self.intervalli(7, 0, 8, 0)), {'morning':0.5})
		self.assertEqual(self.disturbi(*self.intervalli(7, 44, 7, 45)), {'morning':0.25})
		self.assertEqual(self.disturbi(*self.intervalli(7, 45, 8, 0)), {'morning':0.25})
		self.assertEqual(self.disturbi(*self.intervalli(7, 46, 8, 0)), {})

	def test8Weekend(self):
		self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 15)), {}) # giorno feriale
		self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 15, giorno=self.sabato)), {'night':0.25})
		self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 0, giorno=self.sabato)), {'night':3.50})
		self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 0, giorno=self.domenica)), {'night':3.75})
		self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 30, giorno=self.domenica)), {'night':0.5})


if __name__ == '__main__':
	# Spaceless test *****************
	s = """ Questa è una prova
					fatta da molti spazi
			vorrei      ottimizzare un po' la cosa
	"""
	s = reallySpaceless(s)
	print s
	assert(s == "Questa è una prova fatta da molti spazi vorrei ottimizzare un po' la cosa")

	#data_inizio = datetime.datetime(2011, 2, 22, 5, 00)
	#data_fine = datetime.datetime(2011, 2, 22, 7, 45)

	corsa = Viaggio.objects.get(id=76235)
	print "vecchio metodo: ", corsa.disturbi()

	print "\nnuovo metodo*****************"
	trovaDisturbi(corsa.date_start, corsa.get_date_end(recurse=True), metodo=fasce_semilineari)
