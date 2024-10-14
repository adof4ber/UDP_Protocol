import time
from protocol import DataTransferProtocolAdo

def keep_alive(connection, target_ip, target_port):
    while True:
        keep_alive_frame = DataTransferProtocolAdo.build_keep_alive()
        connection.send(keep_alive_frame, (target_ip, target_port))
        time.sleep(5)  

