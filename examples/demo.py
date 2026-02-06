#!/usr/bin/env python3
"""
Quick Demo Script
Demonstrates the basic usage of the satellite communication protocol.
"""

import sys
import os


# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from splat.telemetry_codec import Report, Command, Response, pack, unpack
from splat.telemetry_definition import ENDIANNESS, var_dict, report_dict, command_list, REPORT_IDS, COMMAND_IDS, MAX_PACKET_SIZE
from splat.telemetry_helper import validate_definitions, get_variable_size, get_report_size, get_command_size
import time


def demo_basic_usage():
    """Demonstrate basic pack/unpack operations."""
    print("=" * 80)
    print("SATELLITE COMMUNICATION PROTOCOL - QUICK DEMO")
    print("=" * 80)
    
    # Validate definitions
    print("\n1. Validating protocol definitions...")
    is_valid, errors = validate_definitions()
    if is_valid:
        print("   ✓ Protocol definitions are valid!")
    else:
        print("   ✗ Errors found:")
        for error in errors:
            print(f"     - {error}")
        return
    
    # Create a report
    print("\n2. Creating a telemetry report...")
    report = Report("TM_TEST")
    report.set_variables(
        TIME=int(time.time()),
        SC_STATE=1,  
        GPS_MESSAGE_ID=2 
    )
    print(f"   Created: {report}")
    print(f"   Variables: {report.variables}")
    
    # Pack the report
    print("\n3. Packing report to binary...")
    packed_report = pack(report)
    print(f"   Packed size: {len(packed_report)} bytes")
    print(f"   Hex: {packed_report.hex()}")
    print(f"   Binary: {' '.join(f'{b:08b}' for b in packed_report[:8])}...")
    
    # Unpack the report
    print("\n4. Unpacking binary back to report...")
    unpacked_report = unpack(packed_report)
    print(f"   Unpacked: {unpacked_report}")
    print(f"   Variables: {unpacked_report.variables}")
    
    # Verify data integrity
    print("\n5. Verifying data integrity...")
    original_time = report.get_variable("TIME")
    unpacked_time = unpacked_report.get_variable("TIME")
    if abs(original_time - unpacked_time) < 0.01:
        print(f"   ✓ Time: {original_time:.2f} == {unpacked_time:.2f}")
    else:
        print(f"   ✗ Temperature mismatch!")
    
    # Create a command
    print("\n6. Creating a command...")
    cmd = Command("SWITCH_TO_STATE")
    cmd.add_argument("target_state_id", 1)
    cmd.add_argument("time_in_state", 60)
    print(f"   Created: {cmd}")
    print(f"   Arguments: {cmd.arguments}")
    
    # Pack the command
    print("\n7. Packing command to binary...")
    packed_cmd = pack(cmd)
    print(f"   Packed size: {len(packed_cmd)} bytes")
    print(f"   Hex: {packed_cmd.hex()}")
    
    # Unpack the command
    print("\n8. Unpacking binary back to command...")
    unpacked_cmd = unpack(packed_cmd, data_type='command')
    print(f"   Unpacked: {unpacked_cmd}")
    print(f"   Arguments: {unpacked_cmd.arguments}")
    
    print("\n" + "=" * 80)
    print("✓ DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 80)
   
    # Show protocol summary
    print("\n" + "=" * 80)
    print("Full Protocol Summary:")
    print("=" * 80)
    print("\nRun 'python telemetry_helper.py' to see the complete protocol summary")
    print("Run 'python satellite_server.py' to start the satellite simulator")
    print("Run 'python ground_station_client.py' to connect to the satellite")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demo_basic_usage()
