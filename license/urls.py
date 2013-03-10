from django.conf.urls import url, patterns
from django.shortcuts import render

urlpatterns = patterns('licence.views',
	url(r'^license/$', render, {'template_name': 'license.html'}, name="tam_license" ),
#	url(r'^licenza/$', 'notLicensed', name="tamLicense" ),
#	url(r"^activation/$", "activation", name="tamActivation"),
)