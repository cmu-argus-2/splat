"""
This will be the sat
"""

import os
import sys

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import socket
import threading
from splat.telemetry_codec import unpack, Command, Ack, pack
from splat.telemetry_definition import MAX_PACKET_SIZE
from splat.telemetry_helper import format_bytes
from splat.transport_layer import transaction_manager, Transaction


import time


HOST = "127.0.0.1"
PORT = 65432


# this will contain the packets (bytes) that should be transmitted
transmit_list = [] 
    

def process_command(cmd: Command):
    """
    Receives the command and will process it
    """    
    global transmit_list
    
    if cmd.name == "SUM":
        print(f"Received SUM command with arguments {cmd.arguments}")
        op1 = cmd.arguments.get("op1", 0)
        op2 = cmd.arguments.get("op2", 0)
        result = op1 + op2
        print(f"Result of SUM: {result}")
        return f"Result of SUM: {result}"

    if cmd.name == "CREATE_TRANS":
        file_path = cmd.arguments.get("string_command", None)
        tid = cmd.arguments.get("tid", None)
        # recieved a transaction request
        print(f"Received image request for: {file_path}")
        print(f"Transaction ID: {tid}")
        
        # 1. check if the file exists
        if not os.path.isfile(file_path):
            print(f"File {file_path} does not exist.")
            return False
        
        # 2. create transaction (manager handles tid allocation and registration)
        transaction = transaction_manager.create_transaction(file_path=file_path, tid=tid, is_tx=True)
        if transaction is None:
            print("Could not create transaction (max transactions reached).")
            return False
        
        print(f"Created transaction with id {tid} for file {file_path} and number of packets {transaction.number_of_packets}")
        
        #5.  convert transaction to INIT stage command
        transaction.change_state(2)
        
        #6. generate command to send back (transaction init command)
        cmd = Command("INIT_TRANS")
        cmd.set_arguments(tid=tid, number_of_packets=transaction.number_of_packets)
        hash_MSB, hash_middlesb, hash_LSB = transaction.get_hash_as_integers()
        cmd.set_arguments(hash_MSB=hash_MSB, hash_middlesb=hash_middlesb, hash_LSB=hash_LSB)
        
        transmit_list.append(pack(cmd))   # add the transaction to the transmit list, this will be used by the transport layer to know which files to send and how to split them into packets
        print(f"Added INIT_trans command to transmit list for transaction id {tid}")
        print(f"  {format_bytes(pack(cmd))}")
        
        #4. now i should respond back with ack
        return [cmd.command_id, tid]   # this is the data that will be sent back with the ack
    
    if cmd.name == "GENERATE_ALL_PACKETS":
        tid = cmd.arguments.get("tid", None)
        print(f"Received GENERATE_ALL_PACKETS command for transaction id {tid}")
        
        # get the transaction from the manager
        transaction = transaction_manager.get_transaction(tid)
        
        if transaction is None:
            # we were not able to find the transaction
            print(f"Transaction with id {tid} not found.")
            return False
        
        # change the state to 
        transaction.change_state(3)   # change the state to sending
        
        packet_list = transaction.generate_all_packets()   # generate the packet list for this transaction and add it to the transmit list
        transmit_list.extend(packet_list)
        print(f"Added {len(packet_list)} packets to transmit list for transaction id {tid}")
        
        # from this point on we will have a bunch of packets to send
        # lets switch the state of the transaction
        transaction.change_state(4)
        return "hello"
    
    if cmd.name == "GENERATE_X_PACKETS":
        tid = cmd.arguments.get("tid", None)
        x = cmd.arguments.get("x", None)
        print(f"Received GENERATE_X_PACKETS command for transaction id {tid} and x {x}")
        
        transaction = transaction_manager.get_transaction(tid)
        if transaction is None:
            print(f"Transaction with id {tid} not found.")
            return False
        
        packet_list = transaction.generate_x_packets(x)
        transmit_list.extend(packet_list)
        print(f"Added {len(packet_list)} packets to transmit list for transaction id {tid}")
        return f"Generated {len(packet_list)} packets for transaction id {tid} and x {x}"
        
    
    if cmd.name == "GET_SINGLE_PACKET":
        # receiver is asking for a single specific packet
        tid = cmd.arguments.get("tid", None)
        seq_number = cmd.arguments.get("seq_number", None)
        
        print(f"Received GET_SINGLE_PACKET command for transaction id {tid} and sequence number {seq_number}")
        
        transaction = transaction_manager.get_transaction(tid)
        if transaction is None:
            print(f"Transaction with id {tid} not found.")
            return False
        
        packet = transaction.generate_specific_packet(seq_number)
        transmit_list.append(packet)
        return f"Packet generated for transaction {tid} and sequence number {seq_number}"
        

def process_packet(data: bytes) -> str:
    """
    Will receive the raw bytes from the client and process them
    """
    
    unpacked_data = unpack(data)
    
    if isinstance(unpacked_data, Command):
        print(f"Received command: {unpacked_data.name} with arguments {unpacked_data.arguments}")
        response = process_command(unpacked_data)
        print(f" Response: {response}")

        return response
    else:
        print("Received unknown data format")
        return "Unknown data format"


def handle_client(conn, addr):
    """Handles a single client connection."""
    print(f"[NEW CONNECTION] {addr} connected.")
    
    connected = True
    while connected:
        try:
            # Wait for data (blocking call)
            data = conn.recv(1024)

            if not data:
                # If recv returns empty bytes, the client disconnected
                break

            print(f"[{addr}] Raw bytes: {format_bytes(data)}")

            
            response = process_packet(data)
            # generate ack packet
            # hard code response status at 0, does not matter for this example
            ack = Ack(0, response) # assuming that the command status is always 1 for now
            transmit_list.append(pack(ack))   # add the ack to the transmit list, this will be sent back to the client in the next iteration of the loop
            

            # check to see if there is anything to send
            while(len(transmit_list) > 0):
                # print(f"Transmitting packet to {addr}: {format_bytes(transmit_list[0])}")
                packet = transmit_list.pop(0)
                conn.send(packet)
                time.sleep(0.05)   # add a small delay to avoid overwhelming the client with packets
            

        except ConnectionResetError:
            break

    conn.close()
    print(f"[DISCONNECTED] {addr} disconnected.")

def start():
    """Starts the server and listens for connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow port reuse immediately after closing (avoids "Address already in use" errors)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")
    
    while True:
        # Accept new connection
        conn, addr = server.accept()
        
        # Create a new thread to handle this specific client
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        
        # Print active connections (subtract 1 for main thread)
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start()