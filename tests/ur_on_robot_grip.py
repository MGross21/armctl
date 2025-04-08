import socket
import time

UR_IP = "192.168.1.111"
PORT = 30002

def send_urscript(script):
    print(f"[SEND]: {script.strip()}")
    with socket.create_connection((UR_IP, PORT), timeout=5) as s:
        s.sendall((script + '\n').encode())
        time.sleep(0.2)

# Gripper control using Modbus via Tool I/O (no URCap needed)
script = """
write_output_integer_register(0, 1)    # Activate gripper
sleep(1.0)
write_output_integer_register(1, 200)  # Set target position
write_output_integer_register(2, 50)  # Set force
sleep(0.2)
write_output_integer_register(0, 16)   # Close
sleep(2)
write_output_integer_register(0, 10)   # Open
"""

send_urscript(script)