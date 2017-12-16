# coding=utf-8
import json
import logging

from channels import Group
from channels.generic.websockets import JsonWebsocketConsumer

from rtmap.models import Positions

logger = logging.getLogger('tam.rtam')


def get_positions_msg(position=None):
    # get the last position of all users
    if position is None:
        logger.debug("Getting all positions")
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
    else:
        return [
            dict(user=position.user.username,
                 lat=position.lat,
                 lon=position.lon,
                 )
        ]


class MapConsumer(JsonWebsocketConsumer):
    http_user = True

    @staticmethod
    def positions_message(position=None):
        positions_msg = get_positions_msg(position)
        return {"text": json.dumps(
            {'type': 'realtimePositions',
             'positions': positions_msg,
             }
        )}

    def connect(self, message, **kwargs):
        logger.debug("Connected {user}".format(
            user=self.message.user,
        ))

        self.message.reply_channel.send({"accept": True})  # ack the connection

        self.message.reply_channel.send(
            self.positions_message()
        )

        Group("rtmap").add(message.reply_channel)
        # self.close() # DEBUG: to test disconnection right after connection

    def receive(self, content, **kwargs):
        logger.debug("Message from {user}: {content}".format(
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
            logger.debug("Broadcasting position")
            Group("rtmap").send(
                self.positions_message(position)
            )

    def disconnect(self, message, **kwargs):
        logger.debug("disconnected {user}".format(
            user=self.message.user,
        ))
        Group("rtmap").discard(message.reply_channel)
