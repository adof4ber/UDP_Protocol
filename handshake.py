import time
from protocol import DataTransferProtocolAdo

def handshake(connection, target_ip, target_port, my_protocol_number, their_protocol_number):
    sequence_number = 1  

    if my_protocol_number < their_protocol_number:
        while True:
            syn_frame = DataTransferProtocolAdo.build_syn(sequence_number)
            connection.send(syn_frame, (target_ip, target_port))
            print(f"[Handshake] Sent SYN message {sequence_number}, waiting for SYN-ACK...")

            try:
                response, _ = connection.receive()
                if response is None:
                    continue
                
                msg_type, _, _, data = DataTransferProtocolAdo.parse_frame(response)

                if msg_type == DataTransferProtocolAdo.MSG_TYPE_SYN_ACK and data == f"SYN-ACK {sequence_number}":
                    print("[Handshake] Received SYN-ACK, sending ACK...")
                    ack_frame = DataTransferProtocolAdo.build_ack(sequence_number)
                    connection.send(ack_frame, (target_ip, target_port))
                    print(f"[Handshake] Sent ACK message {sequence_number}, connection established!")
                    return True
            except Exception as e:
                print(f"[Handshake] No response received, retrying...: {e}")

            time.sleep(3)  

    else:
        while True:
            try:
                response, _ = connection.receive()
                if response is None:
                    continue
                
                msg_type, _, _, data = DataTransferProtocolAdo.parse_frame(response)

                if msg_type == DataTransferProtocolAdo.MSG_TYPE_SYN and data == f"SYN {sequence_number}":
                    print("[Handshake] Received SYN, sending SYN-ACK...")
                    syn_ack_frame = DataTransferProtocolAdo.build_syn_ack(sequence_number)
                    connection.send(syn_ack_frame, (target_ip, target_port))

                    response, _ = connection.receive()
                    if response is None:
                        continue
                    
                    msg_type, _, _, data = DataTransferProtocolAdo.parse_frame(response)

                    if msg_type == DataTransferProtocolAdo.MSG_TYPE_ACK and data == f"ACK {sequence_number}":
                        print("[Handshake] Received ACK, connection established!")
                        return True
            except Exception as e:
                print(f"[Handshake] No response received, retrying...: {e}")

            time.sleep(3)  

    return False  