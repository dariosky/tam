from django.conf.urls.defaults import * #@UnusedWildImport

urlpatterns = patterns('prenotazioni.views.main',
    url(r'^$', 'prenota', name="tamPrenotazioni"),
    url(r'^edit/(?P<id_prenotazione>\d+)/$', 'prenota', name="tamPrenotazioni-edit"),
    
    url(r'^storico/$', 'cronologia', name="tamCronoPrenotazioni"),
)
