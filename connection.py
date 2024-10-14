import socket

class UDPConnection:
    def __init__(self, listen_port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', listen_port))
        self.socket.settimeout(1)  

    def send(self, frame, address):
        self.socket.sendto(frame, address)

    def receive(self):
        try:
            data, addr = self.socket.recvfrom(1024)
            return data, addr
        except socket.timeout:
            return None, None  
        except Exception as e:
            print(f"Error receiving data: {e}")
            return None, None

    def set_timeout(self, timeout):
        self.socket.settimeout(timeout)

    def close(self):
        self.socket.close()
