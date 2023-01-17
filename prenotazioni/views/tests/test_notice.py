# coding=utf-8
import datetime
from datetime import timedelta

from prenotazioni.views.notice import notice_required

rundate = datetime.datetime(2016, 8, 14, 8, 0)

notice = lambda d: notice_required(
    d, working_hours=(7, 20), night_notice=12, work_notice=2
)
work_delta = timedelta(hours=2)
night_delta = timedelta(hours=12)


def test_end_of_shift():
    d = rundate.replace(hour=20)
    maxtime = notice(d)
    assert maxtime == d - work_delta


def test_start_of_shift():
    d = rundate.replace(hour=7)
    maxtime = notice(d)
    assert maxtime == d - night_delta


def test_nighttime():
    d = rundate.replace(hour=22)
    maxtime = notice(d)
    assert maxtime == d - night_delta


def test_worktime():
    d = rundate.replace(hour=12)
    maxtime = notice(d)
    assert maxtime == d - work_delta
