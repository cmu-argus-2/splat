#!/usr/bin/env python3
"""
SPLAT Web Interface - Flask Application
A Flask-based web server for unpacking and packing SPLAT protocol messages.
"""

import sys
import os
# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os
from flask import Flask, render_template, request, jsonify
import traceback
from splat.telemetry_codec import unpack, pack, Report, Command
from splat.telemetry_definition import report_dict, command_list, var_dict
from splat.telemetry_helper import list_all_reports, list_all_commands
from config import config


def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Register routes
    register_routes(app)
    
    return app


def register_routes(app):
    """Register all application routes."""
    
    @app.route('/')
    def index():
        """Serve the main web interface."""
        return render_template('index.html')

    @app.route('/api/reports')
    def get_reports():
        """Get all available reports."""
        return jsonify(list_all_reports())

    @app.route('/api/commands')
    def get_commands():
        """Get all available commands."""
        return jsonify(list_all_commands())

    @app.route('/api/unpack', methods=['POST'])
    def api_unpack():
        """Handle unpacking hex data."""
        try:
            data = request.get_json()
            hex_input = data.get('hex', '')
            
            # Parse hex input - remove "0x" prefixes and spaces
            hex_clean = hex_input.replace('0x', '').replace(' ', '').replace('\n', '').replace('\r', '')
            
            # Convert to bytes
            byte_data = bytes.fromhex(hex_clean)
            
            # Try to unpack
            result = unpack_and_format(byte_data)
            
            return jsonify({
                'success': True,
                'result': result,
                'byte_count': len(byte_data)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 400

    @app.route('/api/pack', methods=['POST'])
    def api_pack():
        """Handle packing data to hex."""
        try:
            data = request.get_json()
            pack_type = data.get('type')  # 'report' or 'command'
            name = data.get('name')
            values = data.get('values', {})
            
            if pack_type == 'report':
                result = pack_report(name, values)
            elif pack_type == 'command':
                result = pack_command(name, values)
            else:
                raise ValueError(f"Unknown pack type: {pack_type}")
            
            return jsonify({
                'success': True,
                'result': result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 400


# Create the app instance
app = create_app()





def unpack_and_format(byte_data):
    """Unpack bytes and format for display."""
    unpack_obj = unpack(byte_data)
    
    # Try as report
    if type(unpack_obj) == Report:
        return format_report(unpack_obj, byte_data)
    
    # Try as command
    elif type(unpack_obj) == Command:
        return format_command(unpack_obj, byte_data)
    
    else:
        return {
            'type': 'unknown',
            'first_byte': f'0x{byte_data[0]:02X}',
            'hex': byte_data.hex(),
            'error': f'Unknown ID: 0x{byte_data[0]:02X}. Not a valid report or command ID.'
        }


def format_report(report, byte_data):
    """Format a report for display."""
    variables = []
    for subsystem in sorted(report.variables.keys()):
        for var_name, value in sorted(report.variables[subsystem].items()):
            var_info = var_dict.get(var_name, ['Unknown', '?', None])
            variables.append({
                'name': var_name,
                'subsystem': subsystem,
                'value': value,
                'type': var_info[1],
                'scale': var_info[2]
            })
    
    return {
        'type': 'report',
        'name': report.name,
        'id': report.report_id,
        'variables': variables,
        'hex': byte_data.hex(),
        'hex_formatted': ' '.join(f'0x{b:02X}' for b in byte_data),
        'size': len(byte_data)
    }


def format_command(command, byte_data):
    """Format a command for display."""
    arguments = []
    for arg_name, value in command.arguments.items():
        arguments.append({
            'name': arg_name,
            'value': value
        })
    
    return {
        'type': 'command',
        'name': command.name,
        'id': command.command_id,
        'arguments': arguments,
        'hex': byte_data.hex(),
        'hex_formatted': ' '.join(f'0x{b:02X}' for b in byte_data),
        'size': len(byte_data)
    }


def pack_report(report_name, values):
    """Pack a report from values."""
    report = Report(report_name)
    # Set variables
    for var_name, value in values.items():
        # Find subsystem for this variable
        subsystem = None
        for vname in report_dict[report_name]:
            if vname == var_name:
                subsystem = report_dict[report_name][vname]
                break
        
        if subsystem is not None:
            # Convert value to appropriate type
            var_type = var_dict[var_name][1]
            if var_type in ['f', 'd']:
                value = float(value)
            elif var_type in ['B', 'b', 'H', 'h', 'I', 'i', 'L', 'l', 'Q', 'q']:
                value = int(value)
            elif var_type == '?':
                value = bool(value)
            
            report.add_variable(var_name, subsystem, value)
    
    # Pack
    packed = pack(report)
    
    return {
        'hex': packed.hex(),
        'hex_formatted': ' '.join(f'0x{b:02X}' for b in packed),
        'size': len(packed),
        'type': 'report',
        'name': report_name
    }


def pack_command(command_name, arguments):
    """Pack a command from arguments."""
    command = Command(command_name)
    
    # Set arguments
    for arg_name, value in arguments.items():
        # Convert value to appropriate type (simplified)
        try:
            value = int(value)
        except (ValueError, TypeError):
            pass  # Keep as string
        
        command.add_argument(arg_name, value)
    
    # Pack
    packed = pack(command)
    
    return {
        'hex': packed.hex(),
        'hex_formatted': ' '.join(f'0x{b:02X}' for b in packed),
        'size': len(packed),
        'type': 'command',
        'name': command_name
    }


def main():
    """Start the SPLAT web server."""
    print("=" * 80)
    print("SPLAT Protocol Web Interface (Flask)")
    print("=" * 80)
    print(f"\nServer starting at http://localhost:5000")
    print(f"\nOpen your browser and navigate to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=8080)


if __name__ == "__main__":
    main()
