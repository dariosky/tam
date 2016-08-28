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
    cond = Conducente(nome="Dario", nick="DkR", attivo=True)
    cond.save()

    lrif = Luogo(nome='Home')
    lrif.save()

    Viaggio(annullato=True,
            data=date_enforce(datetime.date(2016, 1, 11)),
            da=lrif, a=lrif, luogoDiRiferimento=lrif,
            prezzo=1000,
            conducente=cond,
            ).save()

    Viaggio(data=date_enforce(datetime.date(2016, 1, 11)),
            da=lrif, a=lrif, luogoDiRiferimento=lrif,
            prezzo=10,
            conducente=cond,
            ).save()

    Viaggio(data=date_enforce(datetime.date(2016, 1, 12)),
            da=lrif, a=lrif, luogoDiRiferimento=lrif,
            prezzo=10,
            conducente=cond,
            ).save()

    Viaggio(data=date_enforce(datetime.date(2016, 2, 12)),
            da=lrif, a=lrif, luogoDiRiferimento=lrif,
            prezzo=10,
            conducente=cond,
            ).save()

    # Testing the query
    qs = Viaggio.objects.filter(annullato=False,
                                data__gte=date_enforce(datetime.date(2016, 1, 11)),
                                data__lt=date_enforce(datetime.date(2016, 2, 14)))
    qs = (qs
          .order_by()
          .annotate(year=Extract('data', what_to_extract='year'),
                    month=Extract('data', what_to_extract='month'))
          # .values('year', 'month')
          .annotate(tot=Sum('prezzo'),
                    # commissione=Sum(
                    #     Case(When(tipo_commissione='F', then=F('commissione')),
                    #          When(tipo_commissione='P',
                    #               then=F('commissione') * F('prezzo') / Value(100)),
                    #          ),
                    #     output_field=DecimalField(max_digits=9, decimal_places=2, default=0),
                    #
                    # ),
                    conducente__nome=F('conducente__nome')
                    ).order_by('conducente__nome')
          )
    print(qs.query)
    print(len(qs))
    pprint(list(qs))



if __name__ == '__main__':
    testing_annotations()
