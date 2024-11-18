import threading
import socket
import time
from connection import UDPConnection
from protocol import DataTransferProtocolAdo
from data_transfer import DataTransfer
from file_transfer import FileTransfer
from keep_alive import keep_alive
from handshake import handshake
from handshake_close import close_handshake, handle_close_sequence

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
    
    threading.Thread(target=keep_alive, args=(udp_connection, target_ip, target_port, connection_active), daemon=True).start()


    data_transfer = DataTransfer(udp_connection, target_ip, target_port, fragment_size)
    file_transfer = FileTransfer(udp_connection, target_ip, target_port, fragment_size)

    threading.Thread(
        target=handle_close_sequence,
        args=(udp_connection, target_ip, target_port, connection_active),
        daemon=True
    ).start()

    def listen_for_messages():
        while connection_active[0]:
            data_transfer.receive_message()

    def data_transfer_menu():
        while connection_active[0]:
            print("\nMenu:")
            print("1 - Send Message")
            print("2 - Send File")
            print("q - Quit Program")
            choice = input("Select an option: ")

            if choice == "1":
                threading.Thread(target=listen_for_messages, daemon=True).start()
                while True:
                    message = input("Enter your message (or 'q' to return to menu): ")
                    if message.lower() == 'q':
                        print("Returning to menu...")
                        break
                    data_transfer.send_message(message)
            elif choice == "2":
                while True:
                    file_path = input("Enter file path to send (or 'q' to return to menu): ")
                    if file_path.lower() == 'q':
                        print("Returning to menu")
                        break
                    file_transfer.send_file(file_path)
            elif choice.lower() == 'q':
                print("Initiating close handshake")
                close_handshake(udp_connection, target_ip, target_port)
                print("Sending CLOSE_INIT")
                while connection_active[0]:
                    time.sleep(0.1)  
                break
            else:
                print("Invalid option. Please try again.")

    data_transfer_thread = threading.Thread(target=data_transfer_menu, daemon=True)
    data_transfer_thread.start()

    try:
        while connection_active[0]:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting program.")

    data_transfer_thread.join()

    print("Goodbye.")

if __name__ == "__main__":
    main()
