# coding=utf-8
import json
import logging

from channels.generic.websockets import JsonWebsocketConsumer
from django.http import HttpResponse
from channels.handler import AsgiHandler

# def http_consumer(message):
#     # Make standard HTTP response - access ASGI path attribute directly
#     response = HttpResponse("Hello world! You asked for %s" % message.content['path'])
#     # Encode that response into message format (ASGI)
#     for chunk in AsgiHandler.encode_response(response):
#         message.reply_channel.send(chunk)


# def ws_message(message):
#     # ASGI WebSocket packet-received and send-packet message types
#     # both have a "text" key for their textual data.
#     print("Received %s" % message.content['text'])
#     message.reply_channel.send({
#         "text": message.content['text'],
#     })
from rtmap.models import Positions

logger = logging.getLogger('tam.rtam')


def get_all_positions():
    # get the last position of all users
    positions = (
        Positions.objects
            .prefetch_related('user')
            .order_by('user', '-last_update')
            .values('user__username', 'lat', 'lon')
            .distinct('user')
    )
    return [
        dict(user=position['user__username'],
             lat=position['lat'],
             lon=position['lon'],
             )
        for position in positions
    ]


class MapConsumer(JsonWebsocketConsumer):
    http_user = True

    def connect(self, message, **kwargs):
        print("connected {user}".format(
            user=self.message.user,
        ))
        self.message.reply_channel.send({"accept": True})
        all_positions = get_all_positions()
        self.message.reply_channel.send(
            {"text": json.dumps(
                {'type': 'realtimePositions',
                 'positions': all_positions,
                 }
            )}
        )
        # self.close() # DEBUG: to test disconnection right after connection

    def receive(self, content, **kwargs):
        print("received from {user}: {content}".format(
            user=self.message.user,
            content=content
        ))
        if 'position' in content:
            user = self.message.user
            logger.debug(f"Saving position for user {user}")
            lat, lon = content['position']
            position = Positions(
                user=user,
                lat=lat, lon=lon,
            )
            position.save()

    def disconnect(self, message, **kwargs):
        print("disconnected {user}".format(
            user=self.message.user,
        ))
