import pytest
import splat.telemetry_definition
from splat.telemetry_codec import (
    Command,
    COMMAND_IDS
)

# ------------------------------------------------------------
# Initialization Tests
# ------------------------------------------------------------

class TestCommandInitialization:
    """
    Tests initialization of the Command class.
    """
    # @pytest.mark.parametrize("cmd_name", COMMAND_IDS.keys())
    def test_valid_command_init(self):
        cmd = Command("SUM")
        assert cmd.name == "SUM"
        assert cmd.command_id == 1
        assert cmd.precondition == "valid_inputs"
        assert cmd.satellite_func == "SUM"
        assert cmd.arg_names == ["op1", "op2"]
        assert cmd.arguments == {}
        
    
    def test_invalid_command_init(self):
        with pytest.raises(ValueError, match="not found in command_list"):
            Command("BAD_CMD")

class TestCommandUtilities:

    # --- add_argument --- 
    def test_add_argument_success(self):
        cmd = Command("SUM")
        cmd.add_argument("op1",10)
        assert cmd.get_argument("op1") == 10

    def test_add_argument_invalid(self):
        cmd = Command("SUM")
        with pytest.raises(ValueError, match= "not valid for command"):
            cmd.add_argument("BAD_ARG", 10)

    # --- set_arguments ---
    def test_set_arguments_positional(self):
        cmd = Command("SUM")
        cmd.set_arguments(3, 5)

        assert cmd.get_argument("op1") == 3
        assert cmd.get_argument("op2") == 5

    def test_set_arguments_keyword(self):
        cmd = Command("SUM")
        cmd.set_arguments(op1=7, op2=9)

        assert cmd.get_argument("op1") == 7
        assert cmd.get_argument("op2") == 9

    def test_set_arguments_mixed(self):
        cmd = Command("SUM")
        cmd.set_arguments(1, op2=99)

        assert cmd.get_argument("op1") == 1
        assert cmd.get_argument("op2") == 99

    def test_set_arguments_too_many_positional(self):
        cmd = Command("SUM")
        with pytest.raises(ValueError, match="Too many positional arguments"):
            cmd.set_arguments(1, 2, 3)

    def test_get_argument_unset_returns_none(self):
        cmd = Command("SUM")
        print(f"test: {cmd.get_argument("op1")}")
        assert cmd.get_argument("op1") is None

    # --- get_arguments_list ---
    def test_get_arguments_list_order(self):
        cmd = Command("SUM")
        cmd.set_arguments(op1=10, op2=20)

        arg_list = cmd.get_arguments_list()

        assert arg_list == [10, 20]

    def test_get_arguments_list_partial(self):
        cmd = Command("SUM")
        cmd.set_arguments(op2=5)

        arg_list = cmd.get_arguments_list()

        assert arg_list == [None,5]