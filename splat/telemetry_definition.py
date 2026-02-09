
# Configuration
ENDIANNESS = ">"  # '>' for big-endian, '<' for little-endian
MAX_PACKET_SIZE = 256  # Maximum packet size in bytes


# define the header sizes (ideally they are byte matched)
# in bits
MSG_TYPE_SIZE = 3

REPORT_ID_SIZE = 5      # it will be possible to have 2^5 = 32 reports

VARIABLE_SS_SIZE = 3
VARIABLE_ID_SIZE = 10

COMMAND_ID_SIZE = 13

JPACKET_TID_SIZE = 3
JPACKET_NUM_SIZE = 13   # this is the number of packets for the transaction
JPACKET_SEQ_SIZE = 13   # this is the sequence number of the packet in the transaction

# index for the available subsystems
# [check] - should add a check to make sure that I do not have more ss than what I can have according to the  VARIABLE_SS_SIZE and COMMAND_SS_SIZE
SS_map = {
    "CDH": 0,
    "EPS": 1,
    "ADCS": 2,
    "GPS": 3,
    "STORAGE": 4,
    "COMMS": 5,
}

# this is to map the id to a specific message (cmd, reponse, report... )
MSG_TYPE_DICT = {
    "reports": 0,
    "variable": 1,
    "commands": 2,
    "responses": 3,
    "ota": 4,
    "image_data": 5,
    "ack": 6,
    
}

# Variable definitions
# Format: "var_name": [subsystem, struct_type, scale_factor]
# scale_factor is used to convert to/from SI units (None = no scaling)
var_dict = {
    # --- CDH / SYSTEM ---
    "TIME": ["CDH", "I", None],  # Unix timestamp
    "SC_STATE": ["CDH", "B", None],  # Spacecraft state
    "SD_USAGE": ["CDH", "I", None],  # Bytes
    "CURRENT_RAM_USAGE": ["CDH", "B", None],  # %
    "REBOOT_COUNT": ["CDH", "B", None],  # Count
    "WATCHDOG_TIMER": ["CDH", "B", None],  # Status
    "HAL_BITFLAGS": ["CDH", "B", None],  # Flags
    "DETUMBLING_ERROR_FLAG": ["CDH", "B", None],  # Flag
    # --- EPS (Power) ---
    "EPS_POWER_FLAG": ["EPS", "B", None],
    "MAINBOARD_TEMPERATURE": ["EPS", "h", 10],  # 0.1°C -> °C
    "MAINBOARD_VOLTAGE": ["EPS", "h", 1000],  # mV -> V
    "MAINBOARD_CURRENT": ["EPS", "h", 1000],  # mA -> A
    "BATTERY_PACK_TEMPERATURE": ["EPS", "h", 10],  # 0.1°C -> °C
    "BATTERY_PACK_REPORTED_SOC": ["EPS", "B", 1],  # %
    "BATTERY_PACK_REPORTED_CAPACITY": ["EPS", "H", 1],  # mAh
    "BATTERY_PACK_CURRENT": ["EPS", "h", 1000],  # mA -> A
    "BATTERY_PACK_VOLTAGE": ["EPS", "h", 1000],  # mV -> V
    "BATTERY_PACK_MIDPOINT_VOLTAGE": ["EPS", "h", 1000],  # mV -> V
    "BATTERY_PACK_TTE": ["EPS", "I", 1],  # Seconds
    "BATTERY_PACK_TTF": ["EPS", "I", 1],  # Seconds
    # Coils (Magnetorquers)
    "XP_COIL_VOLTAGE": ["EPS", "h", 1000],
    "XP_COIL_CURRENT": ["EPS", "h", 1000],
    "XM_COIL_VOLTAGE": ["EPS", "h", 1000],
    "XM_COIL_CURRENT": ["EPS", "h", 1000],
    "YP_COIL_VOLTAGE": ["EPS", "h", 1000],
    "YP_COIL_CURRENT": ["EPS", "h", 1000],
    "YM_COIL_VOLTAGE": ["EPS", "h", 1000],
    "YM_COIL_CURRENT": ["EPS", "h", 1000],
    "ZP_COIL_VOLTAGE": ["EPS", "h", 1000],
    "ZP_COIL_CURRENT": ["EPS", "h", 1000],
    "ZM_COIL_VOLTAGE": ["EPS", "h", 1000],
    "ZM_COIL_CURRENT": ["EPS", "h", 1000],
    # Payload & Solar Inputs
    "JETSON_INPUT_VOLTAGE": ["EPS", "h", 1000],
    "JETSON_INPUT_CURRENT": ["EPS", "h", 1000],
    "RF_LDO_OUTPUT_VOLTAGE": ["EPS", "h", 1000],
    "RF_LDO_OUTPUT_CURRENT": ["EPS", "h", 1000],
    "GPS_VOLTAGE": ["EPS", "h", 1000],
    "GPS_CURRENT": ["EPS", "h", 1000],
    # Solar Arrays
    "XP_SOLAR_CHARGE_VOLTAGE": ["EPS", "h", 1000],
    "XP_SOLAR_CHARGE_CURRENT": ["EPS", "h", 1000],
    "XM_SOLAR_CHARGE_VOLTAGE": ["EPS", "h", 1000],
    "XM_SOLAR_CHARGE_CURRENT": ["EPS", "h", 1000],
    "YP_SOLAR_CHARGE_VOLTAGE": ["EPS", "h", 1000],
    "YP_SOLAR_CHARGE_CURRENT": ["EPS", "h", 1000],
    "YM_SOLAR_CHARGE_VOLTAGE": ["EPS", "h", 1000],
    "YM_SOLAR_CHARGE_CURRENT": ["EPS", "h", 1000],
    "ZP_SOLAR_CHARGE_VOLTAGE": ["EPS", "h", 1000],
    "ZP_SOLAR_CHARGE_CURRENT": ["EPS", "h", 1000],
    "ZM_SOLAR_CHARGE_VOLTAGE": ["EPS", "h", 1000],
    "ZM_SOLAR_CHARGE_CURRENT": ["EPS", "h", 1000],
    # --- ADCS ---
    "MODE": ["ADCS", "B", None],
    # Custom 'X' (High Precision) mapped to 'i' with 1e7 scaling
    "GYRO_X": ["ADCS", "f", 10000000],
    "GYRO_Y": ["ADCS", "f", 10000000],
    "GYRO_Z": ["ADCS", "f", 10000000],
    "MAG_X": ["ADCS", "f", 10000000],
    "MAG_Y": ["ADCS", "f", 10000000],
    "MAG_Z": ["ADCS", "f", 10000000],
    "SUN_STATUS": ["ADCS", "B", None],
    "SUN_VEC_X": ["ADCS", "f", 10000000],
    "SUN_VEC_Y": ["ADCS", "f", 10000000],
    "SUN_VEC_Z": ["ADCS", "f", 10000000],
    # Light Sensors
    "LIGHT_SENSOR_XP": ["ADCS", "H", None],
    "LIGHT_SENSOR_XM": ["ADCS", "H", None],
    "LIGHT_SENSOR_YP": ["ADCS", "H", None],
    "LIGHT_SENSOR_YM": ["ADCS", "H", None],
    "LIGHT_SENSOR_ZP1": ["ADCS", "H", None],
    "LIGHT_SENSOR_ZP2": ["ADCS", "H", None],
    "LIGHT_SENSOR_ZP3": ["ADCS", "H", None],
    "LIGHT_SENSOR_ZP4": ["ADCS", "H", None],
    "LIGHT_SENSOR_ZM": ["ADCS", "H", None],
    # Coil Status flags
    "XP_COIL_STATUS": ["ADCS", "B", None],
    "XM_COIL_STATUS": ["ADCS", "B", None],
    "YP_COIL_STATUS": ["ADCS", "B", None],
    "YM_COIL_STATUS": ["ADCS", "B", None],
    "ZP_COIL_STATUS": ["ADCS", "B", None],
    "ZM_COIL_STATUS": ["ADCS", "B", None],
    # --- GPS ---
    "GPS_MESSAGE_ID": ["GPS", "B", None],
    "GPS_FIX_MODE": ["GPS", "B", None],
    "GPS_NUMBER_OF_SV": ["GPS", "B", None],
    "GPS_GNSS_WEEK": ["GPS", "H", None],
    "GPS_GNSS_TOW": ["GPS", "I", None],
    "GPS_LATITUDE": ["GPS", "i", 10000000],  # 1e-7 deg -> deg
    "GPS_LONGITUDE": ["GPS", "i", 10000000],  # 1e-7 deg -> deg
    "GPS_ELLIPSOID_ALT": ["GPS", "i", 100],  # cm -> m
    "GPS_MEAN_SEA_LVL_ALT": ["GPS", "i", 100],  # cm -> m
    "GPS_ECEF_X": ["GPS", "i", 100],  # cm -> m
    "GPS_ECEF_Y": ["GPS", "i", 100],
    "GPS_ECEF_Z": ["GPS", "i", 100],
    "GPS_ECEF_VX": ["GPS", "i", 100],  # cm/s -> m/s
    "GPS_ECEF_VY": ["GPS", "i", 100],
    "GPS_ECEF_VZ": ["GPS", "i", 100],
    # --- STORAGE ---
    "STORAGE_TOTAL": ["STORAGE", "I", None],
    "CDH_NUM_FILES": ["STORAGE", "I", None],
    "CDH_DIR_SIZE": ["STORAGE", "I", None],
    "EPS_NUM_FILES": ["STORAGE", "I", None],
    "EPS_DIR_SIZE": ["STORAGE", "I", None],
    "ADCS_NUM_FILES": ["STORAGE", "I", None],
    "ADCS_DIR_SIZE": ["STORAGE", "I", None],
    "COMMS_NUM_FILES": ["STORAGE", "I", None],
    "COMMS_DIR_SIZE": ["STORAGE", "I", None],
    "GPS_NUM_FILES": ["STORAGE", "I", None],
    "GPS_DIR_SIZE": ["STORAGE", "I", None],
    "PAYLOAD_NUM_FILES": ["STORAGE", "I", None],
    "PAYLOAD_DIR_SIZE": ["STORAGE", "I", None],
    "COMMAND_NUM_FILES": ["STORAGE", "I", None],
    "COMMAND_DIR_SIZE": ["STORAGE", "I", None],
}

# Report definitions
# Each report is a collection of variables that are sent together
# Format: "report_name": {variable_name: subsystem}
report_dict = {
    # Corresponds to MSG_ID_SAT_TM_NOMINAL (0x05)
    "TM_HEARTBEAT": {
        # CDH
        "TIME": "CDH",
        "SC_STATE": "CDH",
        "SD_USAGE": "CDH",
        "CURRENT_RAM_USAGE": "CDH",
        "REBOOT_COUNT": "CDH",
        "WATCHDOG_TIMER": "CDH",
        "HAL_BITFLAGS": "CDH",
        "DETUMBLING_ERROR_FLAG": "CDH",
        # EPS
        "EPS_POWER_FLAG": "EPS",
        "MAINBOARD_TEMPERATURE": "EPS",
        "MAINBOARD_VOLTAGE": "EPS",
        "MAINBOARD_CURRENT": "EPS",
        "BATTERY_PACK_TEMPERATURE": "EPS",
        "BATTERY_PACK_REPORTED_SOC": "EPS",
        "BATTERY_PACK_REPORTED_CAPACITY": "EPS",
        "BATTERY_PACK_CURRENT": "EPS",
        "BATTERY_PACK_VOLTAGE": "EPS",
        "BATTERY_PACK_MIDPOINT_VOLTAGE": "EPS",
        "BATTERY_PACK_TTE": "EPS",
        "BATTERY_PACK_TTF": "EPS",
        "XP_COIL_VOLTAGE": "EPS",
        "XP_COIL_CURRENT": "EPS",
        "XM_COIL_VOLTAGE": "EPS",
        "XM_COIL_CURRENT": "EPS",
        "YP_COIL_VOLTAGE": "EPS",
        "YP_COIL_CURRENT": "EPS",
        "YM_COIL_VOLTAGE": "EPS",
        "YM_COIL_CURRENT": "EPS",
        "ZP_COIL_VOLTAGE": "EPS",
        "ZP_COIL_CURRENT": "EPS",
        "ZM_COIL_VOLTAGE": "EPS",
        "ZM_COIL_CURRENT": "EPS",
        "JETSON_INPUT_VOLTAGE": "EPS",
        "JETSON_INPUT_CURRENT": "EPS",
        "RF_LDO_OUTPUT_VOLTAGE": "EPS",
        "RF_LDO_OUTPUT_CURRENT": "EPS",
        "GPS_VOLTAGE": "EPS",
        "GPS_CURRENT": "EPS",
        "XP_SOLAR_CHARGE_VOLTAGE": "EPS",
        "XP_SOLAR_CHARGE_CURRENT": "EPS",
        "XM_SOLAR_CHARGE_VOLTAGE": "EPS",
        "XM_SOLAR_CHARGE_CURRENT": "EPS",
        "YP_SOLAR_CHARGE_VOLTAGE": "EPS",
        "YP_SOLAR_CHARGE_CURRENT": "EPS",
        "YM_SOLAR_CHARGE_VOLTAGE": "EPS",
        "YM_SOLAR_CHARGE_CURRENT": "EPS",
        "ZP_SOLAR_CHARGE_VOLTAGE": "EPS",
        "ZP_SOLAR_CHARGE_CURRENT": "EPS",
        "ZM_SOLAR_CHARGE_VOLTAGE": "EPS",
        "ZM_SOLAR_CHARGE_CURRENT": "EPS",
        # ADCS
        "MODE": "ADCS",
        "GYRO_X": "ADCS",
        "GYRO_Y": "ADCS",
        "GYRO_Z": "ADCS",
        "MAG_X": "ADCS",
        "MAG_Y": "ADCS",
        "MAG_Z": "ADCS",
        "SUN_STATUS": "ADCS",
        "SUN_VEC_X": "ADCS",
        "SUN_VEC_Y": "ADCS",
        "SUN_VEC_Z": "ADCS",
        "LIGHT_SENSOR_XP": "ADCS",
        "LIGHT_SENSOR_XM": "ADCS",
        "LIGHT_SENSOR_YP": "ADCS",
        "LIGHT_SENSOR_YM": "ADCS",
        "LIGHT_SENSOR_ZP1": "ADCS",
        "LIGHT_SENSOR_ZP2": "ADCS",
        "LIGHT_SENSOR_ZP3": "ADCS",
        "LIGHT_SENSOR_ZP4": "ADCS",
        "LIGHT_SENSOR_ZM": "ADCS",
        "XP_COIL_STATUS": "ADCS",
        "XM_COIL_STATUS": "ADCS",
        "YP_COIL_STATUS": "ADCS",
        "YM_COIL_STATUS": "ADCS",
        "ZP_COIL_STATUS": "ADCS",
        "ZM_COIL_STATUS": "ADCS",
        # GPS
        "GPS_MESSAGE_ID": "GPS",
        "GPS_FIX_MODE": "GPS",
        "GPS_NUMBER_OF_SV": "GPS",
        "GPS_GNSS_WEEK": "GPS",
        "GPS_GNSS_TOW": "GPS",
        "GPS_LATITUDE": "GPS",
        "GPS_LONGITUDE": "GPS",
        "GPS_ELLIPSOID_ALT": "GPS",
        "GPS_MEAN_SEA_LVL_ALT": "GPS",
        "GPS_ECEF_X": "GPS",
        "GPS_ECEF_Y": "GPS",
        "GPS_ECEF_Z": "GPS",
        "GPS_ECEF_VX": "GPS",
        "GPS_ECEF_VY": "GPS",
        "GPS_ECEF_VZ": "GPS",
    },
    # Corresponds to MSG_ID_SAT_TM_STORAGE (0x03)
    "TM_STORAGE": {
        "TIME": "CDH",
        "SC_STATE": "CDH",
        "SD_USAGE": "CDH",
        "CURRENT_RAM_USAGE": "CDH",
        "REBOOT_COUNT": "CDH",
        "WATCHDOG_TIMER": "CDH",
        "HAL_BITFLAGS": "CDH",
        "DETUMBLING_ERROR_FLAG": "CDH",
        "STORAGE_TOTAL": "STORAGE",
        "CDH_NUM_FILES": "STORAGE",
        "CDH_DIR_SIZE": "STORAGE",
        "EPS_NUM_FILES": "STORAGE",
        "EPS_DIR_SIZE": "STORAGE",
        "ADCS_NUM_FILES": "STORAGE",
        "ADCS_DIR_SIZE": "STORAGE",
        "COMMS_NUM_FILES": "STORAGE",
        "COMMS_DIR_SIZE": "STORAGE",
        "GPS_NUM_FILES": "STORAGE",
        "GPS_DIR_SIZE": "STORAGE",
        "PAYLOAD_NUM_FILES": "STORAGE",
        "PAYLOAD_DIR_SIZE": "STORAGE",
        "COMMAND_NUM_FILES": "STORAGE",
        "COMMAND_DIR_SIZE": "STORAGE",
    },
    # Corresponds to MSG_ID_SAT_TM_HAL (0x02)
    "TM_HAL": {
        "TIME": "CDH",
        "SC_STATE": "CDH",
        "SD_USAGE": "CDH",
        "CURRENT_RAM_USAGE": "CDH",
        "REBOOT_COUNT": "CDH",
        "WATCHDOG_TIMER": "CDH",
        "HAL_BITFLAGS": "CDH",
        "DETUMBLING_ERROR_FLAG": "CDH",
    },
    
    "TM_TEST":{
        "TIME": "CDH",
        "SC_STATE": "CDH",
        "GPS_MESSAGE_ID": "GPS",
    }
}

# Argument type definitions
# These are the possible argument types for commands
argument_dict = {
    "target_state_id": "B",  # Target state ID
    "time_in_state": "I",  # Time to stay in the state (seconds)
    "time_reference": "I",  # Unix timestamp for time reference
    "file_id": "I",  # ID of the file to request/downlink
    "file_time": "I",  # Timestamp of the file to request/downlink

    "op1": "I",  # Operand 1 for math operations
    "op2": "I",  # Operand 2 for math operations
    
}

# Return type definitions
return_dict = {
    "status": "B",  # Command status (success/fail)
    "check": "B",  # Checksum or validation byte
    "ack": "?",  # Boolean acknowledgment
}



# command name, precondition function, argument list, function to be called in satellite
# [check] - should i add the subsystem here
command_list = [
    ("FORCE_REBOOT", None, [], "FORCE_REBOOT"),
    ("SUM", "valid_inputs", ["op1", "op2"], "SUM"),
    ("SWITCH_TO_STATE", "valid_state", ["target_state_id", "time_in_state"], "SWITCH_TO_STATE"),
    ("UPLINK_TIME_REFERENCE", "valid_time_format", ["time_reference"], "UPLINK_TIME_REFERENCE"),
    ("TURN_OFF_PAYLOAD", None, [], "TURN_OFF_PAYLOAD"),
    ("SCHEDULE_OD_EXPERIMENT", None, [], "SCHEDULE_OD_EXPERIMENT"),
    ("REQUEST_TM_NOMINAL", None, [], "REQUEST_TM_NOMINAL"),
    ("REQUEST_TM_HAL", None, [], "REQUEST_TM_HAL"),
    ("REQUEST_TM_STORAGE", None, [], "REQUEST_TM_STORAGE"),
    ("REQUEST_TM_PAYLOAD", None, [], "REQUEST_TM_PAYLOAD"),
    (
        "REQUEST_FILE_METADATA",
        "file_id_exists",
        ["file_id", "file_time"],
        "REQUEST_FILE_METADATA",
    ),
    ("REQUEST_FILE_PKT", "file_id_exists", ["file_id", "file_time"], "REQUEST_FILE_PKT"),
    ("REQUEST_IMAGE", None, [], "REQUEST_IMAGE"),
    ("DOWNLINK_ALL", "file_id_exists", ["file_id", "file_time"], "DOWNLINK_ALL"),
]



# Command IDs (sorted alphabetically to ensure consistency)
all_cmd_names = [x[0] for x in command_list]   # [check] - maybe this could go to the codec page
COMMAND_IDS = {name: idx for idx, name in enumerate(all_cmd_names)}
# COMMAND_NAMES = {idx: name for name, idx in COMMAND_IDS.items()} ## dont need this anymore because I am using a list now

# Report IDs (sorted alphabetically to ensure consistency)
REPORT_IDS = {report: idx for idx, report in enumerate(sorted(report_dict.keys()))}
REPORT_NAMES = {idx: report for report, idx in REPORT_IDS.items()}

# Variable IDs
# We filter the variables for the subsystem, then SORT them before assigning IDs
VAR_ID_TO_NAME = {
    ss_id: {
        idx: name 
        for idx, name in enumerate(
            sorted(k for k, v in var_dict.items() if v[0] == ss_name)
        )
    } 
    for ss_name, ss_id in SS_map.items()
}



# This will be used to create the report order list. Does not have the same format as the previous
# has all the varialbes as keys and value is a tuple of (subsystem, var_id)
VAR_NAME_TO_ID = {name: (ss_id, var_id) for ss_id, vars in VAR_ID_TO_NAME.items() for var_id, name in vars.items()}
# these are the dictionaries that will be used to force an order on packing and unpacking
ORDERED_SS_LIST = sorted(SS_map, key=SS_map.get)



# this is a dict that will have the report name as key and the value is a list with the odered variables as tuples
# the format of the list will be [[var_id, var_ss],....]
# [check] - do not love having this here. There might be a more clever solution to avoid this
# but I think not having a json/yml and having everythin in a python file and human readable is quite important
ORDERED_REPORT_DICT = {}

for report_name in report_dict:

    # get all the variables in the report
    report_vars = report_dict[report_name].keys()

    # build the list of variables in the desired format (var_id, var_ss)
    packing_list = []
    for var_name in report_vars:
        if var_name in VAR_NAME_TO_ID:
            ss_id, var_id = VAR_NAME_TO_ID[var_name]
            packing_list.append([var_id, ss_id])
        else:
            print(f"Warning: Variable {var_name} not found in ID definitions.")

    # Sort the list
    # Primary Sort Key: x[1] (Subsystem ID) - to group by CDH, EPS, etc.
    # Secondary Sort Key: x[0] (Variable ID) - to order 0, 1, 2... within that subsystem
    packing_list.sort(key=lambda x: (x[1], x[0]))
    
    ORDERED_REPORT_DICT[report_name] = packing_list

