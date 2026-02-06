
import sys
import os


# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from splat.telemetry_definition import ENDIANNESS, var_dict, report_dict, command_list, REPORT_IDS, COMMAND_IDS, MAX_PACKET_SIZE
from splat.telemetry_definition import MSG_TYPE_SIZE, REPORT_ID_SIZE, COMMAND_ID_SIZE, VARIABLE_ID_SIZE, VARIABLE_SS_SIZE# import header sizes
from splat.telemetry_helper import get_variable_size, get_report_size, get_command_size, validate_definitions

def print_summary():
    """
    Print a summary of all telemetry definitions.
    """
    print("=" * 80)
    print("TELEMETRY PROTOCOL SUMMARY")
    print("=" * 80)
    
    print(f"\nConfiguration:")
    print(f"  Endianness: {'Big-endian' if ENDIANNESS == '>' else 'Little-endian'}")
    print(f"  Max Packet Size: {MAX_PACKET_SIZE} bytes")
    
    # print header info
    print(f"\nHeader Sizes:")
    # report header size
    report_header_size = (MSG_TYPE_SIZE + REPORT_ID_SIZE) // 8  # Convert bits to bytes
    print(f"  Report Header: {report_header_size} bytes (MSG_TYPE + REPORT_ID)")
    # command header size
    command_header_size = (MSG_TYPE_SIZE + COMMAND_ID_SIZE) // 8  # Convert bits to bytes
    print(f"  Command Header: {command_header_size} bytes (MSG_TYPE + COMMAND_ID)")
    # variable header size
    variable_header_size = (MSG_TYPE_SIZE + VARIABLE_SS_SIZE + VARIABLE_ID_SIZE) // 8  # Convert bits to bytes
    print(f"  Variable Header: {variable_header_size} bytes (MSG_TYPE + VARIABLE_SS + VARIABLE_ID)")
    
    print(f"\nVariables: {len(var_dict)}")
    for var_name, (subsystem, var_type, scale) in var_dict.items():
        size = get_variable_size(var_name)
        print(f"  {var_name:20s} [{subsystem:6s}] {var_type:3s} ({size:2d} bytes) scale={scale}")
    
    print(f"\nReports: {len(report_dict)}")
    for report_name, variables in report_dict.items():
        size = get_report_size(report_name)
        report_id = REPORT_IDS[report_name]
        num_vars = len(variables) if isinstance(variables, list) else len(variables)
        print(f"  {report_name:20s} (ID={report_id:2d}, {size:3d} bytes) {num_vars} variables")
    
    print(f"\nCommands: {len(command_list)}")
    for cmd_name, precondition, args, satellite_func in command_list:
        cmd_size = get_command_size(cmd_name)
        cmd_id = COMMAND_IDS[cmd_name]
        print(f"  {cmd_name:25s} (ID={cmd_id:2d}) [{subsystem:6s}] {cmd_size:3d} bytes")
    
    print("\nValidation:")
    is_valid, errors = validate_definitions()
    if is_valid:
        print("  All definitions are valid")
    else:
        print(f"  Found {len(errors)} error(s):")
        for error in errors:
            print(f"    - {error}")
    
    print("=" * 80)


if __name__ == "__main__":
    print_summary()
