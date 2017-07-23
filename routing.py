# coding=utf-8
from channels.routing import route_class, route

from rtmap.consumer import MapConsumer

channel_routing = [
    # route("http.request", "tam.consumer.http_consumer"),
    # route("websocket.receive", ws_message),
    route_class(MapConsumer),

    route('tam.quickbook', 'bots.quickbook.consumer')
]
