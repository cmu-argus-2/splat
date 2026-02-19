import pytest

from splat.telemetry_codec import Ack


# ------------------------------------------------------------
# Initialization Tests
# ------------------------------------------------------------

class TestAckInitialization:

    def test_ack_with_string_args(self):
        ack = Ack(response_id=1, ack_args="OK")

        assert ack.response_id == 1
        assert ack.ack_args == "OK"

    def test_ack_with_non_string_args(self):
        ack = Ack(response_id=2, ack_args=123)

        assert ack.response_id == 2
        assert ack.ack_args == "123"  # converted to string

    def test_ack_with_none_args(self):
        ack = Ack(response_id=3)

        assert ack.response_id == 3
        assert ack.ack_args is None


# ------------------------------------------------------------
# Representation Tests
# ------------------------------------------------------------

class TestAckRepresentation:

    def test_repr_with_args(self):
        ack = Ack(response_id=5, ack_args="SUCCESS")

        repr_str = repr(ack)

        assert "rid=5" in repr_str
        assert "SUCCESS" in repr_str

    def test_repr_without_args(self):
        ack = Ack(response_id=7)

        repr_str = repr(ack)

        assert "rid=7" in repr_str
        assert "None" in repr_str
