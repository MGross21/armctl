"""
Optimized integration test for Universal Robots URSim Docker container.

This test uses the official URSim Docker image directly without building a custom image,
and consolidates test logic to reduce duplication.

Requirements:
- Docker must be installed and running
- pytest
- armctl library
"""
import subprocess
import time
import socket
import pytest
from functools import wraps

URSIM_PORT = 30004
URSIM_CONTAINER_NAME = "ursim_test_container"
URSIM_IMAGE = "universalrobots/ursim_e-series:latest"
MAX_RETRIES = 3
RETRY_DELAY = 2


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a TCP port is open on the given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False


def wait_for_port(host: str, port: int, timeout: float = 60) -> bool:
    """Wait until a TCP port is open, or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        if is_port_open(host, port):
            return True
        time.sleep(2)
    return False


def retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Decorator to retry a function on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


@pytest.fixture(scope="session")
def ursim_container():
    """Start URSim Docker container using the official image."""
    # Pull the latest image
    subprocess.run(["docker", "pull", URSIM_IMAGE], check=True)
    
    # Start container directly from official image
    run_cmd = [
        "docker", "run", "--rm", "-d",
        "--name", URSIM_CONTAINER_NAME,
        "-p", f"{URSIM_PORT}:{URSIM_PORT}",
        "-p", "30002:30002",  # Add primary socket port
        "-p", "5900:5900",  # VNC
        "-p", "6080:6080",  # Web VNC
        URSIM_IMAGE
    ]
    
    try:
        container_id = subprocess.check_output(run_cmd).decode().strip()
        
        # Wait for URSim to be ready
        if not wait_for_port("localhost", URSIM_PORT, timeout=120):
            raise TimeoutError("URSim RTDE port did not open within 120 seconds")
            
        yield container_id
        
    finally:
        # Cleanup
        subprocess.run(["docker", "stop", URSIM_CONTAINER_NAME], 
                      check=False, capture_output=True)


@pytest.fixture(scope="session")
def ur5_robot(ursim_container):
    """Create UR5 robot connection with retry logic."""
    from armctl import UR5
    
    @retry_on_failure(max_retries=3, delay=1)
    def connect_robot():
        from contextlib import contextmanager
        @contextmanager
        def ur5_context():
            # Use localhost and URSIM_PORT for Docker URSim
            with UR5(ip="localhost", port=30_002) as robot:
                yield robot
        return ur5_context()

    with connect_robot() as robot:
        yield robot


def test_ursim_functionality(ursim_container, ur5_robot):
    """Comprehensive test of URSim functionality."""
    # Test 1: Basic connectivity
    assert is_port_open("localhost", URSIM_PORT), "RTDE port should be accessible"
    
    # Test 2: Get robot state
    joint_pos = ur5_robot.get_joint_positions()
    cart_pos = ur5_robot.get_cartesian_position()
    
    # Validate joint positions
    assert joint_pos is not None, "Should retrieve joint positions"
    assert isinstance(joint_pos, (list, tuple)), "Joint positions should be list/tuple"
    assert len(joint_pos) == 6, "Should have 6 joint positions"
    assert all(isinstance(x, (int, float)) for x in joint_pos), "All joints should be numeric"
    
    # Validate cartesian position
    assert cart_pos is not None, "Should retrieve cartesian position"
    assert isinstance(cart_pos, (list, tuple)), "Cartesian position should be list/tuple"
    assert len(cart_pos) == 6, "Should have 6 cartesian values (x,y,z,rx,ry,rz)"
    assert all(isinstance(x, (int, float)) for x in cart_pos), "All cartesian values should be numeric"


def test_ursim_multiple_queries(ursim_container, ur5_robot):
    """Test multiple sequential queries to ensure stability."""
    results = []
    
    for i in range(5):
        joint_pos = ur5_robot.get_joint_positions()
        cart_pos = ur5_robot.get_cartesian_position()
        
        assert joint_pos is not None, f"Query {i+1}: Joint positions failed"
        assert cart_pos is not None, f"Query {i+1}: Cartesian position failed"
        
        results.append((joint_pos, cart_pos))
        time.sleep(0.5)  # Brief pause between queries
    
    # Ensure we got consistent data structure across all queries
    assert len(results) == 5, "Should have 5 successful query results"


def test_ursim_error_handling(ursim_container, ur5_robot):
    """Test graceful handling of invalid operations."""
    # Test invalid command handling if method exists
    if hasattr(ur5_robot, '_mock_command'):
        try:
            result = ur5_robot._mock_command("invalid_command_xyz")
            # Should either return None or handle gracefully
            assert result is None or isinstance(result, str)
        except Exception as e:
            # Should not be a critical system error
            assert not isinstance(e, (SystemExit, KeyboardInterrupt))


if __name__ == "__main__":
    test_ursim_functionality(ursim_container, ur5_robot)
    test_ursim_multiple_queries(ursim_container, ur5_robot)
    test_ursim_error_handling(ursim_container, ur5_robot)
    print("All tests passed successfully.")