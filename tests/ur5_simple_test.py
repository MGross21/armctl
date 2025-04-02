import socket
import struct
import time

# Function to establish connection with the robot
def connect_to_robot(host, port):
    # Create a socket and connect to the robot's controller
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print(f"Connected to {host}:{port}")
    return s

# Function to receive and process data from the robot
def receive_data(s):
    while True:
        data = s.recv(4096)  # Adjust buffer size as necessary
        if data:
            packet_length = struct.unpack('!i', data[0:4])[0]
            timestamp = struct.unpack('!Q', data[10:18])[0]
            packet_type = struct.unpack('!b', data[4:5])[0]

            print(f"Packet Length: {packet_length}")
            print(f"Timestamp: {timestamp}")
            print(f"Packet Type: {packet_type}")

            if packet_type == 16:  # Robot State packet type
                process_robot_state(data, packet_length)

# Function to process robot state information (joint positions, TCP, etc.)
def process_robot_state(data, packet_length):
    i = 0
    while i + 5 < packet_length:
        msg_len = struct.unpack('!i', data[5+i:9+i])[0]
        msg_type = struct.unpack('!b', data[9+i:10+i])[0]

        if msg_type == 1:  # Joint data
            joint_angles = [0] * 6
            for j in range(6):
                joint_angles[j] = struct.unpack('!d', data[10 + i + (j * 41):18 + i + (j * 41)])[0]
                print(f"Joint {j} angle: {joint_angles[j]}")
        
        elif msg_type == 4:  # Cartesian data (TCP pose)
            x = struct.unpack('!d', data[10 + i:18 + i])[0]
            y = struct.unpack('!d', data[18 + i:26 + i])[0]
            z = struct.unpack('!d', data[26 + i:34 + i])[0]
            rx = struct.unpack('!d', data[34 + i:42 + i])[0]
            ry = struct.unpack('!d', data[42 + i:50 + i])[0]
            rz = struct.unpack('!d', data[50 + i:58 + i])[0]
            
            print(f"TCP Pose - X: {x}, Y: {y}, Z: {z}")
            print(f"TCP Pose - RX: {rx}, RY: {ry}, RZ: {rz}")

        i += msg_len

# Main function to manage the workflow
def main():
    # Define the host and port for the robot's controller
    host = '192.168.1.111'
    port = 30002
    
    # Establish connection to the robot
    s = connect_to_robot(host, port)

    try:
        # Start receiving data from the robot
        receive_data(s)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        s.close()

if __name__ == "__main__":
    main()