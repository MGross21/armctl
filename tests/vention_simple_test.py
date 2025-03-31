import socket
import time

def control_vention_slider():
    # Connection parameters
    HOST = '192.168.7.2'  # Replace with your MachineMotion's IP address
    PORT = 9999
    
    # Create socket and connect
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to MachineMotion
        s.connect((HOST, PORT))
        print("Connection initiated...")
        
        # Check initial response
        response = s.recv(1024).decode()
        print(f"Connection response: {response}")
        
        # Check if ready
        s.send("isReady;".encode())
        response = s.recv(1024).decode()
        print(f"Ready check: {response}")
        
        # Configure speed and acceleration
        s.send("SET speed/300/;".encode())
        response = s.recv(1024).decode()
        print(f"Speed setup: {response}")
        
        s.send("SET acceleration/100/;".encode())
        response = s.recv(1024).decode()
        print(f"Acceleration setup: {response}")
        
        # Move to absolute position
        s.send("SET de_move_abs_1/1500/;".encode())
        response = s.recv(1024).decode()
        print(f"Absolute move setup: {response}")
        
        s.send("de_move_abs_exec;".encode())
        response = s.recv(1024).decode()
        print(f"Absolute move execution: {response}")
        
        # # Wait for motion to complete
        time.sleep(5)  
        
        # # Move relatively
        # s.send("SET de_move_rel_1/-50/;".encode())
        # response = s.recv(1024).decode()
        # print(f"Relative move setup: {response}")
        
        # s.send("de_move_rel_exec;".encode())
        # response = s.recv(1024).decode()
        # print(f"Relative move execution: {response}")
        
        # time.sleep(5)
        
        # # Start continuous movement
        # s.send("SET im_conv_1 S50 A100;".encode())
        # response = s.recv(1024).decode()
        # print(f"Continuous move: {response}")
        
        # time.sleep(5)
        
        # # Stop all motion
        # s.send("Stop all motion;".encode())
        # response = s.recv(1024).decode()
        # print(f"Stop motion: {response}")
        
    finally:
        # Close the connection
        s.close()
        print("Connection closed")

if __name__ == "__main__":
    control_vention_slider()
