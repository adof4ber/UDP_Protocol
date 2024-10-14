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
    MSG_TYPE_ACK_NACK = 4
    MSG_TYPE_KEEP_ALIVE = 5

    @staticmethod
    def build_crc(payload):
        return zlib.crc32(payload) & 0xFFFF

    @staticmethod
    def build_frame(msg_type, fragment_id, total_fragments, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        crc = DataTransferProtocolAdo.build_crc(data)
        header = struct.pack(DataTransferProtocolAdo.HEADER_FORMAT, msg_type, fragment_id, total_fragments, crc)
        return header + data  

    @staticmethod
    def parse_frame(frame):
        header = frame[:DataTransferProtocolAdo.HEADER_SIZE]
        msg_type, fragment_id, total_fragments, crc = struct.unpack(DataTransferProtocolAdo.HEADER_FORMAT, header)

        data = frame[DataTransferProtocolAdo.HEADER_SIZE:]

        if DataTransferProtocolAdo.build_crc(data) != crc:
            raise ValueError("CRC check failed: Data is corrupted.")
        
        return msg_type, fragment_id, total_fragments, data.decode('utf-8') 

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
    def build_keep_alive():
        return DataTransferProtocolAdo.build_frame(DataTransferProtocolAdo.MSG_TYPE_KEEP_ALIVE, 0, 1, "KEEP_ALIVE")
