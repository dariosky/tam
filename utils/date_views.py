# coding=utf-8
import datetime
from collections import namedtuple

from django.views import View
from django.views.generic.base import ContextMixin

from tam import tamdates
from tam.tamdates import MONTH_NAMES

ThreeMonths = namedtuple(
    "ThreeMonths",
    (
        "currentName",
        "prevName",
        "prevprevName",  # the names of nearby months
        "current",  # the current month as YYYY-mm
        "date_start",
        "date_end",  # selected date range
    ),
)


class ThreeMonthsView(ContextMixin, View):
    """Enrich the context with threemonths object
    uses request.GET['month'] to choose the selected month
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = tamdates.ita_today()
        delta_month = 0
        d = today.replace(day=1)

        if "month" in self.request.GET:
            delta_requested = self.request.GET.get("month", None)
            if delta_requested == "cur":
                delta_month = 0
            elif delta_requested == "prev":
                delta_month = -1
            elif delta_requested == "prevprev":
                delta_month = -2
            else:
                d = datetime.datetime.strptime(delta_requested, "%Y-%m")

        # get the start-end dates
        for _ in range(0, delta_month, -1):
            d = (d - datetime.timedelta(days=1)).replace(day=1)
        date_start = d
        # the first day of next month (end not inclusive)
        date_end = (date_start + datetime.timedelta(days=32)).replace(day=1)

        threemonths = ThreeMonths(
            currentName=MONTH_NAMES[(today.month - 1) % 12],
            prevName=MONTH_NAMES[(today.month - 2) % 12],
            prevprevName=MONTH_NAMES[(today.month - 3) % 12],
            current=date_start.strftime("%Y-%m"),
            date_start=date_start,
            date_end=date_end,
        )
        context.update(
            {
                "months": threemonths,
                "mediabundleJS": ("tamUI",),
                "mediabundleCSS": ("tamUI",),
            }
        )

        return context
