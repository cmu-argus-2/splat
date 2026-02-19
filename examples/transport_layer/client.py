"""
Lets change this to send a command instead of a normal message

this will be the GS
"""

import os
import sys


# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import socket
import time

from splat.telemetry_codec import Command, pack, unpack, Ack
from splat.telemetry_helper import format_bytes
from splat.telemetry_definition import COMMAND_IDS, MAX_PACKET_SIZE

from splat.transport_layer import transaction_manager, Transaction

HOST = "127.0.0.1"
PORT = 65432


transmit_list = []   # this will contain the packets (bytes) that should be transmitted, this will be used by the transport layer to know which files to send and how to split them into packets



def generate_dump_packet(tid):
    cmd = Command("GENERATE_ALL_PACKETS")
    cmd.set_arguments(tid=tid)
    return cmd



def process_command(cmd):
    global transmit_list
    if not isinstance(cmd, Command):
        print(f"[ERROR][COMMAND RECEIVED] Command: {cmd} is not a command")
        return
    
    if cmd.name == "INIT_TRANS":
        print(f"[INIT_TRANS RECEIVED] Command: {cmd}")
        
        #1. create the transaction on the client side using tid from server
        tid = cmd.get_argument("tid")
        number_of_packets = cmd.get_argument("number_of_packets")
        hash_MSB = cmd.get_argument("hash_MSB")
        hash_middlesb = cmd.get_argument("hash_middlesb")
        hash_LSB = cmd.get_argument("hash_LSB")
        file_hash = hash_MSB.to_bytes(8, byteorder='big') + hash_middlesb.to_bytes(8, byteorder='big') + hash_LSB.to_bytes(4, byteorder='big')
        
        trans = transaction_manager.create_transaction(tid=tid, file_hash=file_hash, number_of_packets=number_of_packets, is_tx=False)
        if trans is None:
            print(f"[ERROR] Could not create transaction for INIT_TRANS")
            return
        
        # change the state of the transaction to Init
        trans.change_state(2)
        
        #2. generate the dump command and add it to the transmit list
        cmd = generate_dump_packet(tid)
        transmit_list.append(pack(cmd))

        
        print(f"[COMMAND PROCESSED] Generated GENERATE_ALL_PACKETS command for transaction id {tid} and added to transmission list")
        print(f"  {format_bytes(pack(cmd))}")
        return
    
    if cmd.name == "TRANS_PAYLOAD":

        tid = cmd.get_argument("tid")
        seq_number = cmd.get_argument("seq_number")
        payload_frag = cmd.get_argument("payload_frag")
        transaction = transaction_manager.get_transaction(tid)
        if transaction is None:
            print(f"[ERROR] Transaction with id {tid} not found.")
            return
        isCompleted = transaction.add_packet(seq_number, payload_frag)
        print(f"[COMMAND PROCESSED] Added payload fragment for transaction id {tid} with sequence number {seq_number} to transaction")
        if isCompleted:
            print(f"[INFO] Transaction {tid} has received all packets. Writing file to disk.")
            transaction.write_file("received_image.jpg")
        return
        
    
def start_client():
    try:
        # Create socket and connect
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        print(f"[CONNECTED] Connected to server at {HOST}:{PORT}")
        return client
    except Exception as e:
        print(f"[ERROR] Could not connect to server: {e}")
        return None
    
def program_loop(client):
    # Send the command to request the image
    image_name = "image_test.jpg"
    cmd = Command("CREATE_TRANS")
    cmd.set_arguments(string_command=image_name)
    packed_cmd = pack(cmd)
    client.sendall(packed_cmd)
    print(f"[SENT] Sent command to request image: {image_name}")
        
        
    while True:
        # wait for ack
        data = client.recv(1024*12)
        # print(f"[RECEIVED] Received data: {format_bytes(data)}")

        unpacked = unpack(data)
        print(f"[UNPACKED] Unpacked data: {unpacked}")
        if isinstance(unpacked, Ack):
            print(f"[ACK RECEIVED] Acknowledgement: {unpacked}")
        elif isinstance(unpacked, Command):
            print(f"[COMMAND RECEIVED] Command: {unpacked}")
            process_command(unpacked)
        else:
            print(f"[ERROR] unknown type received: {type(unpacked)} {unpacked}")

        while len( transmit_list) > 0:
            packet = transmit_list.pop(0)
            client.sendall(packet)
            print(f"[SENT] Sent packet from transmission list: {format_bytes(packet)}")
            

def single_packet_loop(client):
    """
    In this function will implement the logic to get a single packet at a time
    
    will create the transaction
    for each packet in the missing fragments list
        will generate the packet and send it
        will wait for the server to send and packet, process it and move to the next one
    """
    # Send the command to request the image
    image_name = "image_test.jpg"
    cmd = Command("CREATE_TRANS")
    cmd.set_arguments(string_command=image_name)
    packed_cmd = pack(cmd)
    client.sendall(packed_cmd)
    print(f"[SENT] Sent command to request image: {image_name}")
    
    
    # wait for the server to send init message
    data = client.recv(1024)
    unpacked = unpack(data)
    if isinstance(unpacked, Command) and unpacked.name == "INIT_TRANS":
        print(f"[INIT_TRANS RECEIVED] Command: {unpacked}")
        
        # create the transaction on the client side using tid from server
        tid = unpacked.get_argument("tid")
        number_of_packets = unpacked.get_argument("number_of_packets")
        hash_MSB = unpacked.get_argument("hash_MSB")
        hash_middlesb = unpacked.get_argument("hash_middlesb")
        hash_LSB = unpacked.get_argument("hash_LSB")
        file_hash = hash_MSB.to_bytes(8, byteorder='big') + hash_middlesb.to_bytes(8, byteorder='big') + hash_LSB.to_bytes(4, byteorder='big')
        transaction = transaction_manager.create_transaction(tid=tid, file_hash=file_hash, number_of_packets=number_of_packets, is_tx=False)
        if transaction is None:
            print(f"[ERROR] Could not create transaction for INIT_TRANS")
            return
    else:
        print(f"[ERROR] Expected INIT_TRANS command, but received: {unpacked}")
        return
    
    # now we have the transaction created, lets start asking for the packets one by one
    while(len(transaction.missing_fragments) > 0):
        seq_number = transaction.missing_fragments[0]   # get the first missing fragment number
        
        cmd = Command("GET_SINGLE_PACKET")
        cmd.set_arguments(tid=tid, seq_number=seq_number)
        packed_cmd = pack(cmd)
        
        client.sendall(packed_cmd)
        print(f"[SENT] Sent GET_SINGLE_PACKET command for transaction id {tid} and sequence number {seq_number}")
        
        received_packet = False
        timeout = time.time() + 30  # 30 second timeout
        while not received_packet and time.time() < timeout:
            data = client.recv(1024)
            unpacked = unpack(data)

            # i am looking for a trans payload command with whatever seq_number, ideally the one i requested
            if isinstance(unpacked, Command) and unpacked.name == "TRANS_PAYLOAD":
                received_tid = unpacked.get_argument("tid")
                received_seq_number = unpacked.get_argument("seq_number")
                payload_frag = unpacked.get_argument("payload_frag")
                
                if received_tid != tid:
                    print(f"[ERROR] Received packet with tid {received_tid} but expected {tid}")
                    continue

                # if i am here, it means i got the packet i was expecting
                transaction.add_packet(received_seq_number, payload_frag)
                print(f"[RECEIVED] Received packet for transaction id {tid} and sequence number {received_seq_number}")
                received_packet = True
                
        if not received_packet:
            print(f"[ERROR] Did not receive packet for transaction id {tid} and sequence number {seq_number} within timeout")
            
    
    # ideally here the transmission has finished
    if transaction.is_completed():
        print(f"[INFO] Transaction {tid} has received all packets. Writing file to disk.")
        transaction.write_file("received_image.jpg")
    else:
        print(f"[ERROR] Transaction {tid} is not complete, missing fragments: {transaction.missing_fragments}")


def single_packet_and_dump_loop(client):
    """
    This will test the single packet and the dump feature all at the same time time
    
    it will start by reqeusting the image and creating the transaction when the init message is received
    
    it will proceed to ask for the first 10 packets like the single packet loop.
    
    it will then send the message to add_received_list with the fragments that have been received
    
    it will then send the dump comamnd to get the missing packets
    
    ideally will not sent the packets that have already been received
    """
    
    # Send the command to request the image
    image_name = "image_test.jpg"
    cmd = Command("CREATE_TRANS")
    cmd.set_arguments(string_command=image_name)
    packed_cmd = pack(cmd)
    client.sendall(packed_cmd)
    print(f"[SENT] Sent command to request image: {image_name}")
    
    # Wait for the server to send init message
    data = client.recv(1024)
    unpacked = unpack(data)
    if isinstance(unpacked, Command) and unpacked.name == "INIT_TRANS":
        print(f"[INIT_TRANS RECEIVED] Command: {unpacked}")
        
        # Create the transaction on the client side using tid from server
        tid = unpacked.get_argument("tid")
        number_of_packets = unpacked.get_argument("number_of_packets")
        hash_MSB = unpacked.get_argument("hash_MSB")
        hash_middlesb = unpacked.get_argument("hash_middlesb")
        hash_LSB = unpacked.get_argument("hash_LSB")
        file_hash = hash_MSB.to_bytes(8, byteorder='big') + hash_middlesb.to_bytes(8, byteorder='big') + hash_LSB.to_bytes(4, byteorder='big')
        transaction = transaction_manager.create_transaction(tid=tid, file_hash=file_hash, number_of_packets=number_of_packets, is_tx=False)
        if transaction is None:
            print(f"[ERROR] Could not create transaction for INIT_TRANS")
            return
    else:
        print(f"[ERROR] Expected INIT_TRANS command, but received: {unpacked}")
        return
    
    # Request first 10 packets individually using single packet loop logic
    packets_requested = 0
    while packets_requested < 10 and len(transaction.missing_fragments) > 0:
        seq_number = transaction.missing_fragments[0]
        
        cmd = Command("GET_SINGLE_PACKET")
        cmd.set_arguments(tid=tid, seq_number=seq_number)
        packed_cmd = pack(cmd)
        
        client.sendall(packed_cmd)
        print(f"[SENT] Sent GET_SINGLE_PACKET for seq {seq_number}")
        
        # Wait for packet with timeout
        received_packet = False
        timeout = time.time() + 30  # 30 second timeout
        while not received_packet and time.time() < timeout:
            data = client.recv(1024)
            unpacked = unpack(data)
            
            if isinstance(unpacked, Command) and unpacked.name == "TRANS_PAYLOAD":
                received_tid = unpacked.get_argument("tid")
                received_seq_number = unpacked.get_argument("seq_number")
                payload_frag = unpacked.get_argument("payload_frag")
                
                if received_tid != tid:
                    print(f"[WARNING] Received packet for different transaction {received_tid}, ignoring")
                    continue
                
                transaction.add_packet(received_seq_number, payload_frag)
                print(f"[RECEIVED] Received packet seq {received_seq_number} for transaction {tid}")
                received_packet = True
                packets_requested += 1
        
        if not received_packet:
            print(f"[ERROR] Timeout waiting for packet seq {seq_number}")
            break

    breakpoint()
    
    # Now send GENERATE_ALL_PACKETS to get all remaining packets at once
    print(f"[INFO] Requested {packets_requested} packets individually. Now requesting all remaining packets with GENERATE_ALL_PACKETS")
    cmd = Command("GENERATE_ALL_PACKETS")
    cmd.set_arguments(tid=tid)
    packed_cmd = pack(cmd)
    
    client.sendall(packed_cmd)
    print(f"[SENT] Sent GENERATE_ALL_PACKETS command for transaction id {tid}")
    
    # Receive all remaining packets
    timeout = time.time() + 60  # 60 second timeout for bulk transfer
    while len(transaction.missing_fragments) > 0 and time.time() < timeout:
        data = client.recv(1024)
        unpacked = unpack(data)
        
        if isinstance(unpacked, Command) and unpacked.name == "TRANS_PAYLOAD":
            received_tid = unpacked.get_argument("tid")
            received_seq_number = unpacked.get_argument("seq_number")
            payload_frag = unpacked.get_argument("payload_frag")
            
            if received_tid != tid:
                print(f"[WARNING] Received packet for different transaction {received_tid}, ignoring")
                continue
            
            transaction.add_packet(received_seq_number, payload_frag)
            print(f"[RECEIVED] Received packet seq {received_seq_number} for transaction {tid}")
    
    # Check if transaction is complete
    if transaction.is_completed():
        print(f"[INFO] Transaction {tid} has received all packets. Writing file to disk.")
        transaction.write_file("received_image.jpg")
    else:
        print(f"[ERROR] Transaction {tid} is not complete, missing fragments: {transaction.missing_fragments}")
        
    
        
        
if __name__ == "__main__":
    client = start_client()
    if client:
        # program_loop(client)
        # single_packet_loop(client)
        single_packet_and_dump_loop(client)
        breakpoint()