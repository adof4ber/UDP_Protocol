import threading
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
    connection_active = [True]  # Used to control when to stop listening

    def handshake_thread():
        handshake_successful[0] = handshake(udp_connection, target_ip, target_port, protocol_number, target_port)

    threading.Thread(target=handshake_thread, daemon=True).start()

    while not handshake_successful[0]:
        time.sleep(1)

    print("Handshake completed. Ready for communication.")
    
    threading.Thread(target=keep_alive, args=(udp_connection, target_ip, target_port), daemon=True).start()

    data_transfer = DataTransfer(udp_connection, target_ip, target_port, fragment_size)
    file_transfer = FileTransfer(udp_connection, target_ip, target_port, fragment_size)

    threading.Thread(
        target=handle_close_sequence,
        args=(udp_connection, target_ip, target_port, connection_active),
        daemon=True
    ).start()

    def receive_message_thread():
        data_transfer.receive_message()

    threading.Thread(target=receive_message_thread, daemon=True).start()

    while connection_active[0]:
        print("\nMenu:")
        print("1 - Send Message")
        print("2 - Send File")
        print("q - Quit Program")
        choice = input("Select an option: ")

        if choice == "1":
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
                    print("Returning to menu...")
                    break
                file_transfer.send_file(file_path)
        elif choice.lower() == 'q':
            print("Initiating close handshake...")
            close_handshake(udp_connection, target_ip, target_port)
            print("Close handshake initiated. Waiting for peer response...")
            while connection_active[0]:
                time.sleep(0.1)  
            break
        else:
            print("Invalid option. Please try again.")

    print("Exiting program. Goodbye.")

if __name__ == "__main__":
    main()
