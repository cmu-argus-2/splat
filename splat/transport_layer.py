import os
import time


from .telemetry_codec import Fragment
from .telemetry_definition import MAX_PAYLOAD_SIZE
from .telemetry_helper import format_bytes


class trans_state():
    REQUESTED = 1     # this is the default state when transaction is created. The transaction is created when the GS or SAT receive 
    INIT = 2          # after receiving the transaction request, the transmitter will check if the file exists, create the transaction and send init trans information
    SENDING = 3       # this will be the state after at least one fragment has been requested for sending
    RECEIVING = 4     # this will be the state after at least one fragment has been received
    COMPLETED = 5     # this will be the state after all the fragments have been received
    SUCCESS = 6       # this will be the state after all the fragments have been received and the file has been written to disk successfully
    FAILED = 7        # this will be the state if the transaction has failed for any reason, such as timeout, etc.

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
    
    def create_transaction(self, tid: int = None, file_path: str = None, number_of_packets: int = None, is_tx: bool = None):
        """
        Create a new transaction and allocate it a tid.
        
        Args:
            tid: Transaction ID (required for the TX side, will be set by RX side)
            file_path: Path to file (necessary on both sides)
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
        trans = Transaction(tid, file_path=file_path, number_of_packets=number_of_packets, is_tx=is_tx)
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
            'missing_fragments_count': trans._missing_fragments_count,
            'missing_fragments': list(list(trans._iter_missing_fragments())[:100]),  # Limit to first 100 for display
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
    
    def __init__(self, tid: str, file_path: str = None, number_of_packets: int = None, is_tx=False):


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
        
        # MEMORY NOTE: Using bitset (bytearray) instead of list for missing fragments tracking
        # For 2157 packets: bitset uses ~270 bytes vs ~17KB for list. Critical for memory-constrained targets.
        self._missing_fragments_bitset = bytearray((self.number_of_packets + 7) // 8) if self.number_of_packets is not None and self.number_of_packets > 0 else bytearray()
        # Initialize all bits to 1 (all fragments missing)
        if self.number_of_packets is not None and self.number_of_packets > 0:
            for i in range(len(self._missing_fragments_bitset)):
                self._missing_fragments_bitset[i] = 0xFF
            # Clear unused bits in the last byte
            if self.number_of_packets % 8 != 0:
                last_byte_bits = self.number_of_packets % 8
                self._missing_fragments_bitset[-1] &= (0xFF << (8 - last_byte_bits))
        self._missing_fragments_count = self.number_of_packets if self.number_of_packets is not None else 0

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
        return (self.file_size + MAX_PAYLOAD_SIZE - 1) // MAX_PAYLOAD_SIZE
        
    # normal functions
    
    def set_number_packets(self, number_of_packets):
        """
        This function will be called on the client side when it receives the init_trans command
        in the command it will contain info about the number of packets
        will also set the missing_fragments bitset
        """
        self.number_of_packets = number_of_packets
        # MEMORY NOTE: Initialize bitset for missing fragments (avoids large list allocation)
        self._missing_fragments_bitset = bytearray((number_of_packets + 7) // 8) if number_of_packets > 0 else bytearray()
        # Initialize all bits to 1 (all fragments missing)
        if number_of_packets > 0:
            for i in range(len(self._missing_fragments_bitset)):
                self._missing_fragments_bitset[i] = 0xFF
            # Clear unused bits in the last byte
            if number_of_packets % 8 != 0:
                last_byte_bits = number_of_packets % 8
                self._missing_fragments_bitset[-1] &= (0xFF << (8 - last_byte_bits))
        self._missing_fragments_count = number_of_packets
    
    def is_completed(self):
        """
        This will return if it is completed based on the state
        """
        return self.state == trans_state.COMPLETED

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
            print(f"[PAYLOAD] [WARNING] Fragment with sequence number {seq_number} already exists in transaction {self.tid}. Overwriting.")

        # change to receiving state if we are not already in it
        if self.state != trans_state.RECEIVING:
            print(f"[PAYLOAD] [INFO] Transaction {self.tid} changing state to RECEIVING.")
            self.change_state(trans_state.RECEIVING)

        self.fragment_dict[seq_number] = fragment
        
        # Mark fragment as received in bitset (clear the bit)
        if self._is_missing(seq_number):
            byte_idx = seq_number // 8
            bit_idx = seq_number % 8
            self._missing_fragments_bitset[byte_idx] &= ~(1 << (7 - bit_idx))
            self._missing_fragments_count -= 1
        elif check:
            print(f"[PAYLOAD] [WARNING] Adding fragment {seq_number} to transaction {self.tid}. But not in missing fragments")
        
        # check if the transaction is completed
        if check and len(self.fragment_dict) == self.number_of_packets:
            print(f"[PAYLOAD] [INFO] Transaction {self.tid} has received all packets. Changing state to COMPLETED.")
            self.change_state(trans_state.COMPLETED)
            return True

        # print the count of missing fragments
        print(f"[PAYLOAD] - len of missing fragments: {self._missing_fragments_count}")
    
        return False
    
    
    def write_partial_file(self, folder=None):
        """
        Write currently available fragments in fragment_dict to disk and free memory.

        Behavior:
        - Writes all currently available fragments to their correct offsets.
        - If there are gaps between fragment 0 and the highest available fragment,
          the file is padded with 0x00 bytes for the missing regions.
        - After each fragment is written, it is removed from fragment_dict.

        Note:
        - This method is intended for incremental/partial writes.
        - It does not perform final file completion checks and does not set SUCCESS.
        """

        if len(self.fragment_dict) == 0:
            print(f"[WARNING] No fragments available for partial write in transaction {self.tid}.")
            return False

        if folder is not None:
            # CircuitPython-compatible path join (no os.path)
            file_path = folder.rstrip("/") + "/" + self.file_path.lstrip("/")
        else:
            file_path = self.file_path

        # check if destination needs folders to be created
        file_dir = file_path.split("/")[:-1]
        file_dir = "/".join(file_dir)

        def _ensure_dir_exists(path):
            """
            CircuitPython-compatible recursive directory creation.
            Uses only os.stat/os.mkdir (no os.path, no os.makedirs).
            """
            if path in ("", "/"):
                return True

            is_absolute = path.startswith("/")
            parts = [p for p in path.split("/") if p]
            current = "/" if is_absolute else ""

            for part in parts:
                if current in ("", "/"):
                    next_path = ("/" + part) if current == "/" else part
                else:
                    next_path = current + "/" + part

                try:
                    os.stat(next_path)
                except Exception:
                    try:
                        os.mkdir(next_path)
                        print(f"[PAYLOAD] Created directory {next_path}")
                    except Exception as mkdir_error:
                        print(f"[ERROR] Failed to create directory {next_path}: {mkdir_error}")
                        return False

                current = next_path

            return True

        if file_dir != "":
            if not _ensure_dir_exists(file_dir):
                print(f"[ERROR] Could not prepare destination directory {file_dir} for transaction {self.tid}.")
                return False
            print(f"[PAYLOAD] Directory {file_dir} is ready.")
            
        # Ensure we have space for missing fragments (assumed zeros)
        max_seq = max(self.fragment_dict.keys())
        target_size = (max_seq + 1) * MAX_PAYLOAD_SIZE

        print(f"[PAYLOAD] Writing partial file for transaction {self.tid} at {file_path}.")
        print(f"[PAYLOAD] max_seq: {max_seq}, target_size: {target_size}")
        # if os.path.exists(file_path):    # cant use os.path because cpy does not support
        try:
            current_size = os.stat(file_path)[6]
            mode = "r+b"
            print(f"[PAYLOAD] File {file_path} exists. Current size: {current_size}")
        except Exception as e:
            current_size = 0
            mode = "wb+"
            print(f"[PAYLOAD] Creating file {file_path}.")
        
        total_bytes_written = 0
        written_fragments = 0

        with open(file_path, mode) as f:
            # If there are missing fragments, assume them as 0x00 bytes by extending file
            if current_size < target_size:
                f.seek(target_size - 1)
                f.write(b"\x00")

            # Write available fragments and remove them from memory
            seq_numbers = sorted(self.fragment_dict.keys())
            for seq_number in seq_numbers:
                fragment = self.fragment_dict.pop(seq_number)
                if fragment is None:
                    continue

                f.seek(seq_number * MAX_PAYLOAD_SIZE)
                bytes_written = f.write(fragment)
                total_bytes_written += bytes_written
                written_fragments += 1

        if self.state != trans_state.RECEIVING:
            self.change_state(trans_state.RECEIVING)

        print(
            f"[INFO] Partial file write for transaction {self.tid} at {file_path}. Fragments written: {written_fragments}, bytes written: {total_bytes_written}."
        )

        return True
    
    
    def write_file(self, folder=None):
        """
        This will take all the information in the fragment_dict and will write the file to disk
        this will be a dump version that will write everything, later better version will be written
        that will allow to write part of the files
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
        
        # File written and verified successfully
        print(f"[INFO] File for transaction {self.tid} has been written to disk at {file_path}. Total bytes written: {total_bytes_written}")
        
        self.change_state(trans_state.SUCCESS)
        return True
    
    
    def _is_missing(self, seq_number):
        """
        Check if a fragment is missing using bitset.
        Returns True if the fragment is missing, False if received.
        """
        if seq_number >= self.number_of_packets or seq_number < 0:
            return False
        byte_idx = seq_number // 8
        bit_idx = seq_number % 8
        return bool(self._missing_fragments_bitset[byte_idx] & (1 << (7 - bit_idx)))
    
    def _iter_missing_fragments(self):
        """
        Generator that yields missing fragment sequence numbers from the bitset.
        MEMORY NOTE: Avoids materializing full list, enabling iteration on constrained targets.
        """
        for seq_number in range(self.number_of_packets):
            if self._is_missing(seq_number):
                yield seq_number
    
    def _get_missing_fragments_list(self):
        """
        Returns a list of missing fragment sequence numbers.
        Used for backward compatibility and debugging.
        """
        return list(self._iter_missing_fragments())
    
    @property
    def missing_fragments(self):
        """
        Property for backward compatibility. Returns list of missing fragments.
        MEMORY NOTE: This materializes the list, so use _iter_missing_fragments() when possible.
        """
        return self._get_missing_fragments_list()
    
    @missing_fragments.setter
    def missing_fragments(self, value):
        """
        Setter for backward compatibility. Accepts a list and updates the bitset.
        """
        if self.number_of_packets is None or self.number_of_packets <= 0:
            self._missing_fragments_bitset = bytearray()
            self._missing_fragments_count = 0
            return

        # Reinitialize bitset with all bits cleared (all received),
        # then set only the fragments explicitly listed as missing.
        self._missing_fragments_bitset = bytearray((self.number_of_packets + 7) // 8)

        unique_missing = set()
        for seq_number in value:
            if isinstance(seq_number, int) and 0 <= seq_number < self.number_of_packets:
                unique_missing.add(seq_number)

        for seq_number in unique_missing:
            byte_idx = seq_number // 8
            bit_idx = seq_number % 8
            self._missing_fragments_bitset[byte_idx] |= (1 << (7 - bit_idx))

        self._missing_fragments_count = len(unique_missing)

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
            
            # MEMORY NOTE: Using bitset iteration instead of list slicing
            for i in self._iter_missing_fragments():
                payload_frag = file_data[i*MAX_PAYLOAD_SIZE:(i+1)*MAX_PAYLOAD_SIZE]
                # Keep as raw bytes - codec will handle it
                frag = Fragment(self.tid, i)
                frag.add_payload(payload_frag)
                self.packet_list.append(frag)
                self.last_batch.append(i)
        
        return self.packet_list
    
    def generate_x_packets(self, x, update_missing_fragments=False):
        """
        Will generate the next x packets in the missing fragments list
        reutrns a list with the packed commands for those fragments ready to be sent to the receiver
        
        if update_missing_fragments is true each packet sent will removed fro missing fragments
        so the next time this function is called will send new packets and do not need to confirm the batch
        using this method, if you miss any packets you will have to run the functions that will add the missed packet
        to the missing list

        this is mostly to avoid memory issues, but still allow to send many packets
        """
        
        generated_packets = []

        # discard the last batch
        self.last_batch = []

        # MEMORY NOTE: Using bitset count instead of list length
        x = min(x, self._missing_fragments_count)

        for seq_number in self._iter_missing_fragments():
            if len(self.last_batch) >= x:
                break
                
            self.last_batch.append(seq_number)
            with open(self.file_path, "rb") as f:
                f.seek(seq_number * MAX_PAYLOAD_SIZE)
                payload_frag = f.read(MAX_PAYLOAD_SIZE)
            
            frag = Fragment(self.tid, seq_number)
            frag.add_payload(payload_frag)
            generated_packets.append(frag)
        return generated_packets
    
    def update_missing_fragments_bitmap(self, seq_offset, bitmap, max_bits=64):
        """
        Receives a seq_offset and a bitmap, from the seq_offset it will add remove all the indexes to the missing fragment list
        if respective bit in bitmap is 0, it will add
        if respective bit in bitmap is 1, it will remove
        accepts bitmap as int or (bitmap_high, bitmap_low) tuple/list
        """
        if self.number_of_packets is None or seq_offset is None:
            return

        if seq_offset < 0:
            return

        # Accept (bitmap_high, bitmap_low) tuple/list
        if isinstance(bitmap, (list, tuple)) and len(bitmap) == 2:
            bitmap = ((int(bitmap[0]) & 0xFFFFFFFF) << 32) | (int(bitmap[1]) & 0xFFFFFFFF)

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
                    
    def generate_missing_bitmaps(self, max_bits=64):
        """
        Helper function that will be used during transaction
        meant to be used in the receiver, it will generate a list with all the missing fragments
        missing fragments are represented with a seq_number (representing offset) and a bitmap
        the receiver will be able to take the data generated here to send the commands         
        bitmap will be represented as two ints (the high 32 bits and the low 32 bits)
        """
        
        # bitmap_entry = [seq_offset, bitmap]
        # self.bitmap_list = [bitmap_entry, ...]
        
            
        if self.number_of_packets is None or self._missing_fragments_count == self.number_of_packets:
            return []

        bitmap_list = []

        # Iterate in windows of max_bits
        for seq_offset in range(0, self.number_of_packets, max_bits):

            bitmap = 0
            width = min(max_bits, self.number_of_packets - seq_offset)

            for bit_index in range(width):
                seq_number = seq_offset + bit_index

                # If fragment is received → set bit to 1
                if not self._is_missing(seq_number):
                    bit_pos = (width - 1) - bit_index  # MSB-first within window
                    bitmap |= (1 << bit_pos)

            bitmap_high = (bitmap >> 32) & 0xFFFFFFFF
            bitmap_low = bitmap & 0xFFFFFFFF
            bitmap_list.append([seq_offset, bitmap_high, bitmap_low])
        return bitmap_list
        

    def confirm_last_batch(self, bitmap):
        """
        Will receive a bitmap to confirm the last batch of fragments
        each bit in the bitmap will represent a number in the last_batch list
        
        to facilitate, assuming that usually you will get all the packets we will invert the logic
            1 means that the packet was not received
            0 means that the packet was received
        this way if you received everything, you can just send 0
        
        the bitmap will come in as a int value
        """
        if not self.last_batch:
            return len(self.missing_fragments)

        # Accept (bitmap_high, bitmap_low) tuple/list
        tuple_bitmap = isinstance(bitmap, (list, tuple)) and len(bitmap) == 2
        if tuple_bitmap:
            bitmap = ((int(bitmap[0]) & 0xFFFFFFFF) << 32) | (int(bitmap[1]) & 0xFFFFFFFF)

        bitmap = int(bitmap)
        width = min(len(self.last_batch), 64) if tuple_bitmap else len(self.last_batch)

        missing_set = set(self.missing_fragments)
        last_batch_missing_list = []
        
        for i in range(width):
            bit_pos = (width - 1) - i  # MSB-first within window
            if ((bitmap >> bit_pos) & 1) == 0:
                seq_number = self.last_batch[i]
                missing_set.discard(seq_number)
            else:
                last_batch_missing_list.append(self.last_batch[i])
        self.missing_fragments = sorted(missing_set)
        
        print(f"Missed packets: {last_batch_missing_list}")
        
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
            f.seek(seq_number * MAX_PAYLOAD_SIZE)
            # Read only the bytes for this fragment
            payload_frag = f.read(MAX_PAYLOAD_SIZE)
            
            frag = Fragment(self.tid, seq_number)
            frag.add_payload(payload_frag)
            return frag
        
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

        return (f"Tid={self.tid}, st={self.state}, path={self.file_path}, #pack={self.number_of_packets}, missing={missing_str}")
