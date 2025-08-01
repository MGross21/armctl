"""
This module provides a `MockSocketRobot` class that inherits from the real
SocketController and Commands classes, enabling realistic socket-based communication
during tests. To avoid the need for an external server, a lightweight TCP echo server
is started in a background thread on initialization and stopped on exit. This allows
all socket commands to be sent and received as if communicating with a real robot,
with the server simply echoing back any data received. The echo server is started
and stopped automatically for each test instance, ensuring isolation and reliability.
"""

import socket
import threading
import time

from armctl.templates import Commands
from armctl.templates import SocketController as Socket

TEST_STRING_PREFIX = "MOCK!!"


def _start_echo_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    stop_event = threading.Event()

    def handle_client(conn, addr):
        with conn:
            while not stop_event.is_set():
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                    conn.sendall(data)
                except Exception:
                    break

    def server_thread():
        while not stop_event.is_set():
            try:
                server.settimeout(0.5)
                conn, addr = server.accept()
                threading.Thread(
                    target=handle_client, args=(conn, addr), daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception:
                break
        server.close()

    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()
    return stop_event, server


def _get_free_port():
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class MockSocketRobot(Socket, Commands):
    """
    Mock robot using real SocketController logic with an integrated echo server.
    Starts a background echo server on a random free port for the lifetime of the object.
    All commands are sent over a real socket and echoed back for test verification.
    """

    def __init__(self, ip: str = "127.0.0.1", port: int = None):
        if port is None:
            port = _get_free_port()
        self._echo_port = port
        self._echo_stop_event, self._echo_server = _start_echo_server(ip, port)
        time.sleep(0.1)  # Give server time to start
        super().__init__(ip, port)

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        self._echo_stop_event.set()
        time.sleep(0.1)  # Allow server thread to exit

    def _mock_command(self, name: str, arg=None) -> str:
        cmd = f"{TEST_STRING_PREFIX} {name.upper()}" + (
            f": {arg}" if arg is not None else ""
        )
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
