
# Configuration
ENDIANNESS = ">"  # '>' for big-endian, '<' for little-endian
MAX_PACKET_SIZE = 255  # Maximum packet size in bytes this is already disconting the header
# but we are not considering encryption here
# it would be nice to handle encryption here but we are not sending in all of the commands

CALLSIGN_SIZE = 6  # Number of bytes for callsign (6 letter string)

# define the header sizes (ideally they are byte matched)
# in bits
MSG_TYPE_SIZE = 3

REPORT_ID_SIZE = 5      # it will be possible to have 2^5 = 32 reports

VARIABLE_SS_SIZE = 3
VARIABLE_ID_SIZE = 10

COMMAND_ID_SIZE = 13


TID_SIZE = 5
FRAGMENT_SEQ_SIZE = 16
MAX_PAYLOAD_SIZE = MAX_PACKET_SIZE - CALLSIGN_SIZE - (FRAGMENT_SEQ_SIZE//8) - 1  # the one is the msg type + tid size

# index for the available subsystems
# [check] - should add a check to make sure that I do not have more ss than what I can have according to the  VARIABLE_SS_SIZE and COMMAND_SS_SIZE
SS_map = {
    "CDH": 0,
    "EPS": 1,
    "ADCS": 2,
    "GPS": 3,
    "STORAGE": 4,
    "COMMS": 5,
    "PAYLOAD_TM": 6,
}

# this is to map the id to a specific message (cmd, reponse, report... )
MSG_TYPE_DICT = {
    "reports": 0,
    "variable": 1,
    "commands": 2,
    "responses": 3,
    "fragments": 4,
    "image_data": 5,
    "ack": 6,
    
}

# Variable definitions
# Format: "var_name": [subsystem, struct_type]
var_dict = {
    # --- CDH / SYSTEM ---
    "TIME": ["CDH", "I"],  # Unix timestamp
    "BOOT_TIME": ["CDH", "I"],  # Time since boot
    "SC_STATE": ["CDH", "B"],  # Spacecraft state
    "CURRENT_RAM_USAGE": ["CDH", "B"],  # %
    "BOOT_COUNT": ["CDH", "B"],  # Count
    "WATCHDOG_TIMER": ["CDH", "B"],  # Status
    "HAL_BITFLAGS": ["CDH", "B"],  # Flags
    "DETUMBLING_ERROR_FLAG": ["CDH", "B"],  # Flag
    #"DEPLOYMENT_STATUS": ["CDH", "B"],  # Flag
    # --- EPS (Power) ---
    "EPS_POWER_FLAG": ["EPS", "B"],
    "MAINBOARD_TEMPERATURE": ["EPS", "h"],  # 0.1°C -> °C
    "MAINBOARD_VOLTAGE": ["EPS", "h"],  # mV -> V
    "MAINBOARD_CURRENT": ["EPS", "h"],  # mA -> A
    "BATTERY_PACK_TEMPERATURE": ["EPS", "h"],  # 0.1°C -> °C
    "BATTERY_PACK_REPORTED_SOC": ["EPS", "B"],  # %
    "BATTERY_PACK_REPORTED_CAPACITY": ["EPS", "H"],  # mAh
    "BATTERY_PACK_CURRENT": ["EPS", "h"],  # mA -> A
    "BATTERY_PACK_VOLTAGE": ["EPS", "h"],  # mV -> V
    "BATTERY_PACK_MIDPOINT_VOLTAGE": ["EPS", "h"],  # mV -> V
    "BATTERY_PACK_TTE": ["EPS", "I"],  # Seconds
    "BATTERY_PACK_TTF": ["EPS", "I"],  # Seconds
    # Coils (Magnetorquers)
    "XP_COIL_VOLTAGE": ["EPS", "h"],
    "XP_COIL_CURRENT": ["EPS", "h"],
    "XM_COIL_VOLTAGE": ["EPS", "h"],
    "XM_COIL_CURRENT": ["EPS", "h"],
    "YP_COIL_VOLTAGE": ["EPS", "h"],
    "YP_COIL_CURRENT": ["EPS", "h"],
    "YM_COIL_VOLTAGE": ["EPS", "h"],
    "YM_COIL_CURRENT": ["EPS", "h"],
    "ZP_COIL_VOLTAGE": ["EPS", "h"],
    "ZP_COIL_CURRENT": ["EPS", "h"],
    "ZM_COIL_VOLTAGE": ["EPS", "h"],
    "ZM_COIL_CURRENT": ["EPS", "h"],
    # Payload & Solar Inputs
    "JETSON_INPUT_VOLTAGE": ["EPS", "h"],
    "JETSON_INPUT_CURRENT": ["EPS", "h"],
    "RF_LDO_OUTPUT_VOLTAGE": ["EPS", "h"],
    "RF_LDO_OUTPUT_CURRENT": ["EPS", "h"],
    "GPS_VOLTAGE": ["EPS", "h"],
    "GPS_CURRENT": ["EPS", "h"],
    # Solar Arrays
    "XP_SOLAR_CHARGE_VOLTAGE": ["EPS", "h"],
    "XP_SOLAR_CHARGE_CURRENT": ["EPS", "h"],
    "XM_SOLAR_CHARGE_VOLTAGE": ["EPS", "h"],
    "XM_SOLAR_CHARGE_CURRENT": ["EPS", "h"],
    "YP_SOLAR_CHARGE_VOLTAGE": ["EPS", "h"],
    "YP_SOLAR_CHARGE_CURRENT": ["EPS", "h"],
    "YM_SOLAR_CHARGE_VOLTAGE": ["EPS", "h"],
    "YM_SOLAR_CHARGE_CURRENT": ["EPS", "h"],
    # --- ADCS ---
    "MODE": ["ADCS", "B"],
    # Custom 'X' (High Precision) mapped to 'i'
    "GYRO_X": ["ADCS", "f"],
    "GYRO_Y": ["ADCS", "f"],
    "GYRO_Z": ["ADCS", "f"],
    "MAG_X": ["ADCS", "f"],
    "MAG_Y": ["ADCS", "f"],
    "MAG_Z": ["ADCS", "f"],
    "SUN_STATUS": ["ADCS", "B"],
    "SUN_VEC_X": ["ADCS", "f"],
    "SUN_VEC_Y": ["ADCS", "f"],
    "SUN_VEC_Z": ["ADCS", "f"],
    # Light Sensors
    "LIGHT_SENSOR_XP": ["ADCS", "H"],
    "LIGHT_SENSOR_XM": ["ADCS", "H"],
    "LIGHT_SENSOR_YP": ["ADCS", "H"],
    "LIGHT_SENSOR_YM": ["ADCS", "H"],
    "LIGHT_SENSOR_ZP_XP": ["ADCS", "H"],
    "LIGHT_SENSOR_ZP_YM": ["ADCS", "H"],
    "LIGHT_SENSOR_ZP_XM": ["ADCS", "H"],
    "LIGHT_SENSOR_ZP_YP": ["ADCS", "H"],
    "LIGHT_SENSOR_ZM": ["ADCS", "H"],
    # Coil Status flags
    "XP_COIL_STATUS": ["ADCS", "B"],
    "XM_COIL_STATUS": ["ADCS", "B"],
    "YP_COIL_STATUS": ["ADCS", "B"],
    "YM_COIL_STATUS": ["ADCS", "B"],
    "ZP_COIL_STATUS": ["ADCS", "B"],
    "ZM_COIL_STATUS": ["ADCS", "B"],
    # --- GPS ---
    "GPS_MESSAGE_ID": ["GPS", "B"],
    "GPS_FIX_MODE": ["GPS", "B"],
    "GPS_GNSS_WEEK": ["GPS", "H"],
    "GPS_GNSS_TOW": ["GPS", "I"],
    "GPS_ECEF_X": ["GPS", "i"],
    "GPS_ECEF_Y": ["GPS", "i"],
    "GPS_ECEF_Z": ["GPS", "i"],
    "GPS_ECEF_VX": ["GPS", "i"],
    "GPS_ECEF_VY": ["GPS", "i"],
    "GPS_ECEF_VZ": ["GPS", "i"],
    # --- PAYLOAD ---
    "SYSTEM_TIME": ["PAYLOAD_TM", "Q"],  # Unix timestamp (seconds)
    "SYSTEM_UPTIME": ["PAYLOAD_TM", "I"],  # System uptime (seconds)
    "LAST_EXECUTED_CMD_TIME": ["PAYLOAD_TM", "I"],
    "NEXT_CMD_TIME": ["PAYLOAD_TM", "I"],
    "PD_STATE_JETSON": ["PAYLOAD_TM", "B"],       # the current state of the payload in terms of jetson (check jetson code)
    "PD_STATE_MAINBOARD": ["PAYLOAD_TM", "B"],    # the current state of the payload in terms of mainboard (check mainboard code)
    "LATEST_ERROR": ["PAYLOAD_TM", "B"],
    "DISK_USAGE": ["PAYLOAD_TM", "B"],  # %
    "TEGRASTATS_PROCESS_STATUS": ["PAYLOAD_TM", "B"],  # 0=not running, 1=running
    "RAM_USAGE": ["PAYLOAD_TM", "B"],  # %
    "SWAP_USAGE": ["PAYLOAD_TM", "B"],  # %
    "ACTIVE_CORES": ["PAYLOAD_TM", "B"],  # count
    "CPU_LOAD_0": ["PAYLOAD_TM", "B"],  # %
    "CPU_LOAD_1": ["PAYLOAD_TM", "B"],  # %
    "CPU_LOAD_2": ["PAYLOAD_TM", "B"],  # %
    "CPU_LOAD_3": ["PAYLOAD_TM", "B"],  # %
    "CPU_LOAD_4": ["PAYLOAD_TM", "B"],  # %
    "CPU_LOAD_5": ["PAYLOAD_TM", "B"],  # %
    "GPU_FREQ": ["PAYLOAD_TM", "H"],  # MHz
    "CPU_TEMP": ["PAYLOAD_TM", "B"],  # °C
    "GPU_TEMP": ["PAYLOAD_TM", "B"],  # °C
    "VDD_IN": ["PAYLOAD_TM", "H"],  # mW
    "VDD_CPU_GPU_CV": ["PAYLOAD_TM", "H"],  # mW
    "VDD_SOC": ["PAYLOAD_TM", "H"],  # mW
    "INFERENCE_RETURN_CODE": ["PAYLOAD_TM", "b"],  # Last inference subprocess return code
    # --- STORAGE ---
    "SD_TOTAL_USAGE": ["STORAGE", "I"],
    "CDH_NUM_FILES": ["STORAGE", "I"],
    "CDH_DIR_SIZE": ["STORAGE", "I"],
    "EPS_NUM_FILES": ["STORAGE", "I"],
    "EPS_DIR_SIZE": ["STORAGE", "I"],
    "EPS_WARNING_NUM_FILES": ["STORAGE", "I"],
    "EPS_WARNING_DIR_SIZE": ["STORAGE", "I"],
    "ADCS_NUM_FILES": ["STORAGE", "I"],
    "ADCS_DIR_SIZE": ["STORAGE", "I"],
    "COMMS_NUM_FILES": ["STORAGE", "I"],
    "COMMS_DIR_SIZE": ["STORAGE", "I"],
    "GPS_NUM_FILES": ["STORAGE", "I"],
    "GPS_DIR_SIZE": ["STORAGE", "I"],
    "PAYLOAD_NUM_FILES": ["STORAGE", "I"],
    "PAYLOAD_DIR_SIZE": ["STORAGE", "I"],
    "CMD_LOGS_NUM_FILES": ["STORAGE", "I"],
    "CMD_LOGS_DIR_SIZE": ["STORAGE", "I"],
    "HAL_NUM_FILES": ["STORAGE", "I"],
    "HAL_DIR_SIZE": ["STORAGE", "I"],
    # --- COMMS ---
    "RX_PACKET_COUNT": ["COMMS", "H"],
    "FAILED_UNPACK_COUNT": ["COMMS", "H"],
    "CRC_ERROR_COUNT": ["COMMS", "H"],
    "UNDEF_ERROR_COUNT": ["COMMS", "H"],
    "PACKET_NONE_COUNT": ["COMMS", "H"],
    "PACKET_AUTH_FAIL_COUNT": ["COMMS", "H"],
    "RX_DIGIPEATER_COUNT": ["COMMS", "H"],
    "TX_PACKET_COUNT": ["COMMS", "H"],
    "TX_FAILED_COUNT": ["COMMS", "H"],
    "TX_DIGIPEATER_COUNT": ["COMMS", "H"],
    "RX_MESSAGE_RSSI": ["COMMS", "e"],
}

# Report definitions
# Each report is a collection of variables that are sent together
# Format: "report_name": {variable_name: subsystem}
report_dict = {
    # Corresponds to MSG_ID_SAT_TM_NOMINAL (0x05)
    "TM_HEARTBEAT": {
        # CDH
        "TIME": "CDH",
        "BOOT_TIME": "CDH",
        "SC_STATE": "CDH",
        "CURRENT_RAM_USAGE": "CDH",
        "BOOT_COUNT": "CDH",
        #"DEPLOYMENT_STATUS": "CDH",
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
        "LIGHT_SENSOR_ZP_XP": "ADCS",
        "LIGHT_SENSOR_ZP_YM": "ADCS",
        "LIGHT_SENSOR_ZP_XM": "ADCS",
        "LIGHT_SENSOR_ZP_YP": "ADCS",
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
        "GPS_GNSS_WEEK": "GPS",
        "GPS_GNSS_TOW": "GPS",
        "GPS_ECEF_X": "GPS",
        "GPS_ECEF_Y": "GPS",
        "GPS_ECEF_Z": "GPS",
        "GPS_ECEF_VX": "GPS",
        "GPS_ECEF_VY": "GPS",
        "GPS_ECEF_VZ": "GPS",
        # COMMS
        "RX_PACKET_COUNT": "COMMS",
        "FAILED_UNPACK_COUNT": "COMMS",
        "CRC_ERROR_COUNT": "COMMS",
        "UNDEF_ERROR_COUNT": "COMMS",
        "PACKET_NONE_COUNT": "COMMS",
        "PACKET_AUTH_FAIL_COUNT": "COMMS",
        "TX_PACKET_COUNT": "COMMS",
        "TX_FAILED_COUNT": "COMMS",
        "RX_MESSAGE_RSSI": "COMMS",
        "RX_DIGIPEATER_COUNT": "COMMS",
        "TX_DIGIPEATER_COUNT": "COMMS",
    },
    # Corresponds to MSG_ID_SAT_TM_STORAGE (0x03)
    "TM_STORAGE": {
        "TIME": "CDH",
        "SC_STATE": "CDH",
        "CURRENT_RAM_USAGE": "CDH",
        "BOOT_COUNT": "CDH",
        #"DEPLOYMENT_STATUS": "CDH",
        "WATCHDOG_TIMER": "CDH",
        "HAL_BITFLAGS": "CDH",
        "DETUMBLING_ERROR_FLAG": "CDH",
        "SD_TOTAL_USAGE": "STORAGE",
        "CDH_NUM_FILES": "STORAGE",
        "CDH_DIR_SIZE": "STORAGE",
        "EPS_NUM_FILES": "STORAGE",
        "EPS_DIR_SIZE": "STORAGE",
        "EPS_WARNING_NUM_FILES": "STORAGE",
        "EPS_WARNING_DIR_SIZE": "STORAGE",
        "ADCS_NUM_FILES": "STORAGE",
        "ADCS_DIR_SIZE": "STORAGE",
        "COMMS_NUM_FILES": "STORAGE",
        "COMMS_DIR_SIZE": "STORAGE",
        "GPS_NUM_FILES": "STORAGE",
        "GPS_DIR_SIZE": "STORAGE",
        "PAYLOAD_NUM_FILES": "STORAGE",
        "PAYLOAD_DIR_SIZE": "STORAGE",
        "CMD_LOGS_NUM_FILES": "STORAGE",
        "CMD_LOGS_DIR_SIZE": "STORAGE",
        "HAL_NUM_FILES": "STORAGE",
        "HAL_DIR_SIZE": "STORAGE",
    },
    # Corresponds to MSG_ID_SAT_TM_HAL (0x02)cd 
    "TM_HAL": {
        "TIME": "CDH",
        "SC_STATE": "CDH",
        "CURRENT_RAM_USAGE": "CDH",
        "BOOT_COUNT": "CDH",
        #"DEPLOYMENT_STATUS": "CDH",
        "WATCHDOG_TIMER": "CDH",
        "HAL_BITFLAGS": "CDH",
        "DETUMBLING_ERROR_FLAG": "CDH",
    },
    
    "TM_TEST":{
        "TIME": "CDH",
        "SC_STATE": "CDH",
        "GPS_MESSAGE_ID": "GPS",
    },
    
    "TM_PAYLOAD":{
        "SYSTEM_TIME": "PAYLOAD_TM",
        "SYSTEM_UPTIME": "PAYLOAD_TM",
        "LAST_EXECUTED_CMD_TIME": "PAYLOAD_TM",   # this value will be filled by the mainboard
        "NEXT_CMD_TIME": "PAYLOAD_TM",            # this value will be filled by the mainboard
        "PD_STATE_MAINBOARD": "PAYLOAD_TM",       # this value will be filled by the mainboard
        "PD_STATE_JETSON": "PAYLOAD_TM",
        "LATEST_ERROR": "PAYLOAD_TM",             # this is the latest state at which it failed it is latching until the next experiment starts
        
        "INFERENCE_RETURN_CODE": "PAYLOAD_TM",  # Last inference subprocess return code
        
        "DISK_USAGE": "PAYLOAD_TM",
        "RAM_USAGE": "PAYLOAD_TM",
        "SWAP_USAGE": "PAYLOAD_TM",
        
        "ACTIVE_CORES": "PAYLOAD_TM",
        "CPU_LOAD_0": "PAYLOAD_TM",
        "CPU_LOAD_1": "PAYLOAD_TM",
        "CPU_LOAD_2": "PAYLOAD_TM",
        "CPU_LOAD_3": "PAYLOAD_TM",
        "CPU_LOAD_4": "PAYLOAD_TM",
        "CPU_LOAD_5": "PAYLOAD_TM",
        
        "TEGRASTATS_PROCESS_STATUS": "PAYLOAD_TM",
        "GPU_FREQ": "PAYLOAD_TM",
        "CPU_TEMP": "PAYLOAD_TM",
        "GPU_TEMP": "PAYLOAD_TM",
        
        "VDD_IN": "PAYLOAD_TM",
        "VDD_CPU_GPU_CV": "PAYLOAD_TM",
        "VDD_SOC": "PAYLOAD_TM",
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
    
    "string_command": "s",  # String command for evaluation
    
    "tid": "B",  # Transaction ID for image transfer commands
    "number_of_packets": "H",  # File size for image transfer commands

    "seq_number": "H",  # Sequence number for transaction packets
    "seq_offset": "H",  # Offset of the sequence number for transaction packets
    "bitmap_high": "L",  # High 32 bits of the missing-fragment bitmap (CONFIRM_LAST_BATCH / UPDATE_MISSING_FRAGMENTS)
    "bitmap_low": "L",  # Low 32 bits of the missing-fragment bitmap (CONFIRM_LAST_BATCH / UPDATE_MISSING_FRAGMENTS)
    "x": "H",  # Number of packets to generate for GENERATE_X_PACKETS command
    "mode_id": "B", # Mode ID for COMMS_MODE command
    "skip_elements": "H",  # Number of elements to skip in the directory listing
    "ts": "I",  # Timestamp for EXPERIMENT command
    "camera_bit_flag": "B",  # Camera bit flag for EXPERIMENT, bit0 = 1 -> camera 0 active, bit1 = 0 -> camera 1 not active
    "level_processing": "B",  # Level of processing for EXPERIMENT command
    "width": "H",  # Capture width for EXPERIMENT command
    "height": "H",  # Capture height for EXPERIMENT command
    "downscale_factor": "f",  # Downscale factor used when DOWNSCALE bit is enabled (default 2.0)
    "camera_defaults_selector": "b",  # -1 -> use program camera defaults; otherwise use explicit camera params below
    "fps": "H",  # FPS (camera_driver constraint: > 0)
    "wbmode": "B",  # WBMode enum [0..9]
    "aelock": "B",  # bool (auto-exposure lock)
    "awblock": "B",  # bool (auto-white-balance lock)
    "exposuretimerange_low": "I",  # 0 and high=0 -> None; else [500_000..65_487_000] ns
    "exposuretimerange_high": "I",  # 0 and low=0 -> None; else [500_000..65_487_000] ns
    "gainrange_low": "f",  # 0.0 and high=0.0 -> None; else [1.0..16.0]
    "gainrange_high": "f",  # 0.0 and low=0.0 -> None; else [1.0..16.0]
    "ispdigitalgainrange_low": "f",  # 0.0 and high=0.0 -> None; else [1.0..256.0]
    "ispdigitalgainrange_high": "f",  # 0.0 and low=0.0 -> None; else [1.0..256.0]
    "ee_mode": "B",  # EdgeEnhancementMode enum [0..2]
    "ee_strength": "f",  # range [-1.0..1.0]
    "aeantibanding": "B",  # AeAntibandingMode enum [0..3]
    "exposurecompensation": "f",  # range [-2.0..2.0]
    "tnr_mode": "B",  # NoiseReductionMode enum [0..2]
    "tnr_strength": "f",  # range [-1.0..1.0]
    "saturation": "f",  # range [0.0..2.0]
}

# Return type definitions
return_dict = {
    "status": "B",  # Command status (success/fail)
    "check": "B",  # Checksum or validation byte
    "ack": "?",  # Boolean acknowledgment
}



# command name, argument list
# [check] - should i add the subsystem here
command_list = [
    ("PING", ["string_command"]),
    ("FORCE_REBOOT", []),
    ("GRACEFUL_REBOOT", []),
    ("MAIN_POWER_REBOOT", []),
    ("REBOOT_ACK", []),
    ("PET_REBOOT", []),
    
    ("SUM", ["op1", "op2"]),
    ("SWITCH_TO_STATE", ["target_state_id", "time_in_state"]),
    ("UPLINK_TIME_REFERENCE", ["time_reference"]),
    ("TURN_OFF_PAYLOAD", []),
    ("TURN_ON_PAYLOAD", []),
    ("SCHEDULE_OD_EXPERIMENT", []),
    ("REQUEST_TM_NOMINAL", []),
    ("REQUEST_TM_HAL", []),
    ("REQUEST_TM_STORAGE", []),
    ("REQUEST_TM_PAYLOAD", []),
    
    ("EVAL_STRING_COMMAND", ["string_command"]),
    
    # Commands to downlink images
    ("CREATE_TRANS", ["tid", "string_command"]),   # for now this is a string command, but eventually should change for a reference number
    ("INIT_TRANS", ["tid", "number_of_packets"]),   # for now this is a string command, but eventually should change for a reference number
    ("GENERATE_ALL_PACKETS", ["tid"]), # sent from gs to satelltie to request sending all the packets in a transaction [check] - this could be the command bellow if x as -1 for example
    ("GENERATE_X_PACKETS", ["tid", "x"]), # sent from gs to satelltie to request sending x packets in a transaction from the missing list
    ("GENERATE_SINGLE_PACKET", ["tid", "seq_number"]), # sent from gs to satelltie to request sending all the packets in a transaction
    ("CONFIRM_LAST_BATCH", ["tid", "bitmap_high", "bitmap_low"]), # send from gs to satellite to update missing_fragments after the last batch tx.
    ("UPDATE_MISSING_FRAGMENTS", ["tid", "seq_offset", "bitmap_high", "bitmap_low"]), # will allow to add or remove 64 packets out of the missing_packet list
    ("LIST_DIR", ["skip_elements", "string_command"]),    # will list all the files in the given directory, skip the first skip_elements files
    ("GET_FILE_SIZE", ["string_command"]),  # will return the size of the file in bytes
    ("DELETE_ALL_FILES", []),  #  will call the DH function to delete all dh files (and images)
    ("UPDATE_SD_USAGE", []),  #  will call the DH function to calculate the sd card usage

    ("RF_STOP", []),
    ("RF_RESUME", []),
    ("DIGIPEATER_ACTIVATE", []),
    ("DIGIPEATER_DEACTIVATE", []),
    ("COMMS_MODE", ["mode_id"]),
    ("SIMPLE_EXPERIMENT", ["ts","camera_bit_flag","level_processing","width","height","downscale_factor",]),  # used  to run experiment with default camera params
    
    (
        "EXPERIMENT",
        [
            "ts",
            "camera_bit_flag",
            "level_processing",
            "width",
            "height",
            "downscale_factor",
            "camera_defaults_selector",
            "fps",
            "wbmode",
            "aelock",
            "awblock",
            "exposuretimerange_low",
            "exposuretimerange_high",
            "gainrange_low",
            "gainrange_high",
            "ispdigitalgainrange_low",
            "ispdigitalgainrange_high",
            "ee_mode",
            "ee_strength",
            "aeantibanding",
            "exposurecompensation",
            "tnr_mode",
            "tnr_strength",
            "saturation",
        ],
    ),
    ("GET_EXPERIMENT_LIST", ["skip_elements"]),  # this command will return the  timestamps for the next scheduled experiments
    ("CLEAR_EXPERIMENT_LIST", []),  # this command will clear the list of scheduled experiments in the payload

    ("PING_EXP", ["ts"]),                     # this is the special ping command for experiment
    ("EXPERIMENT_FINISHED", []),   # this is the command send by the jetson to mainboard when it finishes the experiment. it will move on to download stage
    ("DOWNLOAD_FINISH", []),   # this is the command sent by the jetson to the mainboard to indicate that it has sent all the files
    
    ("GET_COMMAND_LIST", ["skip_elements"]),  # return this command list


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
