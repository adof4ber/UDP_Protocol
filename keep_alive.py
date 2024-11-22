import threading
import time
from protocol import DataTransferProtocolAdo

class KeepAlive(threading.Thread):
    def __init__(self, connection, target_ip, target_port, connection_active):
        super().__init__(daemon=True)
        self.connection = connection
        self.target_ip = target_ip
        self.target_port = target_port
        self.connection_active = connection_active
        self.keep_alive_interval = 5
        self.missed_responses = 0
        self.max_missed_responses = 3

    def run(self):
        while self.connection_active[0]:
            self.send_keep_alive()
            if not self.wait_for_response():
                self.missed_responses += 1
                if self.missed_responses >= self.max_missed_responses:
                    print("No KEEP_ALIVE responses. Connection lost.")
                    self.connection_active[0] = False
            else:
                self.missed_responses = 0  

            time.sleep(self.keep_alive_interval)

    def send_keep_alive(self):
        keep_alive_frame = DataTransferProtocolAdo.build_keep_alive()
        self.connection.send(keep_alive_frame, (self.target_ip, self.target_port))

    def wait_for_response(self):
        start_time = time.time()
        while time.time() - start_time < self.keep_alive_interval:
            frame, _ = self.connection.receive()
            if frame:
                try:
                    msg_type, _, _, _ = DataTransferProtocolAdo.parse_frame(frame)
                    if msg_type == DataTransferProtocolAdo.MSG_TYPE_KEEP_ALIVE_ACK:
                        self.missed_responses = 0  
                        return True
                    elif msg_type == DataTransferProtocolAdo.MSG_TYPE_KEEP_ALIVE:
                        self.send_keep_alive_ack()
                except Exception:
                    continue
        return False

    def send_keep_alive_ack(self):
        keep_alive_ack_frame = DataTransferProtocolAdo.build_frame(
            DataTransferProtocolAdo.MSG_TYPE_KEEP_ALIVE_ACK, 0, 1, "KEEP_ALIVE_ACK"
        )
        self.connection.send(keep_alive_ack_frame, (self.target_ip, self.target_port))
