"""Network scanner for discovering devices on local networks."""

from __future__ import annotations

import platform
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable


class NetworkScanner:
    """Network device discovery and monitoring."""

    @staticmethod
    def get_local_ip() -> str | None:
        """Get local machine IP address."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except OSError:
            try:
                return socket.gethostbyname(socket.gethostname())
            except OSError:
                return None

    @staticmethod
    def get_network_prefix() -> str | None:
        """Get network prefix (e.g., '192.168.1')."""
        local_ip = NetworkScanner.get_local_ip()
        return ".".join(local_ip.split(".")[:3]) if local_ip else None

    @staticmethod
    def ping(ip: str, timeout: int = 1) -> bool:
        """Check if host is reachable."""
        is_windows = platform.system() == "Windows"
        cmd = (
            ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
            if is_windows
            else ["ping", "-c", "1", "-W", str(timeout), ip]
        )
        try:
            result = subprocess.run(
                cmd, capture_output=True, timeout=timeout + 1, check=False
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    @staticmethod
    def scan_network(num_threads: int = 100, timeout: int = 1) -> list[str]:
        """Scan local network for active devices."""
        network_prefix = NetworkScanner.get_network_prefix()
        if not network_prefix:
            return []
        ip_range = [f"{network_prefix}.{i}" for i in range(1, 255)]
        active_devices = []
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_to_ip = {
                executor.submit(NetworkScanner.ping, ip, timeout): ip
                for ip in ip_range
            }
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    if future.result():
                        active_devices.append(ip)
                except Exception:
                    continue
        return sorted(active_devices, key=lambda x: int(x.split(".")[-1]))

    @staticmethod
    def monitor_network(
        interval: int = 10,
        callback: Callable[[set[str], set[str]], None] | None = None,
    ) -> None:
        """Monitor network for device changes."""
        known_devices = set(NetworkScanner.scan_network())
        try:
            while True:
                time.sleep(interval)
                current_devices = set(NetworkScanner.scan_network())
                new_devices = current_devices - known_devices
                removed_devices = known_devices - current_devices
                if callback and (new_devices or removed_devices):
                    callback(new_devices, removed_devices)
                known_devices = current_devices
        except KeyboardInterrupt:
            pass
