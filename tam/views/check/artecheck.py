# coding=utf-8
from functools import partial

if __name__ == '__main__':
    import os
    import django

    os.environ['TAM_SETTINGS'] = "settings_arte"
    django.setup()

from tam.views.check.checks import arrivo_singolo_o_due_arrivi, run_tests, check_associata
from decimal import Decimal
from tam.models import Luogo

if __name__ == '__main__':
    abano = Luogo.objects.get(nome=".Abano Montegrotto")
    venezia = Luogo.objects.get(nome=".VENEZIA  AEROPORTO")
    tests = [partial(arrivo_singolo_o_due_arrivi,
                     da=venezia, a=abano, riferimento=abano,
                     prezzo_singolo=30,
                     expected_double={'prezzoVenezia': Decimal("37.94")},
                     ),
             partial(arrivo_singolo_o_due_arrivi,
                     da=venezia, a=abano, riferimento=abano,
                     prezzo_singolo=31,

                     expected_single1={'prezzoVenezia': Decimal('8.27')},
                     expected_double={'prezzoVenezia': Decimal("40.78")},
                     ),
             partial(check_associata,
                     da=abano, a=venezia, riferimento=abano,
                     prezzo=31,

                     expect_andata={'prezzoVenezia': Decimal('8.27')},
                     expect_ritorno={'prezzoVenezia': Decimal('-1.73')},
                     expect_associata={'puntiAbbinata': 1, 'prezzoPunti': Decimal("56.40")},
                     )
             ]

    run_tests(tests)
