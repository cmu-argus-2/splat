import os
import time
import hashlib


from .telemetry_codec import Command, pack, unpack, Ack, Fragment
from .telemetry_definition import MAX_PACKET_SIZE
from .telemetry_helper import format_bytes


class trans_state():
    REQUESTED = 1     # this is the default state when transaction is created. The transaction is created when the GS or SAT receive 
    INIT = 2          # after receiving the transaction request, the transmitter will check if the file exists, create the transaction and send init trans information
    SENDING = 3       # this will be the state after at least one fragment has been requested for sending
    RECEIVING = 4     # this will be the state after at least one fragment has been received
    COMPLETED = 5     # this will be the state after all the fragments have been received
    SUCCESS = 6       # this will be the state after all the fragments have been received and the file has been written to disk and verified successfully
    FAILED = 7        # this will be the state if the transaction has failed for any reason, such as hash verification failure, timeout, etc. 

# Separate dictionaries for RX (receiving) and TX (transmitting) transactions
rx_dict = {}  # Client-side: transactions for receiving files
tx_dict = {}  # Server-side: transactions for sending files


class TransactionManager:
    """
    Centralized manager for all transactions across the satellite/ground station system.
    
    Responsibilities:
    - Generate and allocate transaction IDs (0-7, max 8 transactions)
    - Create, retrieve, and delete transactions
    - Filter transactions by state
    - Provide statistics and visibility into active transactions
    - Maintain transaction lifecycle
    
    Manages separate rx_dict (receiving) and tx_dict (transmitting) for client and server.
    """
    
    MAX_TRANSACTIONS = 8
    
    def __init__(self):
        """Initialize the transaction manager (singleton pattern)"""
        self.rx_dict = rx_dict  # Client-side receiving transactions
        self.tx_dict = tx_dict  # Server-side transmitting transactions
    
    def create_transaction(self, tid: int = None, file_path: str = None, file_hash: bytes = None, number_of_packets: int = None, is_tx: bool = None):
        """
        Create a new transaction and allocate it a tid.
        
        Args:
            tid: Transaction ID (required for the TX side, will be set by RX side)
            file_path: Path to file (necessary on both sides)
            file_hash: Hash of file (currently disabled, does not make sense for sending images and files)
            number_of_packets: Number of packets (On the rx side this will only be set after init transaction)
            is_tx: True for TX dict (server), False for RX dict (client).
        
        Returns:
            Transaction object if successful, None if max transactions exceeded
        """
        
        target_dict = self.tx_dict if is_tx else self.rx_dict
        dict_name = "TX" if is_tx else "RX"
        
        # For RX side (client), tid must be provided by server
        if is_tx and tid is None:
            print(f"[ERROR] TX transaction creation requires tid from server INIT_TRANS message.")
            return None
        
        # For TX side (server), allocate tid if not provided
        if not is_tx and tid is None:
            if len(target_dict) >= self.MAX_TRANSACTIONS:
                print(f"[ERROR] Maximum number of {dict_name} transactions ({self.MAX_TRANSACTIONS}) reached.")
                return None
            tid = min(set(range(self.MAX_TRANSACTIONS)) - set(target_dict.keys()))
        
        # In tx side if the tid already exists overwrite it
        if tid in target_dict:
            print(f"[INFO] Overwriting existing TX transaction with tid={tid}")
            # [check] - it would be good to return that it has been overwritten in the ack from the command
            del target_dict[tid]
        
        # Create the transaction
        trans = Transaction(tid, file_path=file_path, file_hash=file_hash, number_of_packets=number_of_packets, is_tx=is_tx)
        target_dict[tid] = trans
        
        print(f"[INFO] Created {dict_name} transaction with tid={tid}")
        return trans
    
    def get_transaction(self, tid: int, is_tx: bool = None):
        """
        Retrieve a transaction by its ID.
        
        Args:
            tid: Transaction ID (0-7)
            is_tx: True to search TX dict, False for RX dict, None to search both
        
        Returns:
            Transaction object if found, None otherwise
        """
        if is_tx is True:
            return self.tx_dict.get(tid, None)
        elif is_tx is False:
            return self.rx_dict.get(tid, None)
        else:
            # Search both dictionaries
            return self.tx_dict.get(tid) or self.rx_dict.get(tid)
    
    def delete_transaction(self, tid: int, is_tx: bool = None):
        """
        Delete a transaction by its ID.
        
        Args:
            tid: Transaction ID to delete
            is_tx: True to delete from TX dict, False for RX dict, None to search both
        
        Returns:
            True if deleted, False if not found
        """
        if is_tx is True or is_tx is None:
            if tid in self.tx_dict:
                del self.tx_dict[tid]
                print(f"[INFO] Deleted TX transaction with tid={tid}")
                return True
        
        if is_tx is False or is_tx is None:
            if tid in self.rx_dict:
                del self.rx_dict[tid]
                print(f"[INFO] Deleted RX transaction with tid={tid}")
                return True
        
        return False
    
    def get_all_transactions(self, is_tx: bool = None):
        """
        Get all active transactions.
        
        Args:
            is_tx: True for TX dict only, False for RX dict only, None for both
        
        Returns:
            List of Transaction objects
        """
        if is_tx is True:
            return list(self.tx_dict.values())
        elif is_tx is False:
            return list(self.rx_dict.values())
        else:
            return list(self.tx_dict.values()) + list(self.rx_dict.values())
    
    def get_transactions_by_state(self, state: int, is_tx: bool = None):
        """
        Get all transactions in a specific state.
        
        Args:
            state: Transaction state constant (from trans_state)
            is_tx: True for TX dict only, False for RX dict only, None for both
        
        Returns:
            List of Transaction objects in the specified state
        """
        all_trans = self.get_all_transactions(is_tx=is_tx)
        return [trans for trans in all_trans if trans.state == state]
    
    def get_active_count(self, is_tx: bool = None):
        """
        Get the number of active transactions.
        
        Args:
            is_tx: True for TX dict only, False for RX dict only, None for both
        
        Returns:
            Number of transactions currently in memory
        """
        if is_tx is True:
            return len(self.tx_dict)
        elif is_tx is False:
            return len(self.rx_dict)
        else:
            return len(self.tx_dict) + len(self.rx_dict)
    
    def is_full(self, is_tx: bool = None):
        """
        Check if maximum number of transactions reached.
        
        Args:
            is_tx: True for TX dict, False for RX dict, None for either
        
        Returns:
            True if at max capacity, False otherwise
        """
        if is_tx is True:
            return len(self.tx_dict) >= self.MAX_TRANSACTIONS
        elif is_tx is False:
            return len(self.rx_dict) >= self.MAX_TRANSACTIONS
        else:
            return (len(self.tx_dict) >= self.MAX_TRANSACTIONS or 
                    len(self.rx_dict) >= self.MAX_TRANSACTIONS)
    
    def clear_failed_transactions(self, is_tx: bool = None):
        """
        Remove all failed transactions from memory.
        
        Args:
            is_tx: True for TX dict, False for RX dict, None for both
        
        Returns:
            Number of transactions cleared
        """
        cleared_count = 0
        
        if is_tx is True or is_tx is None:
            failed_tids = [tid for tid, trans in self.tx_dict.items() if trans.state == trans_state.FAILED]
            for tid in failed_tids:
                self.delete_transaction(tid, is_tx=True)
            cleared_count += len(failed_tids)
        
        if is_tx is False or is_tx is None:
            failed_tids = [tid for tid, trans in self.rx_dict.items() if trans.state == trans_state.FAILED]
            for tid in failed_tids:
                self.delete_transaction(tid, is_tx=False)
            cleared_count += len(failed_tids)
        
        return cleared_count
    
    def get_stats(self, is_tx: bool = None):
        """
        Get statistics about all transactions.
        
        Args:
            is_tx: True for TX dict, False for RX dict, None for both
        
        Returns:
            Dictionary with transaction statistics
        """
        stats = {
            'total': self.get_active_count(is_tx=is_tx),
            'tx_count': len(self.tx_dict) if is_tx is None or is_tx is True else 0,
            'rx_count': len(self.rx_dict) if is_tx is None or is_tx is False else 0,
            'by_state': {}
        }
        
        for state_name in ['REQUESTED', 'INIT', 'SENDING', 'RECEIVING', 'COMPLETED', 'SUCCESS', 'FAILED']:
            state_value = getattr(trans_state, state_name, None)
            if state_value is not None:
                count = len(self.get_transactions_by_state(state_value, is_tx=is_tx))
                if count > 0:
                    stats['by_state'][state_name] = count
        
        return stats
    
    def dump_to_disk(self, tid: int, is_tx: bool, folder: str = "transaction_history", dump_fragments: bool = False):
        """
        Dump a transaction to disk for debugging/history purposes.
        
        Args:
            tid: Transaction ID to dump
            is_tx: True for TX dict, False for RX dict
            folder: Folder path to save the dump (default: "transaction_history")
            dump_fragments: If True, dump all received fragments data; if False, omit fragment data
        
        Returns:
            Path to the created file, or None if transaction not found
        """
        import json
        from datetime import datetime
        
        # Get the transaction
        trans = self.get_transaction(tid, is_tx=is_tx)
        if trans is None:
            print(f"[ERROR] Transaction with tid={tid} not found in {'TX' if is_tx else 'RX'} dict")
            return None
        
        # Create folder if it doesn't exist
        os.makedirs(folder, exist_ok=True)
        
        # Get state name
        state_name = "UNKNOWN"
        for name in ['REQUESTED', 'INIT', 'SENDING', 'RECEIVING', 'COMPLETED', 'SUCCESS', 'FAILED']:
            if getattr(trans_state, name, None) == trans.state:
                state_name = name
                break
        
        # Format timestamp from transaction start_date
        timestamp_str = datetime.fromtimestamp(trans.start_date).strftime("%Y_%m_%d-%H_%M_%S")
        
        # Create filename: timestamp_tid_state_txrx.json
        tx_rx_label = "TX" if is_tx else "RX"
        filename = f"{timestamp_str}_tid{tid}_{state_name}_{tx_rx_label}.json"
        filepath = os.path.join(folder, filename)
        
        # Prepare transaction data for serialization
        trans_data = {
            'tid': trans.tid,
            'state': trans.state,
            'state_name': state_name,
            'is_tx': is_tx,
            'start_date': trans.start_date,
            'timestamp': timestamp_str,
            'file_path': trans.file_path,
            'file_size': trans.file_size,
            'number_of_packets': trans.number_of_packets,
            'file_hash': trans.file_hash.hex() if trans.file_hash else None,
            'file_hash_bytes': format_bytes(trans.file_hash) if trans.file_hash else None,
            'missing_fragments_count': len(trans.missing_fragments),
            'missing_fragments': trans.missing_fragments[:100] if len(trans.missing_fragments) > 100 else trans.missing_fragments,  # Limit to first 100
            'received_fragments_count': len(trans.fragment_dict),
            'received_fragments': ", ".join(str(x) for x in (list(trans.fragment_dict.keys())[:100] if len(trans.fragment_dict) > 100 else list(trans.fragment_dict.keys()))),  # Single-line string
            'packets_generated_count': len(trans.packet_list),
            'dump_fragments_flag': dump_fragments,
        }
        
        # Add received fragment data (all fragments if dump_fragments is True)
        if dump_fragments and trans.fragment_dict:
            trans_data['received_fragments_data'] = {}
            for frag_num, frag_data in trans.fragment_dict.items():
                if isinstance(frag_data, bytes):
                    trans_data['received_fragments_data'][str(frag_num)] = {
                        'size': len(frag_data),
                        'bytes': format_bytes(frag_data)  # All bytes in 0x00 format
                    }
                else:
                    trans_data['received_fragments_data'][str(frag_num)] = {
                        'size': len(frag_data) if frag_data else 0,
                        'data': str(frag_data)
                    }
        
        # Write to disk
        try:
            with open(filepath, 'w') as f:
                json.dump(trans_data, f, indent=2)
            print(f"[INFO] Transaction dump saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"[ERROR] Failed to dump transaction to disk: {e}")
            return None
    
    def __repr__(self):
        """String representation showing all active transactions"""
        stats = self.get_stats()
        return f"TransactionManager(total={stats['total']}, tx={stats['tx_count']}, rx={stats['rx_count']}, by_state={stats['by_state']})"


# Create singleton instance
transaction_manager = TransactionManager()


def get_tid_number():
    """
    Legacy function for backward compatibility.
    Use transaction_manager.create_transaction(is_tx=True) instead.
    
    Returns:
        Allocated transaction ID or None if max reached
    """
    trans = transaction_manager.create_transaction(is_tx=True)
    if trans:
        return trans.tid
    return None
    

class Transaction:
    """
    This class will represent a transaction between the client and server
    It will hold the state of the transaction and any relevant information
    
    It will be the same on both sides
    
    on the other side will have all the packets received
    """
    
    def __init__(self, tid: str, file_path: str = None, file_hash: bytes = None, number_of_packets: int = None, is_tx=False):


        self.state = trans_state.REQUESTED   # we currently have no state, will switch to receiving once the first packet is received 
        self.start_date = time.time()     # this will eventually be used for timeout

        # this is on teh rx side
        self.fragment_dict = {}   # this is the dict that will contain the fragments of the file
        # this is on the tx side
        self.packet_list = []   # this will contain the command packets (already packet) ready to be sent to the client

        self.tid = tid
        self.file_path = file_path    # this will be used to save the file on the server side, the client will use to know what to call the file
        
        # these value will be calculated (when the transmitter is creating) or set (via the receiver with after reiceiving the init packet)
        self.file_size = self.get_file_size() if is_tx else None   # this will be used to calculate the number of packets, and will be None on the client side
        self.number_of_packets = self.get_number_of_packets() if is_tx else number_of_packets   # this will be used to know how many packets to expect, None in client until init_trans command is received
        # self.file_hash = self.get_file_hash() if file_hash is None else file_hash    # this will be used to verify the file after it is received, and will be None on the client side until the init packet is received
        self.file_hash = None  # disabled for now, does not make sense to use it while downlinking non critical data
        
        # this is a list that will keep track of the missing fragments. Once the transaction init receiver will add all the fragment number here
        self.missing_fragments = [x for x in range(0, self.number_of_packets)] if self.number_of_packets is not None else []  # every time it receives something, it will remove the number from this list

        self.last_batch = [] # will contain the seq_number of the last batch of fragments that were generated

    # these are the init functions

    def get_file_size(self):
        """
        This function will set the file size for the chosen file
        """
        if self.file_path is None:
            return None
        
        # compatibility with circuitpython
        device = os.uname()[0]
        if device[0:2] == "rp":
            # on circuitpython we will use os.stat to get the file size
            return os.stat(self.file_path)[6]
        
        return os.path.getsize(self.file_path)
        
    def get_number_of_packets(self):
        """
        This function will return the number of packets for the chosen file
        """
        if self.file_size is None:
            return None
        
        if self.file_size <= 0:
            return 0
        return (self.file_size + MAX_PACKET_SIZE - 1) // MAX_PACKET_SIZE
        
    def get_file_hash(self):
        """
        This function will set the file hash for the transaction
        the receiver will call this funciton with the received hash
        """
        if self.file_path is None:
            return None
        
        return self.calculate_file_hash()
    
    # normal functions
    
    def set_number_packets(self, number_of_packets):
        """
        This function will be called on the client side when it receives the init_trans command
        in the command it will contain info about the number of packets
        will also set the missing_fragments list
        """
        self.number_of_packets = number_of_packets
        self.missing_fragments = [x for x in range(0, self.number_of_packets)]
    
    def is_completed(self):
        """
        This will return if it is completed based on the state
        """
        return self.state == trans_state.COMPLETED

    @staticmethod
    def calculate_hash(file_bytes):
        """
        Returns the MD5 digest (16 bytes).
        [check] - using md5 for now, maybe should change to blake2s
        """
        return hashlib.new("sha1", file_bytes).digest()
    
    
    def calculate_file_hash(self):
        """
        Calculates and returns the hash of the file at self.file_path.
        Used when creating a transaction on the sending side.
        """
        if self.file_path is None:
            return None
        
        with open(self.file_path, "rb") as f:
            return self.calculate_hash(f.read())
    
    def get_hash_as_integers(self):
        """
        Returns the file hash as three integers (MSB, MiddleSB, LSB)
        for transmission in INIT_TRANS command.
        SHA1 hash is 20 bytes: split as 8 + 8 + 4 bytes
        """
        if self.file_hash is None:
            return (0, 0, 0)
        
        hash_MSB = int.from_bytes(self.file_hash[:8], byteorder='big')
        hash_middlesb = int.from_bytes(self.file_hash[8:16], byteorder='big')
        hash_LSB = int.from_bytes(self.file_hash[16:20], byteorder='big')
        return (hash_MSB, hash_middlesb, hash_LSB)
    
    def set_hash_from_integers(self, hash_MSB, hash_middlesb, hash_LSB):
        """
        Reconstructs the file hash from three integers (MSB, MiddleSB, LSB)
        received from INIT_TRANS command.
        SHA1 hash is 20 bytes: 8 + 8 + 4 bytes
        """
        hash_bytes_MSB = hash_MSB.to_bytes(8, byteorder='big')
        hash_bytes_middlesb = hash_middlesb.to_bytes(8, byteorder='big')
        hash_bytes_LSB = hash_LSB.to_bytes(4, byteorder='big')
        self.file_hash = hash_bytes_MSB + hash_bytes_middlesb + hash_bytes_LSB
    
    def change_state(self, new_state):
        """
        This function will be called to change the state of the transaction
        it will receive the new state and will update the state variable accordingly
        """
        self.state = new_state
        
    def add_fragment(self, fragment):
        """
        This will be a function that will facilitate adding the fragments to the transaction
        Will receive the fragments as Fragments class
        """
        
        if not isinstance(fragment, Fragment):
            raise TypeError(f"Expected Fragment object, got {type(fragment)}")
        
        # [check] - maybe i could just store the fragments as fragemnets
        # but for now to maintain compatibility will not change
        
        return self.add_packet(fragment.seq_number, fragment.payload, check=True)
    
    def add_packet(self, seq_number, fragment, check=True):
        """
        This function will be called when a packet for this tid has been received
        it will receive the fragment of the packet and can be added directly to the payload dict

        returns true if all packets have been received
        false otherwise
        """
        
        # check if fragment already exists, as of right now it will only warn the user
        if check and seq_number in self.fragment_dict:
            print(f"[WARNING] Fragment with sequence number {seq_number} already exists in transaction {self.tid}. Overwriting.")

        # change to receiving state if we are not already in it
        if self.state != trans_state.RECEIVING:
            print(f"[INFO] Transaction {self.tid} changing state to RECEIVING.")
            self.change_state(trans_state.RECEIVING)

        self.fragment_dict[seq_number] = fragment
        
        # remove the fragment number from the missing fragments list
        if check and seq_number not in self.missing_fragments:
            print(f"[WARNING] Adding fragment {seq_number} to transaction {self.tid}. But not in missing fragments")
        if seq_number in self.missing_fragments:
            self.missing_fragments.remove(seq_number)
        
        # check if the transaction is completed
        if check and len(self.fragment_dict) == self.number_of_packets:
            print(f"[INFO] Transaction {self.tid} has received all packets. Changing state to COMPLETED.")
            self.change_state(trans_state.COMPLETED)
            return True
    
        return False
        
    def write_file(self, folder=None):
        """
        This will take all the information in the fragment_dict and will write the file to disk
        this will be a dump version that will write everything, later better version will be written
        that will allow to write part of the files
        will also check the hash of the file after it is written
        """
        
        if folder is not None:
            file_path = os.path.join(folder,self.file_path)
        else:
            file_path = self.file_path
            
        # check if destination needs folders to be created
        file_dir = os.path.dirname(file_path)
        if file_dir != "" and not os.path.exists(file_dir):
            os.makedirs(file_dir)
        
        total_bytes_written = 0
        
        with open(file_path, "wb") as f:
            for i in range(self.number_of_packets):
                fragment = self.fragment_dict.get(i, None)
                if fragment is None:
                    print(f"[ERROR] Fragment with sequence number {i} is missing from transaction {self.tid}. Cannot write file.")
                    return False
                # Fragment should already be bytes from unpacking
                bytes_written = f.write(fragment)
                total_bytes_written += bytes_written
        
        # Verify hash if provided
        if self.file_hash is not None:
            with open(file_path, "rb") as f:
                file_data = f.read()
                calculated_hash = self.calculate_hash(file_data)
            
            # Compare hash bytes
            if calculated_hash != self.file_hash:
                print(f"[ERROR] Hash verification FAILED for transaction {self.tid}!")
                print(f"[ERROR] Expected: {self.file_hash.hex()}")
                print(f"[ERROR] Got:      {calculated_hash.hex()}")
                # set the state of the transaction to failed
                self.change_state(trans_state.FAILED)
                
                return False
                
            print(f"[INFO] Hash verification PASSED: {calculated_hash.hex()}")
        
        # File written and verified successfully
        print(f"[INFO] File for transaction {self.tid} has been written to disk at {file_path}. Total bytes written: {total_bytes_written}")
        
        self.change_state(trans_state.SUCCESS)
        return True
    
    
    def generate_all_packets(self):
        """
        Read the file from disk and generate all the packets that will be sent
        they will already be packed
        
        if will skip the ones that are not in the missing fragments list
          this will allow the receiver to let the transmitter know what packets it already has
        """
                
        with open(self.file_path, "rb") as f:
            file_data = f.read()
            
            # discard the last batch
            self.last_batch = []  # [check] - not the best place for this as the rest of the code will not support this feature with the max number of packets... But I will most likely use with less packets
            
            for i in self.missing_fragments:
                payload_frag = file_data[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE]
                # Keep as raw bytes - codec will handle it
                frag = Fragment(self.tid, i)
                frag.add_payload(payload_frag)
                self.packet_list.append(pack(frag))
                self.last_batch.append(i)
        
        return self.packet_list
    
    def generate_x_packets(self, x):
        """
        Will generate the next x packets in the missing fragments list
        reutrns a list with the packed commands for those fragments ready to be sent to the receiver

        this is mostly to avoid memory issues, but still allow to send many packets
        """
        
        generated_packets = []

        # discard the last batch
        self.last_batch = []

        for i in range(x):
            if len(self.missing_fragments) == 0:
                break
            seq_number = self.missing_fragments[i]   # will only remove the fragments once they are confirmed
            self.last_batch.append(seq_number)
            with open(self.file_path, "rb") as f:
                f.seek(seq_number * MAX_PACKET_SIZE)
                payload_frag = f.read(MAX_PACKET_SIZE)
            
            frag = Fragment(self.tid, seq_number)
            frag.add_payload(payload_frag)
            generated_packets.append(pack(frag))
        return generated_packets
    
    def update_missing_fragments_bitmap(self, seq_offset, bitmap, max_bits=32):
        """
        Receives a seq_offset and a bitmap, from the seq_offset it will add remove all the indexes to the missing fragment list
        if respective bit in bitmap is 0, it will add
        if respective bit in bitmap is 1, it will remove
        accepts bitmap as int or (msb, lsb) tuple/list
        """
        if self.number_of_packets is None or seq_offset is None:
            return

        if seq_offset < 0:
            return

        # Accept (msb, lsb) tuple/list
        if isinstance(bitmap, (list, tuple)) and len(bitmap) == 2:
            bitmap = (int(bitmap[0]) << 16) | int(bitmap[1])

        bitmap = int(bitmap)
        width = min(max_bits, max(0, self.number_of_packets - seq_offset))
        if width <= 0:
            return

        missing_set = set(self.missing_fragments)

        for i in range(width):
            seq_number = seq_offset + i
            bit_pos = (width - 1) - i  # MSB-first within window
            bit = (bitmap >> bit_pos) & 1
            if bit == 0:
                missing_set.add(seq_number)
            else:
                missing_set.discard(seq_number)

        self.missing_fragments = sorted(missing_set)
                    
    def generate_missing_bitmaps(self, max_bits=32):
        """
        Helper function that will be used during transaction
        meant to be used in the receiver, it will generate a list with all the missing fragments
        missing fragments are represented with a seq_number (representing offset) and a bitmap
        the receiver will be able to take the data generated here to send the commands         
        bitmap will be represented as two ints (the first 16bits and the second 16bits)
        """
        
        # bitmap_entry = [seq_offset, bitmap]
        # self.bitmap_list = [bitmap_entry, ...]
        
            
        if self.number_of_packets is None:
            return []

        bitmap_list = []

        # Sort missing fragments for safety
        missing_set = set(self.missing_fragments)

        # Iterate in windows of max_bits
        for seq_offset in range(0, self.number_of_packets, max_bits):

            bitmap = 0
            width = min(max_bits, self.number_of_packets - seq_offset)

            for bit_index in range(width):
                seq_number = seq_offset + bit_index

                # If fragment is received → set bit to 1
                if seq_number not in missing_set:
                    bit_pos = (width - 1) - bit_index  # MSB-first within window
                    bitmap |= (1 << bit_pos)

            msb_bitmap = (bitmap >> 16) & 0xFFFF
            lsb_bitmap = bitmap & 0xFFFF
            bitmap_list.append([seq_offset, msb_bitmap, lsb_bitmap])
        return bitmap_list
        

    def confirm_last_batch(self, bitmap):
        """
        Will receive a bitmap to confirm the last batch of fragments
        each bit in the bitmap will represent a number in the last_batch list
        if its 1 it means that it received, if its 0 it did not receive
        the bitmap will come in as a int value
        """
        if not self.last_batch:
            return len(self.missing_fragments)

        # Accept (msb, lsb) tuple/list
        if isinstance(bitmap, (list, tuple)) and len(bitmap) == 2:
            bitmap = (int(bitmap[0]) << 16) | int(bitmap[1])

        bitmap = int(bitmap)
        width = len(self.last_batch)

        missing_set = set(self.missing_fragments)

        for i in range(width):
            bit_pos = (width - 1) - i  # MSB-first within window
            if ((bitmap >> bit_pos) & 1) == 1:
                seq_number = self.last_batch[i]
                missing_set.discard(seq_number)

        self.missing_fragments = sorted(missing_set)
        
        self.last_batch = []  # Clear last batch after confirmation
        return len(self.missing_fragments)
    
    def generate_specific_packet(self, seq_number):
        """
        Given a certain seq_number this function will generate the packet for that fragment
        it will return the packed command for that fragment
        it can be sent directly to the receiver
        
        Only reads the specific fragment needed, not the entire file
        """
        if self.file_path is None:
            print(f"[ERROR] Cannot generate packet: no file path set for transaction {self.tid}.")
            return None
        
        if seq_number < 0 or seq_number >= self.number_of_packets:
            print(f"[ERROR] Sequence number {seq_number} is out of range for transaction {self.tid}.")
            return None
        
        with open(self.file_path, "rb") as f:
            # Seek to the start of the fragment
            f.seek(seq_number * MAX_PACKET_SIZE)
            # Read only the bytes for this fragment
            payload_frag = f.read(MAX_PACKET_SIZE)
            
            frag = Fragment(self.tid, seq_number)
            frag.add_payload(payload_frag)
            return pack(frag)
        
    # these are functions that will run in the transmitter to allow the receiver to control the packets that are being sent
        
    def overwrite_missing_fragments(self, new_missing_fragments):
        """
        This function will allow the receiver to send a list of the missing fragments and overwrite the current missing list
        will be used when there are a few missing fragments
        """
        self.missing_fragments = new_missing_fragments
    
    # [check] - find a better name for this function 
    def add_received_list(self, rx_fragment_list):
        """
        This will allow the receiver to send a list with the fragments it has already received
        all the fragments from this list will be removed from the missing fragments list
        """
        for seq_number in rx_fragment_list:
            if seq_number in self.missing_fragments:
                self.missing_fragments.remove(seq_number)
            else:
                print(f"[WARNING] Received list contains sequence number {seq_number} that is not in missing fragments for transaction {self.tid}.")

    def __repr__(self):
        if self.number_of_packets:
            missing_val = (len(self.missing_fragments) / self.number_of_packets) * 100
            missing_str = f"{missing_val:.2f}%"
        else:
            missing_str = "N/A"

        return (f"Tid={self.tid}, st={self.state}, path={self.file_path}, hash={self.file_hash}, #pack={self.number_of_packets}, missing={missing_str}")
