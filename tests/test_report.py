import struct
import pytest
from splat.telemetry_codec import (
    Report,
    REPORT_IDS,
    pack_report,
    unpack_report,
    ORDERED_REPORT_DICT,
    VAR_ID_TO_NAME,
    SS_map
)
from splat.telemetry_definition import (
    REPORT_NAMES,
    MSG_TYPE_SIZE,
    REPORT_ID_SIZE,
    MSG_TYPE_DICT
)
from splat.telemetry_helper import get_report_format

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
        
    def test_get_variable_name_list_not_in_report(self):
        r = Report("TM_TEST")
        with pytest.raises(ValueError, match="Subsystem 'BAD_SS' does not exist in report"):
            r.get_variable_name_list("BAD_SS")

    def test_repr(self):
        r = Report("TM_TEST")
        repr_str = repr(r)
        assert "TM_TEST" in repr_str
        assert "id=4" in repr_str
        assert "variables=3" in repr_str


class TestReportPackUnpack:

    @pytest.mark.parametrize("report_id, report_name", REPORT_NAMES.items())
    def test_round_trip_all_reports(self, report_id, report_name):
        """
        Pack all variable into one report and check if it's unpacked correctly
        """
        report = Report(report_name)

        # Assign deterministic test values
        for var_id, ss_id in ORDERED_REPORT_DICT[report_name]:
            var_name = VAR_ID_TO_NAME[ss_id][var_id]
            ss_name = [k for k, v in SS_map.items() if v == ss_id][0]

            # add the variable with arbiturary value
            report.add_variable(var_name, ss_name, 42)

        packed = pack_report(report)
        unpacked = unpack_report(packed)

        assert unpacked.name == report.name
        assert unpacked.report_id == report.report_id

        for var_id, ss_id in ORDERED_REPORT_DICT[report_name]:
            var_name = VAR_ID_TO_NAME[ss_id][var_id]
            ss_name = [k for k, v in SS_map.items() if v == ss_id][0]

            assert (
                unpacked.variables[ss_name][var_name]
                == report.variables[ss_name][var_name]
            )

    def test_default_variable(self):
        """
        Check if all varaible has default 0 value if not set a custom one
        """

        report_id, report_name = next(iter(REPORT_NAMES.items()))
        report = Report(report_name)

        packed = pack_report(report)
        unpacked = unpack_report(packed)

        for var_id, ss_id in ORDERED_REPORT_DICT[report_name]:
            var_name = VAR_ID_TO_NAME[ss_id][var_id]
            ss_name = [k for k, v in SS_map.items() if v == ss_id][0]

            assert unpacked.variables[ss_name][var_name] == 0

    def test_invalid_type_pack(self):
        """
        pack_report should raise TypeError if not given a Report.
        """
        with pytest.raises(TypeError):
            pack_report("not_a_report")

    def test_unknown_report_id_unpack(self):
        """
        Unpack_report should raise ValueError for unknown report ID.
        """

        header_size = MSG_TYPE_SIZE + REPORT_ID_SIZE

        invalid_id = max(REPORT_NAMES.keys()) + 10 # idmaxxing
        header = (
            (MSG_TYPE_DICT["reports"] << (header_size - MSG_TYPE_SIZE))
            | invalid_id
        )
        header_bytes = header.to_bytes(header_size // 8, "big")
        fake_packet = header_bytes + b"SOME VALUE" 
        # Before the fake packet can be unpacked, 
        # the incorrect report id should be caught first

        with pytest.raises(ValueError, match="Unknown report ID"):
            unpack_report(fake_packet)

    def test_header_correctly_encoded(self):
        """
        Ensure header properly encodes msg_type and report_id.
        """

        report_id, report_name = next(iter(REPORT_NAMES.items()))
        report = Report(report_name)

        packed = pack_report(report)

        header_size = MSG_TYPE_SIZE + REPORT_ID_SIZE
        header_bytes = packed[: header_size // 8]
        header_int = int.from_bytes(header_bytes, "big")

        # calculates the report header manually, compare correctness
        extracted_report_id = header_int & (
            (1 << (header_size - MSG_TYPE_SIZE)) - 1
        )

        extracted_msg_type = header_int >> (header_size - MSG_TYPE_SIZE)

        assert extracted_report_id == report_id
        assert extracted_msg_type == MSG_TYPE_DICT["reports"]

    def test_payload_size_matches_struct(self):
        """
        Ensure payload length matches struct format size.
        """

        report_id, report_name = next(iter(REPORT_NAMES.items()))
        report = Report(report_name)

        packed = pack_report(report)

        header_size = MSG_TYPE_SIZE + REPORT_ID_SIZE
        payload = packed[header_size // 8 :]

        format_str = get_report_format(report_name)

        assert len(payload) == struct.calcsize(format_str)