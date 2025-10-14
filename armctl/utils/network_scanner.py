import platform
import socket
import subprocess
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict, Tuple


class NetworkScanner:
    """Efficient network scanner for discovering devices and services."""
    
    # Standard service ports
    STANDARD_PORTS = {
        22: "SSH", 23: "Telnet", 80: "HTTP", 443: "HTTPS", 
        502: "Modbus", 8080: "HTTP-Alt", 9999: "Generic",
        10000: "Generic", 10001: "Generic", 30002: "Industrial", 30003: "Industrial"
    }

    @staticmethod
    def get_local_ip() -> Optional[str]:
        """Get local machine IP address."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except OSError:
            try:
                return socket.gethostbyname(socket.gethostname())
            except OSError:
                return None

    @staticmethod
    def get_network_prefix() -> Optional[str]:
        """Get network prefix (e.g., '192.168.1')."""
        local_ip = NetworkScanner.get_local_ip()
        return ".".join(local_ip.split(".")[:3]) if local_ip else None

    @staticmethod
    def ping(ip: str, timeout: int = 1) -> bool:
        """Ping an IP address."""
        cmd = (
            ["ping", "-c", "1", "-W", str(timeout), ip]
            if platform.system() != "Windows"
            else ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
        )
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=timeout + 1)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    @staticmethod
    def check_port(ip: str, port: int, timeout: float = 0.5) -> bool:
        """Check if a port is open."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                return s.connect_ex((ip, port)) == 0
        except (socket.error, OSError):
            return False

    @staticmethod
    def scan_network(num_threads: int = 100, timeout: int = 1) -> List[str]:
        """Scan network for active devices."""
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
                if future.result():
                    active_devices.append(ip)

        return sorted(active_devices, key=lambda x: int(x.split('.')[-1]))

    @staticmethod
    def scan_ports(ip: str, ports: Optional[List[int]] = None, timeout: float = 0.3) -> Dict[int, str]:
        """Scan ports on a device."""
        if ports is None:
            ports = list(NetworkScanner.STANDARD_PORTS.keys())
        
        open_ports = {}
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_port = {
                executor.submit(NetworkScanner.check_port, ip, port, timeout): port 
                for port in ports
            }
            
            for future in as_completed(future_to_port):
                port = future_to_port[future]
                if future.result():
                    description = NetworkScanner.STANDARD_PORTS.get(port, "Unknown")
                    open_ports[port] = description

        return open_ports

    @staticmethod
    def scan_for_controllers(target_ports: Optional[List[int]] = None) -> List[Dict[str, any]]:
        """Scan for devices with specific controller ports."""
        if target_ports is None:
            target_ports = [502, 9999, 10000, 10001, 30002, 30003]
        
        active_devices = NetworkScanner.scan_network()
        if not active_devices:
            return []
        
        controllers = []
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            # Submit port scanning tasks for all devices
            future_to_ip = {
                executor.submit(NetworkScanner.scan_ports, ip, target_ports, 0.3): ip 
                for ip in active_devices
            }
            
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                open_ports = future.result()
                
                if open_ports:
                    controllers.append({
                        'ip': ip,
                        'ports': open_ports
                    })
        
        return controllers

    @staticmethod
    def monitor_network(interval: int = 10, callback=None) -> None:
        """Monitor network for changes."""
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


# Efficient network scanner - CLI functionality is in armctl.__main__
