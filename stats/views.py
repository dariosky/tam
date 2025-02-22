# coding=utf-8
import datetime
from decimal import Decimal

from django.contrib.auth.decorators import permission_required
from django.db.models import Case, When, F, DecimalField, Value
from django.db.models.aggregates import Sum
from django.db.models.functions import Extract
from django.utils.decorators import method_decorator
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
        get_mese_fatture = self.request.GET.get("mese", None)
        oggi = tamdates.ita_today()
        quick_month_names = [
            MONTH_NAMES[(oggi.month - 3) % 12],
            MONTH_NAMES[(oggi.month - 2) % 12],
            MONTH_NAMES[(oggi.month - 1) % 12],
        ]  # current month
        quick_month_names.reverse()

        if get_mese_fatture:
            if get_mese_fatture == "cur":
                data_start = oggi.replace(day=1)
                data_end = (data_start + datetime.timedelta(days=32)).replace(
                    day=1
                ) - datetime.timedelta(days=1)
            elif get_mese_fatture == "prev":
                data_end = oggi.replace(day=1) - datetime.timedelta(
                    days=1
                )  # vado a fine mese scorso
                data_start = data_end.replace(
                    day=1
                )  # vado a inizio del mese precedente
            elif get_mese_fatture == "prevprev":  # due mesi fa
                data_end = (oggi.replace(day=1) - datetime.timedelta(days=1)).replace(
                    day=1
                ) - datetime.timedelta(days=1)  # vado a inizio mese scorso
                data_start = data_end.replace(day=1)  # vado a inizio di due mesi fa
            else:
                raise Exception("Unexpected get mese fatture %s" % get_mese_fatture)
        else:
            data_start = parse_datestring(  # dal primo del mese scorso
                (
                    self.request.GET.get("data_start")
                    or self.request.session.get(
                        "{}data_start".format(self.session_prefix)
                    )
                ),
                default=(
                    tamdates.ita_today().replace(day=1) - datetime.timedelta(days=1)
                ).replace(day=1),
            )
            data_end = parse_datestring(  # a oggi
                (
                    self.request.GET.get("data_end")
                    or self.request.session.get(
                        "{}data_end".format(self.session_prefix)
                    )
                ),
                default=tamdates.ita_today(),
            )
        context.update(locals())
        context.update(
            {
                "dontHilightFirst": True,
                "mediabundleJS": ("tamUI",),
                "mediabundleCSS": ("tamUI",),
            }
        )
        return context


class StatsView(MonthDatesMixin):
    @method_decorator(permission_required("stats.can_see_stats"))
    def dispatch(self, request, *args, **kwargs):
        return super(StatsView, self).dispatch(request, *args, **kwargs)

    session_prefix = "stats"

    def get_context_data(self, **kwargs):
        context = super(StatsView, self).get_context_data(**kwargs)
        key = "qgrouper"
        if key in self.request.GET:
            context[key] = self.request.GET.get(key, "").split(",")
        else:
            context[key] = self.request.session.get(
                "{}{}".format(self.session_prefix, key), []
            )

        key = "qtype"
        context[key] = self.request.GET.get(key) or self.request.session.get(
            "{}{}".format(self.session_prefix, key)
        )
        if context[key] is None:
            context[key] = "corse"

        key = "qfilter"
        if key in self.request.GET:
            context[key] = self.request.GET.getlist(key)
        else:
            context[key] = self.request.session.get(
                "{}{}".format(self.session_prefix, key), []
            )

        key = "detailed"
        if key in self.request.GET:
            context[key] = self.request.GET.get(key, "none") != "none"
        else:
            context[key] = self.request.session.get(
                "{}{}".format(self.session_prefix, key), False
            )

        # save the property in the session
        for key in ["qtype", "qgrouper", "qfilter", "detailed"]:
            session_key = "{}{}".format(self.session_prefix, key)
            if self.request.session.get(session_key) != context[key]:
                self.request.session[session_key] = context[key]

        # build the data
        keys = ("data_start", "data_end", "qtype", "qfilter", "qgrouper", "detailed")
        context["data"] = self.get_data(**{key: context[key] for key in keys})
        return context

    def get_data(self, data_start, data_end, qtype, qfilter, qgrouper, detailed):
        def add_details(rows, qs):
            qs = qs.select_related("da", "a", "cliente", "conducente")
            for detail in qs:
                detail_string = "{date} - {da}-{a} - {cliente} - {socio}".format(
                    date=detail.data.astimezone(tamdates.tz_italy).strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                    da=detail.da,
                    a=detail.a,
                    cliente=detail.cliente if detail.cliente else "Privato",
                    socio=detail.conducente or "Non assegnato",
                )
                rows.append(
                    dict(
                        type="detail",
                        data=[
                            detail_string,
                            detail.prezzo,
                            detail.prezzo_commissione(),
                        ],
                    )
                )

        data_end = data_end + datetime.timedelta(days=1)
        qs = Viaggio if qtype == "corse" else Fattura
        qs = qs.objects.all()
        qs = qs.filter(data__gte=data_start, data__lt=data_end)
        if qtype == "corse":
            qs = qs.exclude(annullato=True)
            if "finemese" in qfilter:
                qs = qs.filter(incassato_albergo=True)
            if "fatture" in qfilter:
                qs = qs.filter(fatturazione=True)
            if "carte" in qfilter:
                qs = qs.filter(cartaDiCredito=True)
            if "fattura-pagata" in qfilter:
                qs = qs.filter(riga_fattura__fattura__pagata=True)

        data = dict(tot=qs.count())
        rows = []
        fields = dict(
            tot=Sum("prezzo"),
            commissione=Sum(
                Case(
                    When(tipo_commissione="F", then=F("commissione")),
                    When(
                        tipo_commissione="P",
                        then=F("commissione") * F("prezzo") / Value(100),
                    ),
                ),
                output_field=DecimalField(max_digits=9, decimal_places=2, default=0),
            ),
        )
        if "socio" in qgrouper:
            fields["conducente_nome"] = F("conducente__nome")
        if "cliente" in qgrouper:
            fields["cliente_nome"] = F("cliente__nome")
        if "none" in qgrouper:
            qgrouper.remove("none")
        if not qgrouper:
            num_rows = qs.count()

            headers = ["Totale", "Prezzo", "Commissione"]
            rows.append(dict(type="headers", data=headers))
            if detailed:
                add_details(rows, qs)
            qs = qs.aggregate(**fields)
            if qs:
                tot, commissione = qs["tot"], qs["commissione"]
                rows.append(
                    dict(
                        type="row",
                        data=(
                            "{num} {tipo}".format(num=num_rows, tipo=qtype),
                            tot or 0,
                            commissione.quantize(Decimal("0.01")) if commissione else 0,
                        ),
                    )
                )
        else:
            fields_name = dict(
                socio="conducente", mese="year,month"
            )  # the field name in the model
            fields_name["taxi/collettivo"] = "esclusivo"
            grouper_fields = []
            for c in qgrouper:
                # the fields in the group by clause
                grouper_fields += fields_name.get(c, c).split(",")
            rows.append(dict(type="header", data=qgrouper + ["Prezzo", "Quota Cons."]))
            all_details = qs
            qs = qs.order_by()  # remove existing order, or they'll be used as grouper
            if "mese" in qgrouper:
                # we do an intermediate annotation, before grouping
                qs = qs.annotate(
                    year=Extract("data", lookup_name="year"),
                    month=Extract("data", lookup_name="month"),
                )
            qs = (
                qs.values(*grouper_fields)  # group by
                .annotate(**fields)
                .order_by(*grouper_fields)
            )  # and annotate

            for r in qs:
                row = []
                details = all_details.all()
                for field in qgrouper:
                    value = r.get(field)
                    if field == "socio":
                        details = details.filter(conducente=r.get("conducente"))
                        if r.get("conducente"):
                            value = r.get("conducente_nome")
                        else:
                            value = "*non assegnato*"
                    elif field == "cliente":
                        details = details.filter(cliente=r.get("cliente"))
                        if value is None:
                            value = "*nessun cliente*"
                        else:
                            value = r.get("cliente_nome")
                    elif field == "taxi/collettivo":
                        details = details.filter(esclusivo=r.get("esclusivo"))
                        value = r.get("esclusivo") and "taxi" or "collettivo"
                    elif field == "mese":
                        details = details.filter(data__month=r.get("month"))
                        month = MONTH_NAMES[int(r.get("month")) - 1]
                        value = "%s %s" % (month, int(r.get("year")))
                    row.append(value)
                row += map(
                    lambda x: x.quantize(Decimal("0.01")),
                    [r.get("tot"), r.get("commissione")],
                )
                if detailed:
                    add_details(rows, details)
                rows.append(dict(type="row", data=row))

        data["rows"] = rows
        return data
