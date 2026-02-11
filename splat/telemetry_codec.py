"""
Telemetry Codec
Provides packing and unpacking functions for the satellite telemetry protocol.
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
    REPORT_NAMES,
    VAR_ID_TO_NAME,
    all_cmd_names,
    SS_map,

    # 3. Protocol Constants
    ENDIANNESS,
    MSG_TYPE_DICT,
    MSG_TYPE_SIZE,
    MAX_PACKET_SIZE,
    COMMAND_ID_SIZE,
    REPORT_ID_SIZE,
    VARIABLE_SS_SIZE,
    VARIABLE_ID_SIZE
)

from .telemetry_helper import (
    get_report_format,
    get_command_format,
    get_variable_format,
    format_bytes  # Kept if used for debugging prints, otherwise safe to remove
)


class Report:
    """
    Template class for creating telemetry reports.
    [check] - maybe here I could the variables indexed by their var_id and ss_id
    and maybe here I should use the class Variable to store the Variables instead of the list
    """
    
    def __init__(self, report_name):
        """
        Initialize a report.
        
        Args:
            report_name: Name of the report (must exist in report_dict)
        """
        if report_name not in report_dict:
            raise ValueError(f"Report '{report_name}' not found in report_dict")

        self.name = report_name
        self.report_id = REPORT_IDS[report_name]
        self.variables = {}
        
        self.ss_list = list(report_dict[report_name].values())  # a list with all the subsystems in the report
        
        # Initialize all variables with None
        for var_name, subsystem in report_dict[report_name].items():
            if subsystem not in self.variables:
                self.variables[subsystem] = {}
            self.variables[subsystem][var_name] = None
    
    def add_variable(self, var_name, subsystem, value):
        """
        Add or update a variable value in the report.
        
        Args:
            var_name: Name of the variable
            subsystem: Subsystem the variable belongs to
            value: Value to set (in SI units)
        """
        if var_name not in report_dict[self.name]:
            raise ValueError(f"Variable '{var_name}' not in report '{self.name}'")
        
        if report_dict[self.name][var_name] != subsystem:
            raise ValueError(f"Variable '{var_name}' belongs to subsystem '{report_dict[self.name][var_name]}', not '{subsystem}'")
                
        if subsystem not in self.variables:
            self.variables[subsystem] = {}
        
        self.variables[subsystem][var_name] = value
    
    def set_variables(self, **kwargs):
        """
        Set multiple variables at once using keyword arguments.
        
        Args:
            **kwargs: var_name=value pairs
        """
        for var_name, value in kwargs.items():
            if var_name not in report_dict[self.name]:
                raise ValueError(f"Variable '{var_name}' not in report '{self.name}'")
            subsystem = report_dict[self.name][var_name]
            self.add_variable(var_name, subsystem, value)
    
    def get_variable(self, var_name):
        """
        Get the value of a variable.
        
        Args:
            var_name: Name of the variable
            
        Returns:
            Value of the variable (in SI units) or None if not set
        """
        if var_name not in report_dict[self.name]:
            raise ValueError(f"Variable '{var_name}' not in report '{self.name}'")
        
        subsystem = report_dict[self.name][var_name]
        return self.variables.get(subsystem, {}).get(var_name, None)
    
    def get_variable_name_list(self, ss):
        """
        Get a list of the variable names in the report that belong to a specific subsystem.
        
        Returns:
            List of variable names
        """
        return [var_name for var_name, subsystem in report_dict[self.name].items() if subsystem == ss]
    
    def __repr__(self):
        return f"Report('{self.name}', id={self.report_id}, variables={len(report_dict[self.name])})"


class Command:
    """
    Template class for creating commands.
    """
    
    def __init__(self, cmd_name):
        """
        Initialize a command.
        
        Args:
            cmd_name: Name of the command (must exist in command_list)
        """
        if cmd_name not in all_cmd_names:
            raise ValueError(f"Command '{cmd_name}' not found in command_list")
        
        self.name = cmd_name
        self.command_id = COMMAND_IDS[cmd_name]
        self.precondition = command_list[self.command_id][1]
        self.satellite_func = command_list[self.command_id][3]
        self.arg_names = command_list[self.command_id][2]
        self.arguments = {}   # [check] - could change this to a list
    
    def add_argument(self, arg_name, value):
        """
        Add an argument to the command.
        
        Args:
            arg_name: Name of the argument
            value: Value of the argument
        """
        if arg_name not in self.arg_names:
            raise ValueError(f"Argument '{arg_name}' not valid for command '{self.name}'")
        
        self.arguments[arg_name] = value
    
    def set_arguments(self, *args, **kwargs):
        """
        Set arguments by position or keyword.
        
        Args:
            *args: Positional arguments in order
            **kwargs: Keyword arguments
        """
        # Handle positional arguments
        for i, value in enumerate(args):
            if i >= len(self.arg_names):
                raise ValueError(f"Too many positional arguments for command '{self.name}'")
            self.arguments[self.arg_names[i]] = value
        
        # Handle keyword arguments
        for arg_name, value in kwargs.items():
            self.add_argument(arg_name, value)
    
    def get_argument(self, arg_name):
        """
        Get the value of an argument.
        
        Args:
            arg_name: Name of the argument
            
        Returns:
            Value of the argument or None if not set
        """
        return self.arguments.get(arg_name, None)
    
    def get_arguments_list(self):
        """
        Returns a list with the values of the arguments in the order defined in command list
        """
        return [self.arguments.get(arg_name, None) for arg_name in self.arg_names]
    
    def __repr__(self):
        return f"Command('{self.name}', id={self.command_id}, args: {self.arg_names})"


class Response:
    """
    Template class for command responses.
    """
    
    def __init__(self, cmd_name, data=None):
        """
        Initialize a response.
        
        Args:
            cmd_name: Name of the command this is responding to
            data: Response data (optional)
        """
        if cmd_name not in command_dict:
            raise ValueError(f"Command '{cmd_name}' not found in command_dict")
        
        self.command_name = cmd_name
        self.return_type = command_dict[cmd_name][2]
        self.data = data
    
    def set_data(self, data):
        """Set the response data."""
        self.data = data
    
    def __repr__(self):
        return f"Response(command='{self.command_name}', data={self.data})"
    
class Variable:
    """
    Template class for a telemetry variable.
    this is a more simple class
    """
    #[check] - not sure that I am okay with passing the variable here
    def __init__(self, var_name, subsystem, value=None):
        """
        Initialize a variable.
        
        Args:
            var_name: Name of the variable
            subsystem: Subsystem the variable belongs to
            value: Value of the variable (in SI units)
        """
        if var_name not in var_dict:
            raise ValueError(f"Variable '{var_name}' not found in var_dict")
        
        self.name = var_name
        self.subsystem = subsystem
        self.subsystem_id = SS_map[subsystem]
        self.value = value

        for var_id in VAR_ID_TO_NAME[self.subsystem_id]:
            if VAR_ID_TO_NAME[self.subsystem_id][var_id] == var_name:
                self.var_id = var_id
                return
            
        # if we reach here, the variable was not found
        raise ValueError(f"Variable ID for '{var_name}' not found in subsystem '{subsystem}'")
    
    def set_value(self, value):
        """Set the variable value."""
        # [check] - it would be interesting to check the value type here
        self.value = value
    
    def __repr__(self):
        return f"Variable('{self.name}', subsystem='{self.subsystem}', value={self.value})"

class Ack:
    """
    Template class for acknowledgments.
    Ack will be special as they will support variable size strings, as long as they fit in the maximum frame size
    it will contain the header, the response_id, and the rest of the message will be optional string with the response args
    """
    
    def __init__(self, response_id, ack_args=None):
        """
        Initialize an acknowledgment.
        
        Args:
            ack_name: Name of the acknowledgment (must exist in ack_dict)
        """
        self.response_id = response_id
        if ack_args is not None and not isinstance(ack_args, str):
            ack_args = str(ack_args)  # convert to string if not already a string
        self.ack_args = ack_args    # this has to be a string
    
    def __repr__(self):
        return f"Ack('rid={self.response_id}', args={self.ack_args})"
        
def pack_ack(ack):
    """
    Pack an Ack object.
    Byte 0: [MsgType (3 bits)] + [ResponseID (5 bits)]
    Byte 1+: UTF-8 encoded string arguments
    """
    if not isinstance(ack, Ack):
        raise TypeError("Expected Ack object")
        
    msg_type = MSG_TYPE_DICT["ack"]
    
    # --- 1. Validation ---
    # Msg Type must fit in 3 bits (0-7)
    if msg_type > 7:
        raise ValueError("Message type > 7 cannot fit in 3 bits")
        
    # Response ID must fit in 5 bits (0-31)
    if ack.response_id > 31:
        raise ValueError(f"Response ID {ack.response_id} is too large for 5 bits (Max 31)")

    # --- 2. Bitwise Packing ---
    # Shift msg_type 5 spots to the left to occupy the top 3 bits
    # OR (|) it with the response_id to fill the bottom 5 bits
    header_byte_val = (msg_type << 5) | ack.response_id
    
    # Convert integer to a single byte
    header_bytes = struct.pack('B', header_byte_val)
    
    # --- 3. Payload Encoding ---
    payload_bytes = b''
    if ack.ack_args:
        payload_bytes = ack.ack_args.encode('utf-8')[:MAX_PACKET_SIZE - 1]  # Ensure total size does not exceed max packet size (accounting for header)
        
    return header_bytes + payload_bytes
    

def pack_report(report):
    """
    Pack a Report object into bytes.
    
    Args:
        report: Report object to pack
        
    Returns:
        Packed bytes
    """
    if not isinstance(report, Report):
        raise TypeError("Expected Report object")
    
    # Get the format string
    format_str = get_report_format(report.name)
    # print("Format string:", format_str)

    #build the header
    header_size = MSG_TYPE_SIZE + REPORT_ID_SIZE
    header = (MSG_TYPE_DICT["reports"] << (header_size - MSG_TYPE_SIZE)) | report.report_id
    # print("Header:", header)

    # Start with report ID
    values = []  # first byte is the message type and report id
    # Add variables in the order defined in report_dict
    
    # need to force order in the packing of the variables
    
    for var_id, ss_id in ORDERED_REPORT_DICT[report.name]:
        var_name = VAR_ID_TO_NAME[ss_id][var_id]
        ss_name = [k for k,v in SS_map.items() if v == ss_id][0]
        value = report.variables.get(ss_name, {}).get(var_name, None)  # doing this way to make sure it does not fail
        # [check] - maybe it would be faster to guarante somewhere else that this will not fail
        
        # If value is None, use 0
        if value is None:
            value = 0
        
        # # Apply scaling if needed
        # scale = var_dict[var_name][2]
        # if scale is not None:
        #     value = value * scale
        
        values.append(value)
    
    # Pack the data
    packed_data = struct.pack(format_str, *values)
    # print("Packed data no header:", format_bytes(packed_data))
    # [check] - remove hardcoded endianess
    return header.to_bytes(header_size // 8, 'big') + packed_data


def unpack_report(data):
    """
    Unpack bytes into a Report object.
    
    Args:
        data: Packed bytes
        
    Returns:
        Report object with unpacked data
    """
    # First byte is the header (msg_type and report ID)
    header_size = MSG_TYPE_SIZE + REPORT_ID_SIZE
    header = data[:header_size // 8]
    header_int = int.from_bytes(header, 'big') # [check] - should remove the hardcode endianess
    report_id = header_int & ((1 << ((header_size) - MSG_TYPE_SIZE)) - 1)
    
    # remove the first byte from data
    data = data[(header_size) // 8:]
    
    if report_id not in REPORT_NAMES:
        raise ValueError(f"Unknown report ID: {report_id}")
    
    report_name = REPORT_NAMES[report_id]
    
    # Get the format string
    format_str = get_report_format(report_name)
    
    # Unpack the data
    unpacked = struct.unpack(format_str, data[:struct.calcsize(format_str)])
    
    # Create the report object
    report = Report(report_name)
    
    # Fill in the variables (skip first value which is report ID)
    # for i, var_name in enumerate(report_dict[report_name].keys()):
    counter = 0
    for var_id, ss_id in ORDERED_REPORT_DICT[report.name]:
        var_name = VAR_ID_TO_NAME[ss_id][var_id]
        
        subsystem = report_dict[report_name][var_name]
        value = unpacked[counter]
        
        # # Apply inverse scaling if needed
        # scale = var_dict[var_name][2]
        # if scale is not None:
        #     value = value / scale
        
        report.add_variable(var_name, subsystem, value)
        counter += 1
    
    return report

def unpack_ack(data):
    # Get the first byte as an integer
    header = data[0] 
    
    # Extract Msg Type: Shift right 5 bits to drop the ID
    msg_type = header >> 5
    
    # Extract ID: Mask with 0001 1111 (0x1F) to keep only bottom 5 bits
    response_id = header & 0x1F
    
    # The rest is the string
    ack_args = data[1:].decode('utf-8')
    
    return Ack(response_id, ack_args)

def pack_command(command):
    """
    Pack a Command object into bytes.
    
    Args:
        command: Command object to pack
        
    Returns:
        Packed bytes
    """
    if not isinstance(command, Command):
        raise TypeError("Expected Command object")
    
    # Get the format string
    cmd_format = get_command_format(command.name)
    # print("Format string:", cmd_format)
    
    # build the header msg_type: 3 bits, command id: 13 bits
    header_size = MSG_TYPE_SIZE + COMMAND_ID_SIZE
    header = (MSG_TYPE_DICT["commands"] << (header_size - MSG_TYPE_SIZE)) | command.command_id
    # print("Header:", header)
    
    # Start with command ID
    values = []
    # Add arguments in the order defined in command_list
    for arg_name in command.arg_names:
        # print(f"Packing argument '{arg_name}' for command '{command.name}'")
        value = command.arguments.get(arg_name, None)
        
        if value is None:
            raise ValueError(f"Argument '{arg_name}' not set for command '{command.name}'")
        
        # Handle string arguments
        arg_type = argument_dict[arg_name]
        if 's' in arg_type:
            # remove s from the format string
            cmd_format = cmd_format.replace('s', '')
            continue # will not be handled here
            
        values.append(value)

    # Pack the data
    packed_data = struct.pack(cmd_format, *values)
    
    if any('s' in argument_dict[arg_name] for arg_name in command.arg_names):
        # Handle string arguments separately (append them as UTF-8 encoded bytes)
        for arg_name in command.arg_names:
            arg_type = argument_dict[arg_name]
            if 's' in arg_type:
                string_value = command.arguments.get(arg_name, "")
                packed_data += string_value.encode('utf-8')
                    
    return header.to_bytes(header_size // 8, 'big') + packed_data


def unpack_command(data):
    """
    Unpack bytes into a Command object.
    
    Args:
        data: Packed bytes
        
    Returns:
        Command object with unpacked data
    """
    # First 3 bits are the msg_type, next 3 bits are the ss and the last 10 bits are the command ID
    header_size = MSG_TYPE_SIZE + COMMAND_ID_SIZE
    header = data[:header_size // 8]
    header_int = int.from_bytes(header, 'big') # [check] - should remove the hardcode endianess
    
    command_id = header_int & 0x1FFF   # mask to get the last 13 bits
    
    if command_id > len(command_list):
        raise ValueError(f"Unknown command ID: {command_id}")
    
    data = data[(header_size) // 8:]  # remove the header bytes

        
    cmd_name = all_cmd_names[command_id]
    # print("Command name:", cmd_name)
    
    # Get the format string
    cmd_format = get_command_format(cmd_name)
    # print("Format string:", cmd_format)


    # check if there is a string argument in the command
    # for now there can only be one string argument and it should be the last one
    # i want to calculate the size of the other arguments and seperate the bytes
    string_arg_value = None # default value if there is no string argument
    if any('s' in argument_dict[arg_name] for arg_name in command_list[command_id][2]):
        # Handle string arguments separately (the string will be the remaining bytes after unpacking the other arguments)
        cmd_format = cmd_format.replace('s', '')
        non_string_size = struct.calcsize(cmd_format)

        string_data = data[non_string_size:]
        data = data[:non_string_size]  # only keep the non-string part for unpacking        
        
        string_arg_value = string_data.decode('utf-8')
    
    # Unpack the data
    unpacked = struct.unpack(cmd_format, data[:struct.calcsize(cmd_format)])
    if string_arg_value is not None:
        unpacked += (string_arg_value,)  # add the string argument back to the unpacked tuple
    
    # Create the command object
    command = Command(cmd_name)

    # Fill in the arguments (skip first value which is command ID)
    for i, arg_name in enumerate(command.arg_names):
        value = unpacked[i]
        
        # this would be a way to handle the string, but I am doing it seperately above
        # # Handle string arguments
        # arg_type = argument_dict[arg_name]
        # if 's' in arg_type:
        #     # Decode bytes to string and strip null bytes
        #     value = value.rstrip(b'\x00').decode('utf-8')
        
        
        command.add_argument(arg_name, value)
    
    return command


def pack_response(response):
    """
    Pack a Response object into bytes.
    
    Args:
        response: Response object to pack
        
    Returns:
        Packed bytes or None if response type is variable
    """
    if not isinstance(response, Response):
        raise TypeError("Expected Response object")
    
    if response.return_type is None or response.return_type == '?':
        # Variable or no return type
        return None
    
    # Get the format string
    _, response_format = get_command_format(response.command_name)
    
    if response_format is None:
        return None
    
    # Pack the response data
    packed_data = struct.pack(response_format, response.data)
    return packed_data


def unpack_response(cmd_name, data):
    """
    Unpack bytes into a Response object.
    
    Args:
        cmd_name: Name of the command this is a response to
        data: Packed bytes
        
    Returns:
        Response object with unpacked data
    """
    if cmd_name not in command_dict:
        raise ValueError(f"Command '{cmd_name}' not found in command_dict")
    
    return_type = command_dict[cmd_name][2]
    
    if return_type is None or return_type == '?':
        # Variable or no return type - return raw data
        response = Response(cmd_name, data)
        return response
    
    # Get the format string
    _, response_format = get_command_format(cmd_name)
    
    # Unpack the data
    unpacked = struct.unpack(response_format, data[:struct.calcsize(response_format)])
    
    # Create response object (single value expected)
    response = Response(cmd_name, unpacked[0])
    return response


def pack_variable(variable):
    """
    Pack a Variable object into bytes.
    
    Args:
        report: Report object to pack
        
    Returns:
        Packed bytes
    """
    
    if not isinstance(variable, Variable):
        raise TypeError("Expected Variable object")

    # get the format string
    format_str = get_variable_format(variable.name)
    
    
    # build the header    
    header_size = MSG_TYPE_SIZE + VARIABLE_SS_SIZE + VARIABLE_ID_SIZE
    header = (MSG_TYPE_DICT["variable"] << (header_size - MSG_TYPE_SIZE)) | (variable.subsystem_id << VARIABLE_ID_SIZE) | variable.var_id
    
    packed_data = struct.pack(format_str, variable.value)

    return header.to_bytes((header_size + 7) // 8, byteorder='big') + packed_data


def unpack_variable(data):
    """
    Unpack bytes into a Variable object.
    
    Args:
        var_name: Name of the variable
        data: Packed bytes
        
    Returns:
        Variable object with unpacked data
    """
    
    # First 3 bits are the msg_type, next 3 bits are the ss and the last 10 bits are the command ID
    header_size = MSG_TYPE_SIZE + VARIABLE_SS_SIZE + VARIABLE_ID_SIZE
    header = data[:header_size // 8]
    header_int = int.from_bytes(header, 'big') # [check] - should remove the hardcode endianess
    
    ss_id = (header_int >> 10) & 0x07 # mask to get the middle 3 bits
    variable_id = header_int & 0x3FF   # mask to get the last 10 bits
    
    if variable_id not in VAR_ID_TO_NAME[ss_id]:
        raise ValueError(f"Unknown variable ID: {variable_id} with ss_id: {ss_id}")
    
    data = data[(header_size) // 8:]  # remove the header bytes
        
    var_name = VAR_ID_TO_NAME[ss_id][variable_id]
    ss_name = [k for k,v in SS_map.items() if v == ss_id][0]
    print("Variable name:", var_name)
    
    # Get the format string
    var_format = get_variable_format(var_name)
    print("Format string:", var_format)
    
    # Unpack the data
    unpacked = struct.unpack(var_format, data[:struct.calcsize(var_format)])
    print("Unpacked data:", unpacked)
    
    
    # Create the variable object
    variable = Variable(var_name, ss_name)
    variable.set_value(unpacked[0])
    
    return variable


def pack(data):
    """
    Universal pack function that handles Reports, Commands, and Responses.
    
    Args:
        data: Report, Command, or Response object to pack
        
    Returns:
        Packed bytes
    """
    
    if isinstance(data, Report):
        return pack_report(data)
    elif isinstance(data, Variable):
        return pack_variable(data)
    elif isinstance(data, Command):
        return pack_command(data)
    elif isinstance(data, Response):
        return pack_response(data)
    elif isinstance(data, Ack):
        return pack_ack(data)
    else:
        raise TypeError(f"Cannot pack object of type {type(data)}")


def unpack(data, **kwargs):
    """
    Universal unpack function that handles Reports, Commands, and Responses.
    Use the msg_type contained in the header (the first byte) to determine the type.
    
    Args:
        data: Packed bytes to unpack
        **kwargs: Additional arguments (e.g., cmd_name for responses)
        
    Returns:
        Unpacked Report, Command, or Response object
    """
    msg_type = (data[0] >> (8 - MSG_TYPE_SIZE)) & ((1 << MSG_TYPE_SIZE) - 1)

    if msg_type == MSG_TYPE_DICT["reports"]:    
        return unpack_report(data)
    
    if msg_type == MSG_TYPE_DICT["variable"]:
        return unpack_variable(data)
    
    if msg_type == MSG_TYPE_DICT["commands"]:
        return unpack_command(data)
            
    if msg_type == MSG_TYPE_DICT["responses"]:
        cmd_name = kwargs.get('cmd_name')
        return unpack_response(cmd_name, data)
    
    if msg_type == MSG_TYPE_DICT["ack"]:
        # For now, we will just return the raw data for acks, as they are variable length and format
        return unpack_ack(data)
    
    raise ValueError("Unable to unpack data - unknown format")
