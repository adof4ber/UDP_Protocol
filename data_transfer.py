import time
from protocol import DataTransferProtocolAdo

class DataTransfer:
    def __init__(self, connection, target_ip, target_port, fragment_size, window_size=4, timeout=2, timeout_increment=0.5, timeout_decrement=0.1):
        self.connection = connection
        self.target_ip = target_ip
        self.target_port = target_port
        self.fragment_size = fragment_size
        self.window_size = window_size
        self.timeout = timeout
        self.timeout_increment = timeout_increment  
        self.timeout_decrement = timeout_decrement 

    def fragment_message(self, message):
        fragments = [message[i:i + self.fragment_size] for i in range(0, len(message), self.fragment_size)]
        return fragments

    def send_message(self, message):
        fragments = self.fragment_message(message)
        total_fragments = len(fragments)

        base = 0  
        next_seq = 0  
        acked = [False] * total_fragments  

        while base < total_fragments:
            while next_seq < base + self.window_size and next_seq < total_fragments:
                frame = DataTransferProtocolAdo.build_frame(
                    DataTransferProtocolAdo.MSG_TYPE_DATA, next_seq, total_fragments, fragments[next_seq]
                )
                self.connection.send(frame, (self.target_ip, self.target_port))
                print(f"Sent fragment {next_seq + 1}/{total_fragments}")
                next_seq += 1

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

                        while base < total_fragments and acked[base]:
                            base += 1

                        if base == total_fragments:
                            print("All fragments acknowledged.")
                            return

                    elif msg_type == DataTransferProtocolAdo.MSG_TYPE_NACK:
                        print(f"Received NACK for fragment {fragment_id + 1}/{total_fragments}")
                        next_seq = fragment_id  # Reset sequence to the NACKed fragment
                        break

                except Exception as e:
                    print(f"Error parsing frame: {e}")

            if base < total_fragments and not all(acked[base:base+self.window_size]):
                print("Timeout reached. Resending frames...")
                self.timeout += self.timeout_increment  
                next_seq = base  
            else:
                self.timeout = max(0.2, self.timeout - self.timeout_decrement)

    def receive_message(self):
        received_fragments = {}
        expected_seq = 0
        total_fragments = None

        while True:
            frame, _ = self.connection.receive()
            if frame is None:
                continue

            try:
                msg_type, fragment_id, total_fragments, data = DataTransferProtocolAdo.parse_frame(frame)

                if msg_type == DataTransferProtocolAdo.MSG_TYPE_KEEP_ALIVE:
                    continue

                if msg_type == DataTransferProtocolAdo.MSG_TYPE_DATA:
                    if total_fragments is None:
                        total_fragments = total_fragments

                    if fragment_id == expected_seq:
                        received_fragments[fragment_id] = data
                        print(f"Received fragment {fragment_id + 1}/{total_fragments}")

                        ack_frame = DataTransferProtocolAdo.build_ack(fragment_id)
                        self.connection.send(ack_frame, (self.target_ip, self.target_port))
                        expected_seq += 1

                    else:
                        print(f"Out of order fragment {fragment_id + 1}/{total_fragments}, expected {expected_seq + 1}")
                        nack_frame = DataTransferProtocolAdo.build_nack(expected_seq)
                        self.connection.send(nack_frame, (self.target_ip, self.target_port))

                if len(received_fragments) == total_fragments:
                    message = ''.join(received_fragments[i] for i in range(total_fragments))
                    print(f"Complete message received: {message}")
                    return message

            except Exception as e:
                print(f"Error parsing frame: {e}")

#TODO - ked prijme ACK za vsetky fragmenty treba ukoncit while cyklus prenosu lebo to pislea fragmenty do nekonecna
