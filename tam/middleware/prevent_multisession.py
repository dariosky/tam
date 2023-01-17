# coding=utf-8
# Logs user out from all other sessions on login, django 1.8
# source: http://stackoverflow.com/questions/8927327/allowing-only-single-active-session-per-user-in-django-app
import logging

from django.contrib.sessions.models import Session
from django.contrib.auth.signals import user_logged_in
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger("tam.appconfig")


def get_concurrent_sessions(request, user):
    results = []
    for session in Session.objects.filter(
        ~Q(session_key=request.session.session_key), expire_date__gte=timezone.now()
    ):
        data = session.get_decoded()
        session.decoded = data
        if data.get("_auth_user_id", None) == str(user.id):
            results.append(session)
    return results


def on_login_expire_older_sessions(sender, user, request, **kwargs):
    # this will be slow for sites with LOTS of active users
    for session in get_concurrent_sessions(request, user):
        # found duplicate session, expire it
        logger.info(f"{request.user.username} is logging in more than one device")
        session.expire_date = timezone.now()
        session.save()
    return


def register_session_limit():
    user_logged_in.connect(on_login_expire_older_sessions)
