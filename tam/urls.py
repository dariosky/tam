from django.conf.urls.defaults import * #@UnusedWildImport
from django.views.generic.simple import direct_to_template
from tam.models import * #@UnusedWildImport
#import django.contrib.auth.views

urlpatterns = patterns('tam.views',
    url(r'^$', 'listaCorse', name="tamCorse"), 

	url(r'^api/get/luogo/$', 'getList', {"model":Luogo}, name="tamGetLuogo"), 
	url(r'^api/get/passeggero/$', 'getList', {"model":Passeggero.objects}, name="tamGetPasseggero"), 
	url(r'^api/get/cliente/$', 'getList', {"model":Cliente.objects.filter(attivo=True)}, name="tamGetCliente"),
	url(r'^api/get/cliente/json/$', 'getList',
							{"model":Cliente.objects.filter(attivo=True), "format":'json',
							"fields":("id", "nome", "attivo")},
							name="tamGetClienteJson"),
	url(r'^api/get/conducente/json/$', 'getList',
							{"model":Conducente.objects, "format":'json',
							"fields":("id", "nick")},
							name="tamGetConducenteJson"),
    
    url(r'^corsa/$', 'corsa', name="tamNuovaCorsa"), 
    url(r'^corsa/dettagli/$', 'corsa', {"step":2}, name="tamNuovaCorsa2"), 
    url(r'^corsa/clear/$', 'corsaClear', name="tamCorsaClear"), 
    
    url(r'^corsa/(?P<id>\d*)/$', 'corsa', name="tamNuovaCorsaId"),
    url(r'^corsa/(?P<id>\d*)/dettagli/$', 'corsa', {"step":2}, name="tamNuovaCorsa2Id"),
    url(r'^corsa/(?P<id>\d*)/delete/$', 'corsa', {"delete":True}, name="tamCorsaIdDel"),
    url(r'^corsa/(?P<id>\d*)/copy/$', 'corsaCopy', name="tamCorsaCopy"),
    
    url(r'^cliente/$', 'cliente', name="tamCliente"),
    url(r'^cliente/(?P<id_cliente>\d*)/$', 'cliente', name="tamClienteId"),
    
    url(r'^clienti/$', 'clienti', name="tamListini"),
    
    url(r'^listino/$', 'listino', name="tamNuovoListino"), 
    url(r'^listino/(?P<id>\d*)/$', 'listino', name="tamListinoId"), 
    url(r'^listino/(?P<id>\d*)/(?P<prezzoid>\d*)/$', 'listino', name="tamListinoPrezzoId"),
    url(r'^listino/(?P<id>\d*)/del/$', 'listinoDelete', name="tamListinoIdDel"),
    url(r'^listino/(?P<id>\d*)/copia/$', 'clonaListino', name="tamClonaListinoId"), 
    
    url(r'^luoghi/$', 'luoghi', name="tamLuoghi"), 	# elenco di bacini/luoghi e tratte

    url(r'^bacino/$', 'bacino', {"Model": Bacino, "redirectOk":"/luoghi/" }, name="tamNuovoBacino"), 
    url(r'^bacino/(?P<id>\d*)/$', 'bacino', {"Model": Bacino, "redirectOk":"/luoghi/" }, name="tamBacinoId"), 
    url(r'^bacino/(?P<id>\d*)/delete/$', 'bacino', \
	   {"Model": Bacino, "redirectOk":"/luoghi/", "delete":True, "note":"Tutti i luoghi ad esso associati rimarranno orfani." }, \
	   name="tamBacinoIdDel"),
    
    url(r'^luogo/$', 'bacino', {"Model": Luogo, "redirectOk":"/luoghi/" }, name="tamNuovoLuogo"), 
    url(r'^luogo/(?P<id>\d*)/$', 'bacino', {"Model": Luogo, "redirectOk":"/luoghi/" }, name="tamLuogoId"), 
    url(r'^luogo/(?P<id>\d*)/delete/$', 'bacino', \
	   {"Model": Luogo, "redirectOk":"/luoghi/", "delete":True, "note":"Verranno eliminate anche le tratte e le corse da e per questo luogo." }, \
	   name="tamLuogoIdDel"),

    url(r'^tratta/$', 'bacino', {"Model": Tratta, "redirectOk":"/luoghi/", "unique":(("da","a"),) }, name="tamNuovaTratta"),
    url(r'^tratta/(?P<id>\d*)/$', 'bacino', {"Model": Tratta, "redirectOk":"/luoghi/", "unique":(("da","a"),) }, name="tamTrattaId"), 
    url(r'^tratta/(?P<id>\d*)/delete/$', 'bacino', {"Model": Tratta, "redirectOk":"/luoghi/", "delete":True, "unique":(("da","a"),) }, name="tamTrattaIdDel"),

    url(r'^privati/$', 'privati', name="tamPrivati"),
    
    url(r'^privato/$', 'bacino', {"Model": Passeggero, "redirectOk":"/privati/" }, name="tamNuovoPrivato"),
    url(r'^privato/(?P<id>\d*)/$', 'bacino', {"Model": Passeggero, "redirectOk":"/privati/" }, name="tamPrivatoId"),
    url(r'^privato/(?P<id>\d*)/delete/$', 'bacino', {"Model": Passeggero, "redirectOk":"/privati/", "delete":True, "note":"Verranno eliminate tutte le corse con questo privato." }, name="tamPrivatoIdDel"),
    
    url(r'^CC/$', 'conducenti', name="tamConducenti"),

    url(r'^conducente/$', 'conducente', {"Model": Conducente, "redirectOk":"/CC/" }, name="tamNuovoConducente"),
    url(r'^conducente/(?P<id>\d*)/$', 'conducente', {"Model": Conducente, "redirectOk":"/CC/" }, name="tamConducenteId"),
    url(r'^conducente/(?P<id>\d*)/delete/$', 'conducente', {"Model": Conducente, "redirectOk":"/CC/", "delete":True, "note":"Verranno eliminate tutte le corse di questo conducente." }, name="tamConducenteIdDel"),
    
    url(r'^profilo/$', 'profilo', {"Model": ProfiloUtente, "unique":[] }, name="tamUserProfile" ),

    url(r'^conguaglio/$', 'conducenti', {"confirmConguaglio":True}, name="tamConguaglio" ),
    
	url(r"^util/$", "util", name="tamUtil"),
	url(r"^backup/$", "backup", name="tamBackup"),
    url(r"^backup/(?P<backupdate>.*)/$", "getbackup", name="tamGetBackup"),
    url(r"^resetSessions/$", "resetSessions", name="tamResetSessions"),
    url(r"^permissions/$", "permissions", name="tamManage"),
	url(r"^permissions/(?P<username>.*)/$", "permissions", name="tamManage"),
    url(r"^newuser/$", "newUser", name="newUser"),
	url(r"^deluser/(?P<username>.*)/$", "delUser", name="delUser"),
	url(r"^log/$", "actionLog", name="actionLog"),

	url(r'^password/$', 'passwordChangeAndReset', name='change_password'),

	url(r'^fixAction/$', 'fixAction', name='fix_action'),

)

urlpatterns += patterns('tam.views',
#	url(r'^login/$', 'django.contrib.auth.views.login', {"template_name":"login.html"}, name="login"),
#    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', {"login_url":"/"}, name="logout")
	url(r'^login/$', 'login', name="login"),
	url(r'^logout/$', 'logout', name="logout")
)

urlpatterns += patterns('',
	url(r'^changelog/$', direct_to_template, {'template': 'static/changelog.html'}, name="tam_changelog" ),
	url(r'^rules/$', direct_to_template, {'template': 'static/rules.html'}, name="tam_rules" ),
)


#from autocomplete.views import autocomplete
#autocomplete.register(
#    id = 'cliente',
#    queryset = Cliente.objects.all(),
#    fields = ('nome',),
#    limit = 8,
#)
#urlpatterns += patterns('',
#    url('^autocomplete/(\w+)/$', autocomplete, name='autocomplete'),
#)

