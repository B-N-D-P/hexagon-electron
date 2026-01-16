#!/usr/bin/env python3
"""
HEXAGON Structural Health - CLI Application
Command-line interface for real-time monitoring
"""

import threading
import serial
import serial.tools.list_ports
from collections import deque
import numpy as np
from scipy import signal
import csv
import json
from datetime import datetime
from pathlib import Path
import time
import sys

# ============================================================================
# SERIAL DATA HANDLER
# ============================================================================

class SerialDataThread(threading.Thread):
    """Thread to read data from Arduino"""
    
    def __init__(self, port, baudrate=115200):
        super().__init__(daemon=True)
        self.port = port
        self.baudrate = baudrate
        self.running = False
        self.ser = None
        self.data_callback = None
        
    def run(self):
        """Read data from Arduino"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self.running = True
            buffer = ""
            
            while self.running:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line and self.data_callback:
                            try:
                                values = [float(x) for x in line.split(',')]
                                self.data_callback(values)
                            except ValueError:
                                pass
                                
        except Exception as e:
            print(f"❌ Serial error: {e}")
        finally:
            self.stop()
            
    def stop(self):
        """Stop reading"""
        self.running = False
        if self.ser:
            self.ser.close()

# ============================================================================
# PARAMETER CALCULATOR
# ============================================================================

class ParameterCalculator:
    """Calculate 50+ structural parameters"""
    
    def __init__(self, buffer_size=1000, fs=50):
        self.buffer_size = buffer_size
        self.fs = fs
        self.data_s1 = deque(maxlen=buffer_size)
        self.data_s2 = deque(maxlen=buffer_size)
        
    def add_data(self, values):
        """Add data point"""
        if len(values) >= 6:
            self.data_s1.append([values[0], values[1], values[2]])
            self.data_s2.append([values[3], values[4], values[5]])
            
    def compute_parameters(self):
        """Compute all parameters"""
        if len(self.data_s1) < 10:
            return {}
            
        s1 = np.array(list(self.data_s1))
        s2 = np.array(list(self.data_s2))
        
        params = {}
        
        # Time-domain parameters
        for axis_idx, axis_name in enumerate(['x', 'y', 'z']):
            for sensor_idx, sensor_name in enumerate(['s1', 's2']):
                data = s1[:, axis_idx] if sensor_idx == 0 else s2[:, axis_idx]
                key = f'{sensor_name}_{axis_name}'
                
                params[f'{key}_rms'] = float(np.sqrt(np.mean(data**2)))
                params[f'{key}_peak'] = float(np.max(np.abs(data)))
                params[f'{key}_mean'] = float(np.mean(data))
                params[f'{key}_std'] = float(np.std(data))
                params[f'{key}_var'] = float(np.var(data))
                params[f'{key}_crest'] = float(np.max(np.abs(data)) / np.sqrt(np.mean(data**2)) if np.sqrt(np.mean(data**2)) > 0 else 0)
                
        # Magnitude
        mag_s1 = np.sqrt(s1[:, 0]**2 + s1[:, 1]**2 + s1[:, 2]**2)
        mag_s2 = np.sqrt(s2[:, 0]**2 + s2[:, 1]**2 + s2[:, 2]**2)
        
        params['mag_s1_rms'] = float(np.sqrt(np.mean(mag_s1**2)))
        params['mag_s2_rms'] = float(np.sqrt(np.mean(mag_s2**2)))
        
        # Correlation
        if len(s1) > 1:
            try:
                params['corr_s1_xy'] = float(np.corrcoef(s1[:, 0], s1[:, 1])[0, 1])
                params['corr_s1_xz'] = float(np.corrcoef(s1[:, 0], s1[:, 2])[0, 1])
                params['corr_s1_yz'] = float(np.corrcoef(s1[:, 1], s1[:, 2])[0, 1])
                params['corr_s2_xy'] = float(np.corrcoef(s2[:, 0], s2[:, 1])[0, 1])
                params['corr_s2_xz'] = float(np.corrcoef(s2[:, 0], s2[:, 2])[0, 1])
                params['corr_s2_yz'] = float(np.corrcoef(s2[:, 1], s2[:, 2])[0, 1])
                params['corr_mag'] = float(np.corrcoef(mag_s1, mag_s2)[0, 1])
            except:
                pass
        
        return params

# ============================================================================
# MAIN CLI APPLICATION
# ============================================================================

def clear_screen():
    """Clear terminal"""
    print("\033[2J\033[H", end="")

def display_header():
    """Display application header"""
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  HEXAGON Structural Health - Real-Time Monitoring CLI".center(78) + "║")
    print("║" + "  Professional Desktop Application (Lightweight Version)".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")

def display_menu():
    """Display main menu"""
    print("\n📋 MAIN MENU:")
    print("  1. Connect to Arduino")
    print("  2. Monitor Real-Time Data")
    print("  3. Record Data Session")
    print("  4. Export to CSV")
    print("  5. Show Available Ports")
    print("  6. Exit")
    print("\nSelect option (1-6): ", end="")

def list_ports():
    """List available serial ports"""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("\n❌ No serial ports found")
        return None
    
    print("\n📡 Available Serial Ports:")
    for i, (port, desc, hwid) in enumerate(ports, 1):
        print(f"  {i}. {port} - {desc}")
    
    return ports

def connect_arduino():
    """Connect to Arduino"""
    ports = list_ports()
    if not ports:
        return None
    
    choice = input("\nSelect port number: ").strip()
    try:
        port_idx = int(choice) - 1
        if 0 <= port_idx < len(ports):
            return ports[port_idx][0]
    except:
        pass
    
    print("❌ Invalid selection")
    return None

def monitor_data(port):
    """Monitor real-time data"""
    calculator = ParameterCalculator()
    sample_count = 0
    
    print(f"\n🔌 Connecting to {port}...")
    
    def on_data(values):
        nonlocal sample_count
        calculator.add_data(values)
        sample_count += 1
    
    thread = SerialDataThread(port)
    thread.data_callback = on_data
    thread.start()
    
    print("✅ Connected! Monitoring data (Press Ctrl+C to stop)...\n")
    
    try:
        last_display = time.time()
        while thread.running:
            if time.time() - last_display >= 1.0:  # Update every second
                clear_screen()
                display_header()
                
                params = calculator.compute_parameters()
                
                print(f"\n📊 Live Parameters (Samples: {sample_count})")
                print("=" * 80)
                
                if params:
                    print("\n📈 SENSOR 1 (S1):")
                    print(f"  X: RMS={params.get('s1_x_rms', 0):.4f}  Peak={params.get('s1_x_peak', 0):.4f}  Mean={params.get('s1_x_mean', 0):.4f}")
                    print(f"  Y: RMS={params.get('s1_y_rms', 0):.4f}  Peak={params.get('s1_y_peak', 0):.4f}  Mean={params.get('s1_y_mean', 0):.4f}")
                    print(f"  Z: RMS={params.get('s1_z_rms', 0):.4f}  Peak={params.get('s1_z_peak', 0):.4f}  Mean={params.get('s1_z_mean', 0):.4f}")
                    
                    print("\n📈 SENSOR 2 (S2):")
                    print(f"  X: RMS={params.get('s2_x_rms', 0):.4f}  Peak={params.get('s2_x_peak', 0):.4f}  Mean={params.get('s2_x_mean', 0):.4f}")
                    print(f"  Y: RMS={params.get('s2_y_rms', 0):.4f}  Peak={params.get('s2_y_peak', 0):.4f}  Mean={params.get('s2_y_mean', 0):.4f}")
                    print(f"  Z: RMS={params.get('s2_z_rms', 0):.4f}  Peak={params.get('s2_z_peak', 0):.4f}  Mean={params.get('s2_z_mean', 0):.4f}")
                    
                    print("\n🔗 CORRELATION:")
                    print(f"  S1: XY={params.get('corr_s1_xy', 0):.4f}  XZ={params.get('corr_s1_xz', 0):.4f}  YZ={params.get('corr_s1_yz', 0):.4f}")
                    print(f"  S2: XY={params.get('corr_s2_xy', 0):.4f}  XZ={params.get('corr_s2_xz', 0):.4f}  YZ={params.get('corr_s2_yz', 0):.4f}")
                    print(f"  Cross-Sensor: {params.get('corr_mag', 0):.4f}")
                    
                    print("\n📊 MAGNITUDE:")
                    print(f"  S1: RMS={params.get('mag_s1_rms', 0):.4f}")
                    print(f"  S2: RMS={params.get('mag_s2_rms', 0):.4f}")
                
                print("\n" + "=" * 80)
                print("Press Ctrl+C to stop monitoring")
                
                last_display = time.time()
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped")
    finally:
        thread.stop()
        thread.join()

def record_session(port):
    """Record data session"""
    calculator = ParameterCalculator()
    recorded_data = []
    
    print(f"\n🔌 Connecting to {port}...")
    
    def on_data(values):
        calculator.add_data(values)
        recorded_data.append(values)
    
    thread = SerialDataThread(port)
    thread.data_callback = on_data
    thread.start()
    
    print("✅ Recording started (Press Ctrl+C to stop)...\n")
    
    try:
        last_display = time.time()
        while thread.running:
            if time.time() - last_display >= 1.0:
                elapsed = int(time.time() - start_time) if 'start_time' in locals() else 0
                print(f"⏱️  Recording... Samples: {len(recorded_data):5d}  Time: {elapsed:3d}s", end="\r")
                if 'start_time' not in locals():
                    start_time = time.time()
                last_display = time.time()
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n")
    finally:
        thread.stop()
        thread.join()
    
    if recorded_data:
        export_csv(recorded_data)
    else:
        print("❌ No data recorded")

def export_csv(data):
    """Export data to CSV"""
    if not data:
        print("❌ No data to export")
        return
    
    filename = f"structural_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    print(f"\n💾 Exporting to {filename}...")
    
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['S1_X', 'S1_Y', 'S1_Z', 'S2_X', 'S2_Y', 'S2_Z'])
            for row in data:
                writer.writerow(row[:6])
        
        print(f"✅ Data exported successfully!")
        print(f"   File: {filename}")
        print(f"   Samples: {len(data)}")
    except Exception as e:
        print(f"❌ Export failed: {e}")

def main():
    """Main application loop"""
    port = None
    
    while True:
        clear_screen()
        display_header()
        
        if port:
            print(f"\n✅ Connected to: {port}\n")
        else:
            print("\n❌ Not connected\n")
        
        display_menu()
        
        choice = input().strip()
        
        if choice == "1":
            port = connect_arduino()
        elif choice == "2":
            if port:
                monitor_data(port)
            else:
                print("\n❌ Please connect to Arduino first (option 1)")
                input("Press Enter to continue...")
        elif choice == "3":
            if port:
                record_session(port)
            else:
                print("\n❌ Please connect to Arduino first (option 1)")
                input("Press Enter to continue...")
        elif choice == "4":
            print("\n📝 Recording a quick sample...")
            if port:
                recorded_data = []
                def on_data(values):
                    recorded_data.append(values)
                
                thread = SerialDataThread(port)
                thread.data_callback = on_data
                thread.start()
                
                print("Collecting 100 samples...")
                while len(recorded_data) < 100 and thread.running:
                    time.sleep(0.01)
                
                thread.stop()
                export_csv(recorded_data)
                input("Press Enter to continue...")
            else:
                print("\n❌ Please connect to Arduino first")
                input("Press Enter to continue...")
        elif choice == "5":
            list_ports()
            input("\nPress Enter to continue...")
        elif choice == "6":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid option")
            input("Press Enter to continue...")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Application terminated")
    except Exception as e:
        print(f"\n❌ Error: {e}")
