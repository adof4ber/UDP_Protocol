import time
from protocol import DataTransferProtocolAdo

def keep_alive(connection, target_ip, target_port, connection_active):
    missed_responses = 0
    max_missed_responses = 3
    
    while connection_active[0]:
        keep_alive_frame = DataTransferProtocolAdo.build_keep_alive()
        connection.send(keep_alive_frame, (target_ip, target_port))
        
        response_received = False
        start_time = time.time()

        while time.time() - start_time < 5.5:
            frame, _ = connection.receive()
            if frame:
                try:
                    msg_type, _, _, _ = DataTransferProtocolAdo.parse_frame(frame)
                    if msg_type == DataTransferProtocolAdo.MSG_TYPE_KEEP_ALIVE:
                        response_received = True
                        break
                except Exception as e:
                    print(f"Error parsing frame: {e}")
 
        if not response_received:
            missed_responses += 1
        else:
            missed_responses = 0

        if missed_responses >= max_missed_responses:
            print("No KEEP_ALIVE messages, closing connection")
            connection_active[0] = False
            break

        elapsed = time.time() - start_time
        if elapsed < 5:
            time.sleep(5 - elapsed)