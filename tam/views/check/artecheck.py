# coding=utf-8
if __name__ == '__main__':
    import os
    import django

    os.environ['TAM_SETTINGS'] = "settings_arte"
    django.setup()

import pytz
from decimal import Decimal
import datetime
from django.db import transaction
from django.conf import settings
from tam.models import Viaggio, Luogo
from tam.views.tamviews import associate

tz_italy = pytz.timezone('Europe/Rome')


class EndOfTestExeption(Exception):
    pass


def classifica_assertion(classifica, assertions, message=""):
    """
    @param message: the message to presento when the assertion fail
    @type assertions: dict(str:Decimal)
    @type classifica: dict(str:Decimal)
    """
    errors = []
    for key, expected in assertions.items():
        if classifica[key] != expected:
            errors.append("{key} is {val} instead of {expected}".format(
                key=key, val=classifica[key], expected=expected
            ))
    assert errors == [], "\n".join(errors) + ("\n" + message) if message else ""


def unarrivo_vs_dueassociati():
    """
        Test congruenza mail Rob. Lup. 26/6/2015
    """
    try:
        with transaction.atomic():
            abano = Luogo.objects.get(nome=".Abano Montegrotto")
            venezia = Luogo.objects.get(nome=".VENEZIA  AEROPORTO")
            arrivo_singolo = Viaggio(
                data=tz_italy.localize(datetime.datetime(2020, 6, 27, 12, 12)),
                da=venezia,
                a=abano,
                prezzo=Decimal("60"),
                numero_passeggeri=2,
                esclusivo=False,
                luogoDiRiferimento=abano,
            )
            arrivo_singolo.costo_autostrada = arrivo_singolo.costo_autostrada_default()
            arrivo_singolo.abbuono_fisso = settings.ABBUONO_AEROPORTI
            arrivo_singolo.updatePrecomp(force_save=True)

            classifica_assertion(arrivo_singolo.classifiche(),
                                 {'prezzoVenezia': Decimal("27.94")})

            arrivo_v1 = Viaggio(
                data=tz_italy.localize(datetime.datetime(2020, 6, 27, 12, 12)),
                da=venezia,
                a=abano,
                prezzo=Decimal("30"),
                numero_passeggeri=1,
                esclusivo=False,
                luogoDiRiferimento=abano,
            )
            arrivo_v1.costo_autostrada = arrivo_v1.costo_autostrada_default()
            arrivo_v1.abbuono_fisso = settings.ABBUONO_AEROPORTI
            arrivo_v1.updatePrecomp(force_save=True)
            arrivo_v2 = Viaggio(
                data=tz_italy.localize(datetime.datetime(2020, 6, 27, 12, 12)),
                da=venezia,
                a=abano,
                prezzo=Decimal("30"),
                numero_passeggeri=1,
                esclusivo=False,
                luogoDiRiferimento=abano,
            )
            arrivo_v2.costo_autostrada = arrivo_v2.costo_autostrada_default()
            arrivo_v2.abbuono_fisso = settings.ABBUONO_AEROPORTI
            arrivo_v2.updatePrecomp(force_save=True)

            associate(assoType='link', viaggiIds=[arrivo_v1.id, arrivo_v2.id])

            # I have to retake the objects from the db
            arrivo_v1.refresh_from_db()
            arrivo_v2.refresh_from_db()
            print arrivo_v1.classifiche()
            print arrivo_singolo.classifiche()

            classifica_assertion(
                arrivo_v1.classifiche(),
                {'prezzoVenezia': arrivo_singolo.prezzoVenezia},
                "Due singoli in arrivo dovrebbe avere le stesse caratteristiche di arrivo singolo"
            )
            raise EndOfTestExeption
    except EndOfTestExeption:
        print "Everything ok, changes rolledback"


def unarrivo_vs_dueassociati2():
    """
        Test congruenza mail Rob. Lup. 29/8/2015
    """
    try:
        with transaction.atomic():
            abano = Luogo.objects.get(nome=".Abano Montegrotto")
            venezia = Luogo.objects.get(nome=".VENEZIA  AEROPORTO")
            partenza_singolo = Viaggio(
                data=tz_italy.localize(datetime.datetime(2020, 6, 27, 12, 12)),
                da=venezia,
                a=abano,
                prezzo=Decimal("62"),
                numero_passeggeri=2,
                esclusivo=False,
                luogoDiRiferimento=abano,
            )
            partenza_singolo.costo_autostrada = partenza_singolo.costo_autostrada_default()
            partenza_singolo.abbuono_fisso = 0
            partenza_singolo.updatePrecomp(force_save=True)

            classifica_assertion(partenza_singolo.classifiche(),
                                 {'prezzoVenezia': Decimal("40.78")}, "Check prezzoVenezia")

            partenza_v1 = Viaggio(
                data=tz_italy.localize(datetime.datetime(2020, 6, 27, 12, 11)),
                da=abano,
                a=venezia,
                prezzo=Decimal("31"),
                numero_passeggeri=1,
                esclusivo=False,
                luogoDiRiferimento=abano,
            )

            partenza_v1.costo_autostrada = partenza_v1.costo_autostrada_default()
            partenza_v1.abbuono_fisso = 0
            partenza_v1.updatePrecomp(force_save=True)
            assert partenza_v1.classifiche()['prezzoVenezia'] == Decimal('8.27')

            partenza_v2 = Viaggio(
                data=tz_italy.localize(datetime.datetime(2020, 6, 27, 12, 12)),
                da=abano,
                a=venezia,
                prezzo=Decimal("31"),
                numero_passeggeri=1,
                esclusivo=False,
                luogoDiRiferimento=abano,
            )
            partenza_v2.costo_autostrada = partenza_v2.costo_autostrada_default()
            partenza_v2.abbuono_fisso = 0
            partenza_v2.updatePrecomp(force_save=True)

            associate(assoType='link', viaggiIds=[partenza_v1.id, partenza_v2.id])

            # I have to retake the objects from the db
            partenza_v1.refresh_from_db()
            partenza_v2.refresh_from_db()
            assert partenza_v1.classifiche()['prezzoVenezia'] == Decimal(56)
            print "doppia in partenza", partenza_v1.classifiche()
            print "singolo", partenza_singolo.classifiche()

            classifica_assertion(
                partenza_v1.classifiche(),
                {'prezzoVenezia': partenza_singolo.prezzoVenezia},
                "Due singoli in arrivo dovrebbe avere le stesse caratteristiche di arrivo singolo"
            )
            raise EndOfTestExeption
    except EndOfTestExeption:
        print "Everything ok, changes rolledback"


if __name__ == '__main__':
    # unarrivo_vs_dueassociati()
    unarrivo_vs_dueassociati2()
