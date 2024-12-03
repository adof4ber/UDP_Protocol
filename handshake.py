import time
from protocol import DataTransferProtocolAdo

def handshake(connection, target_ip, target_port, my_protocol_number, their_protocol_number):
    sequence_number = 1  

    print("[Connection] Attempting to establish connection...")
    
    keep_alive_frame = DataTransferProtocolAdo.build_keep_alive()
    connection.send(keep_alive_frame, (target_ip, target_port))
    
    try:
        start_time = time.time()
        while time.time() - start_time < 3:  
            response = connection.receive()  
            if response:
                msg_type, _, _, _ = DataTransferProtocolAdo.parse_frame(response[0]) if response[0] else (None, None, None, None)
                if msg_type == DataTransferProtocolAdo.MSG_TYPE_KEEP_ALIVE_ACK:
                    print("[Connection] Connection successfully re-established with KEEP ALIVE.")
                    return True
    except Exception as e:
        print(f"[Connection] No KEEP ALIVE response: {e}")

    print("[Connection] KEEP ALIVE failed, initiating handshake...")

    if my_protocol_number < their_protocol_number:
        while True:
            syn_frame = DataTransferProtocolAdo.build_syn(sequence_number)
            connection.send(syn_frame, (target_ip, target_port))

            try:
                response = connection.receive()
                if response:
                    msg_type, _, _, data = DataTransferProtocolAdo.parse_frame(response[0]) if response[0] else (None, None, None, None)
                    if msg_type == DataTransferProtocolAdo.MSG_TYPE_SYN_ACK and data == f"SYN-ACK {sequence_number}":
                        ack_frame = DataTransferProtocolAdo.build_ack(sequence_number)
                        connection.send(ack_frame, (target_ip, target_port))
                        print(f"[Handshake] Connection established via handshake.")
                        return True
            except Exception as e:
                print(f"[Handshake] No response, retrying...: {e}")

            time.sleep(3)

    else:
        while True:
            try:
                response = connection.receive()
                if response:
                    msg_type, _, _, data = DataTransferProtocolAdo.parse_frame(response[0]) if response[0] else (None, None, None, None)
                    if msg_type == DataTransferProtocolAdo.MSG_TYPE_SYN and data == f"SYN {sequence_number}":
                        syn_ack_frame = DataTransferProtocolAdo.build_syn_ack(sequence_number)
                        connection.send(syn_ack_frame, (target_ip, target_port))

                        response = connection.receive()
                        if response:
                            msg_type, _, _, data = DataTransferProtocolAdo.parse_frame(response[0]) if response[0] else (None, None, None, None)
                            if msg_type == DataTransferProtocolAdo.MSG_TYPE_ACK and data == f"ACK {sequence_number}":
                                print("[Handshake] Connection established via handshake.")
                                return True
            except Exception as e:
                print(f"[Handshake] No response, retrying...: {e}")

            time.sleep(3)

    return False
