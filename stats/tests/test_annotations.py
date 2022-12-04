import datetime
from pprint import pprint

import pytest
from django.db.models import Case, DecimalField
from django.db.models import F
from django.db.models import Sum
from django.db.models import Value
from django.db.models import When

from stats.views import Extract
from tam.models import Viaggio, Conducente, Luogo
from tam.tamdates import date_enforce


@pytest.mark.django_db
def testing_annotations():
    cond1 = Conducente(nome="Luke Skywalker", nick="Luke", attivo=True)
    cond1.save()
    cond2 = Conducente(nome="Anakin Skywalker", nick=None, attivo=True)
    cond2.save()

    lrif = Luogo(nome='Home')
    lrif.save()

    Viaggio(annullato=True,
            data=date_enforce(datetime.date(2016, 1, 11)),
            da=lrif, a=lrif, luogoDiRiferimento=lrif,
            prezzo=1000,
            conducente=cond1, conducente_confermato=True,
            ).save()

    Viaggio(data=date_enforce(datetime.date(2016, 1, 11)),
            da=lrif, a=lrif, luogoDiRiferimento=lrif,
            prezzo=10,
            conducente=cond1, conducente_confermato=True,
            ).save()

    Viaggio(data=date_enforce(datetime.date(2016, 1, 12)),
            da=lrif, a=lrif, luogoDiRiferimento=lrif,
            prezzo=10,
            conducente=cond1, conducente_confermato=True,
            ).save()

    Viaggio(data=date_enforce(datetime.date(2016, 1, 12)),
            da=lrif, a=lrif, luogoDiRiferimento=lrif,
            prezzo=30,
            conducente=cond2, conducente_confermato=True,
            ).save()

    Viaggio(data=date_enforce(datetime.date(2016, 2, 12)),
            da=lrif, a=lrif, luogoDiRiferimento=lrif,
            prezzo=10,
            conducente=cond1, conducente_confermato=True,
            ).save()

    # Testing the query
    qs = Viaggio.objects.filter(annullato=False,
                                data__gte=date_enforce(datetime.date(2016, 1, 11)),
                                data__lt=date_enforce(datetime.date(2016, 2, 14)))
    qs = (qs
          .order_by()
          .annotate(year=Extract('data', lookup_name='year'),
                    month=Extract('data', lookup_name='month'))
          .order_by('conducente')
          .values('year', 'month')
          .annotate(tot=Sum('prezzo'),
                    commissione=Sum(
                        Case(When(tipo_commissione='F', then=F('commissione')),
                             When(tipo_commissione='P',
                                  then=F('commissione') * F('prezzo') / Value(100)),
                             ),
                        output_field=DecimalField(max_digits=9, decimal_places=2, default=0),

                    ),
                    conducente__nome=F('conducente__nome')
                    ).order_by('conducente__nome')
          )
    # print(qs.query)
    qs = list(qs)
    pprint(list(qs))
    assert len(qs) == 3, "We should have 3 rows: Luke with 2 months, Ana with 1"

    luke_runs = list(filter(lambda x: x['conducente__nome'] == 'Luke Skywalker', qs))
    assert len(luke_runs) == 2
    assert luke_runs[0]['month'] == 1 and luke_runs[0]['tot'] == 20
    assert luke_runs[1]['month'] == 2 and luke_runs[1]['tot'] == 10

    anakin_runs = list(filter(lambda x: x['conducente__nome'] == 'Anakin Skywalker', qs))
    assert len(anakin_runs) == 1
    assert anakin_runs[0]['month'] == 1 and anakin_runs[0]['tot'] == 30
