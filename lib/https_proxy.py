import logging
import socket
import ssl
import threading

from lib import (
        certs,
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

logger = logging.getLogger("https_proxy")


class Proxy(object):

    def __init__(self, host="127.0.0.1", port=443):
        self.root_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.root_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.root_server.bind((host, port))
        self.root_server.listen(1024)
        self.connections = {}
        self.lock = threading.Lock()
        self.requester = requester.Requester(secure=True)

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
        headers["method"] = req_headers[0]
        headers["url"] = req_headers[1]
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

    def transfer(self, client, target):
        recvobj = recvline.Recvline(client)
        target = target.decode("utf-8")
        host, port = target.split(":")
        while 1:
            try:
                headers = self.receive_header(recvobj)
            except Exception:
                break
            if headers is None:
                break
            if "upgrade" in headers["header"]:
                if headers["header"]["upgrade"] == "websocket":
                    ws = websocket.WebSocket(secure=True)
                    ws.websocket(client, target, headers)
                    break
            try:
                continued = self.requester.delegate(
                        client, recvobj, target, headers)
            except Exception:
                break
            if not continued:
                break
        client.close()

    def worker(self, index, client):
        raw = client.recv(1024)
        header = raw.split(b"\r\n")[0]
        if not header.startswith(b"CONNECT"):
            client.close()
            del self.connections[index]
            return
        target = header.split(b" ")[1]
        host, port = target.split(b":")
        host = host.decode("utf-8")
        try:
            self.lock.acquire()
            certs.create_cert(host)
        except Exception:
            pass
        finally:
            self.lock.release()
        client.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        try:
            client = ssl.wrap_socket(
                    client,
                    keyfile="CA/demoCA/private/cakey.pem",
                    certfile=f"CA/certs/{host}.crt",
                    server_side=True)
        except Exception:
            try:
                self.lock.acquire()
                certs.refresh_cert(host)
                client.close()
                del self.connections[index]
                logger.error(f"Failed to create the connection of SSL "
                             f"to {target.decode('utf-8')}")
            except Exception:
                pass
            finally:
                self.lock.release()
            return
        try:
            self.transfer(client, target)
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
