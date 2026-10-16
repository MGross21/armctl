"""SocketController-backed robot whose commands are echoed back by an in-process TCP server."""

import socket
import threading
import time

from armctl.templates import Commands
from armctl.templates import SocketController as Socket

TEST_STRING_PREFIX = "MOCK!!"


def _start_echo_server(host):
    server = socket.create_server((host, 0))
    server.settimeout(0.5)
    stop_event = threading.Event()

    def handle_client(conn):
        with conn:
            conn.sendall(b"READY")
            while not stop_event.is_set():
                data = conn.recv(4096)
                if not data:
                    break
                conn.sendall(data)

    def serve():
        with server:
            while not stop_event.is_set():
                try:
                    conn, _ = server.accept()
                except socket.timeout:
                    continue
                threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

    threading.Thread(target=serve, daemon=True).start()
    return stop_event, server.getsockname()[1]


class MockSocketRobot(Socket, Commands):
    def __init__(self, ip: str = "127.0.0.1"):
        self._echo_stop_event, port = _start_echo_server(ip)
        super().__init__(ip, port)

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        self._echo_stop_event.set()

    def _mock_command(self, name: str, arg=None) -> str:
        cmd = f"{TEST_STRING_PREFIX} {name.upper()}" + (f": {arg}" if arg is not None else "")
        return self.send_command(cmd)

    def move_joints(self, pos) -> str:
        return self._mock_command("move_joints", pos)

    def move_cartesian(self, pose) -> str:
        return self._mock_command("move_cartesian", pose)

    def get_joint_positions(self) -> str:
        return self._mock_command("get_joint_positions")

    def get_cartesian_position(self) -> str:
        return self._mock_command("get_cartesian_position")

    def stop_motion(self) -> str:
        return self._mock_command("stop_motion")

    def get_robot_state(self) -> str:
        return self._mock_command("get_robot_state")

    def sleep(self, seconds: float):
        time.sleep(seconds)
