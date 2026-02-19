import pytest
import splat.telemetry_definition
from splat.telemetry_codec import (
    Report,
    REPORT_IDS
)

# ------------------------------------------------------------
# Initialization Tests
# ------------------------------------------------------------

class TestReportInitialization:
    """
    Tests initialization of the Report class.
    """

    @pytest.mark.parametrize("report_name",list(REPORT_IDS.keys()))
    
    def test_valid_report_init(self, report_name):
        r = Report(report_name)
        
        assert r.name in REPORT_IDS.keys()
        assert r.report_id == REPORT_IDS[r.name]

    # NOTE: maybe you shouldn't be allowed to initiate without a param? tbh?
    @pytest.mark.parametrize("r_name", ["BAD_NAME", "", None])
    def test_invalid_report_init(self, r_name):
        with pytest.raises(ValueError, match="not found in report_dict"):
            Report(r_name)

# ------------------------------------------------------------
# Variable Manipulation Tests
# ------------------------------------------------------------

class TestReportUtilities: 
    """
    Tests getter + setter + repr of the Report class.
    """

    # --- add_variable ---
    def test_add_variable_success(self):
        r = Report("TM_TEST")

        r.add_variable("TIME", "CDH", 25)

        assert r.get_variable("TIME") == 25

    def test_add_variable_wrong_ss(self):
        r = Report("TM_TEST")
        with pytest.raises(ValueError, match="belongs to subsystem 'CDH', not 'GPS"):
            r.add_variable("TIME", "GPS", 25)

    def test_add_variable_not_in_report(self):
        r = Report("TM_TEST")
        with pytest.raises(ValueError, match="not in report"):
            r.add_variable("BAD_VAR", "GPS", 25)

    # --- set_variable ---
    def test_set_variables_success(self):
        r = Report("TM_TEST")
        r.set_variables(TIME=0,SC_STATE=5,GPS_MESSAGE_ID=1)
        assert r.get_variable("TIME") == 0
        assert r.get_variable("SC_STATE") == 5
        assert r.get_variable("GPS_MESSAGE_ID") == 1
        
    def test_set_variables_not_in_report(self):
        r = Report("TM_TEST")
        with pytest.raises(ValueError, match="Variable 'BAD_VAR' not in report"):
            r.set_variables(BAD_VAR=10)
 
    # --- get_variable ---
    def test_get_variable_not_in_report(self):
        r = Report("TM_TEST")
        with pytest.raises(ValueError, match="Variable 'BAD_VAR' not in report"):
            r.get_variable("BAD_VAR")   

    def test_get_variable_name_list_success(self):
        r = Report("TM_TEST")
        assert r.get_variable_name_list("CDH") == ["TIME","SC_STATE"]
        assert r.get_variable_name_list("GPS") == ["GPS_MESSAGE_ID"]
        
    def test_get_variable_name_list_not_in_r(self):
        r = Report("TM_TEST")
        with pytest.raises(ValueError, match="Subsystem 'BAD_SS' does not exist in report"):
            r.get_variable_name_list("BAD_SS")

    def test_repr(self):
        r = Report("TM_TEST")
        repr_str = repr(r)
        assert "TM_TEST" in repr_str
        assert "id=4" in repr_str
        assert "variables=3" in repr_str