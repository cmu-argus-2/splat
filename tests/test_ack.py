import pytest

from splat.telemetry_codec import (
    Ack, pack_ack, unpack_ack,
    MSG_TYPE_DICT, MAX_PACKET_SIZE
)


# ------------------------------------------------------------
# Initialization Tests
# ------------------------------------------------------------

class TestAckInitialization:
    """
    Check if Ack classes are initialized correctly
    """
    def test_ack_with_string_args(self):
        ack = Ack(response_status=1, ack_args="OK")

        assert ack.response_status == 1
        assert ack.ack_args == "OK"

    def test_ack_with_non_string_args(self):
        ack = Ack(response_status=2, ack_args=123)

        assert ack.response_status == 2
        assert ack.ack_args == "123"  # converted to string

    def test_ack_with_none_args(self):
        ack = Ack(response_status=3)

        assert ack.response_status == 3
        assert ack.ack_args is None


# ------------------------------------------------------------
# Representation Tests
# ------------------------------------------------------------

class TestAckUtilities:
    """
    Checks for pack and unpack Ack functions 
    """
    def test_repr_with_args(self):
        ack = Ack(response_status=5, ack_args="SUCCESS")

        repr_str = repr(ack)

        assert "rid=5" in repr_str
        assert "SUCCESS" in repr_str

    def test_repr_without_args(self):
        ack = Ack(response_status=7)

        repr_str = repr(ack)

        assert "rid=7" in repr_str
        assert "None" in repr_str

# ------------------------------------------------------------
# Pack/Unpacking Tests
# ------------------------------------------------------------

class TestAckPack:
    """
    Verify pack and unpack ack without payload
    """
    def test_pack_requires_ack_instance(self):
        with pytest.raises(TypeError, match="Expected Ack object"):
            pack_ack("not_an_ack")

    def test_response_status_too_large(self):
        ack = Ack(response_status=32) #bin(100000)+1 = 32 

        with pytest.raises(ValueError, match="too large for 5 bits"):
            pack_ack(ack)

    def test_header_byte_structure(self):
        """
        Checking if the header is organized as:
        Top 3 bits = msg_type of ack
        Bottom 5 bits = response_status
        """
        response_status = 5

        packed = pack_ack(Ack(response_status=response_status))

        header = packed[0]

        msg_type = MSG_TYPE_DICT["ack"]

        extracted_msg_type = header >> 5
        extracted_response = header & 0x1F

        assert extracted_msg_type == msg_type
        assert extracted_response == response_status

class TestAckPackPayload:
    """
    Verify pack and unpack ack with payload + edge cases
    """
    def test_with_string_payload(self):
        response_status = 13
        ack_args="OK"
        ack = Ack(response_status, ack_args)

        packed = pack_ack(ack)
        assert packed[1:] == b"OK"

        unpacked = unpack_ack(packed)
        assert unpacked.response_status == response_status
        assert unpacked.ack_args == ack_args

    def test_pack_without_payload(self):
        response_status = 31
        ack = Ack(response_status)

        packed = pack_ack(ack)
        assert len(packed) == 1 

        unpacked = unpack_ack(packed)
        assert unpacked.response_status == response_status

    def test_pack_with_payload_truncation(self):
        response_status = 31
        print("response status", bin(response_status))
        long_string = "A" * (MAX_PACKET_SIZE+10)
        ack = Ack(response_status, ack_args=long_string)

        packed = pack_ack(ack)
        # 1 byte header + (MAX_PACKET_SIZE - 1) payload max
        assert len(packed) == MAX_PACKET_SIZE
        expected_payload_length = MAX_PACKET_SIZE - 1
        assert len(packed[1:]) == expected_payload_length

        unpacked = unpack_ack(packed)
        assert unpacked.response_status == response_status
        assert unpacked.ack_args == long_string[:expected_payload_length]
