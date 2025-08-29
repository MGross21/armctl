import platform
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor


class NetworkScanner:
    """A network listener that scans for active devices and detects new ones appearing on the network."""

    @staticmethod
    def get_local_ip():
        """Returns the local machine's IP address."""
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return None

    @staticmethod
    def get_network_prefix():
        """Extracts the network prefix from the local IP (e.g., '192.168.1')."""
        local_ip = NetworkScanner.get_local_ip()
        return ".".join(local_ip.split(".")[:3]) if local_ip else None

    @staticmethod
    def ping(ip):
        """Pings an IP and returns True if it's online."""
        cmd = (
            ["ping", "-c", "1", "-W", "1", ip]
            if platform.system() != "Windows"
            else ["ping", "-n", "1", "-w", "500", ip]
        )
        return (
            ip
            if subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            ).returncode
            == 0
            else None
        )

    @staticmethod
    def scan_network(num_threads=20):
        """Scans the local network for active devices using multithreading."""
        network_prefix = NetworkScanner.get_network_prefix()
        if not network_prefix:
            return []

        ip_range = [f"{network_prefix}.{i}" for i in range(1, 255)]
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            return [
                ip for ip in executor.map(NetworkScanner.ping, ip_range) if ip
            ]

    @staticmethod
    def scan_ports(ip, ports=None, timeout=1):
        """Scans specified ports on a device to check if they are open."""
        open_ports = []
        ports = ports or [
            22,
            80,
            443,
            8080,
            3389,
        ]  # Default common ports (SSH, HTTP, HTTPS, RDP)

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(
                lambda port: NetworkScanner._check_port(ip, port, timeout),
                ports,
            )

        return [port for port in results if port]

    @staticmethod
    def _check_port(ip, port, timeout):
        """Checks if a specific port is open on a device."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            if s.connect_ex((ip, port)) == 0:
                return port  # Open port
        return None

    @staticmethod
    def listen_for_changes(interval=10, scan_ports=False):
        """Continuously monitors the network for new devices and optionally scans ports."""
        print("Listening for new devices... Press Ctrl+C to stop.")

        try:
            known_devices = set(NetworkScanner.scan_network())

            while True:
                time.sleep(interval)
                current_devices = set(NetworkScanner.scan_network())

                new_devices = current_devices - known_devices
                if new_devices:
                    print("\n🔔 New Device(s) Detected!")
                    for device in new_devices:
                        print(f" - {device}")

                        if scan_ports:
                            ports = NetworkScanner.scan_ports(device)
                            print(
                                f"   🔍 Open Ports: {ports if ports else 'None'}"
                            )

                known_devices = current_devices
        except KeyboardInterrupt:
            print("\nExiting...", end=" ")
        finally:
            print("Done!")


# Run directly
if __name__ == "__main__":
    NetworkScanner.listen_for_changes(scan_ports=True)  # Enable port scanning
