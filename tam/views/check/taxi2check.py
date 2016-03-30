# coding=utf-8
from functools import partial

if __name__ == '__main__':
    import os
    import django

    os.environ['TAM_SETTINGS'] = "settings_taxi2"
    django.setup()

from tam.views.check.checks import arrivo_singolo_o_due_arrivi, run_tests, check_associata
from decimal import Decimal
from tam.models import Luogo

if __name__ == '__main__':
    abano = Luogo.objects.get(nome=".Abano-Montegrotto")
    venezia = Luogo.objects.get(nome=".Venezia Marco Polo")
    tests = [
        partial(arrivo_singolo_o_due_arrivi,
                da=venezia, a=abano, riferimento=abano,
                prezzo_singolo=30,
                expected_single1=dict(prezzoPunti=Decimal("24.20"), puntiAbbinata=1),
                expected_double=dict(prezzoPunti=Decimal("54.20"), puntiAbbinata=1),
                ),
        partial(arrivo_singolo_o_due_arrivi,
                da=abano, a=venezia, riferimento=abano,
                prezzo_singolo=30,
                expected_single1=dict(prezzoPunti=Decimal("24.20"), puntiAbbinata=1),
                expected_double=dict(prezzoPunti=Decimal("54.20"), puntiAbbinata=1),
                ),
        partial(check_associata,
                da=abano, a=venezia, riferimento=abano,
                prezzo=30,

                expect_andata=dict(prezzoPunti=Decimal("24.20"), puntiAbbinata=1),
                expect_ritorno=dict(prezzoPunti=Decimal("18.20"), puntiAbbinata=1),
                expect_associata=dict(prezzoPunti=Decimal("48.20"), puntiAbbinata=1),
                )
    ]

    run_tests(tests)
