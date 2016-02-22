# coding=utf-8
import django
from pprint import pprint
import datetime

django.setup()
from decimal import Decimal
from django.db.models import Case, When, F, DecimalField, Value, Func
from django.db.models.aggregates import Sum
from django.views.generic import TemplateView

from fatturazione.models import Fattura
from tam import tamdates
from tam.models import Viaggio
from tam.tamdates import MONTH_NAMES, parse_datestring, date_enforce


class Extract(Func):
    """
    source: http://stackoverflow.com/questions/32897891/django-getting-month-from-date-for-aggregation
    Performs extraction of `what_to_extract` from `*expressions`.

    Arguments:
        *expressions (string): Only single value is supported, should be field name to
                               extract from.
        what_to_extract (string): Extraction specificator.

    Returns:
        class: Func() expression class, representing 'EXTRACT(`what_to_extract` FROM `*expressions`)'.
    """

    function = 'EXTRACT'
    template = '%(function)s(%(what_to_extract)s FROM %(expressions)s  at TIME ZONE \'CET\')'


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
        key = 'qgrouper'
        if key in self.request.GET:
            context[key] = self.request.GET.get(key, "").split(",")
        else:
            context[key] = self.request.session.get('{}{}'.format(self.session_prefix, key), [])

        key = 'qtype'
        context[key] = self.request.GET.get(key) or self.request.session.get('{}{}'.format(self.session_prefix, key))
        if context[key] is None:
            context[key] = 'corse'

        key = 'qfilter'
        if key in self.request.GET:
            context[key] = self.request.GET.getlist(key)
        else:
            context[key] = self.request.session.get('{}{}'.format(self.session_prefix, key), [])

        # save the property in the session
        for key in ['qtype', 'qgrouper', 'qfilter']:
            session_key = '{}{}'.format(self.session_prefix, key)
            if self.request.session.get(session_key) != context[key]:
                self.request.session[session_key] = context[key]

        # build the data
        keys = ('data_start', 'data_end', 'qtype', 'qfilter', 'qgrouper')
        context['data'] = self.get_data(**{key: context[key] for key in keys})
        return context

    def get_data(self, data_start, data_end, qtype, qfilter, qgrouper, **kwargs):
        data_end = data_end + datetime.timedelta(days=1)
        qs = Viaggio if qtype == 'corse' else Fattura
        qs = qs.objects.all()
        qs = qs.filter(data__gte=data_start, data__lt=data_end)
        if qtype == 'corse':
            qs = qs.exclude(annullato=True)
            if 'finemese' in qfilter:
                qs = qs.filter(incassato_albergo=True)
            if 'fatture' in qfilter:
                qs = qs.filter(fatturazione=True)
            if 'carte' in qfilter:
                qs = qs.filter(cartaDiCredito=True)

        data = dict(tot=qs.count())
        rows = []
        fields = dict(tot=Sum('prezzo'),
                      commissione=Sum(
                          Case(When(tipo_commissione='F', then=F('commissione')),
                               When(tipo_commissione='P', then=F('commissione') * F('prezzo') / Value(100)),
                               ),
                          output_field=DecimalField(max_digits=9, decimal_places=2, default=0),

                      )
                      )
        if 'socio' in qgrouper:
            fields['conducente_nome'] = F('conducente__nome')
        if 'cliente' in qgrouper:
            fields['cliente_nome'] = F('cliente__nome')
        if 'none' in qgrouper:
            qgrouper.remove('none')
        if not qgrouper:
            num_rows = qs.count()
            qs = qs.aggregate(**fields)
            headers = ["Totale", "Prezzo", "Commissione"]
            rows.append(headers)
            rows.append(("{num} {tipo}".format(num=num_rows, tipo=qtype),
                         qs['tot'],
                         qs['commissione'].quantize(Decimal("0.01"))))
        else:
            fields_name = dict(socio='conducente',
                               mese='year,month')  # the field name in the model
            fields_name['taxi/collettivo'] = 'esclusivo'
            grouper_fields = []
            for c in qgrouper:
                # the fields in the group by clause
                grouper_fields += fields_name.get(c, c).split(",")
            qs = (qs
                  .order_by()  # remove existing order, or they'll be used as grouper
                  )
            if 'mese' in qgrouper:
                # we do an intermediate annotation, before grouping
                qs = (qs
                      .annotate(year=Extract('data', what_to_extract='year'),
                                month=Extract('data', what_to_extract='month'))
                      )
            qs = (qs
                  .values(*grouper_fields)  # group by
                  .annotate(**fields)
                  .order_by(*grouper_fields)
                  )  # and annotate
            rows.append(qgrouper + ["Prezzo", "Quota Cons."])

            for r in qs:
                row = []
                for field in qgrouper:
                    value = r.get(field)
                    if field == 'socio':
                        if r.get('conducente'):
                            value = r.get('conducente_nome')
                        else:
                            value = "*non assegnato*"
                    elif field == 'cliente':
                        if value is None:
                            value = "*nessun cliente*"
                        else:
                            value = r.get('cliente_nome')
                    elif field == 'taxi/collettivo':
                        value = r.get("esclusivo") and 'taxi' or 'collettivo'
                    elif field == 'mese':
                        month = MONTH_NAMES[int(r.get('month')) - 1]
                        value = "%s %s" % (month, int(r.get('year')))
                    row.append(value)
                row += map(lambda x: x.quantize(Decimal("0.01")),
                           [r.get('tot'), r.get('commissione')]
                           )
                rows.append(row)
                print row

        data['rows'] = rows
        return data


def testing_annotations():
    # Testing the query
    qs = Viaggio.objects.filter(annullato=False,
                                data__gte=date_enforce(datetime.date(2016, 1, 11)),
                                data__lt=date_enforce(datetime.date(2016, 2, 14)))
    qs = (qs
          .order_by()
          .annotate(year=Extract('data', what_to_extract='year'),
                    month=Extract('data', what_to_extract='month'))
          .values('year', 'month')
          .annotate(tot=Sum('prezzo'),
                    commissione=Sum(
                        Case(When(tipo_commissione='F', then=F('commissione')),
                             When(tipo_commissione='P', then=F('commissione') * F('prezzo') / Value(100)),
                             ),
                        output_field=DecimalField(max_digits=9, decimal_places=2, default=0),

                    ),
                    conducente__nome=F('conducente__nome')
                    ).order_by('conducente__nome')
          )
    print len(qs)
    print qs.query
    pprint(list(qs))


if __name__ == '__main__':
    testing_annotations()
