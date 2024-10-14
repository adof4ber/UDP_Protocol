import threading
import time
from connection import UDPConnection
from data_transfer import DataTransfer
from keep_alive import keep_alive
from handshake import handshake

def print_banner():
    banner = """
    ***************************************
    *                                     *
    *   Data Transfer Protocol Ado (DTPA) *
    *   Peer-to-Peer Communication Tool   *
    *                                     *
    ***************************************
    """
    print(banner)

def main():
    print_banner()

    listen_port = int(input("Number of port you want to listen on: "))
    target_ip = input("Destination IP address: ")
    target_port = int(input("Destination port: "))
    fragment_size = int(input("Set the fragment size (bytes): "))
    protocol_number = listen_port

    udp_connection = UDPConnection(listen_port)

    handshake_successful = [False]

    def handshake_thread():
        handshake_successful[0] = handshake(udp_connection, target_ip, target_port, protocol_number, target_port)

    threading.Thread(target=handshake_thread, daemon=True).start()

    while not handshake_successful[0]:
        time.sleep(1)

    print("Handshake completed. Ready for communication.")
    
    threading.Thread(target=keep_alive, args=(udp_connection, target_ip, target_port), daemon=True).start()

    data_transfer = DataTransfer(udp_connection, target_ip, target_port, fragment_size)

    threading.Thread(target=data_transfer.receive_message, daemon=True).start()

    while True:
        message = input("Enter your message (or 'q' to quit): ")
        if message.lower() == 'q':
            print("Closing connection...")
            break
        data_transfer.send_message(message)

if __name__ == "__main__":
    main()
