# coding: utf-8

"""Controlla che le funzionalità richieste dal server siano rispettate"""

import re

import django

django.setup()
from tamArchive.models import ViaggioArchive
from tam.models import Conducente
import csv


def export_conducente(conducente_id):
    c = Conducente.objects.get(pk=conducente_id)
    print(f"Export di {c.nome}")
    corse_archiviate = ViaggioArchive.objects.filter(conducente=c)
    print(f"{corse_archiviate.count()} corse")

    headers = ["data", "da", "a", "cliente", "pezzo", "dettagli prezzo"]
    with open(f"{c.nome}_archive.csv", "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(headers)

        for v in corse_archiviate.all():
            details = re.sub(
                r"[\s\n\t]+", " ", v.prezzo_detail, flags=re.DOTALL | re.MULTILINE
            )
            details = re.sub(r"<(.*?)>(.*?)</\1>", r"\2", details)
            details = re.sub(
                r"[\s\n\t]+", " ", details, flags=re.DOTALL | re.MULTILINE
            ).strip()
            row = [v.data, v.da, v.a, v.cliente, v.prezzo, details]
            csvwriter.writerow(row)
            # print(row)


if __name__ == "__main__":
    export_conducente("09")
