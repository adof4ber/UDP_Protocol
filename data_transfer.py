import time
from protocol import DataTransferProtocolAdo

class DataTransfer:
    def __init__(self, connection, target_ip, target_port, fragment_size, window_size=4, timeout=2):
        self.connection = connection
        self.target_ip = target_ip
        self.target_port = target_port
        self.fragment_size = fragment_size
        self.window_size = window_size
        self.timeout = timeout

    def fragment_message(self, message):
        fragments = [message[i:i + self.fragment_size] for i in range(0, len(message), self.fragment_size)]
        return fragments

    def send_message(self, message):
        fragments = self.fragment_message(message)
        total_fragments = len(fragments)

        base = 0  # The lowest sequence number of unacknowledged frame
        next_seq = 0  # The next sequence number to send
        acked = [False] * total_fragments  # Acknowledgment status for each fragment

        while base < total_fragments:
            # Send frames in the window
            while next_seq < base + self.window_size and next_seq < total_fragments:
                frame = DataTransferProtocolAdo.build_frame(
                    DataTransferProtocolAdo.MSG_TYPE_DATA, next_seq, total_fragments, fragments[next_seq]
                )
                self.connection.send(frame, (self.target_ip, self.target_port))
                print(f"Sent fragment {next_seq + 1}/{total_fragments}")
                next_seq += 1

            # Wait for ACKs or timeout
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                frame, _ = self.connection.receive()
                if frame is None:
                    continue

                try:
                    msg_type, fragment_id, total_fragments, data = DataTransferProtocolAdo.parse_frame(frame)

                    # Ignore system messages
                    if msg_type in {
                        DataTransferProtocolAdo.MSG_TYPE_SYN,
                        DataTransferProtocolAdo.MSG_TYPE_SYN_ACK,
                        DataTransferProtocolAdo.MSG_TYPE_ACK,
                        DataTransferProtocolAdo.MSG_TYPE_CLOSE_INIT,
                        DataTransferProtocolAdo.MSG_TYPE_CLOSE_ACK,
                        DataTransferProtocolAdo.MSG_TYPE_CLOSE_FINAL
                    }:
                        continue

                    if msg_type == DataTransferProtocolAdo.MSG_TYPE_ACK:
                        acked[fragment_id] = True
                        print(f"Received ACK for fragment {fragment_id + 1}/{total_fragments}")

                        # Move window base forward
                        while base < total_fragments and acked[base]:
                            base += 1

                        break
                except Exception as e:
                    print(f"Error parsing frame: {e}")

            # If timeout occurred, resend all frames in the window
            if time.time() - start_time >= self.timeout:
                print("Timeout reached. Resending frames...")
                next_seq = base  # Retransmit the unacknowledged fragments

    def receive_message(self):
        received_fragments = {}  # Store received fragments
        total_fragments = None  # We will get the total fragments from the first fragment

        while True:
            frame, _ = self.connection.receive()
            if frame is None:  
                continue  

            try:
                msg_type, fragment_id, total_fragments, data = DataTransferProtocolAdo.parse_frame(frame)

                # Ignore system messages
                if msg_type in {
                    DataTransferProtocolAdo.MSG_TYPE_SYN,
                    DataTransferProtocolAdo.MSG_TYPE_SYN_ACK,
                    DataTransferProtocolAdo.MSG_TYPE_ACK,
                    DataTransferProtocolAdo.MSG_TYPE_CLOSE_INIT,
                    DataTransferProtocolAdo.MSG_TYPE_CLOSE_ACK,
                    DataTransferProtocolAdo.MSG_TYPE_CLOSE_FINAL
                }:
                    continue

                # If it's the first fragment, initialize total_fragments
                if total_fragments is None:
                    total_fragments = total_fragments

                # Store the fragment
                received_fragments[fragment_id] = data
                print(f"Received fragment {fragment_id + 1}/{total_fragments}")

                # Check if all fragments are received
                if len(received_fragments) == total_fragments:
                    # Reassemble the message
                    message = ''.join(received_fragments[i] for i in range(total_fragments))
                    print(f"Complete message received: {message}")
                    break

            except Exception as e:
                print(f"Error parsing frame: {e}")
