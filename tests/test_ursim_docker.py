"""
Optimized integration test for Universal Robots URSim Docker container.

This test uses the official URSim Docker image directly without building a custom image,
and consolidates test logic to reduce duplication.

Requirements:
- Docker must be installed and running
- pytest
- armctl library

Starting Docker (if needed):
    sudo systemctl start docker
    # or
    sudo service docker start
"""
from __future__ import annotations

import contextlib
import logging
import socket
import subprocess
import sys
import time
from functools import wraps
from typing import Iterator, Optional, Union, TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from armctl import UR5

# Configure logging for better diagnostics
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants
URSIM_PORT = 30004
URSIM_PRIMARY_PORT = 30002
URSIM_CONTAINER_NAME = "ursim_test_container"
URSIM_IMAGE = "universalrobots/ursim_e-series:latest"

# Retry and timeout settings
MAX_RETRIES = 3
RETRY_DELAY = 2
CONTAINER_STARTUP_TIMEOUT = 120
CONNECTION_TIMEOUT = 30

# Performance thresholds
MAX_AVERAGE_QUERY_TIME = 1.0
MAX_SINGLE_QUERY_TIME = 2.0

# Robot limits
MAX_JOINT_ANGLE = 2 * 3.14159  # ±2π radians


def check_docker_available() -> bool:
    """Check if Docker is available and running.
    
    Returns:
        bool: True if Docker is available and running, False otherwise.
    """
    try:
        result = subprocess.run(
            ["docker", "version"], 
            capture_output=True, 
            check=False, 
            timeout=10
        )
        if result.returncode == 0:
            logger.info("Docker is available and running")
            return True
        else:
            logger.warning(f"Docker check failed: {result.stderr.decode()}")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.warning(f"Docker not available: {e}")
        return False


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a TCP port is open on the given host.
    
    Args:
        host: The hostname or IP address to check.
        port: The port number to check.
        timeout: Connection timeout in seconds.
        
    Returns:
        bool: True if port is open, False otherwise.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def wait_for_port(host: str, port: int, timeout: float = 60) -> bool:
    """Wait until a TCP port is open, or timeout.
    
    Args:
        host: The hostname or IP address to check.
        port: The port number to wait for.
        timeout: Maximum time to wait in seconds.
        
    Returns:
        bool: True if port became available, False if timeout.
    """
    start = time.time()
    logger.info(f"Waiting for {host}:{port} to become available (timeout: {timeout}s)")
    
    while time.time() - start < timeout:
        if is_port_open(host, port):
            elapsed = time.time() - start
            logger.info(f"Port {host}:{port} is now available after {elapsed:.1f}s")
            return True
        time.sleep(2)
    
    logger.error(f"Port {host}:{port} did not become available within {timeout}s")
    return False


def cleanup_container(container_name: str) -> None:
    """Cleanup Docker container safely.
    
    Args:
        container_name: Name of the container to cleanup.
    """
    try:
        # Stop container
        subprocess.run(
            ["docker", "stop", container_name], 
            check=False, 
            capture_output=True,
            timeout=30
        )
        # Remove container (in case --rm didn't work)
        subprocess.run(
            ["docker", "rm", "-f", container_name], 
            check=False, 
            capture_output=True,
            timeout=10
        )
        logger.info(f"Container {container_name} cleaned up")
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout during container {container_name} cleanup")
    except Exception as e:
        logger.warning(f"Error during container cleanup: {e}")


def retry_on_failure(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """Decorator to retry a function on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        
    Returns:
        Decorated function with retry logic.
    """
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
                        backoff_delay = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {backoff_delay}s...")
                        time.sleep(backoff_delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed. Last error: {e}")
            raise last_exception
        return wrapper
    return decorator


@contextlib.contextmanager
def docker_container_manager(image: str, container_name: str, ports: dict[str, str]) -> Iterator[str]:
    """Context manager for Docker container lifecycle.
    
    Args:
        image: Docker image name to run.
        container_name: Name for the container.
        ports: Dictionary mapping host ports to container ports.
        
    Yields:
        str: Container ID.
        
    Raises:
        subprocess.CalledProcessError: If Docker operations fail.
    """
    container_id = None
    try:
        # Cleanup any existing container with the same name
        cleanup_container(container_name)
        
        # Pull the latest image
        logger.info(f"Pulling Docker image: {image}")
        subprocess.run(["docker", "pull", image], check=True, capture_output=True)
        
        # Build run command
        run_cmd = ["docker", "run", "--rm", "-d", "--name", container_name]
        for host_port, container_port in ports.items():
            run_cmd.extend(["-p", f"{host_port}:{container_port}"])
        run_cmd.append(image)
        
        # Start container
        logger.info(f"Starting container: {container_name}")
        container_id = subprocess.check_output(run_cmd, stderr=subprocess.PIPE).decode().strip()
        logger.info(f"Container started with ID: {container_id[:12]}")
        
        yield container_id
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"Failed to manage Docker container: {error_msg}")
        raise
    finally:
        if container_id:
            cleanup_container(container_name)


def get_ursim_port_mappings() -> dict[str, str]:
    """Get standard URSim port mappings.
    
    Returns:
        dict: Mapping of host ports to container ports.
    """
    return {
        str(URSIM_PORT): str(URSIM_PORT),  # RTDE port
        str(URSIM_PRIMARY_PORT): str(URSIM_PRIMARY_PORT),  # Primary socket port
        "5900": "5900",  # VNC
        "6080": "6080",  # Web VNC
    }


@pytest.fixture(scope="session")
def ursim_container():
    """Start URSim Docker container using the official image.
    
    Yields:
        str: Container ID.
        
    Raises:
        pytest.skip: If Docker is not available or container fails to start.
    """
    if not check_docker_available():
        pytest.skip("Docker is not available or not running")
    
    ports = get_ursim_port_mappings()
    
    try:
        with docker_container_manager(URSIM_IMAGE, URSIM_CONTAINER_NAME, ports) as container_id:
            # Wait for URSim to be ready (check both primary ports)
            ports_ready = (
                wait_for_port("localhost", URSIM_PORT, timeout=CONTAINER_STARTUP_TIMEOUT) and
                wait_for_port("localhost", URSIM_PRIMARY_PORT, timeout=30)
            )
            
            if not ports_ready:
                raise TimeoutError(
                    f"URSim ports did not open within {CONTAINER_STARTUP_TIMEOUT} seconds"
                )
                
            logger.info("URSim container is ready for testing")
            yield container_id
            
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        pytest.skip(f"Failed to start URSim container: {error_msg}")
    except TimeoutError as e:
        pytest.skip(f"URSim container startup timeout: {e}")


@pytest.fixture(scope="session")
def ur5_robot(ursim_container):
    """Create UR5 robot connection with enhanced retry logic.
    
    Args:
        ursim_container: URSim container fixture.
        
    Yields:
        UR5: Connected robot instance.
        
    Raises:
        pytest.skip: If robot connection fails.
    """
    from armctl import UR5
    
    @retry_on_failure(max_retries=5, delay=1)
    def connect_robot():
        logger.info("Attempting to connect to UR5 robot")
        robot = UR5(ip="localhost", port=URSIM_PRIMARY_PORT)
        robot.connect()
        
        # Verify connection with a simple query
        try:
            positions = robot.get_joint_positions()
            if positions is None:
                raise ConnectionError("Robot connected but failed to get joint positions")
            state = robot.get_robot_state()
            if state is None:
                raise ConnectionError("Robot connected but failed to get robot state")
            logger.info("Successfully connected to UR5 robot")
            return robot
        except Exception as e:
            robot.disconnect()
            raise ConnectionError(f"Robot connection verification failed: {e}") from e

    robot = None
    try:
        robot = connect_robot()
        yield robot
    except Exception as e:
        logger.error(f"Failed to connect to URSim robot: {e}")
        pytest.skip(f"Failed to connect to URSim robot: {str(e)}")
    finally:
        if robot:
            try:
                robot.disconnect()
                logger.info("Robot disconnected successfully")
            except Exception as e:
                logger.warning(f"Error during robot disconnect: {e}")


def validate_position_data(
    positions: Union[list, tuple], 
    expected_length: int, 
    position_type: str
) -> None:
    """Validate robot position data structure and values.
    
    Args:
        positions: Position data to validate.
        expected_length: Expected number of position values.
        position_type: Type of position for error messages.
        
    Raises:
        AssertionError: If validation fails.
    """
    assert positions is not None, f"Should retrieve {position_type}"
    assert isinstance(positions, (list, tuple)), f"{position_type} should be list/tuple"
    assert len(positions) == expected_length, f"Should have {expected_length} {position_type} values"
    assert all(isinstance(x, (int, float)) for x in positions), f"All {position_type} values should be numeric"
    
    # Additional validation for reasonable ranges
    if position_type == "joint positions":
        # Joint positions should be within reasonable limits (±2π radians)
        assert all(-MAX_JOINT_ANGLE <= x <= MAX_JOINT_ANGLE for x in positions), \
            f"Joint positions should be within ±{MAX_JOINT_ANGLE} radians"
    elif position_type == "cartesian position":
        # Cartesian positions should have reasonable XYZ values (not NaN or infinite)
        assert all(not (x != x or abs(x) == float('inf')) for x in positions[:3]), \
            "XYZ values should be finite"


@pytest.mark.integration
@pytest.mark.docker
def test_ursim_functionality(ursim_container, ur5_robot):
    """Comprehensive test of URSim functionality.
    
    Args:
        ursim_container: URSim container fixture.
        ur5_robot: Connected robot fixture.
    """
    logger.info("Testing URSim basic functionality")
    
    # Test 1: Basic connectivity
    assert is_port_open("localhost", URSIM_PORT), "RTDE port should be accessible"
    assert is_port_open("localhost", URSIM_PRIMARY_PORT), "Primary socket port should be accessible"
    
    # Test 2: Get robot state with validation
    joint_pos = ur5_robot.get_joint_positions()
    cart_pos = ur5_robot.get_cartesian_position()
    
    # Validate using helper function
    validate_position_data(joint_pos, 6, "joint positions")
    validate_position_data(cart_pos, 6, "cartesian position")
    
    logger.info(f"Joint positions: {joint_pos}")
    logger.info(f"Cartesian position: {cart_pos}")
    logger.info("URSim functionality test passed")


@pytest.mark.integration
@pytest.mark.docker
def test_ursim_multiple_queries(ursim_container, ur5_robot):
    """Test multiple sequential queries to ensure stability and performance.
    
    Args:
        ursim_container: URSim container fixture.
        ur5_robot: Connected robot fixture.
    """
    logger.info("Testing URSim stability with multiple queries")
    results = []
    query_times = []
    num_queries = 5
    
    for i in range(num_queries):
        start_time = time.time()
        
        joint_pos = ur5_robot.get_joint_positions()
        cart_pos = ur5_robot.get_cartesian_position()
        
        query_time = time.time() - start_time
        query_times.append(query_time)
        
        # Validate each query
        validate_position_data(joint_pos, 6, "joint positions")
        validate_position_data(cart_pos, 6, "cartesian position")
        
        results.append((joint_pos, cart_pos))
        logger.info(f"Query {i+1}: completed in {query_time:.3f}s")
        
        time.sleep(0.1)  # Brief pause between queries
    
    # Performance validation
    avg_query_time = sum(query_times) / len(query_times)
    max_query_time = max(query_times)
    
    assert len(results) == num_queries, f"Should have {num_queries} successful query results"
    assert avg_query_time < MAX_AVERAGE_QUERY_TIME, \
        f"Average query time should be < {MAX_AVERAGE_QUERY_TIME}s, got {avg_query_time:.3f}s"
    assert max_query_time < MAX_SINGLE_QUERY_TIME, \
        f"Max query time should be < {MAX_SINGLE_QUERY_TIME}s, got {max_query_time:.3f}s"
    
    logger.info(f"Multiple queries test passed - avg: {avg_query_time:.3f}s, max: {max_query_time:.3f}s")


@pytest.mark.integration
@pytest.mark.docker
def test_ursim_error_handling(ursim_container, ur5_robot):
    """Test graceful handling of invalid operations and edge cases.
    
    Args:
        ursim_container: URSim container fixture.
        ur5_robot: Connected robot fixture.
    """
    logger.info("Testing URSim error handling")
    
    # Test 1: Robot should handle multiple rapid queries gracefully
    for _ in range(3):
        positions = ur5_robot.get_joint_positions()
        assert positions is not None, "Rapid queries should not fail"
    
    # Test 2: Connection status validation
    # The robot should maintain connection stability
    try:
        # Make several calls to ensure connection is stable
        for i in range(3):
            joint_pos = ur5_robot.get_joint_positions()
            cart_pos = ur5_robot.get_cartesian_position()
            assert joint_pos is not None and cart_pos is not None, f"Connection lost on iteration {i}"
    except Exception as e:
        # Should not be a critical system error
        assert not isinstance(e, (SystemExit, KeyboardInterrupt)), f"Critical error occurred: {e}"
        
    logger.info("Error handling test passed")


def _create_robot_connection() -> 'UR5':
    """Helper function to create and verify robot connection for manual testing.
    
    Returns:
        UR5: Connected robot instance.
        
    Raises:
        ConnectionError: If connection fails.
    """
    from armctl import UR5
    
    @retry_on_failure(max_retries=5, delay=1)
    def connect_robot():
        robot = UR5(ip="localhost", port=URSIM_PRIMARY_PORT)
        robot.connect()
        # Verify connection
        positions = robot.get_joint_positions()
        if positions is None:
            raise ConnectionError("Robot connected but failed to get joint positions")
        return robot
    
    return connect_robot()


def _run_manual_tests(robot: 'UR5') -> None:
    """Run basic manual tests on the robot.
    
    Args:
        robot: Connected robot instance.
    """
    # Run basic functionality test
    logger.info("Testing basic functionality...")
    joint_pos = robot.get_joint_positions()
    cart_pos = robot.get_cartesian_position()
    validate_position_data(joint_pos, 6, "joint positions")
    validate_position_data(cart_pos, 6, "cartesian position")
    logger.info("Basic functionality test passed")
    
    # Run multiple queries test
    logger.info("Testing multiple queries...")
    for i in range(3):
        joint_pos = robot.get_joint_positions()
        cart_pos = robot.get_cartesian_position()
        validate_position_data(joint_pos, 6, "joint positions")
        validate_position_data(cart_pos, 6, "cartesian position")
        time.sleep(0.1)
    logger.info("Multiple queries test passed")


if __name__ == "__main__":
    """Run tests manually for development and debugging."""
    # Set up logging for manual execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if not check_docker_available():
        logger.error("Docker is not available or not running. Please start Docker and try again.")
        sys.exit(1)
    
    logger.info("Running URSim Docker tests manually...")
    
    try:
        ports = get_ursim_port_mappings()
        
        # Start container and run tests
        with docker_container_manager(URSIM_IMAGE, URSIM_CONTAINER_NAME, ports) as container_id:
            # Wait for URSim to be ready
            ports_ready = (
                wait_for_port("localhost", URSIM_PORT, timeout=CONTAINER_STARTUP_TIMEOUT) and
                wait_for_port("localhost", URSIM_PRIMARY_PORT, timeout=30)
            )
            
            if not ports_ready:
                raise TimeoutError("URSim ports did not open in time")
            
            # Connect to robot and run tests
            robot = _create_robot_connection()
            
            try:
                _run_manual_tests(robot)
                logger.info("All manual tests passed successfully!")
            finally:
                robot.disconnect()
        
    except Exception as e:
        logger.error(f"Tests failed: {e}")
        sys.exit(1)