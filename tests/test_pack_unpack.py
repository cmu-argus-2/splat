import pytest

from splat.telemetry_codec import (
    Report, REPORT_NAMES, pack_report, 
    Variable, pack_variable,
    Command, pack_command,
    Ack, pack_ack,
    pack,unpack,
    MSG_TYPE_SIZE,
    command_list
)

from splat.telemetry_definition import(
    var_dict
)


class TestUniversalPackUnpack:
    """
    Tests the universal pack() and unpack() dispatcher logic.
    """

    # -------------------------
    # PACK DISPATCH TESTS
    # -------------------------

    def test_pack_dispatch_report(self):
        report_id, report_name = next(iter(REPORT_NAMES.items()))
        r = Report(report_name)

        packed = pack(r)

        # Ensure universal pack equals specific pack
        assert packed == pack_report(r)

    def test_pack_dispatch_variable(self):
        var_name, var_data = next(iter(var_dict.items()))
        v = Variable(var_name, var_data[0])
        v.set_value(1)

        packed = pack(v)

        assert packed == pack_variable(v)

    def test_pack_dispatch_command(self):
        cmd_name = command_list[0][0]
        c = Command(cmd_name)

        packed = pack(c)

        assert packed == pack_command(c)

    def test_pack_dispatch_ack(self):
        a = Ack(1, "OK")

        packed = pack(a)

        assert packed == pack_ack(a)

    def test_pack_invalid_type(self):
        with pytest.raises(TypeError):
            pack(12345)

    # -------------------------
    # UNPACK DISPATCH TESTS
    # -------------------------

    def test_unpack_dispatch_report(self):
        report_id, report_name = next(iter(REPORT_NAMES.items()))
        r = Report(report_name)

        packed = pack_report(r)
        unpacked = unpack(packed)

        assert isinstance(unpacked, Report)
        assert unpacked.name == r.name

    def test_unpack_dispatch_variable(self):
        var_name, var_data = next(iter(var_dict.items()))
        v = Variable(var_name, var_data[0])
        v.set_value(5)

        packed = pack_variable(v)
        unpacked = unpack(packed)

        assert isinstance(unpacked, Variable)
        assert unpacked.name == v.name
        assert unpacked.value == v.value

    def test_unpack_dispatch_command(self):
        cmd_name = command_list[0][0]
        c = Command(cmd_name)

        packed = pack_command(c)
        unpacked = unpack(packed)

        assert isinstance(unpacked, Command)
        assert unpacked.name == c.name

    def test_unpack_dispatch_ack(self):
        a = Ack(2, "HELLO")

        packed = pack_ack(a)
        unpacked = unpack(packed)

        assert isinstance(unpacked, Ack)
        assert unpacked.response_status == a.response_status
        assert unpacked.ack_args == a.ack_args

    def test_unpack_unknown_msg_type(self):
        """
        Create a fake packet with invalid msg_type.
        """
        invalid_msg_type = 7  # choose a value not used in MSG_TYPE_DICT

        fake_header = invalid_msg_type << (8 - MSG_TYPE_SIZE)
        fake_packet = bytes([fake_header]) + b"\x00\x00"

        with pytest.raises(ValueError):
            unpack(fake_packet)