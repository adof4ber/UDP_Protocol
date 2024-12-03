import time
import threading
from protocol import DataTransferProtocolAdo
from handshake_close import handle_close_sequence

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

    def encrypt_message(self, message):
        encrypted = []
        for i in range(0, len(message) - 1, 2):
            encrypted.append(message[i + 1] + message[i])

        if len(message) % 2 != 0:
            encrypted.append(message[-1])
        
        return " ".join(encrypted)

    def fragment_message(self, message):
        fragments = [message[i:i + self.fragment_size] for i in range(0, len(message), self.fragment_size)]
        return [(seq, fragment) for seq, fragment in enumerate(fragments)]

    def send_message(self, message):
        print(f"Starting to send message: {message}")
        encrypted_message = self.encrypt_message(message)
        print(f"Encrypted message: {encrypted_message}")
        self._send_message(encrypted_message)

    def _send_message(self, message):
        fragments = self.fragment_message(message)
        total_fragments = len(fragments)
        total_size = sum(len(fragment) for _, fragment in fragments)

        print(f"Total size of message: {total_size} bytes")
        print(f"Total fragments to send: {total_fragments}")

        for seq, fragment in fragments:
            ack_received = False
            retries = 0
            while not ack_received and retries < 3:
                frame = DataTransferProtocolAdo.build_frame(
                    DataTransferProtocolAdo.MSG_TYPE_DATA, seq, total_fragments, fragment
                )
                self.connection.send(frame, (self.target_ip, self.target_port))
                fragment_size = len(fragment)
                print(f"Sent fragment {seq + 1}/{total_fragments} (Size: {fragment_size} bytes)")

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
                        elif msg_type == DataTransferProtocolAdo.MSG_TYPE_NACK:
                            print(f"Received NACK for fragment. Resending...")
                            break
                    except Exception as e:
                        print(f"Error parsing frame: {e}")

                if not ack_received:
                    retries += 1

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
                        fragment_size = len(data)
                        print(f"Received fragment {fragment_id + 1}/{total_fragments} (Size: {fragment_size} bytes)")

                    if last_ack_id != fragment_id:
                        ack_frame = DataTransferProtocolAdo.build_ack(fragment_id)
                        self.connection.send(ack_frame, sender_address)
                        print(f"Sent ACK for fragment {fragment_id + 1}/{total_fragments}")
                        last_ack_id = fragment_id

                    if len(received_fragments) == total_fragments:
                        message = ''.join(received_fragments[i] for i in range(total_fragments))
                        parts = message.split(" ")
                        encrypted_message = " ".join(parts[:-1]) if len(parts[-1]) == 1 else message
                        pair_count = encrypted_message.count(" ") + 1
                        print(f"Encrypted message received: {encrypted_message}")
                        print(f"Number of received pairs: {pair_count}")
                        return encrypted_message

                elif msg_type == DataTransferProtocolAdo.MSG_TYPE_END:
                    print("Received END signal. Ready for next message.")
                    return None

                elif msg_type == DataTransferProtocolAdo.MSG_TYPE_CLOSE_INIT:
                    print("Received CLOSE_INIT. Sending CLOSE_ACK and closing connection.")
                    ack_frame = DataTransferProtocolAdo.build_close_ack()
                    self.connection.send(ack_frame, sender_address)
                    self.connection_active[0] = False
                    self.transfer_active = False
                    handle_close_sequence(self.connection, self.target_port, self.connection_active, self.connection_active)
                    return None

            except Exception as e:
                print(f"Error parsing frame: {e}")
                nack_frame = DataTransferProtocolAdo.build_nack(0)
                self.connection.send(nack_frame, sender_address)
                print(f"Sent NACK")