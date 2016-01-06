# coding=utf-8
import datetime
from django.views.generic import TemplateView

from fatturazione.models import Fattura
from tam import tamdates
from tam.models import Viaggio
from tam.tamdates import MONTH_NAMES, parse_datestring


class MonthDatesMixin(TemplateView):
    template_name = "stats/stat_corse.html"
    session_prefix = ""

    def get_context_data(self, **kwargs):
        context = super(MonthDatesMixin, self).get_context_data(**kwargs)
        get_mese_fatture = self.request.GET.get('mese', None)
        oggi = tamdates.ita_today()
        quick_month_names = [MONTH_NAMES[(oggi.month - 3) % 12],
                             MONTH_NAMES[(oggi.month - 2) % 12],
                             MONTH_NAMES[(oggi.month - 1) % 12]]  # current month
        quick_month_names.reverse()

        if get_mese_fatture:
            if get_mese_fatture == "cur":
                data_start = oggi.replace(day=1)
                data_end = (data_start + datetime.timedelta(days=32)).replace(
                    day=1) - datetime.timedelta(days=1)
            elif get_mese_fatture == 'prev':
                data_end = oggi.replace(day=1) - datetime.timedelta(
                    days=1)  # vado a fine mese scorso
                data_start = data_end.replace(day=1)  # vado a inizio del mese precedente
            elif get_mese_fatture == 'prevprev':  # due mesi fa
                data_end = (oggi.replace(day=1) - datetime.timedelta(days=1)).replace(
                    day=1) - datetime.timedelta(
                    days=1)  # vado a inizio mese scorso
                data_start = data_end.replace(day=1)  # vado a inizio di due mesi fa
            else:
                raise Exception("Unexpected get mese fatture %s" % get_mese_fatture)
        else:
            data_start = parse_datestring(  # dal primo del mese scorso
                (self.request.GET.get("data_start") or
                 self.request.session.get('{}data_start'.format(self.session_prefix))),
                default=(
                    tamdates.ita_today().replace(
                        day=1) - datetime.timedelta(days=1)).replace(day=1)
            )
            data_end = parse_datestring(  # a oggi
                (self.request.GET.get("data_end") or
                 self.request.session.get('{}data_end'.format(self.session_prefix))),
                default=tamdates.ita_today()
            )
        context.update(locals())
        context.update({
            "dontHilightFirst": True,
            "mediabundleJS": ('tamUI',),
            "mediabundleCSS": ('tamUI',),
        })
        return context


class StatsView(MonthDatesMixin):
    session_prefix = "stats"

    def get_context_data(self, **kwargs):
        context = super(StatsView, self).get_context_data(**kwargs)
        key = 'grouper'
        if key in self.request.GET:
            context[key] = self.request.GET.get(key).split(",")
        else:
            context[key] = self.request.session.get('{}{}'.format(self.session_prefix, key))

        key = 'type'
        context[key] = self.request.GET.get(key) or self.request.session.get('{}{}'.format(self.session_prefix, key))

        context['filter'] = (self.request.GET.getlist('filter') or
                             self.request.session.get(
                                 '{}{}'.format(self.session_prefix, 'filter')))
        if context['type'] is None:
            context['type'] = 'corse'

        # save the property in the session
        for key in ['type', 'grouper', 'filter']:
            session_key = '{}{}'.format(self.session_prefix, key)
            if self.request.session.get(session_key) != context[key]:
                self.request.session[session_key] = context[key]

        # build the data
        keys = ('data_start', 'data_end', 'type', 'filter', 'grouper')
        context['data'] = self.get_data(**{key: context[key] for key in keys})
        return context

    def get_data(self, data_start, data_end, type, filter, grouper, **kwargs):
        data_end = data_end + datetime.timedelta(days=1)
        qs = Viaggio if type == 'corse' else Fattura
        qs = qs.objects.all()
        qs = qs.filter(data__gte=data_start, data__lt=data_end)
        return qs
