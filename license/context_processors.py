# coding=utf-8
from django.utils.http import urlquote

__author__ = "Dario Varotto"
__date__ = "$30-dic-2010 17.04.59$"

from .license_functions import get_license_detail
from django.conf import settings


def license_details(request):
    """ Add license detail to request context """
    result = get_license_detail()
    result["tam_version"] = settings.TAM_VERSION
    result["tam_stealth"] = False

    # Aggiungo al contesto il percorso completo della richiesta (mi serve per i "?next=")
    if request.META["QUERY_STRING"]:
        result["full_request_path"] = request.path + "?" + urlquote(request.META["QUERY_STRING"])
    else:
        result["full_request_path"] = request.path
    return result
