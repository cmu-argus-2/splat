import sys
import os


# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from splat.telemetry_codec import pack, unpack, Report, Command, Response
from splat.telemetry_helper import format_bytes

if __name__ == "__main__":
    import time
    
    print("=" * 80)
    print("TELEMETRY CODEC TEST")
    print("=" * 80)
    
    # Test 1: Create and pack a report
    print("\n--- Test 1: Report Packing/Unpacking ---")
    myReport = Report("TM_TEST")
    myReport.add_variable("TIME", "CDH", int(time.time()))
    myReport.add_variable("SC_STATE", "CDH", 2)
    myReport.add_variable("GPS_MESSAGE_ID", "GPS", 1)
    
    print(f"Original report: {myReport}")
    print(f"Variables: {myReport.variables}")
    
    packed_report = pack(myReport)
    print(f"Packed size: {len(packed_report)} bytes")
    print(f"Packed data (hex): {format_bytes(packed_report)}")
    
    unpacked_report = unpack(packed_report)
    print(f"Unpacked report: {unpacked_report}")
    print(f"Variables: {unpacked_report.variables}")
    
    # Test 2: Create and pack a command
    print("\n--- Test 2: Command Packing/Unpacking ---")
    myCommand = Command("SUM")
    myCommand.add_argument("op1", 300)
    myCommand.add_argument("op2", 300)
    
    print(f"Original command: {myCommand}")
    print(f"Arguments: {myCommand.arguments}")
    
    packed_cmd = pack(myCommand)
    print(f"Packed size: {len(packed_cmd)} bytes")
    print(f"Packed data (hex): {format_bytes(packed_cmd)}")
    
    unpacked_cmd = unpack(packed_cmd, data_type='command')
    print(f"Unpacked command: {unpacked_cmd}")
    print(f"Arguments: {unpacked_cmd.arguments}")
    
    
    # Test 3: Using set_variables convenience method
    print("\n--- Test 3: Convenience Methods ---")
    myReport2 = Report("TM_TEST")
    myReport2.set_variables(
        TIME=int(time.time()),
        SC_STATE=1,
        GPS_MESSAGE_ID=2
    )
    
    print(f"Report with set_variables: {myReport2}")
    print(f"Variables: {myReport2.variables}")
    
    packed_report2 = pack(myReport2)
    print(f"Packed size: {len(packed_report2)} bytes")
    
    print("\n" + "=" * 80)
