import pytest
import os
import sys
import tempfile
import hashlib
from pathlib import Path

# Add parent directory to path to import splat module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from splat.transport_layer import Transaction, trans_state, get_tid_number, rx_dict, tx_dict, transaction_manager
from splat.telemetry_definition import MAX_PACKET_SIZE


class TestTransactionInitialization:
    """Test Transaction class initialization"""
    
    def test_transaction_creation_without_file(self):
        """Test creating a transaction without a file"""
        trans = Transaction(tid=1)
        assert trans.tid == 1
        assert trans.state == trans_state.REQUESTED
        assert trans.file_path is None
        assert trans.file_hash is None
        assert trans.number_of_packets is None
        assert trans.fragment_dict == {}
        assert len(trans.missing_fragments) == 0
    
    def test_transaction_creation_with_file(self):
        """Test creating a transaction with a file"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content " * 100)
            temp_file = f.name
        
        try:
            trans = Transaction(tid=2, file_path=temp_file)
            assert trans.tid == 2
            assert trans.file_path == temp_file
            assert trans.file_hash is not None
            assert trans.number_of_packets > 0
            assert len(trans.missing_fragments) == trans.number_of_packets
        finally:
            os.unlink(temp_file)
    
    def test_transaction_creation_with_explicit_hash(self):
        """Test creating a transaction with explicit hash and number of packets"""
        test_hash = hashlib.md5(b"test").digest()
        trans = Transaction(tid=3, file_hash=test_hash, number_of_packets=5)
        assert trans.tid == 3
        assert trans.file_hash == test_hash
        assert trans.number_of_packets == 5
        assert len(trans.missing_fragments) == 5


class TestHashCalculation:
    """Test hash calculation functionality"""
    
    def test_calculate_hash_static_method(self):
        """Test the static calculate_hash method"""
        data = b"test data"
        hash_result = Transaction.calculate_hash(data)
        expected = hashlib.md5(data).digest()
        assert hash_result == expected
        assert len(hash_result) == 16  # MD5 produces 16 bytes
    
    def test_calculate_file_hash(self):
        """Test calculating hash of a file"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_data = b"file content for hashing"
            f.write(test_data)
            temp_file = f.name
        
        try:
            trans = Transaction(tid=4, file_path=temp_file)
            calculated = trans.calculate_file_hash()
            expected = hashlib.md5(test_data).digest()
            assert calculated == expected
        finally:
            os.unlink(temp_file)
    
    def test_calculate_file_hash_returns_none_without_file(self):
        """Test that calculate_file_hash returns None when no file is set"""
        trans = Transaction(tid=5)
        assert trans.calculate_file_hash() is None


class TestHashConversion:
    """Test hash conversion to/from integers"""
    
    def test_get_hash_as_integers(self):
        """Test converting hash to MSB and LSB integers"""
        test_hash = bytes(range(16))  # 16 bytes: 0x00, 0x01, ..., 0x0f
        trans = Transaction(tid=6, file_hash=test_hash)
        
        hash_MSB, hash_LSB = trans.get_hash_as_integers()
        
        # First 8 bytes as big-endian int
        expected_MSB = int.from_bytes(test_hash[:8], byteorder='big')
        # Last 8 bytes as big-endian int
        expected_LSB = int.from_bytes(test_hash[8:], byteorder='big')
        
        assert hash_MSB == expected_MSB
        assert hash_LSB == expected_LSB
    
    def test_get_hash_as_integers_returns_zero_when_no_hash(self):
        """Test that get_hash_as_integers returns (0, 0) when no hash is set"""
        trans = Transaction(tid=7)
        hash_MSB, hash_LSB = trans.get_hash_as_integers()
        assert hash_MSB == 0
        assert hash_LSB == 0
    
    def test_set_hash_from_integers(self):
        """Test reconstructing hash from MSB and LSB integers"""
        original_hash = bytes(range(16))
        hash_MSB = int.from_bytes(original_hash[:8], byteorder='big')
        hash_LSB = int.from_bytes(original_hash[8:], byteorder='big')
        
        trans = Transaction(tid=8)
        trans.set_hash_from_integers(hash_MSB, hash_LSB)
        
        assert trans.file_hash == original_hash
    
    def test_hash_conversion_round_trip(self):
        """Test round-trip conversion: hash -> integers -> hash"""
        original_hash = hashlib.md5(b"round trip test").digest()
        
        trans = Transaction(tid=9, file_hash=original_hash)
        hash_MSB, hash_LSB = trans.get_hash_as_integers()
        
        trans2 = Transaction(tid=10)
        trans2.set_hash_from_integers(hash_MSB, hash_LSB)
        
        assert trans2.file_hash == original_hash


class TestFragmentManagement:
    """Test fragment adding and tracking"""
    
    def test_add_packet(self):
        """Test adding a fragment"""
        trans = Transaction(tid=11, number_of_packets=5)
        assert len(trans.missing_fragments) == 5
        
        trans.add_packet(0, b"fragment 0")
        assert 0 not in trans.missing_fragments
        assert len(trans.fragment_dict) == 1
        assert trans.fragment_dict[0] == b"fragment 0"
    
    def test_add_all_packets_returns_true(self):
        """Test that add_packet returns True when all packets are received"""
        trans = Transaction(tid=12, number_of_packets=2)
        
        result1 = trans.add_packet(0, b"frag 0")
        assert result1 is False
        
        result2 = trans.add_packet(1, b"frag 1")
        assert result2 is True
    
    def test_add_duplicate_packet_warns(self):
        """Test that adding duplicate packet warns user"""
        trans = Transaction(tid=13, number_of_packets=2)
        trans.add_packet(0, b"fragment 0")
        trans.add_packet(0, b"new fragment 0")  # Should warn
        
        # Verify it was overwritten
        assert trans.fragment_dict[0] == b"new fragment 0"
    
    def test_missing_fragments_tracking(self):
        """Test that missing_fragments list is properly maintained"""
        trans = Transaction(tid=14, number_of_packets=3)
        assert set(trans.missing_fragments) == {0, 1, 2}
        
        trans.add_packet(1, b"frag 1")
        assert set(trans.missing_fragments) == {0, 2}
        
        trans.add_packet(0, b"frag 0")
        assert set(trans.missing_fragments) == {2}


class TestStateManagement:
    """Test transaction state changes"""
    
    def test_change_state(self):
        """Test changing transaction state"""
        trans = Transaction(tid=15)
        assert trans.state == trans_state.REQUESTED
        
        trans.change_state(trans_state.INIT)
        assert trans.state == trans_state.INIT
        
        trans.change_state(trans_state.SENDING)
        assert trans.state == trans_state.SENDING
    
    def test_state_transition_to_failed_on_hash_mismatch(self):
        """Test that state changes to FAILED on hash verification failure"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            test_data = b"test data for verification"
            f.write(test_data)
            temp_file = f.name
        
        try:
            trans = Transaction(tid=16, file_path=temp_file)
            
            # Add fragments
            for i, chunk in enumerate([test_data[i:i+MAX_PACKET_SIZE] for i in range(0, len(test_data), MAX_PACKET_SIZE)]):
                trans.add_packet(i, chunk)
            
            # Set wrong hash
            trans.file_hash = hashlib.md5(b"wrong data").digest()
            
            result = trans.write_file(temp_file + ".received")
            
            assert result is False
            assert trans.state == trans_state.FAILED
            
            # Clean up
            if os.path.exists(temp_file + ".received"):
                os.unlink(temp_file + ".received")
        finally:
            os.unlink(temp_file)


class TestFileWriting:
    """Test file writing and verification"""
    
    def test_write_file_with_correct_hash(self):
        """Test writing file with correct hash verification"""
        test_data = b"test file content " * 50
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(test_data)
            source_file = f.name
        
        output_file = source_file + ".received"
        
        try:
            trans = Transaction(tid=17, file_path=source_file)
            
            # Add all fragments
            for i in range(trans.number_of_packets):
                start = i * MAX_PACKET_SIZE
                end = min(start + MAX_PACKET_SIZE, len(test_data))
                trans.add_packet(i, test_data[start:end])
            
            result = trans.write_file(output_file)
            
            assert result is True
            
            # Verify file content
            with open(output_file, 'rb') as f:
                written_data = f.read()
            assert written_data == test_data
        finally:
            os.unlink(source_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_write_file_with_missing_fragment(self):
        """Test that write_file fails when fragments are missing"""
        trans = Transaction(tid=18, number_of_packets=3, file_hash=b"somehash")
        
        # Only add 2 fragments
        trans.add_packet(0, b"fragment 0")
        trans.add_packet(1, b"fragment 1")
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_file = f.name
        
        try:
            result = trans.write_file(output_file)
            assert result is False
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_write_file_without_hash_verification(self):
        """Test writing file without hash verification"""
        test_data = b"test content without hash"
        output_file = None
        
        try:
            trans = Transaction(tid=19, number_of_packets=1)
            trans.add_packet(0, test_data)
            
            with tempfile.NamedTemporaryFile(delete=False) as f:
                output_file = f.name
            
            result = trans.write_file(output_file)
            
            assert result is True
            
            with open(output_file, 'rb') as f:
                written_data = f.read()
            assert written_data == test_data
        finally:
            if output_file and os.path.exists(output_file):
                os.unlink(output_file)


class TestPacketGeneration:
    """Test packet generation functionality"""
    
    def test_generate_all_packets(self):
        """Test generating all packet list"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_data = b"x" * (MAX_PACKET_SIZE * 3 + 100)
            f.write(test_data)
            temp_file = f.name
        
        try:
            trans = Transaction(tid=20, file_path=temp_file)
            packet_list = trans.generate_all_packets()
            
            # Should have packets for all missing fragments
            assert len(packet_list) == trans.number_of_packets
        finally:
            os.unlink(temp_file)
    
    def test_generate_specific_packet(self):
        """Test generating a specific packet"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_data = b"packet test data " * 100
            f.write(test_data)
            temp_file = f.name
        
        try:
            trans = Transaction(tid=21, file_path=temp_file)
            
            # Generate specific packet
            packet = trans.generate_specific_packet(0)
            assert packet is not None
            assert isinstance(packet, bytes)
        finally:
            os.unlink(temp_file)
    
    def test_generate_specific_packet_out_of_range(self):
        """Test generating packet with out-of-range seq_number"""
        trans = Transaction(tid=22, number_of_packets=5)
        
        packet = trans.generate_specific_packet(10)
        assert packet is None
    
    def test_generate_specific_packet_without_file(self):
        """Test generating specific packet without file path"""
        trans = Transaction(tid=23, number_of_packets=5)
        packet = trans.generate_specific_packet(0)
        assert packet is None


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_get_tid_number(self):
        """Test getting available tid"""
        # Clear transaction dicts first
        tx_dict.clear()
        rx_dict.clear()
        
        tid = get_tid_number()
        assert tid is not None
        assert 0 <= tid < 8
    
    def test_get_tid_number_when_full(self):
        """Test getting tid when all are in use"""
        # Fill transaction dict
        tx_dict.clear()
        rx_dict.clear()
        for i in range(8):
            tx_dict[i] = Transaction(tid=i)
        
        tid = get_tid_number()
        assert tid is None
        
        # Clean up
        tx_dict.clear()


class TestTransactionRepr:
    """Test transaction string representation"""
    
    def test_repr(self):
        """Test __repr__ method"""
        trans = Transaction(tid=24, number_of_packets=5)
        repr_str = repr(trans)
        
        assert "Transaction" in repr_str
        assert "tid=24" in repr_str
        assert "number_of_packets=5" in repr_str


class TestMissingFragmentsManagement:
    """Test overwrite_missing_fragments and add_received_list functions"""
    
    def test_overwrite_missing_fragments_changes_packet_generation(self):
        """Test that overwrite actually changes which packets are generated"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * (MAX_PACKET_SIZE * 5))
            temp_file = f.name
        
        try:
            trans = Transaction(tid=27, file_path=temp_file)
            initial_missing = len(trans.missing_fragments)
            
            # Before overwrite: should generate all packets
            all_packets_before = trans.generate_all_packets()
            assert len(all_packets_before) == initial_missing
            
            # Reset for next test
            trans.missing_fragments = list(range(initial_missing))
            trans.packet_list = []
            
            # After overwrite: should only generate 2 packets
            trans.overwrite_mising_fragments([1, 3])
            remaining_packets = trans.generate_all_packets()
            assert len(remaining_packets) == 2
            
            # Verify correct seq_numbers in packets
            from splat.telemetry_codec import unpack
            seq_numbers = set()
            for packet_bytes in remaining_packets:
                unpacked = unpack(packet_bytes)
                seq_numbers.add(unpacked.get_argument("seq_number"))
            
            assert seq_numbers == {1, 3}
        finally:
            os.unlink(temp_file)
    
    def test_overwrite_missing_fragments_empty_stops_generation(self):
        """Test that overwriting with empty list generates no packets"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"y" * (MAX_PACKET_SIZE * 3))
            temp_file = f.name
        
        try:
            trans = Transaction(tid=28, file_path=temp_file)
            initial_missing = len(trans.missing_fragments)
            assert initial_missing > 0
            
            # Overwrite with empty list
            trans.overwrite_mising_fragments([])
            packets = trans.generate_all_packets()
            
            # Should generate 0 packets
            assert len(packets) == 0
        finally:
            os.unlink(temp_file)
    
    def test_overwrite_missing_fragments_non_sequential(self):
        """Test overwriting with non-sequential fragment numbers"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"z" * (MAX_PACKET_SIZE * 10))
            temp_file = f.name
        
        try:
            trans = Transaction(tid=29, file_path=temp_file)
            
            # Overwrite with sparse list
            sparse_list = [0, 3, 5, 9]
            trans.overwrite_mising_fragments(sparse_list)
            packets = trans.generate_all_packets()
            
            assert len(packets) == 4
            
            from splat.telemetry_codec import unpack
            seq_numbers = []
            for packet_bytes in packets:
                unpacked = unpack(packet_bytes)
                seq_numbers.append(unpacked.get_argument("seq_number"))
            
            assert set(seq_numbers) == {0, 3, 5, 9}
        finally:
            os.unlink(temp_file)
    
    def test_add_received_list_reduces_packet_generation(self):
        """Test that add_received_list actually reduces packets generated"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"a" * (MAX_PACKET_SIZE * 6))
            temp_file = f.name
        
        try:
            trans = Transaction(tid=30, file_path=temp_file)
            initial_missing = len(trans.missing_fragments)
            assert initial_missing > 0
            
            # Generate all packets initially
            all_packets = trans.generate_all_packets()
            assert len(all_packets) == initial_missing
            
            # Reset and try with add_received_list
            trans.missing_fragments = list(range(initial_missing))
            trans.packet_list = []
            
            trans.add_received_list([0, 2, 4])
            remaining_packets = trans.generate_all_packets()
            
            # Should only generate fewer packets
            assert len(remaining_packets) < initial_missing
            
            from splat.telemetry_codec import unpack
            seq_numbers = set()
            for packet_bytes in remaining_packets:
                unpacked = unpack(packet_bytes)
                seq_numbers.add(unpacked.get_argument("seq_number"))
            
            # Should not contain the ones we marked as received
            assert 0 not in seq_numbers
            assert 2 not in seq_numbers
            assert 4 not in seq_numbers
        finally:
            os.unlink(temp_file)
    
    def test_add_received_list_all_received_stops_generation(self):
        """Test that marking all as received stops all packet generation"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"b" * (MAX_PACKET_SIZE * 4))
            temp_file = f.name
        
        try:
            trans = Transaction(tid=31, file_path=temp_file)
            initial_missing = len(trans.missing_fragments)
            
            # Mark all as received
            trans.add_received_list(list(range(initial_missing)))
            packets = trans.generate_all_packets()
            
            # Should generate 0 packets
            assert len(packets) == 0
        finally:
            os.unlink(temp_file)
    
    def test_add_received_list_sequential_tracking(self):
        """Test that add_received_list correctly tracks multiple calls"""
        trans = Transaction(tid=32, number_of_packets=10)
        initial_missing = set(trans.missing_fragments)
        assert initial_missing == set(range(10))
        
        # First call
        trans.add_received_list([0, 1])
        assert set(trans.missing_fragments) == {2, 3, 4, 5, 6, 7, 8, 9}
        
        # Second call
        trans.add_received_list([3, 4, 5])
        assert set(trans.missing_fragments) == {2, 6, 7, 8, 9}
        
        # Third call
        trans.add_received_list([2, 6, 7, 8, 9])
        assert len(trans.missing_fragments) == 0
    
    def test_add_received_list_idempotent_with_duplicates(self):
        """Test that calling add_received_list with duplicates is safe"""
        trans = Transaction(tid=33, number_of_packets=5)
        
        # Add same fragments twice
        trans.add_received_list([1, 2])
        result_after_first = set(trans.missing_fragments)
        
        trans.add_received_list([1, 2])  # Call again with same
        result_after_second = set(trans.missing_fragments)
        
        # Should be the same (no error, no change)
        assert result_after_first == result_after_second == {0, 3, 4}
    
    def test_missing_fragments_affect_generate_specific_behavior(self):
        """Test that missing_fragments list doesn't affect generate_specific_packet"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"c" * (MAX_PACKET_SIZE * 4))
            temp_file = f.name
        
        try:
            trans = Transaction(tid=34, file_path=temp_file)
            
            # generate_specific_packet should work regardless of missing_fragments
            packet_1 = trans.generate_specific_packet(2)
            assert packet_1 is not None
            
            # After overwriting missing_fragments
            trans.overwrite_mising_fragments([0, 1])
            
            # Should still be able to generate packet 2
            packet_2 = trans.generate_specific_packet(2)
            assert packet_2 is not None
            
            # Packets should be identical
            from splat.telemetry_codec import unpack
            unpacked_1 = unpack(packet_1)
            unpacked_2 = unpack(packet_2)
            
            assert unpacked_1.get_argument("payload_frag") == unpacked_2.get_argument("payload_frag")
        finally:
            os.unlink(temp_file)


class TestIntegrationEndToEnd:
    """Test end-to-end workflow: generate packets and rebuild file"""
    
    def test_generate_packets_and_rebuild_file(self):
        """Test full roundtrip: file -> packets -> fragments -> file"""
        # Create a test file
        original_data = b"integration test data " * 100
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(original_data)
            source_file = f.name
        
        output_file = source_file + ".rebuilt"
        
        try:
            # 1. Create transaction and generate packets
            sender = Transaction(tid=25, file_path=source_file)
            packet_list = sender.generate_all_packets()
            
            assert len(packet_list) > 0
            assert len(packet_list) == sender.number_of_packets
            
            # 2. Create receiver transaction
            receiver = Transaction(tid=25, number_of_packets=sender.number_of_packets)
            receiver.file_hash = sender.file_hash
            
            # 3. Unpack packets and add fragments to receiver
            from splat.telemetry_codec import unpack
            for packet_bytes in packet_list:
                unpacked = unpack(packet_bytes)
                assert unpacked.name == "TRANS_PAYLOAD"
                
                tid = unpacked.get_argument("tid")
                seq_number = unpacked.get_argument("seq_number")
                payload_frag = unpacked.get_argument("payload_frag")
                
                receiver.add_packet(seq_number, payload_frag)
            
            # 4. Verify all packets received
            assert len(receiver.missing_fragments) == 0
            assert len(receiver.fragment_dict) == sender.number_of_packets
            
            # 5. Write and verify file
            result = receiver.write_file(output_file)
            assert result is True
            
            # 6. Verify rebuilt file matches original
            with open(output_file, 'rb') as f:
                rebuilt_data = f.read()
            
            assert rebuilt_data == original_data
            
        finally:
            os.unlink(source_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_generate_specific_packets_and_rebuild_file(self):
        """Test generating specific packets individually and rebuilding"""
        # Create a test file
        original_data = b"specific packet test " * 50
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(original_data)
            source_file = f.name
        
        output_file = source_file + ".rebuilt"
        
        try:
            # 1. Create sender transaction
            sender = Transaction(tid=26, file_path=source_file)
            
            # 2. Create receiver transaction
            receiver = Transaction(tid=26, number_of_packets=sender.number_of_packets)
            receiver.file_hash = sender.file_hash
            
            # 3. Generate and process packets one by one
            from splat.telemetry_codec import unpack
            for seq_num in range(sender.number_of_packets):
                packet_bytes = sender.generate_specific_packet(seq_num)
                assert packet_bytes is not None
                
                unpacked = unpack(packet_bytes)
                payload_frag = unpacked.get_argument("payload_frag")
                receiver.add_packet(seq_num, payload_frag)
            
            # 4. Verify all packets received
            assert len(receiver.missing_fragments) == 0
            
            # 5. Write and verify file
            result = receiver.write_file(output_file)
            assert result is True
            
            # 6. Verify rebuilt file matches original
            with open(output_file, 'rb') as f:
                rebuilt_data = f.read()
            
            assert rebuilt_data == original_data
            
        finally:
            os.unlink(source_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_partial_packets_then_add_received_list(self):
        """Test: Without add_received_list, sender would resend packets; with it, sender only sends what's needed"""
        # Create a test file
        original_data = b"partial transfer test " * 50
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(original_data)
            source_file = f.name
        
        output_file = source_file + ".rebuilt"
        
        try:
            # 1. Create sender transaction
            sender = Transaction(tid=35, file_path=source_file)
            total_packets = sender.number_of_packets
            
            # 2. Get first half of packets manually
            from splat.telemetry_codec import unpack
            packets_received_count = total_packets // 2
            
            first_half_packets = []
            for seq_num in range(packets_received_count):
                packet_bytes = sender.generate_specific_packet(seq_num)
                first_half_packets.append(packet_bytes)
            
            # 3. CRITICAL: Check what sender would generate WITHOUT add_received_list
            sender_without_sync = Transaction(tid=99, file_path=source_file)
            all_packets_without_sync = sender_without_sync.generate_all_packets()
            assert len(all_packets_without_sync) == total_packets, "Without sync, should generate ALL packets"
            
            # 4. Now apply add_received_list to sync transmitter
            sender.add_received_list(list(range(packets_received_count)))
            
            # 5. Get remaining packets from synced sender
            remaining_packets = sender.generate_all_packets()
            expected_remaining = total_packets - packets_received_count
            assert len(remaining_packets) == expected_remaining, f"After sync, should only generate {expected_remaining} packets"
            
            # 6. Verify we don't duplicate packets
            from splat.telemetry_codec import unpack
            first_half_seq = set()
            for p in first_half_packets:
                unpacked = unpack(p)
                first_half_seq.add(unpacked.get_argument("seq_number"))
            
            remaining_seq = set()
            for p in remaining_packets:
                unpacked = unpack(p)
                remaining_seq.add(unpacked.get_argument("seq_number"))
            
            assert len(first_half_seq & remaining_seq) == 0, "No overlap between first and remaining packets"
            assert first_half_seq | remaining_seq == set(range(total_packets)), "Together should cover all packets"
            
            # 7. Complete transfer with receiver
            receiver = Transaction(tid=35, number_of_packets=total_packets)
            receiver.file_hash = sender.file_hash
            
            # Add first half
            for packet_bytes in first_half_packets:
                unpacked = unpack(packet_bytes)
                payload_frag = unpacked.get_argument("payload_frag")
                receiver.add_packet(unpacked.get_argument("seq_number"), payload_frag)
            
            # Add remaining
            for packet_bytes in remaining_packets:
                unpacked = unpack(packet_bytes)
                payload_frag = unpacked.get_argument("payload_frag")
                receiver.add_packet(unpacked.get_argument("seq_number"), payload_frag)
            
            # 8. Verify complete and write file
            assert len(receiver.missing_fragments) == 0
            result = receiver.write_file(output_file)
            assert result is True
            
            with open(output_file, 'rb') as f:
                rebuilt_data = f.read()
            
            assert rebuilt_data == original_data
            
        finally:
            os.unlink(source_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_overwrite_missing_fragments_end_to_end(self):
        """Test: Without overwrite, would resend all packets; with it, only sends what's needed"""
        # Create a test file
        original_data = b"overwrite test data " * 60
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(original_data)
            source_file = f.name
        
        output_file = source_file + ".rebuilt"
        
        try:
            # 1. Create sender transaction
            sender = Transaction(tid=36, file_path=source_file)
            total_packets = sender.number_of_packets
            
            # 2. Get first 1/3 of packets
            from splat.telemetry_codec import unpack
            first_batch_count = total_packets // 3
            
            first_batch_packets = []
            for seq_num in range(first_batch_count):
                packet_bytes = sender.generate_specific_packet(seq_num)
                first_batch_packets.append(packet_bytes)
            
            # 3. CRITICAL: Without overwrite, sender would still have all missing_fragments
            initial_missing_before_overwrite = sender.missing_fragments.copy()
            assert len(initial_missing_before_overwrite) == total_packets, "Before overwrite, missing_fragments should have all packets"
            
            # 4. Simulate receiver determining what it still needs
            still_missing = [i for i in range(total_packets) if i >= first_batch_count]
            
            # 5. WITHOUT overwrite: sender would generate packets for ALL missing_fragments
            sender_unsync = Transaction(tid=99, file_path=source_file)
            packets_without_sync = sender_unsync.generate_all_packets()
            assert len(packets_without_sync) == total_packets, "Without sync, all packets would be generated"
            
            # 6. NOW apply overwrite to only mark what's actually missing
            sender.overwrite_mising_fragments(still_missing)
            
            # 7. Sender now generates only the packets that are actually missing
            remaining_packets = sender.generate_all_packets()
            expected_count = total_packets - first_batch_count
            assert len(remaining_packets) == expected_count, f"After overwrite, should generate {expected_count} packets, got {len(remaining_packets)}"
            
            # 8. Verify no duplicate packet generation
            first_batch_seq = set()
            for p in first_batch_packets:
                unpacked = unpack(p)
                first_batch_seq.add(unpacked.get_argument("seq_number"))
            
            remaining_seq = set()
            for p in remaining_packets:
                unpacked = unpack(p)
                remaining_seq.add(unpacked.get_argument("seq_number"))
            
            assert len(first_batch_seq & remaining_seq) == 0, "No duplicate packets between batches"
            assert first_batch_seq | remaining_seq == set(range(total_packets)), "All packets covered"
            
            # 9. Complete the transfer
            receiver = Transaction(tid=36, number_of_packets=total_packets)
            receiver.file_hash = sender.file_hash
            
            # Add first batch
            for packet_bytes in first_batch_packets:
                unpacked = unpack(packet_bytes)
                receiver.add_packet(unpacked.get_argument("seq_number"), unpacked.get_argument("payload_frag"))
            
            # Add remaining
            for packet_bytes in remaining_packets:
                unpacked = unpack(packet_bytes)
                receiver.add_packet(unpacked.get_argument("seq_number"), unpacked.get_argument("payload_frag"))
            
            # 10. Verify all received and file written correctly
            assert len(receiver.missing_fragments) == 0
            result = receiver.write_file(output_file)
            assert result is True
            
            with open(output_file, 'rb') as f:
                rebuilt_data = f.read()
            
            assert rebuilt_data == original_data
            
        finally:
            os.unlink(source_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_skip_packets_with_overwrite_missing_fragments(self):
        """Test: receiver requests packets non-sequentially, overwrite prevents redundant resends"""
        # Create a test file
        original_data = b"skip packets test " * 40
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(original_data)
            source_file = f.name
        
        output_file = source_file + ".rebuilt"
        
        try:
            # 1. Create sender transaction
            sender = Transaction(tid=37, file_path=source_file)
            total_packets = sender.number_of_packets
            
            # 2. Simulate receiver requesting packets in random order
            from splat.telemetry_codec import unpack
            # Request pattern: 0, 2, 3, 5, 7, 9, ... (non-sequential)
            packets_to_request = [i for i in range(total_packets) if i % 2 == 0 or i % 3 == 0]
            
            # 3. Store what we've actually received
            packets_received_seq = set()
            received_packets = []
            
            for seq_num in packets_to_request:
                if seq_num < total_packets:
                    packet_bytes = sender.generate_specific_packet(seq_num)
                    received_packets.append(packet_bytes)
                    unpacked = unpack(packet_bytes)
                    packets_received_seq.add(unpacked.get_argument("seq_number"))
            
            # 4. Determine what's still missing from receiver's perspective
            still_missing_from_receiver = [i for i in range(total_packets) if i not in packets_received_seq]
            
            # 5. CRITICAL: Without overwrite, sender still thinks ALL packets are missing
            assert len(sender.missing_fragments) == total_packets, "Before sync, sender has all as missing"
            
            # Create a control sender without sync
            sender_without_sync = Transaction(tid=99, file_path=source_file)
            would_generate_without_sync = sender_without_sync.generate_all_packets()
            assert len(would_generate_without_sync) == total_packets, "Unsynced sender would generate all packets"
            
            # 6. NOW overwrite sender's missing_fragments with actual missing
            sender.overwrite_mising_fragments(still_missing_from_receiver)
            
            # 7. Sender now generates ONLY the packets that are actually missing
            remaining_packets = sender.generate_all_packets()
            expected_remaining = len(still_missing_from_receiver)
            assert len(remaining_packets) == expected_remaining, f"After sync, should generate {expected_remaining} packets, got {len(remaining_packets)}"
            
            # 8. Verify no redundant packet generation
            remaining_seq = set()
            for p in remaining_packets:
                unpacked = unpack(p)
                remaining_seq.add(unpacked.get_argument("seq_number"))
            
            # Should have no overlap
            assert len(packets_received_seq & remaining_seq) == 0, "No duplicate packets between received and remaining"
            assert packets_received_seq | remaining_seq == set(range(total_packets)), "All packets covered exactly once"
            
            # 9. Complete transfer
            receiver = Transaction(tid=37, number_of_packets=total_packets)
            receiver.file_hash = sender.file_hash
            
            # Add received packets
            for packet_bytes in received_packets:
                unpacked = unpack(packet_bytes)
                receiver.add_packet(unpacked.get_argument("seq_number"), unpacked.get_argument("payload_frag"))
            
            # Add remaining
            for packet_bytes in remaining_packets:
                unpacked = unpack(packet_bytes)
                receiver.add_packet(unpacked.get_argument("seq_number"), unpacked.get_argument("payload_frag"))
            
            # 10. Verify file integrity
            assert len(receiver.missing_fragments) == 0
            result = receiver.write_file(output_file)
            assert result is True
            
            with open(output_file, 'rb') as f:
                rebuilt_data = f.read()
            
            assert rebuilt_data == original_data
            
        finally:
            os.unlink(source_file)
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestTransactionManager:
    """Test TransactionManager class for centralized transaction management"""
    
    def setup_method(self):
        """Clear transaction dicts before each test to ensure isolation"""
        tx_dict.clear()
        rx_dict.clear()
    
    def test_transaction_manager_singleton(self):
        """Test that transaction_manager is a singleton"""
        from splat.transport_layer import transaction_manager as tm1
        from splat.transport_layer import transaction_manager as tm2
        
        assert tm1 is tm2
    
    def test_create_transaction_with_file(self):
        """Test creating a transaction with a file path"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data " * 50)
            temp_file = f.name
        
        try:
            trans = transaction_manager.create_transaction(file_path=temp_file, is_tx=True)
            
            assert trans is not None
            assert trans.tid == 0  # First tid should be 0
            assert trans.file_path == temp_file
            assert trans.file_hash is not None
            assert trans.number_of_packets > 0
            assert transaction_manager.get_transaction(0) is trans
        finally:
            os.unlink(temp_file)
    
    def test_create_transaction_without_file(self):
        """Test creating a transaction without file (receiver side)"""
        trans = transaction_manager.create_transaction(
            tid=0,
            file_hash=hashlib.md5(b"test").digest(),
            number_of_packets=10,
            is_tx=False
        )
        
        assert trans is not None
        assert trans.tid == 0
        assert trans.file_path is None
        assert trans.file_hash is not None
        assert trans.number_of_packets == 10
    
    def test_create_multiple_transactions(self):
        """Test creating multiple transactions"""
        trans_list = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"x" * 100)
                temp_file = f.name
            
            trans = transaction_manager.create_transaction(file_path=temp_file, is_tx=True)
            trans_list.append((trans, temp_file))
        
        try:
            assert len(trans_list) == 5
            assert transaction_manager.get_active_count(is_tx=True) == 5
            
            # Verify tids are sequential
            for i, (trans, _) in enumerate(trans_list):
                assert trans.tid == i
        finally:
            for _, temp_file in trans_list:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
    
    def test_create_transaction_max_limit(self):
        """Test that creating more than MAX_TRANSACTIONS fails"""
        trans_list = []
        for i in range(transaction_manager.MAX_TRANSACTIONS):
            trans = transaction_manager.create_transaction(is_tx=True)
            trans_list.append(trans)
        
        # Should have created 8 transactions
        assert len(trans_list) == 8
        assert transaction_manager.is_full(is_tx=True)
        
        # Attempting to create 9th should fail
        trans_9 = transaction_manager.create_transaction(is_tx=True)
        assert trans_9 is None
    
    def test_get_transaction(self):
        """Test retrieving transactions by tid"""
        trans = transaction_manager.create_transaction(is_tx=True)
        
        retrieved = transaction_manager.get_transaction(0)
        assert retrieved is trans
        
        not_found = transaction_manager.get_transaction(99)
        assert not_found is None
    
    def test_delete_transaction(self):
        """Test deleting transactions"""
        trans = transaction_manager.create_transaction(is_tx=True)
        assert transaction_manager.get_active_count() == 1
        
        deleted = transaction_manager.delete_transaction(0)
        assert deleted is True
        assert transaction_manager.get_active_count() == 0
        assert transaction_manager.get_transaction(0) is None
        
        # Delete non-existent should return False
        deleted_again = transaction_manager.delete_transaction(0)
        assert deleted_again is False
    
    def test_get_all_transactions(self):
        """Test getting all active transactions"""
        trans_list = []
        for i in range(3):
            trans = transaction_manager.create_transaction(is_tx=True)
            trans_list.append(trans)
        
        all_trans = transaction_manager.get_all_transactions()
        assert len(all_trans) == 3
        
        for trans in trans_list:
            assert trans in all_trans
    
    def test_get_transactions_by_state(self):
        """Test filtering transactions by state"""
        trans1 = transaction_manager.create_transaction(is_tx=True)
        trans2 = transaction_manager.create_transaction(is_tx=True)
        trans3 = transaction_manager.create_transaction(is_tx=True)
        
        # Change states
        trans1.change_state(trans_state.INIT)
        trans2.change_state(trans_state.INIT)
        trans3.change_state(trans_state.SENDING)
        
        init_trans = transaction_manager.get_transactions_by_state(trans_state.INIT)
        assert len(init_trans) == 2
        assert trans1 in init_trans
        assert trans2 in init_trans
        
        sending_trans = transaction_manager.get_transactions_by_state(trans_state.SENDING)
        assert len(sending_trans) == 1
        assert trans3 in sending_trans
    
    def test_get_active_count(self):
        """Test getting count of active transactions"""
        assert transaction_manager.get_active_count() == 0
        
        transaction_manager.create_transaction(is_tx=True)
        assert transaction_manager.get_active_count() == 1
        
        transaction_manager.create_transaction(is_tx=True)
        assert transaction_manager.get_active_count() == 2
        
        transaction_manager.delete_transaction(0)
        assert transaction_manager.get_active_count() == 1
    
    def test_is_full(self):
        """Test checking if manager is at capacity"""
        assert not transaction_manager.is_full()
        
        for i in range(transaction_manager.MAX_TRANSACTIONS - 1):
            transaction_manager.create_transaction(is_tx=True)
        
        assert not transaction_manager.is_full(is_tx=True)
        
        transaction_manager.create_transaction(is_tx=True)
        assert transaction_manager.is_full(is_tx=True)
    
    def test_clear_failed_transactions(self):
        """Test clearing all failed transactions"""
        trans1 = transaction_manager.create_transaction(is_tx=True)
        trans2 = transaction_manager.create_transaction(is_tx=True)
        trans3 = transaction_manager.create_transaction(is_tx=True)
        
        trans1.change_state(trans_state.FAILED)
        trans2.change_state(trans_state.SUCCESS)
        trans3.change_state(trans_state.FAILED)
        
        cleared = transaction_manager.clear_failed_transactions()
        assert cleared == 2
        assert transaction_manager.get_active_count() == 1
        assert transaction_manager.get_transaction(1) is trans2
    
    def test_get_stats(self):
        """Test getting statistics about transactions"""
        trans1 = transaction_manager.create_transaction(is_tx=True)
        trans2 = transaction_manager.create_transaction(is_tx=True)
        trans3 = transaction_manager.create_transaction(is_tx=True)
        
        trans1.change_state(trans_state.INIT)
        trans2.change_state(trans_state.SENDING)
        trans3.change_state(trans_state.SENDING)
        
        stats = transaction_manager.get_stats()
        
        assert stats['total'] == 3
        assert stats['by_state'].get('INIT') == 1
        assert stats['by_state'].get('SENDING') == 2
    
    def test_repr(self):
        """Test string representation of transaction manager"""
        trans1 = transaction_manager.create_transaction(is_tx=True)
        trans2 = transaction_manager.create_transaction(is_tx=True)
        
        trans1.change_state(trans_state.INIT)
        
        repr_str = repr(transaction_manager)
        
        assert "TransactionManager" in repr_str
        assert "total=2" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
