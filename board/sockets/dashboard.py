# coding=utf-8
from socketio.namespace import BaseNamespace
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.conf import settings
import Cookie
from django.utils import timezone
import time
from board.models import BoardMessage


def getUserFromSession(sid):
    """Find the session if not expired and return the corresponding user
    or None if none can be found
    """
    try:
        s = Session.objects.get(pk=sid, expire_date__gte=timezone.now())
        # print "Session", s.get_decoded()
        uid = s.get_decoded()["_auth_user_id"]
        # print "UID:", uid
        user = User.objects.get(pk=uid)
        return user
    except (Session.DoesNotExist, User.DoesNotExist) as e:
        return None


def getUserFromEnviron(environ):
    cookies = Cookie.SimpleCookie()
    cookies.load(environ["HTTP_COOKIE"])
    sid = cookies[settings.SESSION_COOKIE_NAME].value
    print(sid)
    user = getUserFromSession(sid)
    return user


class MessageBoardNamespace(BaseNamespace):
    """This is a sort of controller for the messageboard"""

    _registry = {}
    _users = {}

    def initialize(self):
        # print "CONNECTED, sending status"
        user = getUserFromEnviron(self.environ)
        print("Connected:", user)
        if user:
            self._users[id(self)] = user
            self._registry[id(self)] = self
            self.emit(
                "protocol",
                [
                    {"successMessage": "Connesso come %s" % user.username},
                    # {'enableSubmit': 1}
                ],
            )  # tell the client we are connected
        else:
            self.emit(
                "protocol",
                [
                    {"errorMessage": "Credenziali di accesso errate."},
                    # {'disableSubmit': 1}
                ],
            )

    def disconnect(self, *args, **kwargs):
        ids = id(self)
        if ids in self._registry:
            del self._registry[ids]
        if ids in self._users:
            del self._users[ids]
        super(MessageBoardNamespace, self).disconnect(*args, **kwargs)

    def on_deleteMessage(self, message_id, *args, **kwargs):
        print("deletemessage", message_id)
        ids = id(self)
        if not ids in self._users:
            self.emit(
                "protocol",
                [{"errorMessage", "Devi essere autenticato per mandare messaggi."}],
            )
            return
        user = self._users[ids]
        message = BoardMessage.objects.get(id=message_id)
        print("Messaggio:", message)
        print("autore:", message.author)
        print("cancellante:", user)
        messageSelector = "#message-%s" % message_id
        if message.author != user:
            print("cancellazione non permessa")
            self.emit(
                "protocol",
                [
                    {"errorMessage": "Puoi cancellare solo i tuoi messaggi."},
                    {"show": messageSelector},
                ],
            )
            return
        # time.sleep(3)
        print("cancello")
        self._broadcast("protocol", [{"remove": messageSelector}])
        message.delete()
        # self.emit('protocol', [{"remove": messageSelector}])

    def broadcastNewMessage(self, message):
        print("broadcasting '%s' from %s" % (message.message, message.author))
        self._broadcast(
            "message",
            dict(
                author=message.author.username,
                message=message.message,
                id=message.id,
                date=message.date.strftime("%d/%m/%Y"),
                attachment={
                    "name": message.attachment_name(),
                    "url": message.attachment.url,
                }
                if message.attachment
                else None,
            ),
        )

    def on_message(self, message):
        print("MESSAGE: %s" % message)
        ids = id(self)
        if not ids in self._users:
            self.emit("error", "Devi essere autenticato per mandare messaggi.")
            return
        user = self._users[ids]
        newMessage = BoardMessage(
            author=user,
            message=message,
            date=timezone.now(),
            # attach
        )
        newMessage.save()
        self.broadcastNewMessage(newMessage)

    def _broadcast(self, event, message):
        for s in self._registry.values():
            s.emit(event, message)
