import os
import time
from protocol import DataTransferProtocolAdo
from threading import Lock

class FileTransfer:
    def __init__(self, connection, target_ip, target_port, fragment_size, save_directory, window_size=50, timeout=0.01):
        self.connection = connection
        self.target_ip = target_ip
        self.target_port = target_port
        self.fragment_size = fragment_size
        self.save_directory = save_directory
        self.window_size = window_size
        self.timeout = timeout
        self.file_name = None
        self.lock = Lock()
        self.sequence_number = 0
        self.sent_frames = {}
        self.received_fragments = {}
        self.received_count = 0

        self._ensure_save_directory()

    def _ensure_save_directory(self):
        if not self.save_directory:
            print("Error: No save directory provided.")
            return

        if not os.path.exists(self.save_directory):
            print(f"Directory '{self.save_directory}' does not exist. Creating it...")
            os.makedirs(self.save_directory)

    def send_file(self, file_path):
        if not file_path:
            print("Error: No file path provided.")
            return

        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist.")
            return

        self.file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        self.sequence_number = 0
        self.sent_frames = {}

        # Odoslanie metadát
        metadata_frame = DataTransferProtocolAdo.build_file_metadata(self.file_name, file_size)
        self.connection.send(metadata_frame, (self.target_ip, self.target_port))
        print(f"Sent file metadata: {self.file_name}, {file_size} bytes")

        try:
            with open(file_path, "rb") as file:
                fragment_id = 0
                total_fragments = (file_size + self.fragment_size - 1) // self.fragment_size
                print(f"Total fragments: {total_fragments}")

                while fragment_id < total_fragments:
                    for i in range(self.window_size):
                        if fragment_id < total_fragments:
                            chunk = file.read(self.fragment_size)
                            self._send_file_data(chunk, fragment_id, total_fragments)
                            fragment_id += 1

                    if fragment_id >= total_fragments:
                        break

                    self._wait_for_ack(total_fragments)

                self._send_end_signal()

            print("File transfer completed.")
        except Exception as e:
            print(f"Error during file transfer: {e}")


    def _send_end_signal(self):
        frame = DataTransferProtocolAdo.build_end()
        self.connection.send(frame, (self.target_ip, self.target_port))
        print("Sent END signal")

    def _send_file_data(self, data, fragment_id, total_fragments):
        if isinstance(data, str):
            data = data.encode("utf-8")

        frame = DataTransferProtocolAdo.build_frame(
            DataTransferProtocolAdo.MSG_TYPE_FILE_DATA,
            fragment_id,
            total_fragments,
            data
        )

        self.sent_frames[fragment_id] = frame
        self.connection.send(frame, (self.target_ip, self.target_port))
        print(f"Sent fragment {fragment_id + 1}/{total_fragments}")

    def _wait_for_ack(self, total_fragments):
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            with self.lock:
                try:
                    frame, sender_address = self.connection.receive()
                    if frame:
                        msg_type, fragment_id, _, _ = DataTransferProtocolAdo.parse_frame(frame)

                        if msg_type == DataTransferProtocolAdo.MSG_TYPE_ACK:
                            if fragment_id in self.sent_frames:
                                del self.sent_frames[fragment_id]
                                print(f"Received ACK for fragment {fragment_id + 1}/{total_fragments}")

                        if not self.sent_frames:
                            break

                except Exception as e:
                    print(f"Error while waiting for ACK: {e}")

    def save_received_file(self, file_data):
        if not self.save_directory:
            print("Error: No save directory provided.")
            return

        self._ensure_save_directory()

        if not self.file_name:
            print("Error: No file name specified.")
            return

        file_path = os.path.join(self.save_directory, self.file_name)

        base_name, extension = os.path.splitext(file_path)
        index = 1
        while os.path.exists(file_path):
            file_path = f"{base_name}({index}){extension}"
            index += 1

        try:
            with open(file_path, "wb") as f:
                f.write(file_data)
            print(f"File saved to {file_path}")
        except Exception as e:
            print(f"Error saving file: {e}")

    def receive_file(self):
        file_data = b''
        fragments = {}
        total_fragments = None
        self.file_name = None

        while True:
            frame, sender_address = self.connection.receive()

            if frame:
                msg_type, fragment_id, total_fragments, data = DataTransferProtocolAdo.parse_frame(frame)

                if msg_type == DataTransferProtocolAdo.MSG_TYPE_KEEP_ALIVE:
                    self._send_keep_alive_ack(sender_address)

                elif msg_type == DataTransferProtocolAdo.MSG_TYPE_FILE_METADATA:
                    self.file_name, file_size = DataTransferProtocolAdo.parse_file_metadata(frame)
                    print(f"Received file metadata: {self.file_name}, size: {file_size} bytes")

                elif msg_type == DataTransferProtocolAdo.MSG_TYPE_FILE_DATA:
                    if fragment_id not in fragments:
                        fragments[fragment_id] = data
                        self.received_count += 1
                        print(f"Received file fragment {fragment_id + 1}/{total_fragments}")

                    if self.received_count == self.window_size:
                        self._send_ack(fragment_id, sender_address)
                        self.received_count = 0

                    if len(fragments) == total_fragments:
                        sorted_fragments = [fragments[i] for i in sorted(fragments.keys())]
                        file_data = b''.join(sorted_fragments)
                        self.save_received_file(file_data)
                        print("File received and saved successfully.")
                        break

                elif msg_type == DataTransferProtocolAdo.MSG_TYPE_END:
                    print("Received END signal, finalizing transfer.")
                    break

        return file_data

    def _send_ack(self, fragment_id, sender_address):
        ack_frame = DataTransferProtocolAdo.build_ack(fragment_id)
        self.connection.send(ack_frame, sender_address)
        print(f"Sent ACK for fragment {fragment_id + 1}")

    def _send_keep_alive_ack(self, sender_address):
        ack_frame = DataTransferProtocolAdo.build_keep_alive_ack()
        self.connection.send(ack_frame, sender_address)
        print("Sent KEEP ALIVE ACK")
