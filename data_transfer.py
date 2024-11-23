import time
from protocol import DataTransferProtocolAdo

class DataTransfer:
    def __init__(self, connection, target_ip, target_port, fragment_size, timeout=0.5, ack_timeout=0.5):
        self.connection = connection
        self.target_ip = target_ip
        self.target_port = target_port
        self.fragment_size = fragment_size
        self.timeout = timeout  
        self.ack_timeout = ack_timeout  
        self.transfer_active = True
        self.connection_active = [True]

    def fragment_message(self, message):
        fragments = [message[i:i + self.fragment_size] for i in range(0, len(message), self.fragment_size)]
        return [(seq, fragment) for seq, fragment in enumerate(fragments)]

    def send_message(self, message):
        print(f"Starting to send message: {message}")
        self._send_message(message)

    def _send_message(self, message):
        fragments = self.fragment_message(message)
        total_fragments = len(fragments)

        for seq, fragment in fragments:
            ack_received = False
            retries = 0
            while not ack_received and retries < 3:  
                frame = DataTransferProtocolAdo.build_frame(
                    DataTransferProtocolAdo.MSG_TYPE_DATA, seq, total_fragments, fragment
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
                        if msg_type == DataTransferProtocolAdo.MSG_TYPE_ACK and fragment_id == seq:
                            ack_received = True
                            print(f"Received ACK for fragment {fragment_id + 1}/{total_fragments}")
                            break
                        elif msg_type == DataTransferProtocolAdo.MSG_TYPE_NACK and fragment_id == seq:
                            print(f"Received NACK for fragment {seq + 1}. Resending...")
                            break  
                    except Exception as e:
                        print(f"Error parsing frame: {e}")

                if not ack_received:
                    retries += 1
                    print(f"Timeout reached for fragment {seq + 1}. Resending... ({retries}/3)")

                time.sleep(self.ack_timeout)

        end_frame = DataTransferProtocolAdo.build_end()
        self.connection.send(end_frame, (self.target_ip, self.target_port))
        print("Sent END frame.")

    def receive_message(self):
        received_fragments = {}
        total_fragments = None
        last_ack_id = -1  

        while self.transfer_active and self.connection_active[0]:
            frame, sender_address = self.connection.receive()
            if frame is None:
                continue

            try:
                msg_type, fragment_id, total_fragments, data = DataTransferProtocolAdo.parse_frame(frame)

                if msg_type == DataTransferProtocolAdo.MSG_TYPE_KEEP_ALIVE:
                    ack_frame = DataTransferProtocolAdo.build_keep_alive_ack()
                    self.connection.send(ack_frame, sender_address)
                    continue

                if msg_type == DataTransferProtocolAdo.MSG_TYPE_DATA:
                    if total_fragments is None:
                        total_fragments = total_fragments  

                    if fragment_id not in received_fragments:
                        received_fragments[fragment_id] = data
                        print(f"Received fragment {fragment_id + 1}/{total_fragments}")

                    if last_ack_id != fragment_id:
                        ack_frame = DataTransferProtocolAdo.build_ack(fragment_id)
                        self.connection.send(ack_frame, sender_address)
                        print(f"Sent ACK for fragment {fragment_id + 1}/{total_fragments}")
                        last_ack_id = fragment_id  

                    if len(received_fragments) == total_fragments:
                        message = ''.join(received_fragments[i] for i in range(total_fragments))
                        print(f"Complete message received: {message}")
                        return message

                elif msg_type == DataTransferProtocolAdo.MSG_TYPE_END:
                    print("Received END signal. Ready for next message.")
                    return None

            except Exception as e:
                print(f"Error parsing frame: {e}")
                if 'fragment_id' in locals():  
                    nack_frame = DataTransferProtocolAdo.build_nack(fragment_id)
                    self.connection.send(nack_frame, sender_address)
                    print(f"Sent NACK for fragment {fragment_id + 1}/{total_fragments}")
                else:
                    print("Cannot send NACK: fragment_id is not available.")


