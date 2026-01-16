"""
Serial communication handler for dual ADXL345 sensors on Arduino.
Handles auto-detection, data streaming, and buffer management.
"""

import serial
import serial.tools.list_ports
import threading
import time
import numpy as np
from collections import deque
from typing import Optional, Callable, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SerialHandler:
    """Manages serial communication with Arduino vibration sensor system."""
    
    def __init__(self, 
                 baud_rate: int = 115200,
                 buffer_size: int = 1500,
                 auto_connect: bool = True):
        """
        Initialize serial handler.
        
        Args:
            baud_rate: Serial communication speed (default 115200)
            buffer_size: Size of circular buffer (default 1500 for 30s @ 50Hz)
            auto_connect: Automatically connect to Arduino on init
        """
        self.baud_rate = baud_rate
        self.buffer_size = buffer_size
        self.serial_conn = None
        self.port = None
        
        # Data buffers (circular for last 30 seconds)
        self.data_buffer = deque(maxlen=buffer_size)
        self.is_recording = False
        self.recording_data = []
        
        # Threading
        self.read_thread = None
        self.running = False
        self.lock = threading.Lock()
        
        # Callbacks
        self.on_data_received = None
        self.on_recording_start = None
        self.on_recording_end = None
        self.on_error = None
        
        # State
        self.connection_status = "disconnected"
        self.last_error = None
        self.sample_count = 0
        self.samples_per_second = 50
        
        if auto_connect:
            self.auto_connect()
    
    def find_arduino_ports(self) -> List[Tuple[str, str, str]]:
        """
        Auto-detect Arduino ports.
        
        Returns:
            List of (port, description, hwid) tuples
        """
        ports = []
        for port in serial.tools.list_ports.comports():
            # Look for common Arduino USB identifiers
            if any(identifier in port.hwid.lower() for identifier in 
                   ['arduino', 'ch340', 'cp210x', 'ftdi', 'usb']):
                ports.append((port.device, port.description, port.hwid))
        
        return ports
    
    def auto_connect(self) -> bool:
        """
        Automatically find and connect to Arduino.
        Tries all available ports and verifies Arduino is responding.
        
        Returns:
            True if connection successful, False otherwise
        """
        ports = self.find_arduino_ports()
        
        if not ports:
            logger.warning("No Arduino ports found. Trying ALL available ports...")
            # If no Arduino-identified ports, try all ports
            all_ports = serial.tools.list_ports.comports()
            ports = [(p.device, p.description, p.hwid) for p in all_ports]
        
        logger.info(f"Found {len(ports)} port(s) to check:")
        for port_info in ports:
            logger.info(f"  - {port_info[0]}: {port_info[1]}")
        
        # Try each port
        for port_info in ports:
            port_name = port_info[0]
            logger.info(f"\n→ Attempting to connect to {port_name}...")
            
            # Try to connect and verify it's Arduino
            if self._try_port_and_verify(port_name):
                logger.info(f"✓ Successfully connected to Arduino on {port_name}")
                return True
            else:
                logger.debug(f"✗ {port_name} is not an Arduino or not responding")
        
        logger.warning("Could not find Arduino on any port")
        return False
    
    def _try_port_and_verify(self, port: str) -> bool:
        """
        Try to connect to a port and verify it's an Arduino.
        
        Args:
            port: Serial port name to test
            
        Returns:
            True if Arduino detected and connected, False otherwise
        """
        try:
            # Quick test connection
            test_conn = serial.Serial(
                port=port,
                baudrate=self.baud_rate,
                timeout=0.5,
                write_timeout=0.5
            )
            
            logger.info(f"  Opened {port}, waiting for Arduino response...")
            time.sleep(1.5)  # Wait for Arduino initialization
            
            # Clear any existing data
            test_conn.reset_input_buffer()
            
            # Read initialization message from Arduino
            response = ""
            timeout_count = 0
            while timeout_count < 10:
                if test_conn.in_waiting > 0:
                    chunk = test_conn.read(test_conn.in_waiting).decode('utf-8', errors='ignore')
                    response += chunk
                    logger.debug(f"  Received: {repr(chunk[:100])}")
                    
                    # Check for Arduino initialization message (more lenient)
                    # Look for key signatures
                    signatures = [
                        "Dual ADXL345", 
                        "Vibration Monitor", 
                        "initialized", 
                        "Sampling Rate",
                        "START_STREAMING",
                        ">>> START_STREAMING <<<",
                    ]
                    
                    if any(sig in response for sig in signatures) or len(response) > 200:
                        logger.info(f"  ✓ Found Arduino signature in response!")
                        test_conn.close()
                        
                        # Now properly connect
                        return self.connect(port)
                
                time.sleep(0.2)
                timeout_count += 1
            
            # Even if no Arduino signature found, try to connect anyway
            # Send 'S' command to test if Arduino responds
            logger.info(f"  Testing port with 'S' command...")
            test_conn.write(b'S')
            time.sleep(0.5)
            
            if test_conn.in_waiting > 0:
                test_response = test_conn.read(test_conn.in_waiting).decode('utf-8', errors='ignore')
                if any(char.isalnum() for char in test_response):
                    logger.info(f"  ✓ Arduino responded to 'S' command!")
                    test_conn.close()
                    return self.connect(port)
            
            logger.info(f"  No response on {port}, trying standard connection anyway...")
            test_conn.close()
            return self.connect(port)
        
        except serial.SerialException as e:
            logger.debug(f"  ✗ {port} error: {e}")
            return False
        except Exception as e:
            logger.debug(f"  ✗ {port} unexpected error: {e}")
            return False
    
    def connect(self, port: str) -> bool:
        """
        Connect to specific serial port.
        
        Args:
            port: Serial port name (e.g., 'COM3', '/dev/ttyUSB0')
            
        Returns:
            True if connection successful
        """
        try:
            self.serial_conn = serial.Serial(
                port=port,
                baudrate=self.baud_rate,
                timeout=1.0,
                write_timeout=1.0
            )
            
            self.port = port
            self.connection_status = "connected"
            logger.info(f"Connected to {port} at {self.baud_rate} baud")
            
            # Start read thread
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            
            # Wait for Arduino to be ready
            time.sleep(2)
            
            return True
        
        except serial.SerialException as e:
            self.connection_status = "error"
            self.last_error = str(e)
            logger.error(f"Failed to connect to {port}: {e}")
            
            if self.on_error:
                self.on_error(str(e))
            
            return False
    
    def disconnect(self) -> None:
        """Disconnect from serial port."""
        self.running = False
        
        if self.read_thread:
            self.read_thread.join(timeout=2)
        
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except:
                pass
        
        self.connection_status = "disconnected"
        logger.info("Disconnected from serial port")
    
    def start_recording(self) -> bool:
        """
        Send command to Arduino to start recording/streaming.
        Sends 'S' command for continuous streaming.
        
        Returns:
            True if command sent successfully
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("Serial connection not open")
            return False
        
        try:
            with self.lock:
                # Send 'S' command to start continuous streaming
                self.serial_conn.write(b'S')
                self.is_recording = True
                self.recording_data = []
                self.sample_count = 0
            
            logger.info("Streaming started (sent 'S' command to Arduino)")
            
            if self.on_recording_start:
                self.on_recording_start()
            
            return True
        
        except serial.SerialException as e:
            logger.error(f"Failed to start streaming: {e}")
            self.last_error = str(e)
            
            if self.on_error:
                self.on_error(str(e))
            
            return False
    
    def stop_recording(self) -> List[np.ndarray]:
        """
        Stop recording/streaming and return collected data.
        Sends 'E' command to Arduino to stop streaming.
        
        Returns:
            List of [sensor1_data, sensor2_data] as numpy arrays
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.warning("Serial connection not open, cannot send stop command")
        else:
            try:
                # Send 'E' command to stop streaming
                self.serial_conn.write(b'E')
                logger.info("Streaming stopped (sent 'E' command to Arduino)")
            except serial.SerialException as e:
                logger.error(f"Failed to send stop command: {e}")
        
        with self.lock:
            self.is_recording = False
            data = self.recording_data.copy()
        
        logger.info(f"Data collection stopped. Collected {len(data)} samples")
        
        if self.on_recording_end:
            self.on_recording_end()
        
        if len(data) == 0:
            return [np.array([]), np.array([])]
        
        # Parse and return data
        return self._parse_recording_data(data)
    
    def _read_loop(self) -> None:
        """Main read loop (runs in separate thread)."""
        line_buffer = ""
        
        while self.running:
            try:
                if not self.serial_conn or not self.serial_conn.is_open:
                    time.sleep(0.1)
                    continue
                
                # Read available data
                if self.serial_conn.in_waiting > 0:
                    chunk = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8', errors='ignore')
                    line_buffer += chunk
                    
                    # Process complete lines
                    while '\n' in line_buffer:
                        line, line_buffer = line_buffer.split('\n', 1)
                        line = line.strip()
                        
                        if not line:
                            continue
                        
                        # Handle protocol markers
                        if line == "START_RECORDING":
                            logger.info("Arduino started recording")
                            continue
                        
                        if line == "END_RECORDING":
                            logger.info("Arduino finished recording")
                            continue
                        
                        # Skip header line
                        if "S1_X" in line or "S2_X" in line:
                            continue
                        
                        # Skip initialization messages
                        if "===" in line or "initialized" in line or "System ready" in line:
                            logger.debug(f"Arduino: {line}")
                            continue
                        
                        # Parse data line
                        try:
                            data_tuple = self._parse_data_line(line)
                            if data_tuple:
                                with self.lock:
                                    # Add to circular buffer
                                    self.data_buffer.append(data_tuple)
                                    
                                    # Add to recording if active
                                    if self.is_recording:
                                        self.recording_data.append(data_tuple)
                                        self.sample_count += 1
                                
                                # Callback for new data
                                if self.on_data_received:
                                    self.on_data_received(data_tuple)
                        
                        except ValueError:
                            # Log non-data lines
                            if line and not any(x in line for x in ['ready', 'Waiting', 'initialized']):
                                logger.debug(f"Skipping line: {line}")
                
                else:
                    time.sleep(0.01)
            
            except UnicodeDecodeError:
                logger.warning("Unicode decode error in serial read")
            except Exception as e:
                logger.error(f"Error in read loop: {e}")
                if self.on_error:
                    self.on_error(str(e))
                time.sleep(0.1)
    
    def _parse_data_line(self, line: str) -> Optional[Tuple]:
        """
        Parse CSV data line from Arduino.
        
        Expected format: S1_X_g, S1_Y_g, S1_Z_g, S2_X_g, S2_Y_g, S2_Z_g
        
        Returns:
            Tuple of (s1_x, s1_y, s1_z, s2_x, s2_y, s2_z) as floats, or None if parse failed
        """
        try:
            # Handle empty or whitespace-only lines
            if not line or not line.strip():
                return None
            
            values = [float(x.strip()) for x in line.split(',')]
            
            if len(values) != 6:
                return None
            
            # Validate values are finite (not NaN or Inf)
            if not all(isinstance(v, (int, float)) and np.isfinite(v) for v in values):
                logger.warning(f"Non-finite values in data line: {values}")
                return None
            
            return tuple(values)
        
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to parse data line '{line}': {e}")
            return None
    
    def _parse_recording_data(self, data: List[Tuple]) -> List[np.ndarray]:
        """
        Parse recording data into sensor arrays.
        
        Args:
            data: List of 6-tuples (s1_x, s1_y, s1_z, s2_x, s2_y, s2_z)
            
        Returns:
            [sensor1_data (Nx3), sensor2_data (Nx3)]
        """
        if len(data) == 0:
            return [np.array([]), np.array([])]
        
        data_array = np.array(data)
        
        # Split into sensor 1 and sensor 2
        sensor1 = data_array[:, :3]  # X, Y, Z for sensor 1
        sensor2 = data_array[:, 3:]  # X, Y, Z for sensor 2
        
        return [sensor1, sensor2]
    
    def get_latest_data(self, n_samples: Optional[int] = None) -> List[np.ndarray]:
        """
        Get latest data from buffer.
        
        Args:
            n_samples: Number of samples to return (default: all)
            
        Returns:
            [sensor1_data (Nx3), sensor2_data (Nx3)]
        """
        with self.lock:
            if n_samples is None:
                data = list(self.data_buffer)
            else:
                data = list(self.data_buffer)[-n_samples:]
        
        return self._parse_recording_data(data)
    
    def get_status(self) -> dict:
        """
        Get current connection and recording status.
        
        Returns:
            Dictionary with status information
        """
        with self.lock:
            buffer_len = len(self.data_buffer)
        
        return {
            'connection_status': self.connection_status,
            'port': self.port,
            'is_recording': self.is_recording,
            'buffer_size': buffer_len,
            'sample_count': self.sample_count,
            'samples_per_second': self.samples_per_second,
            'last_error': self.last_error,
        }
    
    def set_callbacks(self,
                     on_data_received: Optional[Callable] = None,
                     on_recording_start: Optional[Callable] = None,
                     on_recording_end: Optional[Callable] = None,
                     on_error: Optional[Callable] = None) -> None:
        """
        Set callback functions for events.
        
        Args:
            on_data_received: Called when new data received (data_tuple)
            on_recording_start: Called when recording starts ()
            on_recording_end: Called when recording ends ()
            on_error: Called when error occurs (error_message)
        """
        self.on_data_received = on_data_received
        self.on_recording_start = on_recording_start
        self.on_recording_end = on_recording_end
        self.on_error = on_error


# Test code
if __name__ == "__main__":
    # Create handler
    handler = SerialHandler()
    
    # Check if connected
    status = handler.get_status()
    print(f"Connection status: {status['connection_status']}")
    print(f"Port: {status['port']}")
    
    if status['connection_status'] == 'connected':
        # Start recording
        handler.start_recording()
        time.sleep(2)  # Record for 2 seconds
        
        # Get data
        sensor1, sensor2 = handler.stop_recording()
        print(f"Recorded {len(sensor1)} samples")
        print(f"Sensor 1 shape: {sensor1.shape}")
        print(f"Sensor 2 shape: {sensor2.shape}")
    
    # Cleanup
    handler.disconnect()
