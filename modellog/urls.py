from django.conf.urls.defaults import * #@UnusedWildImport

urlpatterns = patterns('modellog.views',
	url(r"^log/$", "actionLog", name="actionLog"),
)
