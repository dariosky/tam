# coding=utf-8
import logging
import traceback
from functools import partial

if __name__ == '__main__':
    import os
    import django

    os.environ['TAM_SETTINGS'] = "settings_taxi2"
    django.setup()

import pytz
from decimal import Decimal
import datetime
from django.db import transaction
from django.conf import settings
from tam.models import Viaggio, Luogo
from tam.views.tamviews import associate

logger = logging.getLogger('tam.axi2.check')
tz_italy = pytz.timezone('Europe/Rome')
abano = Luogo.objects.get(nome=".Abano-Montegrotto")
venezia = Luogo.objects.get(nome=".Venezia Marco Polo")


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
    assert errors == [], "\n".join(errors) + (("\n" + message) if message else "")


def arrivo_singolo_o_due_arrivi(da=venezia, a=abano):
    """
        Test congruenza
    """
    try:
        with transaction.atomic():
            arrivo_singolo = Viaggio(
                data=tz_italy.localize(datetime.datetime(2020, 6, 27, 12, 12)),
                da=da,
                a=a,
                prezzo=Decimal("60"),
                numero_passeggeri=2,
                esclusivo=False,
                luogoDiRiferimento=abano,
            )
            arrivo_singolo.costo_autostrada = arrivo_singolo.costo_autostrada_default()
            arrivo_singolo.abbuono_fisso = 0
            arrivo_singolo.updatePrecomp(force_save=True)

            classifica_assertion(arrivo_singolo.classifiche(),
                                 dict(prezzoPunti=Decimal("54.20"), puntiAbbinata=1))

            arrivo_v1 = Viaggio(
                data=tz_italy.localize(datetime.datetime(2020, 6, 27, 12, 12)),
                da=da,
                a=a,
                prezzo=Decimal("30"),
                numero_passeggeri=1,
                esclusivo=False,
                luogoDiRiferimento=abano,
            )
            arrivo_v1.costo_autostrada = arrivo_v1.costo_autostrada_default()
            arrivo_v1.abbuono_fisso = 0
            arrivo_v1.updatePrecomp(force_save=True)
            classifica_assertion(arrivo_v1.classifiche(),
                                 dict(prezzoPunti=Decimal("24.20"), puntiAbbinata=1))

            arrivo_v2 = Viaggio(
                data=tz_italy.localize(datetime.datetime(2020, 6, 27, 12, 12)),
                da=da,
                a=a,
                prezzo=Decimal("30"),
                numero_passeggeri=1,
                esclusivo=False,
                luogoDiRiferimento=abano,
            )
            arrivo_v2.costo_autostrada = arrivo_v2.costo_autostrada_default()
            arrivo_v2.abbuono_fisso = 0
            arrivo_v2.updatePrecomp(force_save=True)

            associate(assoType='link', viaggiIds=[arrivo_v1.id, arrivo_v2.id])

            # I have to retake the objects from the db
            arrivo_v1.refresh_from_db()
            arrivo_v2.refresh_from_db()

            classifica_assertion(
                arrivo_v1.classifiche(),
                dict(prezzoPunti=arrivo_singolo.prezzoPunti, puntiAbbinata=arrivo_singolo.punti_abbinata),
                "Due singoli in arrivo dovrebbe avere le stesse caratteristiche di arrivo singolo"
            )
            raise EndOfTestExeption
    except EndOfTestExeption:
        logger.info("Ok.")


def check_associata():
    try:
        with transaction.atomic():
            andata = Viaggio(
                data=tz_italy.localize(datetime.datetime(2020, 6, 27, 12, 12)),
                da=abano,
                a=venezia,
                prezzo=Decimal("30"),
                numero_passeggeri=1,
                esclusivo=False,
                luogoDiRiferimento=abano,
            )
            andata.costo_autostrada = andata.costo_autostrada_default()
            andata.updatePrecomp(force_save=True)
            classifica_assertion(andata.classifiche(),
                                 dict(prezzoPunti=Decimal("24.20"), puntiAbbinata=1))

            ritorno = Viaggio(
                data=tz_italy.localize(datetime.datetime(2020, 6, 27, 13, 12)),
                da=venezia,
                a=abano,
                prezzo=Decimal("30"),
                numero_passeggeri=1,
                esclusivo=False,
                luogoDiRiferimento=abano,
            )
            ritorno.costo_autostrada = ritorno.costo_autostrada_default()
            ritorno.updatePrecomp(force_save=True)
            assert ritorno.abbuono_fisso == 0
            classifica_assertion(ritorno.classifiche(),
                                 dict(prezzoPunti=Decimal("24.20"), puntiAbbinata=1))

            associate(assoType='link', viaggiIds=[andata.id, ritorno.id])

            # I have to retake the objects from the db
            andata.refresh_from_db()
            ritorno.refresh_from_db()
            classifica_assertion(andata.classifiche(),
                                 dict(prezzoPunti=Decimal("54.20"), puntiAbbinata=1))
            raise EndOfTestExeption
    except EndOfTestExeption:
        logger.info("Ok.")


if __name__ == '__main__':
    for test in (
        arrivo_singolo_o_due_arrivi,
        partial(arrivo_singolo_o_due_arrivi, da=abano, a=venezia),
        check_associata
    ):
        try:
            func_name = getattr(test, "__name__", None)
            if not func_name:
                func_name = test.func.__name__
            logger.info("Testing %s" % func_name)
            test()
        except:
            logger.error("FAILED")
            logger.error(traceback.format_exc())
