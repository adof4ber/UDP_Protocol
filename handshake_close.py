import time
from protocol import DataTransferProtocolAdo

def close_handshake(udp_connection, target_ip, target_port, connection_active):
    close_init_frame = DataTransferProtocolAdo.build_frame(
        DataTransferProtocolAdo.MSG_TYPE_CLOSE_INIT, 0, 1, "CLOSE_INIT"
    )
    udp_connection.send(close_init_frame, (target_ip, target_port))
    print("Sent CLOSE_INIT")

    # Tu spustíme sekvenciu na uzatvorenie spojenia
    handle_close_sequence(udp_connection, target_ip, target_port, connection_active)

def send_close_ack(udp_connection, sender_address):
    close_ack_frame = DataTransferProtocolAdo.build_frame(
        DataTransferProtocolAdo.MSG_TYPE_CLOSE_ACK, 0, 1, "CLOSE_ACK"
    )
    udp_connection.send(close_ack_frame, sender_address)
    print(f"Sent CLOSE_ACK to {sender_address}")

def send_close_final(udp_connection, target_ip, target_port):
    close_final_frame = DataTransferProtocolAdo.build_frame(
        DataTransferProtocolAdo.MSG_TYPE_CLOSE_FINAL, 0, 1, "CLOSE_FINAL"
    )
    udp_connection.send(close_final_frame, (target_ip, target_port))
    print("Sent CLOSE_FINAL")

def handle_close_sequence(udp_connection, target_ip, target_port, connection_active):
    while connection_active[0]:
        try:
            frame, sender_address = udp_connection.receive()
            if frame is None:
                continue

            msg_type, _, _, _ = DataTransferProtocolAdo.parse_frame(frame)
            print(f"Received message type: {msg_type} from {sender_address}")

            if msg_type == DataTransferProtocolAdo.MSG_TYPE_CLOSE_INIT:
                print("Received CLOSE_INIT. Sending CLOSE_ACK.")
                send_close_ack(udp_connection, sender_address)
            elif msg_type == DataTransferProtocolAdo.MSG_TYPE_CLOSE_ACK:
                print("Received CLOSE_ACK. Sending CLOSE_FINAL.")
                send_close_final(udp_connection, target_ip, target_port)
                print("Closing connection in response to CLOSE_ACK.")
                time.sleep(2)  
                connection_active[0] = False
            elif msg_type == DataTransferProtocolAdo.MSG_TYPE_CLOSE_FINAL:
                print("Received CLOSE_FINAL. Closing connection.")
                connection_active[0] = False
        except Exception as e:
            print(f"Error handling close handshake frame: {e}")
