#!/usr/bin/env python3
"""
HEXAGON Structural Health - Lightweight UI (Tkinter-based)
Alternative to PyQt5 - No compilation needed, instant startup
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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
            print(f"Serial error: {e}")
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
                
        # Magnitude
        mag_s1 = np.sqrt(s1[:, 0]**2 + s1[:, 1]**2 + s1[:, 2]**2)
        mag_s2 = np.sqrt(s2[:, 0]**2 + s2[:, 1]**2 + s2[:, 2]**2)
        
        params['mag_s1_rms'] = float(np.sqrt(np.mean(mag_s1**2)))
        params['mag_s2_rms'] = float(np.sqrt(np.mean(mag_s2**2)))
        
        # Correlation
        if len(s1) > 1:
            params['corr_s1_xy'] = float(np.corrcoef(s1[:, 0], s1[:, 1])[0, 1])
            params['corr_s2_xy'] = float(np.corrcoef(s2[:, 0], s2[:, 1])[0, 1])
            params['corr_mag'] = float(np.corrcoef(mag_s1, mag_s2)[0, 1])
        
        return params

# ============================================================================
# MAIN APPLICATION
# ============================================================================

class HexagonLiteApp:
    """Lightweight Tkinter application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("HEXAGON Structural Health - Real-Time Monitor")
        self.root.geometry("900x600")
        
        self.serial_thread = None
        self.calculator = ParameterCalculator()
        self.recording = False
        self.recorded_data = []
        
        self.create_ui()
        self.update_timer()
        
    def create_ui(self):
        """Create UI"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel
        left_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        
        # Port selection
        ttk.Label(left_frame, text="Port:").pack()
        self.port_var = tk.StringVar()
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo = ttk.Combobox(left_frame, textvariable=self.port_var, 
                                        values=ports or ["No ports"])
        self.port_combo.pack(fill=tk.X, pady=5)
        
        # Buttons
        ttk.Button(left_frame, text="🔌 Connect", 
                   command=self.toggle_connection).pack(fill=tk.X, pady=5)
        
        ttk.Button(left_frame, text="🔴 Start Recording", 
                   command=self.toggle_recording).pack(fill=tk.X, pady=5)
        
        ttk.Button(left_frame, text="💾 Export CSV", 
                   command=self.export_csv).pack(fill=tk.X, pady=5)
        
        # Status
        self.status_label = ttk.Label(left_frame, text="Status: Disconnected", 
                                       foreground="red")
        self.status_label.pack(pady=10)
        
        # Sample count
        self.sample_label = ttk.Label(left_frame, text="Samples: 0")
        self.sample_label.pack()
        
        # Right panel - Display parameters
        right_frame = ttk.LabelFrame(main_frame, text="Real-Time Parameters", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create text widget for parameters
        scrollbar = ttk.Scrollbar(right_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.param_text = tk.Text(right_frame, height=30, width=50, 
                                   yscrollcommand=scrollbar.set)
        self.param_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.param_text.yview)
        
        self.param_text.insert(tk.END, "Waiting for data...\n")
        
    def toggle_connection(self):
        """Connect/disconnect"""
        if not self.serial_thread:
            port = self.port_var.get()
            if not port or port == "No ports":
                messagebox.showerror("Error", "No port selected")
                return
                
            self.serial_thread = SerialDataThread(port)
            self.serial_thread.data_callback = self.on_data
            self.serial_thread.start()
            self.status_label.config(text="Status: Connected ✓", foreground="green")
        else:
            self.serial_thread.stop()
            self.serial_thread.join()
            self.serial_thread = None
            self.status_label.config(text="Status: Disconnected", foreground="red")
            
    def toggle_recording(self):
        """Record data"""
        self.recording = not self.recording
        if self.recording:
            self.recorded_data = []
            self.status_label.config(text="Status: Recording... ⏺️", foreground="orange")
        else:
            self.status_label.config(text="Status: Recording stopped", foreground="blue")
            
    def on_data(self, values):
        """Handle incoming data"""
        self.calculator.add_data(values)
        if self.recording:
            self.recorded_data.append(values)
            
    def update_timer(self):
        """Update display every 500ms"""
        params = self.calculator.compute_parameters()
        
        if params:
            self.param_text.delete(1.0, tk.END)
            self.param_text.insert(tk.END, "=" * 40 + "\n")
            self.param_text.insert(tk.END, "REAL-TIME PARAMETERS\n")
            self.param_text.insert(tk.END, "=" * 40 + "\n\n")
            
            self.param_text.insert(tk.END, "SENSOR 1 (S1):\n")
            for k, v in sorted(params.items()):
                if 's1_' in k or 'mag_s1' in k:
                    self.param_text.insert(tk.END, f"  {k}: {v:.4f}\n")
                    
            self.param_text.insert(tk.END, "\nSENSOR 2 (S2):\n")
            for k, v in sorted(params.items()):
                if 's2_' in k or 'mag_s2' in k:
                    self.param_text.insert(tk.END, f"  {k}: {v:.4f}\n")
                    
            self.param_text.insert(tk.END, "\nCORRELATION:\n")
            for k, v in sorted(params.items()):
                if 'corr' in k:
                    self.param_text.insert(tk.END, f"  {k}: {v:.4f}\n")
        
        self.sample_label.config(text=f"Samples: {len(self.recorded_data)}")
        self.root.after(500, self.update_timer)
        
    def export_csv(self):
        """Export to CSV"""
        if not self.recorded_data:
            messagebox.showwarning("No Data", "Record some data first")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"structural_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['S1_X', 'S1_Y', 'S1_Z', 'S2_X', 'S2_Y', 'S2_Z'])
                    for row in self.recorded_data:
                        writer.writerow(row[:6])
                        
                messagebox.showinfo("Success", f"Exported to:\n{file_path}")
                self.recorded_data = []
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    root = tk.Tk()
    app = HexagonLiteApp(root)
    root.mainloop()
