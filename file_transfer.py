import os
from protocol import DataTransferProtocolAdo

class FileTransfer:
    def __init__(self, connection, target_ip, target_port, fragment_size):
        self.connection = connection
        self.target_ip = target_ip
        self.target_port = target_port
        self.fragment_size = fragment_size
        self.file_name = None

    def send_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist.")
            return

        self.file_name = os.path.basename(file_path)  
        file_size = os.path.getsize(file_path)
        print(f"Sending file '{self.file_name}' of size {file_size} bytes")

        try:
            with open(file_path, "rb") as file:
                fragment_id = 0
                total_fragments = (file_size + self.fragment_size - 1) // self.fragment_size

                for fragment_id in range(total_fragments):
                    chunk = file.read(self.fragment_size)
                    self._send_file_data(chunk, fragment_id, total_fragments)

            print("File transfer completed.")
        except Exception as e:
            print(f"Error during file transfer: {e}")

    def _send_file_data(self, data, fragment_id, total_fragments):
        if isinstance(data, str):
            data = data.encode("utf-8")
 
        frame = DataTransferProtocolAdo.build_frame(
            DataTransferProtocolAdo.MSG_TYPE_FILE_DATA,
            fragment_id,
            total_fragments,
            data
        )
        self.connection.send(frame, (self.target_ip, self.target_port))

    def receive_file_data(self, data, save_directory):
        if isinstance(data, str):
            data = data.encode("utf-8")

        fragment_id, total_fragments, chunk = data[0], data[1], data[2:]

        if self.file_name is None:
            self.file_name = "received_file"  

        file_path = os.path.join(save_directory, self.file_name)  

        with open(file_path, "ab") as file:
            file.write(chunk)
            print(f"Received fragment {fragment_id + 1}/{total_fragments}")

        if fragment_id == total_fragments - 1:
            print(f"File transfer complete. File saved as {file_path}")
