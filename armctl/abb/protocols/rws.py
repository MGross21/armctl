from __future__ import annotations

from requests import Response, Session
from requests.auth import HTTPBasicAuth
from contextlib import contextmanager

# Documentation: https://developercenter.robotstudio.com/api/RWS

class RWS:
    def __init__(self, ip: str, username: str = "Default User", password: str = "robotics"):
        self.ip = ip
        self.base_url = f"http://{ip}"
        self.session = Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.headers.update({
            "Content-Type": "application/x-www-form-urlencoded;v=2.0",
            "Accept": "application/hal+json;v=2.0",
            "Sec-Websocket-Protocol": "rws_subscription",
        })
        self.session.verify = False
        self.timeout = 5

    def _get(self, endpoint: str) -> Response:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response

    def _post(self, endpoint: str, data: dict) -> Response:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        response = self.session.post(url, json=data, timeout=self.timeout)
        response.raise_for_status()
        return response
    
    @contextmanager
    def mastership(self):
        pass

    def set_joint_positions(self, pos: list[float]) -> None:
        pass

    def get_joint_positions(self) -> list[float]:
        pass


    def set_cartesian_position(self, pose: list[float]) -> None:
        pass

    def get_cartesian_position(self) -> list[float]:
        pass

    def stop_motion(self) -> None:
        pass

    def get_robot_state(self) -> dict | str:
        pass