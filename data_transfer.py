from protocol import DataTransferProtocolAdo

class DataTransfer:
    def __init__(self, connection, target_ip, target_port, fragment_size):
        self.connection = connection
        self.target_ip = target_ip
        self.target_port = target_port
        self.fragment_size = fragment_size

    def fragment_message(self, message):

        fragments = [message[i:i + self.fragment_size] for i in range(0, len(message), self.fragment_size)]
        return fragments

    def send_message(self, message):
        fragments = self.fragment_message(message)
        total_fragments = len(fragments)

        for i, fragment in enumerate(fragments):
            frame = DataTransferProtocolAdo.build_frame(
                DataTransferProtocolAdo.MSG_TYPE_DATA, i, total_fragments, fragment
            )
            self.connection.send(frame, (self.target_ip, self.target_port))
            print(f"Sent fragment {i + 1}/{total_fragments}")

    def receive_message(self):
        while True:
            frame, _ = self.connection.receive()
            if frame is None:  #
                continue  

            try:
                msg_type, fragment_id, total_fragments, data = DataTransferProtocolAdo.parse_frame(frame)
                print(f"Received message: {data}")  
            except Exception as e:
                print(f"Error parsing frame: {e}")

