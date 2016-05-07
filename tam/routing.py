# coding=utf-8
from channels.routing import route

from tam.consumer import ws_message

channel_routing = [
    # route("http.request", "tam.consumer.http_consumer"),
    route("websocket.receive", ws_message),
]
