import time
from protocol import DataTransferProtocolAdo

def close_handshake(udp_connection, target_ip, target_port):
    close_init_frame = DataTransferProtocolAdo.build_frame(
        DataTransferProtocolAdo.MSG_TYPE_CLOSE_INIT, 0, 1, "CLOSE_INIT"
    )
    udp_connection.send(close_init_frame, (target_ip, target_port))

def send_close_ack(udp_connection, sender_address):
    close_ack_frame = DataTransferProtocolAdo.build_frame(
        DataTransferProtocolAdo.MSG_TYPE_CLOSE_ACK, 0, 1, "CLOSE_ACK"
    )
    udp_connection.send(close_ack_frame, sender_address)

def send_close_final(udp_connection, target_ip, target_port):
    close_final_frame = DataTransferProtocolAdo.build_frame(
        DataTransferProtocolAdo.MSG_TYPE_CLOSE_FINAL, 0, 1, "CLOSE_FINAL"
    )
    udp_connection.send(close_final_frame, (target_ip, target_port))

def handle_close_sequence(udp_connection, target_ip, target_port, connection_active):
    while connection_active[0]:
        frame, sender_address = udp_connection.receive()
        if frame is None:
            continue

        try:
            msg_type, _, _, _ = DataTransferProtocolAdo.parse_frame(frame)

            if msg_type == DataTransferProtocolAdo.MSG_TYPE_CLOSE_INIT:
                print("Received CLOSE_INIT. Sending CLOSE_ACK...")
                send_close_ack(udp_connection, sender_address)
            elif msg_type == DataTransferProtocolAdo.MSG_TYPE_CLOSE_ACK:
                print("Received CLOSE_ACK. Sending CLOSE_FINAL...")
                send_close_final(udp_connection, target_ip, target_port)
                print("CLOSE_FINAL sent. Waiting 0.5 seconds before closing connection.")
                time.sleep(2)  
                connection_active[0] = False
            elif msg_type == DataTransferProtocolAdo.MSG_TYPE_CLOSE_FINAL:
                print("Received CLOSE_FINAL. Closing connection.")
                connection_active[0] = False

        except Exception as e:
            print(f"Error handling close handshake frame: {e}")

