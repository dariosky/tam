# coding=utf-8
import datetime
from functools import partial

if __name__ == "__main__":
    import os
    import django

    os.environ["TAM_SETTINGS"] = "settings_arte"
    django.setup()

from tam.check.checks import (
    arrivo_singolo_o_due_arrivi,
    run_tests,
    check_associata,
    bus_1go_3back,
    abbinata_con_abbuoni,
)
from decimal import Decimal
from tam.models import Luogo

abano = Luogo.objects.get(nome=".Abano Montegrotto")
venezia = Luogo.objects.get(nome=".VENEZIA  AEROPORTO")
tests = [
    partial(
        arrivo_singolo_o_due_arrivi,
        da=venezia,
        a=abano,
        riferimento=abano,
        prezzo_singolo=31,
        expected_double={"prezzoVenezia": Decimal("40.78")},
        data=datetime.datetime(2016, 3, 31, 10, 0),
        check_equality=False,  # il vecchio sistema, l'equality-check deve fallire
    ),
    partial(
        arrivo_singolo_o_due_arrivi,
        da=venezia,
        a=abano,
        riferimento=abano,
        prezzo_singolo=30,
        expected_double={"prezzoVenezia": Decimal("37.94")},
    ),
    partial(
        arrivo_singolo_o_due_arrivi,
        da=venezia,
        a=abano,
        riferimento=abano,
        prezzo_singolo=31,
        expected_single1={"prezzoVenezia": Decimal("8.27")},
        expected_double={"prezzoVenezia": Decimal("40.78")},
    ),
    partial(
        check_associata,
        da=abano,
        a=venezia,
        riferimento=abano,
        prezzo=31,
        expect_andata={"prezzoVenezia": Decimal("8.27")},
        expect_ritorno={"prezzoVenezia": Decimal("-1.73")},
        expect_associata={"puntiAbbinata": 1, "prezzoPunti": Decimal("56.40")},
    ),
    partial(
        bus_1go_3back,
        abano,
        venezia,
        riferimento=abano,
        expected={"puntiAbbinata": 1, "prezzoPunti": Decimal("149.02")},
        data=datetime.datetime(2020, 4, 1, 12, 0),
    ),
    partial(
        abbinata_con_abbuoni,
        abano,
        venezia,
        riferimento=abano,
        expected=dict(prezzoVenezia=Decimal("66.40")),
    ),
]
if __name__ == "__main__":
    run_tests(tests)
