import pytest

from splat.telemetry_codec import (
    Variable,
    pack_variable,
    unpack_variable
)
from splat.telemetry_definition import (
    MAX_PACKET_SIZE,
    MSG_TYPE_DICT,
    MSG_TYPE_SIZE,
    VARIABLE_ID_SIZE,
    VARIABLE_SS_SIZE,
    var_dict,
    SS_map,
    VAR_ID_TO_NAME,
    VAR_NAME_TO_ID,
)


# ------------------------------------------------------------
# Initialization Tests
# ------------------------------------------------------------

class TestVariableInitialization:

    @pytest.mark.parametrize("var_name", list(var_dict.keys()))
    def test_valid_variable_name_exists(self, var_name):
        """
        Ensures all defined variables can be instantiated
        with a valid subsystem that contains them.
        """
        # given var_name, fetch the id and stuff
        var_ss_id, var_id = VAR_NAME_TO_ID[var_name]
        # something janky. basically just reverse extract the subsystem for the variable
        var_ss = {ss_name for ss_name, ss_id in SS_map.items() if ss_id == var_ss_id}.pop()

        var = Variable(var_name, var_ss)

        assert var.name == var_name
        assert var.subsystem == var_ss
        assert var.subsystem_id == var_ss_id
        assert var.var_id == var_id
        return

    def test_invalid_variable_name(self):
        """
        Ensures that non-existant or variables in
        the wrong subsystems are caught
        """
        with pytest.raises(ValueError, match="not found in var_dict"):
            Variable("BAD_VAR", "CDH")

        with pytest.raises(ValueError, match="not found in subsystem"):
            Variable("MAG_X", "CDH")

# ------------------------------------------------------------
# Value Handling Tests
# ------------------------------------------------------------

class TestVariableValueHandling:

    def test_set_value(self):
        # run one set_value test for every subsystem
        for subsystem, subsystem_id in SS_map.items():
            if subsystem_id in VAR_ID_TO_NAME:
                var_id, var_name = next(iter(VAR_ID_TO_NAME[subsystem_id].items()))
                var = Variable(var_name, subsystem)

                var.set_value(42)
                assert var.value == 42
                return

        pytest.skip("No valid variable found")


# ------------------------------------------------------------
# Representation Tests
# ------------------------------------------------------------

class TestVariableRepresentation:

    def test_repr(self):
        for subsystem, subsystem_id in SS_map.items():
            if subsystem_id in VAR_ID_TO_NAME:
                var_id, var_name = next(iter(VAR_ID_TO_NAME[subsystem_id].items()))
                var = Variable(var_name, subsystem, value=10)

                repr_str = repr(var)
                assert var_name in repr_str
                assert subsystem in repr_str
                assert "10" in repr_str
                return

        pytest.skip("No valid variable found")


# ------------------------------------------------------------
# Pack/Unpacking Tests
# ------------------------------------------------------------

class TestVariablePack:
    """
    Verifying packing and unpacking of a variable
    """
    def test_pack_requires_ack_instance(self):
        with pytest.raises(TypeError, match="Expected Variable object"):
            pack_variable("not_an_var")


    @pytest.mark.parametrize("var", var_dict.items())
    def test_unpack_success(self,var):
        """
        Tests packing (with payload) and check if it can be
        unpacked successfully
        """
        # extract the var name. jank.
        (var_name, var_data) = var
        # var_id, (var_name, var_data) = next(enumerate(var_dict.items()))
        var_struct_type = var_data[1]

        if var_struct_type in ("B", "H", "I", "Q"):
            test_value = 5
        elif var_struct_type in ("f", "d"):
            test_value = 1.5
        else:
            test_value = 1

        v = Variable(var_name=var_name,
                            subsystem=var_data[0],
                            value=test_value)
        
        packed = pack_variable(v)
        unpacked = unpack_variable(packed)
        assert unpacked.name == v.name
        assert unpacked.subsystem == v.subsystem
        assert unpacked.subsystem_id == v.subsystem_id
        assert unpacked.value == v.value 
        

    def test_header_encoding_correct(self):
        """
        Checks header if it encodes msg_type, subsystem, and variable_id correctly.
        """

        var_name, var_data = next(iter(var_dict.items()))
        subsystem_name = var_data[0]

        v = Variable(var_name, subsystem_name)
        v.set_value(1) # type variation was checked before so this is ok

        packed = pack_variable(v)

        header_size = MSG_TYPE_SIZE + VARIABLE_SS_SIZE + VARIABLE_ID_SIZE
        header_bytes = packed[: (header_size + 7) // 8]
        header_int = int.from_bytes(header_bytes, "big")

        # NOTE: header_msg_type should be checked in universal unpack
        extracted_ss = (header_int >> VARIABLE_ID_SIZE) & ((1 << VARIABLE_SS_SIZE) - 1)
        extracted_var_id = header_int & ((1 << VARIABLE_ID_SIZE) - 1)

        assert extracted_ss == v.subsystem_id
        assert extracted_var_id == v.var_id
        

    def test_unpack_unknown_variable_id(self):
        """
        Check unknown variable id error
        """
        # Since we're testing specifically unpack and not the variable set up
        # We need to manually change the header to check trigger
        header_size = MSG_TYPE_SIZE + VARIABLE_SS_SIZE + VARIABLE_ID_SIZE

        fake_ss = 0
        fake_var_id = 999  

        header = (
            (MSG_TYPE_DICT["variable"] << (header_size - MSG_TYPE_SIZE))
            | (fake_ss << VARIABLE_ID_SIZE)
            | fake_var_id
        )

        header_bytes = header.to_bytes((header_size + 7) // 8, "big")
        fake_payload = b"TEST_VALUE"

        with pytest.raises(ValueError):
            unpack_variable(header_bytes + fake_payload)