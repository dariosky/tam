# coding=utf-8
import logging
from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from markViews import prenotazioni
from tam.middleware.prevent_multisession import get_concurrent_sessions
from tam.models import Cliente, Luogo, ProfiloUtente


def reset_sessions(request, template_name="utils/resetSessions.html"):
    user = request.user
    if not user.is_superuser:
        messages.error(request, "Devi essere il superuser per cancellare le sessioni.")
        return HttpResponseRedirect("/")
    if request.method == "POST":
        if "reset" in request.POST:
            logging.debug("reset delle sessioni")
            Session.objects.all().delete()
            return HttpResponseRedirect("/")

    return render(request, template_name, locals())


def reset_user_session(selectedUser):
    from django.contrib.sessions.models import Session

    logging.debug("Cancello le sessioni dell'utente %s" % selectedUser.id)
    for ses in Session.objects.all():
        if ses.get_decoded().get('_auth_user_id') == selectedUser.id:
            ses.delete()


def get_userkeys(user):
    """ Return the keys to order users """
    return hasattr(user, "prenotazioni"), user.username.lower()


def permissions(request, username=None, template_name="utils/manageUsers.html"):
    user = request.user
    quick_book = getattr(settings, 'PRENOTAZIONI_QUICK', False)
    if not user.has_perm('auth.change_user'):
        messages.error(request,
                       "Non hai l'autorizzazione a modificare i permessi.")
        return HttpResponseRedirect("/")

    manage_prenotazioni = request.user.has_perm(
        'prenotazioni.manage_permissions') and "prenotazioni" in settings.PLUGGABLE_APPS
    users = User.objects.exclude(is_superuser=True) \
        .exclude(id=user.id) \
        .exclude(is_active=False)
    users = sorted(users, key=get_userkeys)

    getUsername = request.GET.get("selectedUser", None)
    if getUsername:
        return HttpResponseRedirect(
            reverse("tamManage", kwargs={"username": getUsername}))
    if username:
        selectedUser = User.objects.get(username=username)
        if user == selectedUser:
            messages.error(request, "Non puoi modificare te stesso.")
            return HttpResponseRedirect(reverse("tamManage"))
        if hasattr(selectedUser, "prenotazioni"):
            utentePrenotazioni = selectedUser.prenotazioni
        else:
            utentePrenotazioni = None
        selectedGroups = selectedUser.groups.all()
        groups = Group.objects.all()
        for group in groups:
            if group in selectedGroups: group.selected = True

        password = request.POST.get("password", None)
        passwordbis = request.POST.get("passwordbis", None)
        errors = defaultdict(list)
        if "change" in request.POST:  # effetto la modifica all'utente
            if password:
                if password != passwordbis:
                    errors['password'].append(_("Le due password non coincidono"))
                else:
                    try:
                        validate_password(password, user=selectedUser)
                    except ValidationError as e:
                        for message in e.messages:
                            errors['password'].append(message)
                    else:
                        selectedUser.set_password(password)
                        selectedUser.save()
                        messages.success(request,
                                         "Modificata la password all'utente %s." % selectedUser.username)
                        reset_user_session(selectedUser)

            tipo_utente = request.POST.get('tipo_prenotazioni', 'c')
            if tipo_utente == 'c':  # utente conducente
                logging.debug("resetting groups for a normal user")
                newGroups = request.POST.getlist("selectedGroup")
                selectedUser.groups.clear()
                for groupName in newGroups:
                    group = Group.objects.get(name=groupName)
                    selectedUser.groups.add(group)

            if manage_prenotazioni:  # se posso gestire gli utenti prenotazioni, altrimenti ignoro le richieste eventuali
                if tipo_utente == 'c':  # utente conducente
                    if utentePrenotazioni:
                        messages.warning(request,
                                         ("Faccio diventare l\'utente '%s' un conducente. "
                                          "Attenzione se aveva accesso esterno.") % selectedUser)
                        # elimino l'utente prenotazioni
                        utentePrenotazioni.delete()
                else:
                    # utente prenotazioni
                    from prenotazioni.models import UtentePrenotazioni

                    logging.debug("clearing groups for user prenotazioni")
                    selectedUser.groups.clear()
                    if not utentePrenotazioni:
                        messages.info(request,
                                      "Faccio diventare il conducente"
                                      " '%s' un utente per le prenotazioni." % selectedUser)
                        utentePrenotazioni = UtentePrenotazioni()
                    else:
                        # era già un utente prenotazioni
                        logging.debug("clearing clients for user prenotazioni")
                        utentePrenotazioni.clienti.clear()
                    utentePrenotazioni.user = selectedUser
                    # attuale_prenotazione.cliente_id = request.POST.getlist('prenotazioni_clienti')
                    utentePrenotazioni.luogo_id = request.POST.get('prenotazioni_luogo')
                    utentePrenotazioni.nome_operatore = request.POST.get('operatore')
                    utentePrenotazioni.email = request.POST.get('email')
                    utentePrenotazioni.quick_book = request.POST.get('quickbook') and True or False
                    utentePrenotazioni.save()
                    logging.debug("Setting clients to user prenotazioni")
                    for cliente_id in request.POST.getlist('prenotazioni_clienti'):
                        cliente = Cliente.objects.get(id=cliente_id)
                        utentePrenotazioni.clienti.add(cliente)
                        logging.debug("adding %s" % cliente)
            if not errors:
                return HttpResponseRedirect(reverse("tamManage", kwargs={"username": username}))
        # fine delle azioni per il submit

        if manage_prenotazioni:
            # preparo il dizionario dei clienti e dei luoghi per poterli scegliere
            clienti = Cliente.objects.filter(attivo=True)
            luoghi = Luogo.objects.all()

        if user.has_perm('tam.reset_sessions'):
            sessions = get_concurrent_sessions(request, selectedUser)

            if "resetSessions" in request.POST:
                for session in sessions:
                    session.delete()
                messages.success(request,
                                 "L'utente {username} è stato disconnesso da ogni device".format(
                                     username=username
                                 ))

    return render(request, template_name, locals())


def newUser(request, template_name="utils/newUser.html"):
    user = request.user
    profilo, created = ProfiloUtente.objects.get_or_create(user=user)
    if not user.has_perm('auth.add_user'):
        messages.error(request,
                       "Non hai l'autorizzazione a creare nuovi utenti.")
        return HttpResponseRedirect(reverse("tamUtil"))

    from django.contrib.auth.forms import UserCreationForm

    form = UserCreationForm(request.POST or None)

    if form.is_valid():
        newUser = form.save()
        nuovoProfilo, created = ProfiloUtente.objects.get_or_create(
            user=newUser)
        # @type profilo tam.models.ProfiloUtente
        nuovoProfilo.luogo = profilo.luogo  # prendo il luogo predefinito del creatore
        nuovoProfilo.save()
        messages.success(request,
                         "Creato il nuovo utente in sola lettura %s." % newUser.username)
        return HttpResponseRedirect(
            reverse("tamManage", kwargs={"username": newUser.username}))

    return render(request, template_name, locals())


def delUser(request, username, template_name="utils/delUser.html"):
    user = request.user
    if not user.has_perm('auth.delete_user'):
        messages.error(request,
                       "Non hai l'autorizzazione per cancellare gli utenti.")
        return HttpResponseRedirect(reverse("tamUtil"))
    userToDelete = User.objects.get(username=username)
    if user == userToDelete:
        messages.error(request, "Non puoi cancellare te stesso.")
        return HttpResponseRedirect(reverse("tamManage"))
    if "sure" in request.POST:
        userToDelete.delete()
        messages.success(request,
                         "Eliminato l'utente %s." % userToDelete.username)
        return HttpResponseRedirect(reverse("tamManage"))
    return render(request, template_name, locals())


def passwordChangeAndReset(request, template_name="utils/changePassword.html"):
    form = PasswordChangeForm(request.user, request.POST or None)
    if form.is_valid():
        logging.debug("Changing password for %s" % request.user)
        form.save()
        reset_user_session(request.user)  # reset delle sessioni
        return HttpResponseRedirect('/')
    return render(request, template_name, {'form': form})


@prenotazioni
def password_change_prenotazioni(request, template_name="prenotazioni/changePassword.html"):
    form = PasswordChangeForm(request.user, request.POST or None)
    if form.is_valid():
        logging.debug("Changing password for %s" % request.user)
        form.save()
        return HttpResponseRedirect('/')
    return render(request, template_name, {'form': form,
                                           "logo_consorzio": settings.TRANSPARENT_SMALL_LOGO, })
