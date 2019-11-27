import logging
import socket
import threading

from lib import (
        recvline,
        requester,
        websocket)


METHODS = ["GET",
           "HEAD",
           "POST",
           "PUT",
           "DELETE",
           "CONNECT",
           "OPTIONS",
           "TRACE",
           "PATCH"]

logger = logging.getLogger("http_proxy")


class Proxy(object):

    def __init__(self, host="127.0.0.1", port=80):
        self.root_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.root_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.root_server.bind((host, port))
        self.root_server.listen(1024)
        self.connections = {}
        self.lock = threading.Lock()
        self.requester = requester.Requester(secure=False)

    def receive_header(self, recvobj):
        header = {}
        raw = recvobj.recvline().decode("utf-8")
        if not raw:
            raise Exception("Does not has received data.")
        req_method = raw.split(" ")[0]
        headers = {}
        if req_method not in METHODS:
            raise Exception("Corrupted request")
        req_headers = raw.split(" ")
        full_url = req_headers[1].split("//")[1]
        url = "/" + "/".join(full_url.split("/")[1:])
        target = full_url.split("/")[0]
        if ":" not in target:
            target = f"{target}:80"
        headers["method"] = req_headers[0]
        headers["url"] = url
        headers["target"] = target
        headers["protocol"] = req_headers[2].rstrip()
        while 1:
            raw = recvobj.recvline().decode("utf-8")
            if raw == "\r\n":
                break
            head = raw.split(":")
            key = head[0]
            value = ":".join(head[1:]).strip()
            header[key.lower()] = value
        headers["header"] = header
        return headers

    def transfer(self, client):
        recvobj = recvline.Recvline(client)
        while 1:
            try:
                headers = self.receive_header(recvobj)
            except Exception:
                break
            if headers is None:
                break
            target = headers["target"]
            if "upgrade" in headers["header"]:
                if headers["header"]["upgrade"] == "websocket":
                    ws = websocket.WebSocket(secure=True)
                    ws.websocket(client, target, headers)
                    break
            try:
                continued = self.requester.delegate(
                        client, recvobj, target, headers)
            except Exception as e:
                raise e
                break
            if not continued:
                break
        client.close()

    def worker(self, index, client):
        try:
            self.transfer(client)
        except Exception as e:
            raise e
        finally:
            del self.connections[index]

    def run(self):
        index = 0
        while 1:
            client, addr = self.root_server.accept()
            th = threading.Thread(target=self.worker, args=(index, client))
            th.setDaemon(True)
            th.start()
            self.connections[index] = th
            index += 1
