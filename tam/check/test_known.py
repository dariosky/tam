# coding=utf-8
# from tam.check.artecheck import run_tests as run_arte_tests, tests as taxi2_tests
# from tam.check.taxi2check import run_tests as run_taxi2_tests, tests as arte_tests
from decimal import Decimal
from functools import partial

import pytest
import logging

from tam.check.checks import arrivo_singolo_o_due_arrivi, check_associata, run_tests
from tam.models import Luogo

logger = logging.getLogger("tam.tests.known")


class TestKnownTaxi2:
    @pytest.fixture(autouse=True)
    def initialize(self):
        logger.debug("Creating a couple of places")
        created, self.abano = Luogo.objects.get_or_create(nome=".Abano-Montegrotto")
        created, self.venezia = Luogo.objects.get_or_create(nome=".Venezia Marco Polo")

    @pytest.mark.django_db
    def test_known_taxi2(self):
        print(Luogo.objects.all())
        tests = [
            partial(
                arrivo_singolo_o_due_arrivi,
                da=self.venezia,
                a=self.abano,
                riferimento=self.abano,
                prezzo_singolo=30,
                expected_single1=dict(prezzoPunti=Decimal("24.20"), puntiAbbinata=1),
                expected_double=dict(prezzoPunti=Decimal("54.20"), puntiAbbinata=1),
            ),
            partial(
                arrivo_singolo_o_due_arrivi,
                da=self.abano,
                a=self.venezia,
                riferimento=self.abano,
                prezzo_singolo=30,
                expected_single1=dict(prezzoPunti=Decimal("24.20"), puntiAbbinata=1),
                expected_double=dict(prezzoPunti=Decimal("54.20"), puntiAbbinata=1),
            ),
            partial(
                check_associata,
                da=self.abano,
                a=self.venezia,
                riferimento=self.abano,
                prezzo=30,
                expect_andata=dict(prezzoPunti=Decimal("24.20"), puntiAbbinata=1),
                expect_ritorno=dict(prezzoPunti=Decimal("18.20"), puntiAbbinata=1),
                expect_associata=dict(prezzoPunti=Decimal("416.20"), puntiAbbinata=1),
            ),
        ]

        run_tests(tests)

        # run_taxi2_tests(taxi2_tests)


def test_known_arte():
    # run_arte_tests(arte_tests)
    pass
