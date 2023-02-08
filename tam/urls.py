# coding=utf-8
from django.urls import re_path
from django.shortcuts import render

from tam.views.users import password_change_prenotazioni
from .models import *
from .views import fixAction
from .views import backup, login
from .views.changelog import changeLog
from .views.classifiche import classificheconducenti
from .views.tamviews import (
    listaCorse,
    getList,
    corsa,
    corsaClear,
    corsaCopy,
    cliente,
    clienti,
)
from .views.tamviews import (
    listino,
    listinoDelete,
    clonaListino,
    exportListino,
    luoghi,
    bacino,
    privati,
    passeggero,
    conducente,
    profilo,
    util,
)
from .views.users import (
    permissions,
    newUser,
    delUser,
    passwordChangeAndReset,
    reset_sessions,
)

urlpatterns = [
    re_path(r"^$", listaCorse, name="tamCorse"),
    re_path(r"^api/get/luogo/$", getList, {"model": Luogo}, name="tamGetLuogo"),
    re_path(
        r"^api/get/passeggero/$",
        getList,
        {"model": Passeggero.objects},
        name="tamGetPasseggero",
    ),
    re_path(
        r"^api/get/cliente/$",
        getList,
        {"model": Cliente.objects.filter(attivo=True)},
        name="tamGetCliente",
    ),
    re_path(
        r"^api/get/cliente/json/$",
        getList,
        {
            "model": Cliente.objects.filter(attivo=True),
            "format": "json",
            "fields": ("id", "nome", "attivo"),
        },
        name="tamGetClienteJson",
    ),
    re_path(
        r"^api/get/conducente/json/$",
        getList,
        {"model": Conducente.objects, "format": "json", "fields": ("id", "nick")},
        name="tamGetConducenteJson",
    ),
    re_path(r"^corsa/$", corsa, name="tamNuovaCorsa"),
    re_path(r"^corsa/dettagli/$", corsa, {"step": 2}, name="tamNuovaCorsa2"),
    re_path(r"^corsa/clear/$", corsaClear, name="tamCorsaClear"),
    re_path(r"^corsa/(?P<id>\d*)/$", corsa, name="tamNuovaCorsaId"),
    re_path(
        r"^corsa/(?P<id>\d*)/dettagli/$", corsa, {"step": 2}, name="tamNuovaCorsa2Id"
    ),
    re_path(
        r"^corsa/(?P<id>\d*)/delete/$", corsa, {"delete": True}, name="tamCorsaIdDel"
    ),
    re_path(r"^corsa/(?P<id>\d*)/copy/$", corsaCopy, name="tamCorsaCopy"),
    re_path(r"^cliente/$", cliente, name="tamCliente"),
    re_path(r"^cliente/(?P<id_cliente>\d*)/$", cliente, name="tamClienteId"),
    re_path(r"^clienti/$", clienti, name="tamListini"),
    re_path(r"^listino/$", listino, name="tamNuovoListino"),
    re_path(r"^listino/(?P<id>\d*)/$", listino, name="tamListinoId"),
    re_path(
        r"^listino/(?P<id>\d*)/(?P<prezzoid>\d*)/$", listino, name="tamListinoPrezzoId"
    ),
    re_path(r"^listino/(?P<id>\d*)/del/$", listinoDelete, name="tamListinoIdDel"),
    re_path(r"^listino/(?P<id>\d*)/copia/$", clonaListino, name="tamClonaListinoId"),
    re_path(
        r"^listino/(?P<id_listino>\d*)/print/$", exportListino, name="tamExportListino"
    ),
    re_path(r"^luoghi/$", luoghi, name="tamLuoghi"),  # elenco di bacini/luoghi e tratte
    re_path(
        r"^bacino/$",
        bacino,
        {"Model": Bacino, "redirectOk": "/luoghi/"},
        name="tamNuovoBacino",
    ),
    re_path(
        r"^bacino/(?P<id>\d*)/$",
        bacino,
        {"Model": Bacino, "redirectOk": "/luoghi/"},
        name="tamBacinoId",
    ),
    re_path(
        r"^bacino/(?P<id>\d*)/delete/$",
        bacino,
        {
            "Model": Bacino,
            "redirectOk": "/luoghi/",
            "delete": True,
            "note": "Tutti i luoghi ad esso associati rimarranno orfani.",
        },
        name="tamBacinoIdDel",
    ),
    re_path(
        r"^luogo/$",
        bacino,
        {"Model": Luogo, "redirectOk": "/luoghi/"},
        name="tamNuovoLuogo",
    ),
    re_path(
        r"^luogo/(?P<id>\d*)/$",
        bacino,
        {"Model": Luogo, "redirectOk": "/luoghi/"},
        name="tamLuogoId",
    ),
    re_path(
        r"^luogo/(?P<id>\d*)/delete/$",
        bacino,
        {
            "Model": Luogo,
            "redirectOk": "/luoghi/",
            "delete": True,
            "note": "Verranno eliminate anche le tratte e le corse da e per questo luogo.",
        },
        name="tamLuogoIdDel",
    ),
    re_path(
        r"^tratta/$",
        bacino,
        {"Model": Tratta, "redirectOk": "/luoghi/", "unique": (("da", "a"),)},
        name="tamNuovaTratta",
    ),
    re_path(
        r"^tratta/(?P<id>\d*)/$",
        bacino,
        {"Model": Tratta, "redirectOk": "/luoghi/", "unique": (("da", "a"),)},
        name="tamTrattaId",
    ),
    re_path(
        r"^tratta/(?P<id>\d*)/delete/$",
        bacino,
        {
            "Model": Tratta,
            "redirectOk": "/luoghi/",
            "delete": True,
            "unique": (("da", "a"),),
        },
        name="tamTrattaIdDel",
    ),
    re_path(r"^privati/$", privati, name="tamPrivati"),
    re_path(r"^privato/$", passeggero, name="tamNuovoPrivato"),
    re_path(r"^privato/(?P<id>\d*)/$", passeggero, name="tamPrivatoId"),
    re_path(
        r"^privato/(?P<id>\d*)/delete/$",
        passeggero,
        {"delete": True},
        name="tamPrivatoIdDel",
    ),
    re_path(r"^CC/$", classificheconducenti, name="tamConducenti"),
    re_path(
        r"^conguaglio/$",
        classificheconducenti,
        {"confirmConguaglio": True},
        name="tamConguaglio",
    ),
    re_path(
        r"^conducente/$",
        conducente,
        {"Model": Conducente, "redirectOk": "/CC/"},
        name="tamNuovoConducente",
    ),
    re_path(
        r"^conducente/(?P<id>\d*)/$",
        conducente,
        {"Model": Conducente, "redirectOk": "/CC/"},
        name="tamConducenteId",
    ),
    re_path(
        r"^conducente/(?P<id>\d*)/delete/$",
        conducente,
        {
            "Model": Conducente,
            "redirectOk": "/CC/",
            "delete": True,
            "note": "Verranno eliminate tutte le corse di questo conducente.",
        },
        name="tamConducenteIdDel",
    ),
    re_path(
        r"^profilo/$",
        profilo,
        {"Model": ProfiloUtente, "unique": []},
        name="tamUserserProfile",
    ),
    re_path(r"^util/$", util, name="tamUtil"),
    re_path(r"^resetSessions/$", reset_sessions, name="tamResetSessions"),
    re_path(r"^permissions/$", permissions, name="tamManage"),
    re_path(r"^permissions/(?P<username>.*)/$", permissions, name="tamManage"),
    re_path(r"^newuser/$", newUser, name="newUser"),
    re_path(r"^deluser/(?P<username>.*)/$", delUser, name="delUser"),
    re_path(r"^password/$", passwordChangeAndReset, name="change_password"),
    re_path(
        r"^user_password/$", password_change_prenotazioni, name="change_user_password"
    ),
    re_path(r"^changelog/$", changeLog, {}, name="tam_changelog"),
]

urlpatterns += [
    re_path(r"^backup/$", backup.backup, name="tamBackup"),
    re_path(r"^backup/(?P<backupdate>.*)/$", backup.getbackup, name="tamGetBackup"),
    re_path(r"^fixAction/$", fixAction.fixAction, name="fix_action"),
]

urlpatterns += [
    re_path(r"^login/$", login.login, name="login"),
    re_path(r"^logout/$", login.logout, name="logout"),
]

urlpatterns += [
    # TODO: Create the rules dynamically based on real rules
    re_path(
        r"^rules/$", render, {"template_name": "static/rules.html"}, name="tam_rules"
    ),
]


# from autocomplete.views import autocomplete
# autocomplete.register(
#    id = 'cliente',
#    queryset = Cliente.objects.all(),
#    fields = ('nome',),
#    limit = 8,
# )
# urlpatterns += patterns('',
#    re_path('^autocomplete/(\w+)/$', autocomplete, name='autocomplete'),
# )
