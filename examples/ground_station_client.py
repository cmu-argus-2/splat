"""
Ground Station Client
Sends commands to the satellite and receives telemetry.
"""
import sys
import os


# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import socket
import time
from telemetry_codec import (
    Report, Command, Response, pack, unpack
)
from telemetry_definition import command_dict, report_dict
from telemetry_helper import list_all_commands, list_all_reports


class Colors:
    """ANSI Escape sequences for terminal colors"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class GroundStation:
    """
    Ground station client for communicating with the satellite.
    """
    
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
    
    def connect(self):
        """Connect to the satellite."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"{Colors.GREEN}Connected to satellite at {self.host}:{self.port}{Colors.ENDC}")
            return True
        except Exception as e:
            print(f"{Colors.FAIL}Failed to connect: {e}{Colors.ENDC}")
            return False
    
    def disconnect(self):
        """Disconnect from the satellite."""
        if self.socket:
            self.socket.close()
            self.connected = False
            print(f"{Colors.WARNING}Disconnected from satellite{Colors.ENDC}")
    
    def send_command(self, command, wait_response=True, timeout=5.0):
        """
        Send a command to the satellite.
        
        Args:
            command: Command object
            wait_response: Whether to wait for a response
            timeout: Response timeout in seconds
            
        Returns:
            Response object (Status) or None
        """
        
        if not self.connected:
            print(f"{Colors.FAIL}Not connected to satellite{Colors.ENDC}")
            return None
        
        try:
            # Pack and send command
            packed = pack(command)
            print(f"\n{Colors.CYAN}Sending command: {command.name}{Colors.ENDC}")
            print(f"   Arguments: {command.arguments}")
            print(f"   Packed size: {len(packed)} bytes")
            print(f"   Hex: {packed.hex()}")
            
            self.socket.sendall(packed)
            
            # Wait for response if requested
            if wait_response:
                self.socket.settimeout(timeout)
                response_data = self.socket.recv(1024)
                
                if response_data:
                    print(f"{Colors.BLUE}Received response (Status): {len(response_data)} bytes{Colors.ENDC}")
                    print(f"   Hex: {response_data.hex()}")
                    
                    # Try to unpack response (Status)
                    try:
                        response = unpack(response_data, data_type='response', cmd_name=command.name)
                        print(f"   Status data: {response.data}")
                        return response
                    except Exception as e:
                        print(f"   {Colors.WARNING}Could not unpack response: {e}{Colors.ENDC}")
                        print(f"   Raw response: {response_data.hex()}")
                        return response_data
                else:
                    print(f"{Colors.WARNING}No response received{Colors.ENDC}")
                    return None
            
        except socket.timeout:
            print(f"{Colors.FAIL}Response timeout after {timeout}s{Colors.ENDC}")
            return None
        except Exception as e:
            print(f"{Colors.FAIL}Error sending command: {e}{Colors.ENDC}")
            return None
    
    def request_report(self, report_name):
        """
        Request a telemetry report from the satellite.
        Handles the two-step process:
        1. Receive Status (Response)
        2. Receive Report Data
        """
        command = Command("GET_REPORT")
        command.add_argument("report_name", report_name)
        
        # 1. Send command and get Status
        status_response = self.send_command(command)
        
        # 2. If status is success (1), wait for the report data
        if status_response and getattr(status_response, 'data', 0) == 1:
            print(f"{Colors.CYAN}   Status OK. Waiting for report payload...{Colors.ENDC}")
            try:
                self.socket.settimeout(5.0)
                report_data = self.socket.recv(1024)
                
                if report_data:
                    print(f"{Colors.BLUE}Received payload: {len(report_data)} bytes{Colors.ENDC}")
                    # Unpack report
                    report = unpack(report_data, data_type='report')
                    print(f"   Received report: {report.name}")
                    return report
                else:
                    print(f"{Colors.FAIL}No report payload received{Colors.ENDC}")
                    return None
            except Exception as e:
                print(f"{Colors.FAIL}Error unpacking report payload: {e}{Colors.ENDC}")
                return None
        else:
            print(f"{Colors.WARNING}Report request returned failure status or no response.{Colors.ENDC}")
            return None

    def request_variable(self, subsystem, var_name):
        """
        Request a single variable from the satellite.
        Handles the two-step process:
        1. Receive Status (Response)
        2. Receive Variable Data
        """
        command = Command("GET_VARIABLE")
        command.add_argument("subsystem", subsystem)
        command.add_argument("var_name", var_name)
        
        # 1. Send command and get Status
        status_response = self.send_command(command)
        
        # 2. If status is success (1), wait for the variable data
        if status_response and getattr(status_response, 'data', 0) == 1:
            print(f"{Colors.CYAN}   Status OK. Waiting for variable payload...{Colors.ENDC}")
            try:
                self.socket.settimeout(5.0)
                var_data = self.socket.recv(1024)
                
                if var_data:
                    print(f"{Colors.BLUE}Received payload: {len(var_data)} bytes{Colors.ENDC}")
                    print(f"   Hex: {var_data.hex()}")
                    # Since we don't have a specific unpack_variable in the context,
                    # we return the raw data or try a generic unpack if supported.
                    # Assuming unpack can handle it or we process manually:
                    try:
                        # Attempt to interpret based on standard codec
                        val = unpack(var_data, data_type='variable')
                        print(f"   Value: {val}")
                        return val
                    except:
                        return var_data
                else:
                    print(f"{Colors.FAIL}No variable payload received{Colors.ENDC}")
                    return None
            except Exception as e:
                print(f"{Colors.FAIL}Error unpacking variable payload: {e}{Colors.ENDC}")
                return None
        else:
            print(f"{Colors.WARNING}Variable request returned failure status.{Colors.ENDC}")
            return None
    
    def print_report(self, report):
        """
        Pretty print a telemetry report.
        
        Args:
            report: Report object
        """
        print(f"\n{Colors.HEADER}Telemetry Report: {report.name}{Colors.ENDC}")
        print("=" * 60)
        
        for subsystem, variables in sorted(report.variables.items()):
            print(f"\n{Colors.BOLD}[{subsystem}]{Colors.ENDC}")
            for var_name, value in sorted(variables.items()):
                if value is not None:
                    if isinstance(value, float):
                        print(f"  {var_name:20s} = {Colors.CYAN}{value:.4f}{Colors.ENDC}")
                    else:
                        print(f"  {var_name:20s} = {Colors.CYAN}{value}{Colors.ENDC}")
        print("=" * 60)
    
    def interactive_menu(self):
        """Run an interactive menu for testing."""
        while True:
            print("\n" + "=" * 60)
            print(f"{Colors.HEADER}GROUND STATION - INTERACTIVE MENU{Colors.ENDC}")
            print("=" * 60)
            print("1. Send PING")
            print("2. Request TM_HEARTBEAT report")
            print("3. Request TM_FULL report")
            print("4. Request TM_POWER report")
            print("5. Get single variable") # Added new option
            print("6. Set temperature threshold")
            print("7. Set power mode")
            print("8. Reset EPS")
            print("9. Reboot CDH")
            print("10. List all commands")
            print("11. List all reports")
            print("q. Quit")
            print("=" * 60)
            
            choice = input(f"\n{Colors.BOLD}Enter choice: {Colors.ENDC}").strip().lower()
            
            if choice == '1':
                cmd = Command("PING")
                self.send_command(cmd)
            
            elif choice == '2':
                report = self.request_report("TM_HEARTBEAT")
                if isinstance(report, Report):
                    self.print_report(report)
            
            elif choice == '3':
                report = self.request_report("TM_FULL")
                if isinstance(report, Report):
                    self.print_report(report)
            
            elif choice == '4':
                report = self.request_report("TM_POWER")
                if isinstance(report, Report):
                    self.print_report(report)

            elif choice == '5':
                subsystem = input("Enter subsystem (e.g., CDH, EPS): ").strip().upper()
                var_name = input("Enter variable name (e.g., temp, voltage): ").strip()
                self.request_variable(subsystem, var_name)
            
            elif choice == '6':
                try:
                    temp = float(input("Enter temperature threshold (K): "))
                    cmd = Command("SET_TEMP_THRESHOLD")
                    cmd.add_argument("temp", temp)
                    self.send_command(cmd)
                except ValueError:
                    print(f"{Colors.FAIL}Invalid temperature value{Colors.ENDC}")
            
            elif choice == '7':
                try:
                    mode = int(input("Enter power mode (0-255): "))
                    cmd = Command("SET_POWER_MODE")
                    cmd.add_argument("mode", mode)
                    self.send_command(cmd)
                except ValueError:
                    print(f"{Colors.FAIL}Invalid mode value{Colors.ENDC}")
            
            elif choice == '8':
                cmd = Command("RESET_EPS")
                self.send_command(cmd)
            
            elif choice == '9':
                cmd = Command("REBOOT_CDH")
                self.send_command(cmd)
            
            elif choice == '10':
                print(f"\n{Colors.HEADER}Available Commands:{Colors.ENDC}")
                print("=" * 60)
                commands = list_all_commands()
                for cmd_name, info in sorted(commands.items()):
                    print(f"{cmd_name:30s} [{info['subsystem']:6s}] "
                          f"Args: {info['arguments']}")
                print("=" * 60)
            
            elif choice == '11':
                print(f"\n{Colors.HEADER}Available Reports:{Colors.ENDC}")
                print("=" * 60)
                reports = list_all_reports()
                for report_name, info in sorted(reports.items()):
                    print(f"{report_name:20s} ({info['size']:3d} bytes) "
                          f"Variables: {', '.join(info['variables'])}")
                print("=" * 60)
            
            elif choice == 'q':
                break
            
            else:
                print(f"{Colors.FAIL}Invalid choice{Colors.ENDC}")


def run_automated_tests(gs):
    """Run automated tests of the protocol."""
    print("\n" + "=" * 60)
    print(f"{Colors.HEADER}RUNNING AUTOMATED TESTS{Colors.ENDC}")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Ping
    print(f"\n{Colors.BOLD}[Test 1] PING command{Colors.ENDC}")
    try:
        cmd = Command("PING")
        response = gs.send_command(cmd)
        if response and response.data == True:
            print(f"{Colors.GREEN}PING test passed{Colors.ENDC}")
            tests_passed += 1
        else:
            print(f"{Colors.FAIL}PING test failed{Colors.ENDC}")
            tests_failed += 1
    except Exception as e:
        print(f"{Colors.FAIL}PING test failed: {e}{Colors.ENDC}")
        tests_failed += 1
    
    time.sleep(0.5)
    
    # Test 2: Request heartbeat report
    print(f"\n{Colors.BOLD}[Test 2] Request TM_HEARTBEAT report{Colors.ENDC}")
    try:
        report = gs.request_report("TM_HEARTBEAT")
        if isinstance(report, Report) and report.name == "TM_HEARTBEAT":
            gs.print_report(report)
            print(f"{Colors.GREEN}TM_HEARTBEAT test passed{Colors.ENDC}")
            tests_passed += 1
        else:
            print(f"{Colors.FAIL}TM_HEARTBEAT test failed{Colors.ENDC}")
            tests_failed += 1
    except Exception as e:
        print(f"{Colors.FAIL}TM_HEARTBEAT test failed: {e}{Colors.ENDC}")
        tests_failed += 1
    
    time.sleep(0.5)
    
    # Test 3: Set temperature threshold
    print(f"\n{Colors.BOLD}[Test 3] SET_TEMP_THRESHOLD command{Colors.ENDC}")
    try:
        cmd = Command("SET_TEMP_THRESHOLD")
        cmd.add_argument("temp", 310.5)
        response = gs.send_command(cmd)
        if response and response.data == 1:
            print(f"{Colors.GREEN}SET_TEMP_THRESHOLD test passed{Colors.ENDC}")
            tests_passed += 1
        else:
            print(f"{Colors.FAIL}SET_TEMP_THRESHOLD test failed{Colors.ENDC}")
            tests_failed += 1
    except Exception as e:
        print(f"{Colors.FAIL}SET_TEMP_THRESHOLD test failed: {e}{Colors.ENDC}")
        tests_failed += 1
    
    time.sleep(0.5)
    
    # Test 4: Request full report
    print(f"\n{Colors.BOLD}[Test 4] Request TM_FULL report{Colors.ENDC}")
    try:
        report = gs.request_report("TM_FULL")
        if isinstance(report, Report) and report.name == "TM_FULL":
            gs.print_report(report)
            print(f"{Colors.GREEN}TM_FULL test passed{Colors.ENDC}")
            tests_passed += 1
        else:
            print(f"{Colors.FAIL}TM_FULL test failed{Colors.ENDC}")
            tests_failed += 1
    except Exception as e:
        print(f"{Colors.FAIL}TM_FULL test failed: {e}{Colors.ENDC}")
        tests_failed += 1
    
    time.sleep(0.5)
    
    # Test 5: Reset EPS
    print(f"\n{Colors.BOLD}[Test 5] RESET_EPS command{Colors.ENDC}")
    try:
        cmd = Command("RESET_EPS")
        response = gs.send_command(cmd)
        if response and response.data == 1:
            print(f"{Colors.GREEN}RESET_EPS test passed{Colors.ENDC}")
            tests_passed += 1
        else:
            print(f"{Colors.FAIL}RESET_EPS test failed{Colors.ENDC}")
            tests_failed += 1
    except Exception as e:
        print(f"{Colors.FAIL}RESET_EPS test failed: {e}{Colors.ENDC}")
        tests_failed += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"{Colors.HEADER}TEST SUMMARY: {Colors.GREEN}{tests_passed} passed{Colors.ENDC}, {Colors.FAIL}{tests_failed} failed{Colors.ENDC}")
    print("=" * 60)


def main():
    """Main function."""
    print(f"{Colors.BOLD}{Colors.HEADER}Ground Station Client{Colors.ENDC}")
    print("=" * 60)
    
    gs = GroundStation(host='localhost', port=5555)
    
    if not gs.connect():
        print(f"{Colors.WARNING}Make sure the satellite server is running!{Colors.ENDC}")
        return
    
    try:
        # Ask user what to do
        print("\nWhat would you like to do?")
        print("1. Run automated tests")
        print("2. Interactive menu")
        
        choice = input(f"\nEnter choice (1 or 2): {Colors.ENDC}").strip()
        
        if choice == '1':
            run_automated_tests(gs)
        elif choice == '2':
            gs.interactive_menu()
        else:
            print(f"{Colors.WARNING}Invalid choice, running automated tests{Colors.ENDC}")
            run_automated_tests(gs)
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Interrupted by user{Colors.ENDC}")
    finally:
        gs.disconnect()


if __name__ == "__main__":
    main()