from typing import Any, Dict, Optional

import requests


class DelegateObject(object):

    def __init__(self) -> None:
        self.headers: Dict[str, Any] = {}
        self.header: Dict[str, Any] = {}
        self.target: Optional[str] = None
        self.request_payload: Optional[bytes] = None
        self.protocol: Optional[str] = None

    def set_headers(self, headers: Dict[str, Any]) -> None:
        self.headers = headers
        self.header = headers["header"]

    def set_target(self, target: str) -> None:
        self.target = target

    def set_request_payload(self, request_payload: bytes) -> None:
        self.request_payload = request_payload

    def set_protocol(self, protocol: str) -> None:
        self.protocol = protocol

    def get_request(self) -> requests.Request:
        if self.request_payload:
            req = requests.Request(self.headers["method"],
                                   f"{self.protocol}://{self.target}{self.headers['url']}",
                                   headers=self.headers["header"],
                                   data=self.request_payload)
        else:
            req = requests.Request(self.headers["method"],
                                   f"{self.protocol}://{self.target}{self.headers['url']}",
                                   headers=self.headers["header"])
        return req
