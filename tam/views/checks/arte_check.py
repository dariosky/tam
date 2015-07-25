# coding=utf-8
import os
import pytz

os.environ['TAM_SETTINGS'] = "settings_arte"
from decimal import Decimal
import datetime

import django

django.setup()
from django.db import transaction

from django.conf import settings
from tam.models import Viaggio, Luogo
from tam.views.tamviews import associate

tz_italy = pytz.timezone('Europe/Rome')


class EndOfTestExeption(Exception):
    pass


def classifica_assertion(classifica, assertions, message=""):
    """
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
        print "Everything ok, rolledback changes"


if __name__ == '__main__':
    unarrivo_vs_dueassociati()
