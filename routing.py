# coding=utf-8
from channels.routing import ProtocolTypeRouter  # route_class, route
from django.conf import settings
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

channel_routing = []
# if 'rtmap' in settings.PLUGGABLE_APPS:
#     from rtmap.consumer import MapConsumer
#
#     channel_routing.append(
#         route_class(MapConsumer)
#     )
#
# channel_routing.append(
#     route('tam.quickbook', 'bots.quickbook.consumer')
# )

application = ProtocolTypeRouter({"http": get_asgi_application()})
