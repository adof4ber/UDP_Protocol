import threading
import socket
import time
from connection import UDPConnection
from protocol import DataTransferProtocolAdo
from data_transfer import DataTransfer
from file_transfer import FileTransfer
from keep_alive import KeepAlive
from handshake import handshake
from handshake_close import close_handshake

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
    save_directory = input("Directory to save received files: ")
    protocol_number = listen_port

    udp_connection = UDPConnection(listen_port)

    handshake_successful = [False]
    connection_active = [True]

    def handshake_thread():
        handshake_successful[0] = handshake(udp_connection, target_ip, target_port, protocol_number, target_port)

    threading.Thread(target=handshake_thread, daemon=True).start()

    while not handshake_successful[0]:
        time.sleep(1)

    print("Handshake completed. Ready for communication.")

    data_transfer = DataTransfer(udp_connection, target_ip, target_port, fragment_size)
    file_transfer = FileTransfer(udp_connection, target_ip, target_port, fragment_size, save_directory)

    keep_alive_thread = KeepAlive(udp_connection, target_ip, target_port, connection_active)
    keep_alive_thread.start()

    def listen_for_messages():
        while connection_active[0]:
            message = data_transfer.receive_message()
            if message:
                print(f"Received message: {message}")

    def listen_for_file():
        while connection_active[0]:
            file_data = file_transfer.receive_file()  
            if file_data:
                print("Received file data. Saving file...")

    while connection_active[0]:
        print("\nMenu:")
        print("1 - Send Message")
        print("2 - Send File")
        print("q - Quit Program")
        choice = input("Select an option: ")

        if choice == "1":
            threading.Thread(target=listen_for_messages, daemon=True).start()
            while connection_active[0]:
                message = input("Enter your message (or 'q' to return to menu): ")
                if message.lower() == 'q':
                    print("Returning to menu...")
                    break
                threading.Thread(target=data_transfer.send_message, args=(message,), daemon=True).start()
        elif choice == "2":
            threading.Thread(target=listen_for_file, daemon=True).start()
            while connection_active[0]:
                file_path = input("Enter file path to send (or 'q' to return to menu): ")
                if file_path.lower() == 'q':
                    print("Returning to menu")
                    break
                threading.Thread(target=file_transfer.send_file, args=(file_path,), daemon=True).start()
        elif choice.lower() == 'q':
            print("Initiating close handshake")
            threading.Thread(target=close_handshake, args=(udp_connection, target_ip, target_port, connection_active), daemon=True).start()
            while connection_active[0]: 
                time.sleep(0.1)
            break
        else:
            print("Invalid option. Please try again.")

    print("Goodbye.")

if __name__ == "__main__":
    main()
