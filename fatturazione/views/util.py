from fatturazione.models import Fattura
from django.db.models.aggregates import Max


def ultimoProgressivoFattura(anno, tipo):
    ultimo_progressivo = Fattura.objects.filter(tipo=tipo, anno=anno).aggregate(
        Max("progressivo")
    )["progressivo__max"]
    if ultimo_progressivo is None:
        ultimo_progressivo = 0
    return ultimo_progressivo
