from django.conf.urls import url, patterns

urlpatterns = patterns('modellog.views',
	url(r"^log/$", "actionLog", name="actionLog"),
)
