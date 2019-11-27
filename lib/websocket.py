import socket
import ssl
import threading


class WebSocket(object):

    def __init__(self, secure=False):
        self.secure = secure

    def websocket_client(self, client, server):
        while 1:
            try:
                raw = client.recv(1024)
                if raw:
                    server.send(raw)
                else:
                    break
            except Exception:
                break
        client.close()
        server.close()

    def websocket_server(self, client, server):
        while 1:
            try:
                raw = server.recv(1024)
                if raw:
                    client.send(raw)
                else:
                    break
            except Exception:
                break
        client.close()
        server.close()

    def websocket(self, client, target, headers):
        host, port = target.split(":")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.secure:
            sock = ssl.wrap_socket(sock)
        sock.connect((host, int(port)))
        send_header = f"{headers['method']} {headers['url']} HTTP/1.1\r\n"
        send_header += "\r\n".join([f"{key}: {value}"
                                    for key, value
                                    in headers["header"].items()])
        send_header += "\r\n\r\n"
        sock.send(send_header.encode("utf-8"))
        th_srv = threading.Thread(
                target=self.websocket_server, args=(client, sock))
        th_clt = threading.Thread(
                target=self.websocket_client, args=(client, sock))
        th_srv.setDaemon(True)
        th_clt.setDaemon(True)
        th_srv.start()
        th_clt.start()
        th_srv.join()
        th_clt.join()
