# coding=utf-8
from channels.routing import ProtocolTypeRouter ##route_class, route

from django.conf import settings

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

application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
})
