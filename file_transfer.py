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
        
        # Building the frame for sending the data fragment
        frame = DataTransferProtocolAdo.build_frame(
            DataTransferProtocolAdo.MSG_TYPE_FILE_DATA,
            fragment_id,
            total_fragments,
            data
        )
        # Send the fragment over the connection
        self.connection.send(frame, (self.target_ip, self.target_port))

    def receive_file_data(self, data, save_directory):
        # Ensure the data is in bytes when receiving
        if isinstance(data, str):
            data = data.encode("utf-8")
        
        # Assuming the received data includes fragment_id, total_fragments, and the actual chunk of data
        fragment_id, total_fragments, chunk = data[0], data[1], data[2:]

        # If file_name is None, we assume this is the first fragment, so we initialize it
        if self.file_name is None:
            self.file_name = "received_file"  # Default name if no name is found

        # Save the file as it is received (in chunks)
        file_path = os.path.join(save_directory, self.file_name)  # Automatically use file name

        # Open the file in append mode to write each fragment
        with open(file_path, "ab") as file:
            file.write(chunk)
            print(f"Received fragment {fragment_id + 1}/{total_fragments}")

        # Check if all fragments are received
        if fragment_id == total_fragments - 1:
            print(f"File transfer complete. File saved as {file_path}")
