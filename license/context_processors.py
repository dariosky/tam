__author__="Dario Varotto"
__date__ ="$30-dic-2010 17.04.59$"

from license_functions import get_license_detail
from django.conf import settings

def license_details(request):
	""" Add license detail to request context """
	result=get_license_detail()
	result["tam_version"] = settings.TAM_VERSION
	return result
