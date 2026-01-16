#!/usr/bin/env python3
"""
HEXAGON Structural Health - Real-Time Monitoring IDE
Professional PyQt5 Desktop Application
Data collection, real-time parameter display, and CSV export
"""

import sys
import json
import csv
import os
from datetime import datetime
from pathlib import Path
from collections import deque
import serial.tools.list_ports
import numpy as np
from scipy import signal

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QProgressBar, QStatusBar,
    QGroupBox, QGridLayout, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QMutex
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis
from PyQt5.QtCore import QDateTime

import serial

# ============================================================================
# SERIAL DATA HANDLER THREAD
# ============================================================================

class SerialDataThread(QThread):
    """Thread to read data from Arduino serial port"""
    data_received = pyqtSignal(list)  # Emits list of [s1x, s1y, s1z, s2x, s2y, s2z, ...]
    connection_status = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.ser = None
        self.running = False
        self.port = None
        self.baudrate = 115200
        self.mutex = QMutex()
        
    def set_port(self, port):
        self.mutex.lock()
        self.port = port
        self.mutex.unlock()
        
    def connect_arduino(self):
        """Connect to Arduino"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self.connection_status.emit(True)
            return True
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {str(e)}")
            return False
            
    def run(self):
        """Read data from Arduino"""
        if not self.connect_arduino():
            return
            
        self.running = True
        buffer = ""
        
        while self.running:
            try:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    
                    # Parse complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line:
                            try:
                                values = [float(x) for x in line.split(',')]
                                self.data_received.emit(values)
                            except ValueError:
                                pass
                                
            except Exception as e:
                self.error_occurred.emit(f"Read error: {str(e)}")
                break
                
        self.stop()
        
    def stop(self):
        """Stop reading and close port"""
        self.running = False
        if self.ser:
            self.ser.close()
        self.connection_status.emit(False)

# ============================================================================
# PARAMETER CALCULATOR
# ============================================================================

class ParameterCalculator:
    """Compute 50+ structural health parameters from sensor data"""
    
    def __init__(self, buffer_size=1000, fs=100):
        self.buffer_size = buffer_size
        self.fs = fs  # Sampling frequency (Hz)
        self.data_s1 = deque(maxlen=buffer_size)  # Sensor 1: [x, y, z]
        self.data_s2 = deque(maxlen=buffer_size)  # Sensor 2: [x, y, z]
        
    def add_data(self, values):
        """Add new data point: [s1x, s1y, s1z, s2x, s2y, s2z]"""
        if len(values) >= 6:
            self.data_s1.append([values[0], values[1], values[2]])
            self.data_s2.append([values[3], values[4], values[5]])
            
    def compute_parameters(self):
        """Compute all 50+ parameters"""
        params = {}
        
        if len(self.data_s1) < 10:
            return self._empty_parameters()
            
        # Convert to numpy arrays
        s1 = np.array(list(self.data_s1))
        s2 = np.array(list(self.data_s2))
        
        # ===== SENSOR 1 PARAMETERS =====
        params.update(self._compute_axis_params(s1[:, 0], 's1_x'))
        params.update(self._compute_axis_params(s1[:, 1], 's1_y'))
        params.update(self._compute_axis_params(s1[:, 2], 's1_z'))
        
        # ===== SENSOR 2 PARAMETERS =====
        params.update(self._compute_axis_params(s2[:, 0], 's2_x'))
        params.update(self._compute_axis_params(s2[:, 1], 's2_y'))
        params.update(self._compute_axis_params(s2[:, 2], 's2_z'))
        
        # ===== MAGNITUDE & VECTOR PARAMETERS =====
        mag_s1 = np.sqrt(s1[:, 0]**2 + s1[:, 1]**2 + s1[:, 2]**2)
        mag_s2 = np.sqrt(s2[:, 0]**2 + s2[:, 1]**2 + s2[:, 2]**2)
        
        params.update(self._compute_axis_params(mag_s1, 'mag_s1'))
        params.update(self._compute_axis_params(mag_s2, 'mag_s2'))
        
        # ===== CORRELATION PARAMETERS =====
        params['corr_s1_xy'] = np.corrcoef(s1[:, 0], s1[:, 1])[0, 1] if len(s1) > 1 else 0
        params['corr_s1_xz'] = np.corrcoef(s1[:, 0], s1[:, 2])[0, 1] if len(s1) > 1 else 0
        params['corr_s1_yz'] = np.corrcoef(s1[:, 1], s1[:, 2])[0, 1] if len(s1) > 1 else 0
        
        params['corr_s2_xy'] = np.corrcoef(s2[:, 0], s2[:, 1])[0, 1] if len(s2) > 1 else 0
        params['corr_s2_xz'] = np.corrcoef(s2[:, 0], s2[:, 2])[0, 1] if len(s2) > 1 else 0
        params['corr_s2_yz'] = np.corrcoef(s2[:, 1], s2[:, 2])[0, 1] if len(s2) > 1 else 0
        
        # Cross-sensor correlation
        params['corr_s1s2_mag'] = np.corrcoef(mag_s1, mag_s2)[0, 1] if len(mag_s1) > 1 else 0
        
        # ===== FREQUENCY DOMAIN PARAMETERS =====
        params.update(self._compute_fft_params(s1[:, 0], 's1_x'))
        params.update(self._compute_fft_params(s2[:, 0], 's2_x'))
        
        return params
        
    def _compute_axis_params(self, data, axis_name):
        """Compute parameters for a single axis"""
        if len(data) < 2:
            return {}
            
        params = {}
        params[f'{axis_name}_rms'] = float(np.sqrt(np.mean(data**2)))
        params[f'{axis_name}_peak'] = float(np.max(np.abs(data)))
        params[f'{axis_name}_mean'] = float(np.mean(data))
        params[f'{axis_name}_std'] = float(np.std(data))
        params[f'{axis_name}_var'] = float(np.var(data))
        params[f'{axis_name}_min'] = float(np.min(data))
        params[f'{axis_name}_max'] = float(np.max(data))
        params[f'{axis_name}_range'] = float(np.max(data) - np.min(data))
        
        # Crest factor
        rms = np.sqrt(np.mean(data**2))
        peak = np.max(np.abs(data))
        params[f'{axis_name}_crest'] = float(peak / rms) if rms > 0 else 0
        
        # Skewness and Kurtosis
        params[f'{axis_name}_skew'] = float(np.mean(((data - np.mean(data)) / np.std(data))**3))
        params[f'{axis_name}_kurt'] = float(np.mean(((data - np.mean(data)) / np.std(data))**4))
        
        # Energy
        params[f'{axis_name}_energy'] = float(np.sum(data**2))
        
        return params
        
    def _compute_fft_params(self, data, axis_name):
        """Compute FFT parameters"""
        if len(data) < 4:
            return {}
            
        params = {}
        
        try:
            # Compute FFT
            fft = np.fft.fft(data)
            freqs = np.fft.fftfreq(len(data), 1/self.fs)
            magnitude = np.abs(fft)
            
            # Get positive frequencies only
            pos_idx = freqs > 0
            pos_freqs = freqs[pos_idx]
            pos_mag = magnitude[pos_idx]
            
            if len(pos_mag) > 0:
                # Find dominant frequency
                dominant_idx = np.argmax(pos_mag)
                params[f'{axis_name}_dominant_freq'] = float(pos_freqs[dominant_idx])
                params[f'{axis_name}_dominant_power'] = float(pos_mag[dominant_idx])
                
                # Spectral energy
                params[f'{axis_name}_spectral_energy'] = float(np.sum(pos_mag**2))
                
                # Peak detection
                try:
                    distance = max(1, int(len(pos_mag) * 0.05))
                    peaks, _ = signal.find_peaks(pos_mag, distance=distance)
                    params[f'{axis_name}_num_peaks'] = float(len(peaks))
                except:
                    params[f'{axis_name}_num_peaks'] = 0.0
                    
        except Exception as e:
            pass
            
        return params
        
    def _empty_parameters(self):
        """Return dictionary with all zeros"""
        params = {}
        for axis in ['s1_x', 's1_y', 's1_z', 's2_x', 's2_y', 's2_z', 'mag_s1', 'mag_s2']:
            for param in ['rms', 'peak', 'mean', 'std', 'var', 'min', 'max', 'range', 'crest', 'skew', 'kurt', 'energy']:
                params[f'{axis}_{param}'] = 0.0
        
        for s in [1, 2]:
            for axes in ['xy', 'xz', 'yz']:
                params[f'corr_s{s}_{axes}'] = 0.0
        
        params['corr_s1s2_mag'] = 0.0
        
        for axis in ['s1_x', 's2_x']:
            for param in ['dominant_freq', 'dominant_power', 'spectral_energy', 'num_peaks']:
                params[f'{axis}_{param}'] = 0.0
                
        return params

