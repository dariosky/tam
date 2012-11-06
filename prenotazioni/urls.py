from django.conf.urls.defaults import * #@UnusedWildImport

urlpatterns = patterns('prenotazioni.views.main',
    url(r'^$', 'prenota', name="tamPrenotazioni"),
)
