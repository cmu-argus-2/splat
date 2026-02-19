import pytest

from splat.telemetry_codec import Variable
from splat.telemetry_definition import (
    var_dict,
    SS_map,
    VAR_ID_TO_NAME,
    VAR_NAME_TO_ID
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
