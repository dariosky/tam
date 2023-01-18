# coding=utf-8
# ===============================================================================
# This born on march 2013 when webfaction servers went to UTC
# It contains some helper to keep dates sane on indicated timezone
# ===============================================================================
from collections import OrderedDict

from django.utils import timezone
import datetime
import pytz
import logging
import re

logger = logging.getLogger("tam.dates")

MONTH_TRANSLATIONS = OrderedDict(
    [
        ("gennaio", "january"),
        ("febbraio", "february"),
        ("marzo", "march"),
        ("aprile", "april"),
        ("maggio", "may"),
        ("giugno", "june"),
        ("luglio", "july"),
        ("agosto", "august"),
        ("settembre", "september"),
        ("ottobre", "october"),
        ("novembre", "november"),
        ("dicembre", "december"),
    ]
)
MONTH_NAMES = list(map(str.capitalize, MONTH_TRANSLATIONS.keys()))


def normalizeTimeString(time_string):
    """
    Normalize the timestring to make it a 5 char timestring
    1       >   01:00
    1:00    >   01:00
    1:3     >   01:30
    """
    r = time_string
    if not r:
        return None
    if len(r) < 2 or r[1] == ":":
        r = "0" + r
    if len(r) < 3:
        r += ":"
    if len(r) < 5:
        r += "0" * (5 - len(r))
    return r


def parse_datestring(s, default=None):
    """Parse datestring as it was in Italy trying some format"""
    if not s:
        return default
    s = s.replace(",", "").replace("  ", " ").lower()
    for m_ita, m_eng in MONTH_TRANSLATIONS.items():
        s = s.replace(m_ita, m_eng)  # bring the eventual months in English

    naive_date_time = None
    for time_format in ("%d/%m/%Y", "%d %B %Y", "%B %d %Y"):
        try:
            naive_date_time = datetime.datetime.strptime(s, time_format)
            break
        except ValueError as e:
            logger.warning("Error parsing date. %s" % e)
    if naive_date_time is None:
        return default
    else:
        naive_date = datetime.datetime(*naive_date_time.timetuple()[:3])
        return tz_italy.localize(naive_date)


def ita_now():
    return timezone.now().astimezone(tz_italy)


def ita_today():
    """Use a localize datetime (at midnight) instead of a date"""
    return ita_now().replace(hour=0, minute=0, second=0, microsecond=0)


def get_prossime_inizio():
    """Restituisce la data di inizio delle prossime corse"""
    adesso = ita_now()
    data_ScorsaMezzanotte = adesso.replace(hour=0, minute=0)
    data_DueOreFa = adesso - datetime.timedelta(hours=2)
    return min(data_ScorsaMezzanotte, data_DueOreFa)


def date_enforce(data):
    """Ensure the date is timezone aware"""
    if not data:
        return
    if isinstance(data, datetime.date) and not isinstance(data, datetime.datetime):
        data = datetime.datetime(*data.timetuple()[:3])  # converto da date a datetime
    if timezone.is_naive(data):  # nella sessione ho salvato una data naive
        data = tz_italy.localize(data)
        return data
    else:
        return data.astimezone(tz_italy)


def date2datetime(day):
    """Convert the date to datetime, keeping its timezone
    @param day: datetime.date
    @return: datetime.datetime
    """
    if hasattr(day, "tzinfo"):
        dtime = datetime.time(tzinfo=day.tzinfo)
    else:
        dtime = datetime.time()
    dt = datetime.datetime.combine(day, dtime)
    return dt


def appendTimeToDate(day, time_string):
    """
    Add to date the time indicated in timestring, in the form hh:mm
    @param day: date
    @param time_string: string
    @return: datetime
    """
    if isinstance(day, datetime.date) and not isinstance(day, datetime.datetime):
        day = date2datetime(day)
    h_string, m_string = time_string.split(":")
    return day + datetime.timedelta(hours=int(h_string), minutes=int(m_string))


timedelta_re = re.compile(r"((?P<days>\d+)d)?((?P<hours>\d+)h)?((?P<minutes>\d+)m)?")


def appendTimeFromRegex(day, timedelta_string):
    # parse the string with a regex that will represent a timedelta (to span easly across days)
    # I put it here http://regex101.com/r/zK7uZ9
    if isinstance(day, datetime.date) and not isinstance(day, datetime.datetime):
        day = date2datetime(day)
    m = re.match(timedelta_re, timedelta_string)
    assert m is not None
    timeparts = {
        key: int(value) for key, value in m.groupdict().items() if value is not None
    }
    delta = datetime.timedelta(**timeparts)
    return day + delta


tz_italy = pytz.timezone("Europe/Rome")
timezone.activate(tz_italy)
