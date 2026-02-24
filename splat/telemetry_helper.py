"""
Telemetry Helper Functions
Provides utility functions for working with the telemetry protocol.
"""

import struct
from .telemetry_definition import (
    # 1. Data Structures (Dicts & Lists)
    var_dict,
    report_dict,
    command_list,
    argument_dict,
    ORDERED_REPORT_DICT,

    # 2. Lookup Maps & IDs
    COMMAND_IDS,
    REPORT_IDS,
    VAR_ID_TO_NAME,
    all_cmd_names,

    # 3. Protocol Constants
    ENDIANNESS,
    MAX_PACKET_SIZE,
    MSG_TYPE_SIZE,
    COMMAND_ID_SIZE,
    REPORT_ID_SIZE,
    VARIABLE_SS_SIZE,
    VARIABLE_ID_SIZE
)

def format_bytes(byte_data):
    return " ".join(f"0x{byte:02X}" for byte in byte_data)


def get_variable_size(var_name):
    """
    Get the size in bytes of a variable.
    
    Args:
        var_name: Name of the variable
        
    Returns:
        Size in bytes
    """
    
    header_size = (MSG_TYPE_SIZE + VARIABLE_SS_SIZE + VARIABLE_ID_SIZE) // 8  # Convert bits to bytes
    
    if var_name not in var_dict:
        raise ValueError(f"Variable '{var_name}' not found in var_dict")
    
    var_type = var_dict[var_name][1]
    return struct.calcsize(ENDIANNESS + var_type) + header_size


def get_report_size(report_name):
    """
    Get the total size in bytes of a report
    as of right now it does not include the header size
    
    Args:
        report_name: Name of the report
        
    Returns:
        Size in bytes
    """
    if report_name not in report_dict:
        raise ValueError(f"Report '{report_name}' not found in report_dict")
    
    
    total_size = (MSG_TYPE_SIZE + REPORT_ID_SIZE) // 8  # add the header size (convert bits to bytes)
    # print(f"Report '{report_name}' header size: {total_size} bytes")
    # Add size of each variable in the report
    for var_name in report_dict[report_name].keys():
        variable_format = get_variable_format(var_name)
        variable_size = struct.calcsize(variable_format)
        total_size += variable_size
    
    return total_size


def get_command_size(cmd_name):
    """
    Get the size in bytes of a command
    as of right now it does not include the header size
    
    Args:
        cmd_name: Name of the command
        
    Returns:
        Tuple of (command_size, response_size)
    """
    if cmd_name not in all_cmd_names:
        raise ValueError(f"Command '{cmd_name}' not found in command_list")
    
    # 1 byte for command ID
    cmd_size = (MSG_TYPE_SIZE + COMMAND_ID_SIZE) // 8  # Convert bits to bytes
    # Add size of each argument
    cmd_name, precondition, arguments, satellite_func = command_list[COMMAND_IDS[cmd_name]]
    for arg in arguments:
        if arg not in argument_dict:
            raise ValueError(f"Argument '{arg}' not found in argument_dict")
        arg_type = argument_dict[arg]
        cmd_size += struct.calcsize(ENDIANNESS + arg_type)
    
    return cmd_size

def get_argument_type(arg_name):
    """
    Given the name of a argument, it will look in the argument dict the type of the argument
    and return the struct format string for that type
    as of right now, this will be used to see ir argument is int, float or string

    not returning the endianness
    
    """
    
    if arg_name not in argument_dict:
        raise ValueError(f"Argument '{arg_name}' not found in argument_dict")
    
    arg_type = argument_dict[arg_name]
    return arg_type

# [check] - could have a function that would add endianness to all the formats
def get_report_format(report_name):
    """
    Get the struct format string for a report.
    
    Args:
        report_name: Name of the report
        
    Returns:
        Struct format string (e.g., '>Bdfff')
    """
    if report_name not in report_dict:
        raise ValueError(f"Report '{report_name}' not found in report_dict")
    
    # Start with report ID (unsigned byte)
    format_str = ENDIANNESS
    
    # Add format for each variable
    # for var_name in report_dict[report_name].keys():
    # [check] - should change the code to reference the variables by var_id and ss_id instead of var_name
    for var_id, ss_id in ORDERED_REPORT_DICT[report_name]:
        var_name = VAR_ID_TO_NAME[ss_id][var_id]
        if var_name not in var_dict:
            raise ValueError(f"Variable '{var_name}' in report '{report_name}' not found in var_dict")
        var_type = var_dict[var_name][1]
        format_str += var_type
    
    return format_str

def get_variable_format(var_name):
    """
    Get the struct format string for a variable.
    
    Args:
        var_name: Name of the variable
    Returns:
        Struct format string (e.g., '>B', '>f')
    """
    if var_name not in var_dict:
        raise ValueError(f"Variable '{var_name}' not found in var_dict")
    
    var_type = var_dict[var_name][1]
    format_str = ENDIANNESS + var_type
    return format_str


def get_command_format(cmd_name):
    """
    Get the struct format string for a command.
    
    Args:
        cmd_name: Name of the command
        
    Returns:
        NOTE: i dont think it returns a tuple
        Tuple of (command_format, response_format)
    """
    if cmd_name not in all_cmd_names:
        raise ValueError(f"Command '{cmd_name}' not found in command_list")
    
    # start building the cmd_format
    cmd_format = ENDIANNESS

    # Add format for each argument
    cmd_name, precondition, args, satellite_func = command_list[COMMAND_IDS[cmd_name]]    
    for arg in args:
        if arg not in argument_dict:
            raise ValueError(f"Argument '{arg}' not found in argument_dict")
        cmd_format += argument_dict[arg]

    
    return cmd_format


def list_all_variables():
    """
    List all available variables with their properties.
    
    Returns:
        Dictionary of variables with their properties
    """
    result = {}
    for var_name, (subsystem, var_type, scale) in var_dict.items():
        result[var_name] = {
            'subsystem': subsystem,
            'type': var_type,
            'scale': scale,
            'size': struct.calcsize(ENDIANNESS + var_type)
        }
    return result


def list_all_reports():
    """
    List all available reports with their properties.
    
    Returns:
        Dictionary of reports with their properties
    """
    result = {}
    for report_name, variables in report_dict.items():
        result[report_name] = {
            'id': REPORT_IDS[report_name],
            'variables': list(variables.keys()),
            'size': get_report_size(report_name),
            'format': get_report_format(report_name)
        }
    return result


def list_all_commands():
    """
    List all available commands with their properties.
    
    Returns:
        Dictionary of commands with their properties
    """
    result = {}
  
    for cmd_name, precondition, args, satellite_func in command_list:
        cmd_size = get_command_size(cmd_name)
        result[cmd_name] = {
            'id': COMMAND_IDS[cmd_name],
            'arguments': args,
            'precond': precondition,
            'sat_func': satellite_func,
            'size': cmd_size,
        }
    return result


def validate_definitions():
    """
    Validate the telemetry definitions for consistency.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check that all variables in reports exist in var_dict
    for report_name, variables in report_dict.items():
        for var_name, subsystem in variables.items():
            if var_name not in var_dict:
                errors.append(f"Variable '{var_name}' in report '{report_name}' not found in var_dict")
            elif var_dict[var_name][0] != subsystem:
                errors.append(f"Variable '{var_name}' in report '{report_name}' has mismatched subsystem")
    
    # Check that no report exceeds max packet size
    for report_name in report_dict.keys():
        size = get_report_size(report_name)
        if size > MAX_PACKET_SIZE:
            errors.append(f"Report '{report_name}' size ({size} bytes) exceeds MAX_PACKET_SIZE ({MAX_PACKET_SIZE} bytes)")
    
    # Check that all command arguments are defined
    for cmd_name, precondition, args, satellite_func in command_list:    
        for arg in args:
            if arg not in argument_dict:
                errors.append(f"Argument '{arg}' in command '{cmd_name}' not found in argument_dict")
            
    # Check that all commands fit within max packet size
    for cmd_name, precondition, args, satellite_func in command_list:        
        try:
            cmd_size = get_command_size(cmd_name)
            if cmd_size > MAX_PACKET_SIZE:
                errors.append(f"Command '{cmd_name}' size ({cmd_size} bytes) exceeds MAX_PACKET_SIZE ({MAX_PACKET_SIZE} bytes)")
        except Exception as e:
            errors.append(f"Error calculating size for command '{cmd_name}': {str(e)}")
            
    return len(errors) == 0, errors