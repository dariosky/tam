# coding=utf-8
import datetime
import logging
import traceback
from decimal import Decimal

import pytz
from django.conf import settings
from django.db import transaction

from tam.models import Viaggio
from tam.views.tamviews import associate

tz_italy = pytz.timezone('Europe/Rome')
logger = logging.getLogger('tam.checks')


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


def arrivo_singolo_o_due_arrivi(
    da, a,
    riferimento,
    prezzo_singolo=Decimal(30),
    data=None,
    expected_single1=None,
    expected_single2=None,
    expected_double=None,
    check_equality=True,  # if False, don't check sigle1+single2=double
):
    """
        Test congruenza mail Rob. Lup. 26/6/2015
    """
    if data is None:
        data = datetime.datetime(2020, 6, 27, 10, 0)
    try:
        with transaction.atomic():
            doppio = Viaggio(
                data=tz_italy.localize(data),
                da=da,
                a=a,
                prezzo=prezzo_singolo * 2,
                numero_passeggeri=2,
                esclusivo=False,
                luogoDiRiferimento=riferimento,
            )
            doppio.costo_autostrada = doppio.costo_autostrada_default()
            # doppio.abbuono_fisso = settings.ABBUONO_AEROPORTI
            doppio.updatePrecomp(force_save=True)
            if expected_double:
                classifica_assertion(
                    doppio.classifiche(),
                    expected_double
                )

            singolo_v1 = Viaggio(
                data=tz_italy.localize(data),
                da=da,
                a=a,
                prezzo=prezzo_singolo,
                numero_passeggeri=1,
                esclusivo=False,
                luogoDiRiferimento=riferimento,
            )
            singolo_v1.costo_autostrada = singolo_v1.costo_autostrada_default()
            singolo_v1.abbuono_fisso = 0
            singolo_v1.updatePrecomp(force_save=True)
            if expected_single1:
                classifica_assertion(
                    singolo_v1.classifiche(),
                    expected_single1
                )

            singolo_v2 = Viaggio(
                data=tz_italy.localize(data),
                da=da,
                a=a,
                prezzo=prezzo_singolo,
                numero_passeggeri=1,
                esclusivo=False,
                luogoDiRiferimento=riferimento,
            )
            singolo_v2.costo_autostrada = singolo_v2.costo_autostrada_default()
            singolo_v2.abbuono_fisso = 0
            singolo_v2.updatePrecomp(force_save=True)
            if expected_single2:
                classifica_assertion(
                    singolo_v2.classifiche(),
                    expected_single2,
                )

            associate(assoType='link', viaggiIds=[singolo_v1.id, singolo_v2.id])

            # I have to retake the objects from the db
            singolo_v1.refresh_from_db()
            singolo_v2.refresh_from_db()

            for k, v in singolo_v2.classifiche().items():
                assert v == 0, "La 2nda corsa deve avere tutto a zero"

            if check_equality:
                classifica_assertion(
                    singolo_v1.classifiche(),
                    doppio.classifiche(),
                    "Due singoli in arrivo dovrebbe avere le stesse caratteristiche di arrivo singolo"
                )
            raise EndOfTestExeption
    except EndOfTestExeption:
        logger.info("Ok.")


def check_associata(da, a, riferimento, prezzo,
                    expect_andata=None,
                    expect_ritorno=None,
                    expect_associata=None,
                    data=None
                    ):
    """
        Test congruenza mail Rob. Lup. 26/6/2015
    """
    if data is None:
        data = datetime.datetime(2020, 6, 27, 10, 0)
    try:
        with transaction.atomic():
            andata = Viaggio(
                data=tz_italy.localize(data),
                da=da,
                a=a,
                prezzo=prezzo,
                numero_passeggeri=1,
                esclusivo=False,
                luogoDiRiferimento=riferimento,
            )
            andata.costo_autostrada = andata.costo_autostrada_default()
            andata.updatePrecomp(force_save=True)
            if expect_andata:
                classifica_assertion(
                    andata.classifiche(),
                    expect_andata,
                    "Andata"
                )

            ritorno = Viaggio(
                data=tz_italy.localize(data + datetime.timedelta(hours=1)),
                da=a,  # the way back
                a=da,
                prezzo=prezzo,
                numero_passeggeri=1,
                esclusivo=False,
                luogoDiRiferimento=riferimento,
            )
            ritorno.costo_autostrada = ritorno.costo_autostrada_default()
            ritorno.abbuono_fisso = settings.ABBUONO_AEROPORTI
            ritorno.updatePrecomp(force_save=True)

            if expect_ritorno:
                classifica_assertion(
                    ritorno.classifiche(),
                    expect_ritorno,
                    "Ritorno"
                )

            associate(assoType='link', viaggiIds=[andata.id, ritorno.id])

            # I have to retake the objects from the db
            andata.refresh_from_db()
            ritorno.refresh_from_db()

            if expect_associata:
                classifica_assertion(
                    andata.classifiche(),
                    expect_associata,
                    "Associata"
                )
            raise EndOfTestExeption
    except EndOfTestExeption:
        logger.info("Ok.")


def bus_1go_3back(abano, venezia, riferimento, expected, data=None):
    if data is None:
        data = datetime.datetime(2020, 6, 27, 12, 0)
    try:
        with transaction.atomic():
            andata = Viaggio(
                data=tz_italy.localize(data),
                da=abano,
                a=venezia,
                prezzo=32,
                numero_passeggeri=1,
                esclusivo=False,
                pagamento_differito=True,
                luogoDiRiferimento=riferimento,
            )
            andata.costo_autostrada = andata.costo_autostrada_default()
            andata.updatePrecomp(force_save=True)

            ritorno1 = Viaggio(
                data=tz_italy.localize(data + datetime.timedelta(hours=0, minutes=25)),
                da=venezia,  # the way back
                a=abano,
                prezzo=66,
                numero_passeggeri=2,
                esclusivo=False,
                luogoDiRiferimento=riferimento,
            )
            ritorno1.commissione = 10
            ritorno1.costo_autostrada = ritorno1.costo_autostrada_default()
            ritorno1.abbuono_fisso = 0
            ritorno1.updatePrecomp(force_save=True)

            ritorno2 = Viaggio(
                data=tz_italy.localize(data + datetime.timedelta(hours=0, minutes=30)),
                da=venezia,  # the way back
                a=abano,
                prezzo=29,
                numero_passeggeri=2,
                esclusivo=False,
                luogoDiRiferimento=riferimento,
            )
            ritorno2.costo_autostrada = ritorno1.costo_autostrada_default()
            ritorno2.abbuono_fisso = 0
            ritorno2.updatePrecomp(force_save=True)

            ritorno3 = Viaggio(
                data=tz_italy.localize(data + datetime.timedelta(hours=0, minutes=55)),
                da=venezia,  # the way back
                a=abano,
                prezzo=58,
                numero_passeggeri=2,
                esclusivo=False,
                luogoDiRiferimento=riferimento,
            )
            ritorno3.costo_autostrada = ritorno1.costo_autostrada_default()
            ritorno3.abbuono_fisso = settings.ABBUONO_AEROPORTI
            ritorno3.updatePrecomp(force_save=True)

            associate(assoType='link', viaggiIds=[andata.id, ritorno1.id
                , ritorno2.id, ritorno3.id])
            ritorno2.abbuono_fisso = 0

            # I have to retake the objects from the db
            andata.refresh_from_db()
            ritorno1.refresh_from_db()
            ritorno2.refresh_from_db()
            ritorno3.refresh_from_db()

            if expected:
                classifica_assertion(
                    andata.classifiche(),
                    expected,
                    "Associata"
                )
            raise EndOfTestExeption
    except EndOfTestExeption:
        logger.info("Ok.")


def run_tests(tests):
    for test in tests:
        try:
            func_name = getattr(test, "__name__", None)
            if not func_name:
                func_name = test.func.__name__
            logger.info("Testing %s" % func_name)
            test()
        except:
            logger.error("FAILED")
            logger.error(traceback.format_exc())
