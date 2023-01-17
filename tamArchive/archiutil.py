# coding=utf-8
import os
from decimal import Decimal

import datetime
import django
import logging

if __name__ == "__main__":
    django.setup()

from django.conf import settings
import json
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder

from tam.models import Conducente, get_classifiche

logger = logging.getLogger("tam.archive.util")
default_filename = os.path.join(settings.PROJECT_PATH, "backup", "snapshot.json")


def snapshot_model(Model, filename=None):
    """Do a backup of initials of every driver
    we'll have a way to compare and restore those from the backup
    """
    if filename is None:
        filename = os.path.join(
            settings.PROJECT_PATH,
            "backup",
            "{modelname}-{date}.json".format(
                modelname=Model.__name__,
                date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
    all_dict = {}
    for c in Model.objects.all():
        all_dict[c.pk] = model_to_dict(c)
    with open(filename, "w") as outfile:
        json.dump(all_dict, outfile, cls=DjangoJSONEncoder)
    print("Saved to %s" % filename)


def compare_soci(filename, commit=False):
    with open(default_filename, "r") as infile:
        conducenti_dict = json.load(infile)
    changes = 0
    for c in Conducente.objects.all():
        snapshot = conducenti_dict.get(str(c.pk))
        if snapshot is None:
            print(c, "not found in the snapshot")
        for field in snapshot.keys():
            if hasattr(c, field):
                current_value = getattr(c, field)
                snap_value = snapshot[field]

                if isinstance(current_value, Decimal):
                    snap_value = Decimal(snap_value)
                if current_value != snap_value:
                    print(
                        "{name} {field}: {old} => {new}".format(
                            name=c.nick + " " + c.nome,
                            field=field,
                            old=snap_value,
                            new=current_value,
                        )
                    )
                    changes += 1
                    if commit:
                        setattr(c, field, snap_value)
                        c.save()
    if not changes:
        print("Nothing changed")
    else:
        print("%d changes" % changes)
    return changes


if __name__ == "__main__":
    snapshot_model(Conducente)
    filename = os.path.join(
        settings.PROJECT_PATH,
        "backup",
        "classifiche-{date}.json".format(
            date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ),
    )
    with open(filename, "w") as outfile:
        json.dump(get_classifiche(), outfile, cls=DjangoJSONEncoder)
        print("Classifiche saved as %s" % filename)
        # compare_soci(
        #     soci_filename
        # )
