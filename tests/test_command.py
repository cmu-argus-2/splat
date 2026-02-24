import pytest
from splat.telemetry_codec import (
    Command,
    COMMAND_IDS,
    COMMAND_ID_SIZE,
    MSG_TYPE_SIZE,
    pack_command, unpack_command
)

from splat.telemetry_definition import(
    command_list,
    argument_dict,
    MSG_TYPE_DICT
)
from splat.telemetry_helper import(
    all_cmd_names,
    get_command_format,
    get_command_size
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
    """
    Tests Command class utilities about add/set arguments
    """
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

    # --- get_argument ---
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

class TestCommandHelpers:
    def test_command_get_command_format(self):
        """
        Tests get_command_format
        """
        cmd = "SUM"
        cmd_struct_format = ">II"
        assert get_command_format(cmd) == cmd_struct_format

        with pytest.raises(ValueError,match="not found in command_list"):
            assert get_command_format("BAD_CMD")

    # check if command is an instance of Command
    # check len of get_command_size() and see

# ------------------------------------------------------------
# Pack/Unpacking Tests
# ------------------------------------------------------------

class TestCommandPack:
    

    def test_pack_requires_command_instance(self):
        """
        Only Command types can be packed
        """
        with pytest.raises(TypeError, match= "Expected Command object"):
            pack_command("BAD_CMD")


    def test_missing_required_argument_raises(self):
        """
        Pick the first command with at least one argument and check
        if an exception was raised
        """
        # pick first command that has at least one argument
        for cmd_id, cmd_data in enumerate(command_list):
            arg_names = cmd_data[2]
            if arg_names:
                cmd_name = all_cmd_names[cmd_id]
                cmd = Command(cmd_name)

                # do NOT set arguments
                print(f"cmd{cmd}") 
                with pytest.raises(ValueError, match="not set for command"):
                    pack_command(cmd)
                return

        pytest.skip("No command with arguments found")


    def test_header_bits_correct(self):
        """
        Checks command packing to see if headers are packed correctly 
        Assumes that Command is defined correctly
        """
        # cmd_id = next(iter(command_list))
        # cmd_name = all_cmd_names[cmd_id]

        cmd_id, cmd_data = next(enumerate(command_list))
        cmd_name = cmd_data[0]
        print(cmd_data)
        cmd = Command(cmd_name)

        # set dummy values for arguments, can be any
        for arg in cmd.arg_names:
            if 's' in argument_dict[arg]:
                cmd.add_argument(arg, "A")
            elif 'p' in argument_dict[arg]:
                cmd.add_argument(arg, b"A")
            else:
                cmd.add_argument(arg, 1)

        packed = pack_command(cmd)

        header_size = MSG_TYPE_SIZE + COMMAND_ID_SIZE
        header_bytes = packed[:header_size // 8]
        header_int = int.from_bytes(header_bytes, "big")

        msg_type = header_int >> COMMAND_ID_SIZE
        command_id = header_int & ((1 << COMMAND_ID_SIZE) - 1)

        assert msg_type == MSG_TYPE_DICT["commands"]
        assert command_id == cmd.command_id

class TestCommandPackArguments:
    """
    Test pack/unpacking with different types of arguments.
    Specifically: fixed-sized numeric types, string types, and binary types (pascal string)
    """

    def test_round_trip_fixed_args(self):
        """
        Checks Command pack/unpacking with fixed-sized numeric args
        """
        for cmd_id, cmd_data in enumerate(command_list):
            arg_names = cmd_data[2]

            # skip commands with string/binary args for this test
            if any('s' in argument_dict[a] or 'p' in argument_dict[a] for a in arg_names):
                continue

            cmd_name = cmd_data[0]
            cmd = Command(cmd_name)

            # assign simple values
            for arg in arg_names:
                print(f"arg: {arg}")
                cmd.add_argument(arg, 1)

            packed = pack_command(cmd)
            unpacked = unpack_command(packed)

            assert unpacked.name == cmd.name
            assert unpacked.command_id == cmd.command_id

            for arg in arg_names:
                assert unpacked.get_argument(arg) == 1

            return  # test only first suitable command

        pytest.skip("No fixed-argument command found")
        # it shouldn't reach here


    def test_round_trip_string_argument(self):
        """
        Checks Command pack/unpacking with string args
        """
        for cmd_id, cmd_data in enumerate(command_list):
            arg_names = cmd_data[2]


            string_args = [a for a in arg_names if 's' in argument_dict[a]]
            if not string_args:
                continue

            cmd_name = cmd_data[0]
            # print(cmd_name)
            cmd = Command(cmd_name)
            # print(cmd)
            # print(arg_names)
            for arg in arg_names:
                if arg in string_args:
                    cmd.add_argument(arg, "HELLO TEST ARG")
                else:
                    cmd.add_argument(arg, 1)

            packed = pack_command(cmd)
            unpacked = unpack_command(packed)

            for arg in arg_names:
                assert unpacked.name == cmd.name
                assert unpacked.get_argument(arg) == cmd.get_argument(arg)
            return

        pytest.skip("No string-argument command found")


    def test_round_trip_binary_argument(self):
        """
        Checks Command pack/unpacking with binary args
        """
        for cmd_id, cmd_data in enumerate(command_list):
            arg_names = cmd_data[2]

            binary_args = [a for a in arg_names if 'p' in argument_dict[a]]
            if not binary_args:
                continue

            cmd_name = all_cmd_names[cmd_id]
            cmd = Command(cmd_name)

            for arg in arg_names:
                if arg in binary_args:
                    cmd.add_argument(arg, b"HELLO TEST ARG") # append arg as binary data
                else:
                    cmd.add_argument(arg, 1)

            packed = pack_command(cmd)
            unpacked = unpack_command(packed)

            for arg in arg_names:
                assert unpacked.get_argument(arg) == cmd.get_argument(arg)

            return

        pytest.skip("No binary-argument command found")


    def test_unknown_command_id(self):
        header_size = MSG_TYPE_SIZE + COMMAND_ID_SIZE

        fake_command_id = (1 << COMMAND_ID_SIZE) - 1  # max possible ID
        header_int = (MSG_TYPE_DICT["commands"] << COMMAND_ID_SIZE) | fake_command_id

        header_bytes = header_int.to_bytes(header_size // 8, "big")

        with pytest.raises(ValueError, match="Unknown command ID"):
            unpack_command(header_bytes)


    