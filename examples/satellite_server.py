"""
Satellite Simulator - Server
Simulates a satellite receiving commands and sending telemetry reports.
"""

import sys
import os


# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import socket
import struct
import time
import threading
from telemetry_codec import (
    Report, Command, Response, pack, unpack
)
from telemetry_definition import (
    command_dict, ENDIANNESS
)

import random


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


class SatelliteSimulator:
    """
    Simulates a satellite that can receive commands and send telemetry.
    """
    
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        
        # Simulated satellite state
        self.state = {
            'time': time.time(),
            'temp': 295.15,  # Kelvin
            'cpu_usage': 45,  # %
            'voltage': 3.7,  # V
            'current': 0.5,  # A
            'battery_level': 85,  # %
            'solar_voltage': 5.0,  # V
            'signal_strength': -70,  # dBm
            'packet_count': 0,
            'attitude_x': 0.0,
            'attitude_y': 0.0,
            'attitude_z': 0.0,
            'temp_threshold': 300.0,
            'power_mode': 1,
        }
    
    def start(self):
        """Start the satellite simulator server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.running = True
        
        print(f"{Colors.GREEN}Satellite simulator started on {self.host}:{self.port}{Colors.ENDC}")
        print(f"Waiting for ground station connection...")
        
        # Start background telemetry sender
        telemetry_thread = threading.Thread(target=self.send_periodic_telemetry, daemon=True)
        telemetry_thread.start()
        
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                print(f"\n{Colors.GREEN}Ground station connected from {address}{Colors.ENDC}")
                
                # Handle client in a separate thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"{Colors.FAIL}Error accepting connection: {e}{Colors.ENDC}")
    
    def handle_client(self, client_socket):
        """Handle a connected client."""
        try:
            while self.running:
                # Receive data
                data = client_socket.recv(1024)
                if not data:
                    break
                
                print(f"\n{Colors.BLUE}Received {len(data)} bytes: {data.hex()}{Colors.ENDC}")
                
                # Try to unpack as command
                try:
                    command = unpack(data, data_type='command')
                    print(f"   Command: {command.name}")
                    print(f"   Arguments: {command.arguments}")
                    
                    # Process command - Pass socket to allow multi-step responses
                    response_data = self.process_command(command, client_socket)
                    
                    # Send response (if process_command returned data)
                    # For GET_... commands, this is the 2nd packet (Payload)
                    # For others, this is the only packet (Response)
                    if response_data:
                        client_socket.sendall(response_data)
                        print(f"{Colors.CYAN}Sent response payload: {len(response_data)} bytes{Colors.ENDC}")
                    
                except Exception as e:
                    print(f"   {Colors.FAIL}Error processing command: {e}{Colors.ENDC}")
        
        except Exception as e:
            print(f"{Colors.FAIL}Client handler error: {e}{Colors.ENDC}")
        finally:
            client_socket.close()
            print(f"{Colors.WARNING}Ground station disconnected{Colors.ENDC}")
    
    def process_command(self, command, client_socket):
        """
        Process a received command and return response.
        
        Args:
            command: Command object
            client_socket: The active socket (used for multi-step responses)
            
        Returns:
            Packed response bytes or None
        """
        self.state['packet_count'] += 1
        
        if command.name == "RESET_EPS":
            print(f"   {Colors.BOLD}>> Resetting EPS...{Colors.ENDC}")
            self.state['voltage'] = 3.7
            self.state['current'] = 0.0
            response = Response(command.name, 1)  # Success
            return pack(response)
        
        elif command.name == "SET_TEMP_THRESHOLD":
            temp = command.get_argument('temp')
            print(f"   {Colors.BOLD}>> Setting temperature threshold to {temp}K{Colors.ENDC}")
            self.state['temp_threshold'] = temp
            response = Response(command.name, 1)  # Success
            return pack(response)
        
        elif command.name == "SET_POWER_MODE":
            mode = command.get_argument('mode')
            print(f"   {Colors.BOLD}>> Setting power mode to {mode}{Colors.ENDC}")
            self.state['power_mode'] = mode
            response = Response(command.name, 1)  # Success
            return pack(response)
        
        elif command.name == "REBOOT_CDH":
            print(f"   {Colors.BOLD}>> Rebooting CDH...{Colors.ENDC}")
            time.sleep(0.1)
            response = Response(command.name, 1)  # Success
            return pack(response)
        
        elif command.name == "SET_TX_POWER":
            threshold = command.get_argument('threshold')
            print(f"   {Colors.BOLD}>> Setting TX power to {threshold}{Colors.ENDC}")
            response = Response(command.name, 1)  # Success
            return pack(response)
        
        elif command.name == "SET_ATTITUDE_MODE":
            mode = command.get_argument('mode')
            print(f"   {Colors.BOLD}>> Setting attitude mode to {mode}{Colors.ENDC}")
            response = Response(command.name, 1)  # Success
            return pack(response)
        
        elif command.name == "PING":
            print(f"   {Colors.BOLD}>> PONG!{Colors.ENDC}")
            response = Response(command.name, True)
            return pack(response)
        
        elif command.name == "GET_VARIABLE":
            var_name = command.get_argument('var_name')
            subsystem = command.get_argument('subsystem')
            print(f"   {Colors.BOLD}>> Getting variable {var_name} from {subsystem}{Colors.ENDC}")
            
            if var_name in self.state:
                # 1. Send STATUS Success
                print(f"   {Colors.CYAN}>> Sending Status ACK...{Colors.ENDC}")
                status = Response(command.name, 1)
                client_socket.sendall(pack(status))
                
                # Short delay to separate packets in the stream
                time.sleep(0.1)
                
                # 2. Return PAYLOAD (Variable)
                print(f"   {Colors.CYAN}>> Sending Variable Data...{Colors.ENDC}")
                from telemetry_codec import pack_variable
                var_data = pack_variable(var_name, self.state[var_name])
                return var_data
            else:
                # Send STATUS Fail and return None (no payload)
                print(f"   {Colors.WARNING}>> Variable not found, sending NACK.{Colors.ENDC}")
                response = Response(command.name, 0)
                return pack(response)
        
        elif command.name == "GET_REPORT":
            report_name = command.get_argument('report_name')
            print(f"   {Colors.BOLD}>> Sending report {report_name}{Colors.ENDC}")
            
            # 1. Send STATUS Success
            print(f"   {Colors.CYAN}>> Sending Status ACK...{Colors.ENDC}")
            status = Response(command.name, 1)
            client_socket.sendall(pack(status))

            # Short delay to separate packets in the stream
            time.sleep(0.1)
            
            # 2. Return PAYLOAD (Report)
            print(f"   {Colors.CYAN}>> Sending Report Data...{Colors.ENDC}")
            report = self.generate_report(report_name)
            return pack(report)
        
        else:
            print(f"   {Colors.WARNING}>> Unknown command: {command.name}{Colors.ENDC}")
            return None
    
    def generate_report(self, report_name):
        """
        Generate a telemetry report.
        
        Args:
            report_name: Name of the report to generate
            
        Returns:
            Report object
        """
        from telemetry_definition import report_dict
        
        
        # Update current time
        self.state['time'] = time.time()
        
        # Simulate some dynamics
        self.state['temp'] += (295.15 - self.state['temp']) * 0.1  # Drift toward 295K
        self.state['battery_level'] = random.randint(0,100)
        self.state['cpu_usage'] = random.randint(10,90)
        
        # Create report
        report = Report(report_name)
        
        for var_name, subsystem in report_dict[report_name]:
            if var_name in self.state:
                report.add_variable(var_name, subsystem, self.state[var_name])
    
        return report
    
    def send_periodic_telemetry(self):
        """Send periodic heartbeat telemetry (for future use)."""
        # This could be used to send unsolicited telemetry
        # Not implemented in this basic version
        pass
    
    def stop(self):
        """Stop the satellite simulator."""
        self.running = False
        if self.socket:
            self.socket.close()
        print(f"\n{Colors.WARNING}Satellite simulator stopped{Colors.ENDC}")


def main():
    """Main function to run the satellite simulator."""
    simulator = SatelliteSimulator(host='localhost', port=5555)
    
    try:
        simulator.start()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Shutting down...{Colors.ENDC}")
        simulator.stop()


if __name__ == "__main__":
    main()