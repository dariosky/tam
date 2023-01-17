from socketio.server import SocketIOServer
from socketio import socketio_manage
from board.sockets import dashboard


def manager(environ, start_response):
    print("pathinfo:", environ["PATH_INFO"])
    # if environ['PATH_INFO'].startswith('/bacheca/socket'):
    return socketio_manage(environ, {"/board": dashboard.MessageBoardNamespace})


listen_port = 8080
print("Listen on port %d" % listen_port)
sio_server = SocketIOServer(("", listen_port), manager, policy_server=False)

sio_server.serve_forever()
