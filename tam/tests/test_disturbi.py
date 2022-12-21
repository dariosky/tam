# coding: utf-8
'''
Created on 28/mar/2011

@author: Dario
'''
import os
from functools import partial

os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
import django

django.setup()

import unittest
import datetime
from tam.disturbi import (trovaDisturbi, fasce_lineari, fasce_uno_due, fasce_semilineari, fasce_semilineari_dal)


class DisturbiTest:
    def intervalli(self,
                   oraInizio, minutoInizio,
                   oraFine, minutoFine,
                   giorno=None):
        """ Restituisce due datetime del giorno indicato con le ore indicate, eventualmente spostando la fine al giorno seguente """
        if giorno is None:
            giorno = self.giornoFeriale
        inizio = giorno.replace(hour=oraInizio, minute=minutoInizio)
        fine = giorno.replace(hour=oraFine, minute=minutoFine)
        if fine < inizio:
            fine = fine + datetime.timedelta(days=1)
        return inizio, fine


class TestLineari(unittest.TestCase, DisturbiTest):
    def setUp(self):
        self.giornoFeriale = datetime.datetime(2012, 2, 14, 0, 0)
        self.sabato = datetime.datetime(2012, 2, 18, 0, 0)
        self.domenica = datetime.datetime(2012, 2, 19, 0, 0)
        self.disturbi = partial(trovaDisturbi, metodo=fasce_lineari)

    def test1AttornoAllaPrimaZonaBassa(self):
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 29)), {})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 30)), {})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 31)), {'night': 0.25})

    def test2MezzoraBassaEAdiacenti(self):
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 21, 00)), {'night': 0.25})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 21, 1)),
                         {'night': 0.50})  # primo scatto serale
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 22, 30)), {'night': 1.00})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 22, 31)), {'night': 1.25})

    def test3UnOraDiFasciaAlta(self):
        self.assertEqual(self.disturbi(*self.intervalli(22, 30, 23, 30)), {'night': 1.00})
        self.assertEqual(self.disturbi(*self.intervalli(22, 29, 23, 30)),
                         {'night': 1.25})  # ho anche un quarto in fascia bassa
        self.assertEqual(self.disturbi(*self.intervalli(22, 30, 23, 31)),
                         {'night': 1.25})  # 5 quarti in fascia alta

    def test4AroundMidnight(self):
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 45)), {'night': 0.25})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 46)), {'night': 0.50})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 59)), {'night': 0.50})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 0)), {'night': 0.50})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 1)), {'night': 0.75})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 2)), {'night': 0.75})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 30)), {'night': 1.0})

    def test5AroundCambioGiorno(self):
        self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 0)), {'night': 1.0})
        self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 1)),
                         {'night': 1.0, 'morning': 0.25})
        self.assertEqual(self.disturbi(*self.intervalli(3, 59, 4, 1)),
                         {'night': 0.25, 'morning': 0.25})

    def test6PrimaMattina(self):
        self.assertEqual(self.disturbi(*self.intervalli(4, 0, 6, 0)), {'morning': 2.0})
        self.assertEqual(self.disturbi(*self.intervalli(4, 0, 6, 1)), {'morning': 2.25})

    def test7Mattina(self):
        self.assertEqual(self.disturbi(*self.intervalli(6, 0, 7, 0)), {'morning': 0.5})
        self.assertEqual(self.disturbi(*self.intervalli(7, 0, 7, 45)), {'morning': 0.5})
        self.assertEqual(self.disturbi(*self.intervalli(7, 0, 8, 0)), {'morning': 0.5})

    def test8Weekend(self):
        self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 15)), {})  # giorno feriale
        self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 15, giorno=self.sabato)),
                         {'night': 0.25})
        self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 30, giorno=self.domenica)),
                         {'night': 0.25})


class TestUnaDue(unittest.TestCase):
    def setUp(self):
        self.giornoFeriale = datetime.datetime(2012, 2, 14, 0, 0)
        self.sabato = datetime.datetime(2012, 2, 18, 0, 0)
        self.domenica = datetime.datetime(2012, 2, 19, 0, 0)
        self.disturbi = partial(trovaDisturbi, metodo=fasce_uno_due)

    def intervalli(self,
                   oraInizio, minutoInizio,
                   oraFine, minutoFine,
                   giorno=None):
        """ Restituisce due datetime del giorno indicato con le ore indicate, eventualmente spostando la fine al giorno seguente """
        if giorno is None:
            giorno = self.giornoFeriale
        inizio = giorno.replace(hour=oraInizio, minute=minutoInizio)
        fine = giorno.replace(hour=oraFine, minute=minutoFine)
        if fine < inizio:
            fine = fine + datetime.timedelta(days=1)
        return inizio, fine

    def test1AttornoAllaPrimaZonaBassa(self):
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 29)), {})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 30)), {'night': 1})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 31)), {'night': 1})

    def test2MezzoraBassaEAdiacenti(self):
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 21, 00)), {'night': 1})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 21, 1)),
                         {'night': 1})  # primo scatto serale
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 22, 30)), {'night': 1})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 22, 31)), {'night': 2})

    def test3UnOraDiFasciaAlta(self):
        self.assertEqual(self.disturbi(*self.intervalli(22, 30, 23, 30)), {'night': 2})
        self.assertEqual(self.disturbi(*self.intervalli(22, 29, 23, 30)),
                         {'night': 2})  # ho anche un quarto in fascia bassa
        self.assertEqual(self.disturbi(*self.intervalli(22, 30, 23, 31)),
                         {'night': 2})  # 5 quarti in fascia alta

    def test4AroundMidnight(self):
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 45)), {'night': 2})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 46)), {'night': 2})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 59)), {'night': 2})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 0)), {'night': 2})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 1)), {'night': 2})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 2)), {'night': 2})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 30)), {'night': 2})

    def test5AroundCambioGiorno(self):
        self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 0)), {'night': 2})
        self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 1)), {'night': 2, 'morning': 2})
        self.assertEqual(self.disturbi(*self.intervalli(3, 59, 4, 1)), {'night': 2, 'morning': 2})

    def test6PrimaMattina(self):
        self.assertEqual(self.disturbi(*self.intervalli(4, 0, 6, 0)), {'night': 2, 'morning': 2})
        self.assertEqual(self.disturbi(*self.intervalli(4, 0, 6, 1)), {'night': 2, 'morning': 2})

    def test7Mattina(self):
        self.assertEqual(self.disturbi(*self.intervalli(6, 0, 7, 0)), {'morning': 2})
        self.assertEqual(self.disturbi(*self.intervalli(7, 0, 7, 45)), {'morning': 1})
        self.assertEqual(self.disturbi(*self.intervalli(7, 0, 8, 0)), {'morning': 1})

    def test8Weekend(self):
        self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 15)), {})  # giorno feriale
        self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 15, giorno=self.sabato)),
                         {'night': 1})
        self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 30, giorno=self.domenica)),
                         {'night': 1})


class TestSemiLineare(unittest.TestCase, DisturbiTest):
    def setUp(self):
        self.giornoFeriale = datetime.datetime(2012, 2, 14, 0, 0)
        self.sabato = datetime.datetime(2012, 2, 18, 0, 0)
        self.domenica = datetime.datetime(2012, 2, 19, 0, 0)
        self.disturbi = partial(trovaDisturbi, metodo=fasce_semilineari)

    def test1AttornoAllaPrimaZonaBassa(self):
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 29)), {})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 30)), {'night': 0.25})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 31)), {'night': 0.25})

    def test2MezzoraBassaEAdiacenti(self):
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 20, 59)), {'night': 0.25})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 21, 00)), {'night': 0.5})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 21, 1)),
                         {'night': 0.5})  # primo scatto serale
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 22, 30)), {'night': 1.25})
        self.assertEqual(self.disturbi(*self.intervalli(20, 0, 22, 31)), {'night': 1.25})

    def test3UnOraDiFasciaAlta(self):
        self.assertEqual(self.disturbi(*self.intervalli(22, 30, 23, 30)), {'night': 1.75})
        self.assertEqual(self.disturbi(*self.intervalli(22, 29, 23, 30)),
                         {'night': 1.75})  # ho anche un quarto in fascia bassa
        self.assertEqual(self.disturbi(*self.intervalli(22, 30, 23, 31)),
                         {'night': 1.75})  # 5 quarti in fascia alta

    def test4AroundMidnight(self):
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 45)), {'night': 1.75})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 46)), {'night': 1.75})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 23, 59)), {'night': 1.75})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 0)), {'night': 2.0})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 1)), {'night': 2})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 2)), {'night': 2})
        self.assertEqual(self.disturbi(*self.intervalli(23, 30, 0, 30)), {'night': 2.25})

    def test5AroundCambioGiorno(self):
        self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 0)), {'night': 3.5})
        self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 1)), {'night': 3.5})
        self.assertEqual(self.disturbi(*self.intervalli(3, 59, 4, 1)), {'morning': 2.25})

    def test6PrimaMattina(self):
        self.assertEqual(self.disturbi(*self.intervalli(4, 0, 6, 0)), {'morning': 2})
        self.assertEqual(self.disturbi(*self.intervalli(4, 0, 6, 1)), {'morning': 2})

    def test7Mattina(self):
        self.assertEqual(self.disturbi(*self.intervalli(6, 0, 7, 0)), {'morning': 1})
        self.assertEqual(self.disturbi(*self.intervalli(7, 0, 7, 45)), {'morning': 0.5})
        self.assertEqual(self.disturbi(*self.intervalli(7, 0, 8, 0)), {'morning': 0.5})
        self.assertEqual(self.disturbi(*self.intervalli(7, 44, 7, 45)), {'morning': 0.25})
        self.assertEqual(self.disturbi(*self.intervalli(7, 45, 8, 0)), {'morning': 0.25})
        self.assertEqual(self.disturbi(*self.intervalli(7, 46, 8, 0)), {})

    def test8Weekend(self):
        self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 15)), {})  # giorno feriale
        self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 15, giorno=self.sabato)),
                         {'night': 0.25})
        self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 0, giorno=self.sabato)),
                         {'night': 3.50})
        self.assertEqual(self.disturbi(*self.intervalli(3, 0, 4, 0, giorno=self.domenica)),
                         {'night': 3.75})
        self.assertEqual(self.disturbi(*self.intervalli(19, 30, 20, 30, giorno=self.domenica)),
                         {'night': 0.5})

    def testLineari2022BeforeActivation(self):
        self.assertEqual(
            trovaDisturbi(*self.intervalli(20, 0, 20, 29), metodo=fasce_semilineari),
            trovaDisturbi(*self.intervalli(20, 0, 20, 29), metodo=fasce_semilineari_dal),
        )

    def testLineari2022EarlyNight(self):
        self.assertEqual(
            trovaDisturbi(data_inizio=datetime.datetime(2012, 12, 5, 19),
                          data_fine=datetime.datetime(2012, 12, 5, 22, 0),
                          metodo=fasce_semilineari_dal),
            {'night': 1}
        )

    def test_lineari_2022(self):
        self.assertEqual(
            trovaDisturbi(data_inizio=datetime.datetime(2022, 12, 21, 17),
                          data_fine=datetime.datetime(2022, 12, 21, 21, 30),
                          metodo=fasce_semilineari_dal),
            {'night': 1}
        )
        self.assertEqual(
            trovaDisturbi(data_inizio=datetime.datetime(2022, 12, 21, 17),
                          data_fine=datetime.datetime(2022, 12, 22, 0, 29),
                          metodo=fasce_semilineari_dal),
            {'night': 2}
        )
        self.assertEqual(
            trovaDisturbi(data_inizio=datetime.datetime(2022, 12, 21, 17),
                          data_fine=datetime.datetime(2022, 12, 22, 3, 29),
                          metodo=fasce_semilineari_dal),
            {'night': 3.5}
        )
        self.assertEqual(
            trovaDisturbi(data_inizio=datetime.datetime(2022, 12, 22, 4, 15),
                          data_fine=datetime.datetime(2022, 12, 22, 8, 0),
                          metodo=fasce_semilineari_dal),
            {'morning': 2.75}
        )
        self.assertEqual(
            trovaDisturbi(data_inizio=datetime.datetime(2022, 12, 22, 6, 40),
                          data_fine=datetime.datetime(2022, 12, 22, 8, 0),
                          metodo=fasce_semilineari_dal),
            {'morning': 1}
        )

    def test_lineari_2022_festivi(self):
        self.assertEqual(
            trovaDisturbi(data_inizio=datetime.datetime(2022, 12, 11, 18),
                          data_fine=datetime.datetime(2022, 12, 11, 20, 0),
                          metodo=fasce_semilineari_dal),
            {'night': 1}
        )
        self.assertEqual(
            trovaDisturbi(data_inizio=datetime.datetime(2022, 12, 11, 19, 40),
                          data_fine=datetime.datetime(2022, 12, 11, 21, 30),
                          metodo=fasce_semilineari_dal),
            {'night': 1.25}
        )
        self.assertEqual(
            trovaDisturbi(data_inizio=datetime.datetime(2022, 12, 11, 20, 40),
                          data_fine=datetime.datetime(2022, 12, 11, 22, 30),
                          metodo=fasce_semilineari_dal),
            {'night': 1.25}
        )
        self.assertEqual(
            trovaDisturbi(data_inizio=datetime.datetime(2022, 12, 11, 21, 30),
                          data_fine=datetime.datetime(2022, 12, 11, 23, 00),
                          metodo=fasce_semilineari_dal),
            {'night': 1.5}
        )

    def test_lineari_2022_feriali(self):
        self.assertEqual(
            trovaDisturbi(data_inizio=datetime.datetime(2022, 12, 16, 18, 35),
                          data_fine=datetime.datetime(2022, 12, 16, 23, 17),
                          metodo=fasce_semilineari_dal),
            {'night': 1.5}
        )

        self.assertEqual(
            trovaDisturbi(data_inizio=datetime.datetime(2022, 12, 16, 20, 00),
                          data_fine=datetime.datetime(2022, 12, 16, 22, 40),
                          metodo=fasce_semilineari_dal),
            {'night': 1.25}
        )
