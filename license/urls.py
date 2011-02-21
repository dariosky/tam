from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('licence.views',
	url(r'^license/$', direct_to_template, {'template': 'license.html'}, name="tam_license" ),
#	url(r'^licenza/$', 'notLicensed', name="tamLicense" ),
#	url(r"^activation/$", "activation", name="tamActivation"),
)