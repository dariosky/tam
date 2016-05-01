# coding=utf-8
from django.conf.urls import url
from django.shortcuts import render
from .models import *
from .views import fixAction
from .views import backup, login
from .views.changelog import changeLog
from .views.classifiche import classificheconducenti
from .views.tamviews import listaCorse, getList, corsa, corsaClear, corsaCopy, cliente, clienti
from .views.tamviews import listino, listinoDelete, \
    clonaListino, exportListino, luoghi, bacino, privati, passeggero, conducente, profilo, util
from .views.users import permissions, newUser, delUser, passwordChangeAndReset, resetSessions

urlpatterns = [
    url(r'^$', listaCorse, name="tamCorse"),

    url(r'^api/get/luogo/$', getList, {"model": Luogo}, name="tamGetLuogo"),
    url(r'^api/get/passeggero/$', getList, {"model": Passeggero.objects}, name="tamGetPasseggero"),
    url(r'^api/get/cliente/$', getList, {"model": Cliente.objects.filter(attivo=True)},
        name="tamGetCliente"),
    url(r'^api/get/cliente/json/$', getList,
        {"model": Cliente.objects.filter(attivo=True), "format": 'json',
         "fields": ("id", "nome", "attivo")},
        name="tamGetClienteJson"),
    url(r'^api/get/conducente/json/$', getList,
        {"model": Conducente.objects, "format": 'json',
         "fields": ("id", "nick")},
        name="tamGetConducenteJson"),

    url(r'^corsa/$', corsa, name="tamNuovaCorsa"),
    url(r'^corsa/dettagli/$', corsa, {"step": 2}, name="tamNuovaCorsa2"),
    url(r'^corsa/clear/$', corsaClear, name="tamCorsaClear"),

    url(r'^corsa/(?P<id>\d*)/$', corsa, name="tamNuovaCorsaId"),
    url(r'^corsa/(?P<id>\d*)/dettagli/$', corsa, {"step": 2}, name="tamNuovaCorsa2Id"),
    url(r'^corsa/(?P<id>\d*)/delete/$', corsa, {"delete": True}, name="tamCorsaIdDel"),
    url(r'^corsa/(?P<id>\d*)/copy/$', corsaCopy, name="tamCorsaCopy"),

    url(r'^cliente/$', cliente, name="tamCliente"),
    url(r'^cliente/(?P<id_cliente>\d*)/$', cliente, name="tamClienteId"),

    url(r'^clienti/$', clienti, name="tamListini"),

    url(r'^listino/$', listino, name="tamNuovoListino"),
    url(r'^listino/(?P<id>\d*)/$', listino, name="tamListinoId"),
    url(r'^listino/(?P<id>\d*)/(?P<prezzoid>\d*)/$', listino, name="tamListinoPrezzoId"),
    url(r'^listino/(?P<id>\d*)/del/$', listinoDelete, name="tamListinoIdDel"),
    url(r'^listino/(?P<id>\d*)/copia/$', clonaListino, name="tamClonaListinoId"),
    url(r'^listino/(?P<id_listino>\d*)/print/$', exportListino, name="tamExportListino"),

    url(r'^luoghi/$', luoghi, name="tamLuoghi"),  # elenco di bacini/luoghi e tratte

    url(r'^bacino/$', bacino, {"Model": Bacino, "redirectOk": "/luoghi/"}, name="tamNuovoBacino"),
    url(r'^bacino/(?P<id>\d*)/$', bacino, {"Model": Bacino, "redirectOk": "/luoghi/"},
        name="tamBacinoId"),
    url(r'^bacino/(?P<id>\d*)/delete/$', bacino,
        {"Model": Bacino, "redirectOk": "/luoghi/", "delete": True,
         "note": "Tutti i luoghi ad esso associati rimarranno orfani."},
        name="tamBacinoIdDel"),

    url(r'^luogo/$', bacino, {"Model": Luogo, "redirectOk": "/luoghi/"}, name="tamNuovoLuogo"),
    url(r'^luogo/(?P<id>\d*)/$', bacino, {"Model": Luogo, "redirectOk": "/luoghi/"},
        name="tamLuogoId"),
    url(r'^luogo/(?P<id>\d*)/delete/$', bacino,
        {"Model": Luogo, "redirectOk": "/luoghi/", "delete": True,
         "note": "Verranno eliminate anche le tratte e le corse da e per questo luogo."},
        name="tamLuogoIdDel"),

    url(r'^tratta/$', bacino,
        {"Model": Tratta, "redirectOk": "/luoghi/", "unique": (("da", "a"),)},
        name="tamNuovaTratta"),
    url(r'^tratta/(?P<id>\d*)/$', bacino,
        {"Model": Tratta, "redirectOk": "/luoghi/", "unique": (("da", "a"),)}, name="tamTrattaId"),
    url(r'^tratta/(?P<id>\d*)/delete/$', bacino,
        {"Model": Tratta, "redirectOk": "/luoghi/", "delete": True, "unique": (("da", "a"),)},
        name="tamTrattaIdDel"),

    url(r'^privati/$', privati, name="tamPrivati"),

    url(r'^privato/$', passeggero, name="tamNuovoPrivato"),
    url(r'^privato/(?P<id>\d*)/$', passeggero, name="tamPrivatoId"),
    url(r'^privato/(?P<id>\d*)/delete/$', passeggero, {"delete": True}, name="tamPrivatoIdDel"),

    url(r'^CC/$', classificheconducenti, name="tamConducenti"),
    url(r'^conguaglio/$', classificheconducenti, {"confirmConguaglio": True},
        name="tamConguaglio"),

    url(r'^conducente/$', conducente, {"Model": Conducente, "redirectOk": "/CC/"},
        name="tamNuovoConducente"),
    url(r'^conducente/(?P<id>\d*)/$', conducente, {"Model": Conducente, "redirectOk": "/CC/"},
        name="tamConducenteId"),
    url(r'^conducente/(?P<id>\d*)/delete/$', conducente,
        {"Model": Conducente, "redirectOk": "/CC/", "delete": True,
         "note": "Verranno eliminate tutte le corse di questo conducente."},
        name="tamConducenteIdDel"),

    url(r'^profilo/$', profilo, {"Model": ProfiloUtente, "unique": []}, name="tamUserserProfile"),

    url(r"^util/$", util, name="tamUtil"),
    url(r"^resetSessions/$", resetSessions, name="tamResetSessions"),
    url(r"^permissions/$", permissions, name="tamManage"),
    url(r"^permissions/(?P<username>.*)/$", permissions, name="tamManage"),
    url(r"^newuser/$", newUser, name="newUser"),
    url(r"^deluser/(?P<username>.*)/$", delUser, name="delUser"),

    url(r'^password/$', passwordChangeAndReset, name='change_password'),

    url(r'^changelog/$', changeLog, {}, name="tam_changelog"),

]

urlpatterns += [
    url(r"^backup/$", backup.backup, name="tamBackup"),
    url(r"^backup/(?P<backupdate>.*)/$", backup.getbackup, name="tamGetBackup"),
    url(r'^fixAction/$', fixAction.fixAction, name='fix_action'),
]

urlpatterns += [
    url(r'^login/$', login.login, name="login"),
    url(r'^logout/$', login.logout, name="logout")
]

urlpatterns += [
    # TODO: Create the rules dynamically based on real rules
    url(r'^rules/$', render, {'template_name': 'static/rules.html'}, name="tam_rules"),
]


# from autocomplete.views import autocomplete
# autocomplete.register(
#    id = 'cliente',
#    queryset = Cliente.objects.all(),
#    fields = ('nome',),
#    limit = 8,
# )
# urlpatterns += patterns('',
#    url('^autocomplete/(\w+)/$', autocomplete, name='autocomplete'),
# )
