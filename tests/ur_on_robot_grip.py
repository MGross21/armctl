import socket

UR_IP = "192.168.1.111"  # Replace with your robot's IP address
PORT = 30002             # Secondary client interface

def send_urscript(script_command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((UR_IP, PORT))
        s.sendall(script_command.encode('utf-8'))

# Command to open the gripper
open_gripper = "rg2_open()\n"
send_urscript(open_gripper)

# Command to close the gripper
close_gripper = "rg2_close()\n"
send_urscript(close_gripper)