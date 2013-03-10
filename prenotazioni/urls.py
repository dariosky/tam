from django.conf.urls import url, patterns

urlpatterns = patterns('prenotazioni.views.main',
    url(r'^$', 'prenota', name="tamPrenotazioni"),
    url(r'^edit/(?P<id_prenotazione>\d+)/$', 'prenota', name="tamPrenotazioni-edit"),
    
    url(r'^storico/$', 'cronologia', name="tamCronoPrenotazioni"),
)
