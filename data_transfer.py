import time
from protocol import DataTransferProtocolAdo

class DataTransfer:
    def __init__(self, connection, target_ip, target_port, fragment_size, window_size=10, timeout=2):
        self.connection = connection
        self.target_ip = target_ip
        self.target_port = target_port
        self.fragment_size = fragment_size
        self.window_size = window_size
        self.timeout = timeout
        self.transfer_active = True

    def fragment_message(self, message):
        fragments = [message[i:i + self.fragment_size] for i in range(0, len(message), self.fragment_size)]
        return [(seq, fragment) for seq, fragment in enumerate(fragments)]

    def send_message(self, message):
        print(f"Starting to send message: {message}")
        self._send_message(message)

    def _send_message(self, message):
        fragments = self.fragment_message(message)
        total_fragments = len(fragments)
        base = 0
        acked = [False] * total_fragments

        while base < total_fragments:
            for seq in range(base, min(base + self.window_size, total_fragments)):
                if not acked[seq]:
                    frame = DataTransferProtocolAdo.build_frame(
                        DataTransferProtocolAdo.MSG_TYPE_DATA, seq, total_fragments, fragments[seq][1]
                    )
                    self.connection.send(frame, (self.target_ip, self.target_port))
                    print(f"Sent fragment {seq + 1}/{total_fragments}")

            timeout_start = time.time()
            while time.time() - timeout_start < self.timeout:
                frame, _ = self.connection.receive()
                if frame is None:
                    continue

                try:
                    msg_type, fragment_id, _, _ = DataTransferProtocolAdo.parse_frame(frame)
                    if msg_type == DataTransferProtocolAdo.MSG_TYPE_ACK:
                        acked[fragment_id] = True
                        print(f"Received ACK for fragment {fragment_id + 1}/{total_fragments}")

                    if all(acked[base:base + self.window_size]) or total_fragments - base <= self.window_size:
                        base = min(base + self.window_size, total_fragments)

                except Exception as e:
                    print(f"Error parsing frame: {e}")

            if base < total_fragments and not all(acked[base:base + self.window_size]):
                print("Timeout reached. Resending current window...")

        print("All fragments acknowledged. Transfer complete.")
        end_frame = DataTransferProtocolAdo.build_end()
        self.connection.send(end_frame, (self.target_ip, self.target_port))
        print("Sent END frame.")

    def receive_message(self):
        received_fragments = {}
        total_fragments = None

        while self.transfer_active:
            frame, _ = self.connection.receive()
            if frame is None:
                continue

            try:
                msg_type, fragment_id, total_fragments, data = DataTransferProtocolAdo.parse_frame(frame)
                if msg_type == DataTransferProtocolAdo.MSG_TYPE_KEEP_ALIVE:
                    continue

                if msg_type == DataTransferProtocolAdo.MSG_TYPE_DATA:
                    received_fragments[fragment_id] = data
                    print(f"Received fragment {fragment_id + 1}/{total_fragments}")

                    if fragment_id == total_fragments - 1 or len(received_fragments) == total_fragments:
                        ack_frame = DataTransferProtocolAdo.build_ack(fragment_id)
                        self.connection.send(ack_frame, (self.target_ip, self.target_port))
                        print(f"Sent ACK for fragment {fragment_id + 1}/{total_fragments}")

                    if len(received_fragments) == total_fragments:
                        message = ''.join(received_fragments[i] for i in range(total_fragments))
                        print(f"Complete message received: {message}")
                        end_frame = DataTransferProtocolAdo.build_end()
                        self.connection.send(end_frame, (self.target_ip, self.target_port))
                        print("Sent END frame.")
                        return message

                if msg_type == DataTransferProtocolAdo.MSG_TYPE_END:
                    print("Received END signal. Ready for next message.")
                    return None
                
                

            except Exception as e:
                print(f"Error parsing frame: {e}")
