from typing import Any, Dict, Optional

from lib.content_object import ContentObject
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
        pass

    def get_response(self, response: requests.Response) -> ContentObject:
        pass
