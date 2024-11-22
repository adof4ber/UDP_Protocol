import struct
import zlib

class DataTransferProtocolAdo:
    PROTOCOL_NAME = "DTPA"
    HEADER_FORMAT = "!BHHH"  
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    MSG_TYPE_SYN = 0
    MSG_TYPE_SYN_ACK = 1
    MSG_TYPE_ACK = 2
    MSG_TYPE_DATA = 3
    MSG_TYPE_NACK = 4
    MSG_TYPE_KEEP_ALIVE = 5
    MSG_TYPE_KEEP_ALIVE_ACK = 6  # New message type for Keep-Alive ACK
    MSG_TYPE_FILE_METADATA = 7  
    MSG_TYPE_FILE_DATA = 8      
    MSG_TYPE_CLOSE_INIT = 9  
    MSG_TYPE_CLOSE_ACK = 10   
    MSG_TYPE_CLOSE_FINAL = 11
    MSG_TYPE_END = 12  

    @staticmethod
    def build_crc(payload):
        return zlib.crc32(payload) & 0xFFEF

    @staticmethod
    def build_frame(msg_type, fragment_id, total_fragments, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        crc = DataTransferProtocolAdo.build_crc(data)
        header = struct.pack(DataTransferProtocolAdo.HEADER_FORMAT, msg_type, fragment_id, total_fragments, crc)
        return header + data

    @staticmethod
    def parse_frame(frame):
        header = frame[:DataTransferProtocolAdo.HEADER_SIZE]
        msg_type, fragment_id, total_fragments, crc = struct.unpack(DataTransferProtocolAdo.HEADER_FORMAT, header)

        data = frame[DataTransferProtocolAdo.HEADER_SIZE:]

        if DataTransferProtocolAdo.build_crc(data) != crc:
            raise ValueError(f"CRC check failed: Data is corrupted (MsgType: {msg_type}, Fragment: {fragment_id}).")

        if msg_type in [DataTransferProtocolAdo.MSG_TYPE_FILE_METADATA, DataTransferProtocolAdo.MSG_TYPE_FILE_DATA]:
            return msg_type, fragment_id, total_fragments, data  

        return msg_type, fragment_id, total_fragments, data.decode("utf-8")

    @staticmethod
    def build_syn(sequence_number):
        data = f"SYN {sequence_number}"
        return DataTransferProtocolAdo.build_frame(DataTransferProtocolAdo.MSG_TYPE_SYN, sequence_number, 1, data)

    @staticmethod
    def build_syn_ack(sequence_number):
        data = f"SYN-ACK {sequence_number}"
        return DataTransferProtocolAdo.build_frame(DataTransferProtocolAdo.MSG_TYPE_SYN_ACK, sequence_number, 1, data)

    @staticmethod
    def build_ack(sequence_number):
        data = f"ACK {sequence_number}"
        return DataTransferProtocolAdo.build_frame(DataTransferProtocolAdo.MSG_TYPE_ACK, sequence_number, 1, data)
    
    @staticmethod
    def build_nack(sequence_number):
        data = f"NACK {sequence_number}"
        return DataTransferProtocolAdo.build_frame(DataTransferProtocolAdo.MSG_TYPE_NACK, sequence_number, 1, data)

    @staticmethod
    def build_keep_alive():
        return DataTransferProtocolAdo.build_frame(DataTransferProtocolAdo.MSG_TYPE_KEEP_ALIVE, 0, 1, "KEEP_ALIVE")

    @staticmethod
    def build_keep_alive_ack():
        return DataTransferProtocolAdo.build_frame(DataTransferProtocolAdo.MSG_TYPE_KEEP_ALIVE_ACK, 0, 1, "KEEP_ALIVE_ACK")  # New method for ACK

    @staticmethod
    def build_file_metadata(file_name, file_size):
        data = f"Metadata: {file_name}, {file_size}"
        return DataTransferProtocolAdo.build_frame(DataTransferProtocolAdo.MSG_TYPE_FILE_METADATA, 0, 1, data)

    @staticmethod
    def build_file_data(fragment_id, total_fragments, file_data):
        return DataTransferProtocolAdo.build_frame(DataTransferProtocolAdo.MSG_TYPE_FILE_DATA, fragment_id, total_fragments, file_data)

    @staticmethod
    def parse_file_metadata(frame):
        msg_type, _, _, data = DataTransferProtocolAdo.parse_frame(frame)
        if msg_type != DataTransferProtocolAdo.MSG_TYPE_FILE_METADATA:
            raise ValueError(f"Incorrect message type for file metadata. Expected {DataTransferProtocolAdo.MSG_TYPE_FILE_METADATA}, got {msg_type}.")
        metadata = data.decode("utf-8").split(", ")
        file_name = metadata[0].split(": ")[1]
        file_size = int(metadata[1])
        return file_name, file_size

    @staticmethod
    def parse_file_data(frame):
        msg_type, fragment_id, total_fragments, data = DataTransferProtocolAdo.parse_frame(frame)
        if msg_type != DataTransferProtocolAdo.MSG_TYPE_FILE_DATA:
            raise ValueError(f"Incorrect message type for file transfer. Expected {DataTransferProtocolAdo.MSG_TYPE_FILE_DATA}, got {msg_type}.")
        return fragment_id, total_fragments, data 

    @staticmethod
    def build_end():
        return DataTransferProtocolAdo.build_frame(DataTransferProtocolAdo.MSG_TYPE_END, 0, 1, "END")

    @staticmethod
    def parse_end(frame):
        msg_type, _, _, data = DataTransferProtocolAdo.parse_frame(frame)
        if msg_type != DataTransferProtocolAdo.MSG_TYPE_END:
            raise ValueError(f"Incorrect message type for end signal. Expected {DataTransferProtocolAdo.MSG_TYPE_END}, got {msg_type}.")
        return data == "END"

    @staticmethod
    def build_data(data):
        return DataTransferProtocolAdo.build_frame(DataTransferProtocolAdo.MSG_TYPE_DATA, 0, 1, data)

    @staticmethod
    def parse_data(frame):
        msg_type, _, _, data = DataTransferProtocolAdo.parse_frame(frame)
        if msg_type != DataTransferProtocolAdo.MSG_TYPE_DATA:
            raise ValueError(f"Incorrect message type for data. Expected {DataTransferProtocolAdo.MSG_TYPE_DATA}, got {msg_type}.")
        return data
