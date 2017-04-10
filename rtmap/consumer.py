# coding=utf-8
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


class MapConsumer(JsonWebsocketConsumer):
    http_user = True

    def connect(self, message, **kwargs):
        print("connected {user}".format(
            user=self.message.user,
        ))
        self.message.reply_channel.send({"accept": True})
        # self.close() # DEBUG: to test disconnection right after connection

    def receive(self, content, **kwargs):
        print("received from {user}: {content}".format(
            user=self.message.user,
            content=content
        ))

    def disconnect(self, message, **kwargs):
        print("disconnected {user}".format(
            user=self.message.user,
        ))
