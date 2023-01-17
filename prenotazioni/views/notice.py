# coding=utf-8
import datetime
from datetime import timedelta


def notice_required(run_date, working_hours=(7, 20), night_notice=12, work_notice=2):
    """Return the maximum datetime for make the intended booking at run_date
    Depending if the call arrive in working hour or not, the notice period is different

    @type run_date: datetime
    """
    start, end = working_hours
    work_delta = timedelta(hours=work_notice)
    night_delta = timedelta(hours=night_notice)

    def is_nighty(d):
        return d.hour < start or d.hour >= end

    if not is_nighty(run_date - work_delta):
        return run_date - work_delta

    if is_nighty(run_date):
        return run_date - night_delta

    if is_nighty(run_date - work_delta):
        return run_date - night_delta
    return run_date - work_delta
