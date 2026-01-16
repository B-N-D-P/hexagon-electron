#!/usr/bin/env python3
"""
HEXAGON Structural Health - Main UI Application
Professional PyQt5 Desktop Application
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

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QProgressBar, QStatusBar,
    QGroupBox, QGridLayout, QSplitter, QCheckBox, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QMutex, QDateTime
from PyQt5.QtGui import QFont, QColor, QIcon, QBrush
from PyQt5.QtChart import QChart, QChartView, QLineSeries
import pyqtgraph as pg

# Import from ui.py
from ui import SerialDataThread, ParameterCalculator

# ============================================================================
# MAIN APPLICATION WINDOW
# ============================================================================

class HexagonStructuralHealthUI(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HEXAGON Structural Health - Real-Time Monitoring IDE")
        self.setGeometry(100, 100, 1800, 1000)
        
        # Initialize components
        self.serial_thread = None
        self.param_calculator = ParameterCalculator(buffer_size=1000, fs=50)
        self.recording = False
        self.recorded_data = []
        self.recorded_params = []
        self.data_buffer = deque(maxlen=500)
        
        # Create UI
        self.create_ui()
        self.setup_styles()
        
        # Timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(100)  # Update every 100ms
        
    def create_ui(self):
        """Create main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # ===== LEFT PANEL: CONTROLS =====
        left_panel = self.create_left_panel()
        
        # ===== RIGHT PANEL: DATA & GRAPHS =====
        right_panel = self.create_right_panel()
        
        # Add with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(350)
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.connection_label = QLabel("🔴 Disconnected")
        self.status_bar.addWidget(self.connection_label)
        
    def create_left_panel(self):
        """Create left control panel"""
        layout = QVBoxLayout()
        
        # ===== CONNECTION GROUP =====
        conn_group = QGroupBox("Connection")
        conn_layout = QVBoxLayout()
        
        # Port selection
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.addItems(self.get_available_ports())
        port_layout.addWidget(self.port_combo)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_btn)
        conn_layout.addLayout(port_layout)
        
        # Baudrate
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Baudrate:"))
        self.baud_spin = QSpinBox()
        self.baud_spin.setValue(115200)
        self.baud_spin.setRange(9600, 921600)
        baud_layout.addWidget(self.baud_spin)
        conn_layout.addLayout(baud_layout)
        
        # Connect button
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)
        
        # Status indicator
        self.status_label = QLabel("Status: Not connected")
        conn_layout.addWidget(self.status_label)
        
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # ===== RECORDING GROUP =====
        rec_group = QGroupBox("Recording")
        rec_layout = QVBoxLayout()
        
        # Sample count
        self.sample_label = QLabel("Samples: 0")
        rec_layout.addWidget(self.sample_label)
        
        # Record time
        self.time_label = QLabel("Time: 00:00:00")
        rec_layout.addWidget(self.time_label)
        
        # Record button
        self.record_btn = QPushButton("🔴 Start Recording")
        self.record_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        self.record_btn.clicked.connect(self.toggle_recording)
        self.record_btn.setEnabled(False)
        rec_layout.addWidget(self.record_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        rec_layout.addWidget(self.progress_bar)
        
        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)
        
        # ===== EXPORT GROUP =====
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()
        
        # Export format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV (No Timestamp)", "JSON", "Both"])
        format_layout.addWidget(self.format_combo)
        export_layout.addLayout(format_layout)
        
        # Export location
        loc_layout = QHBoxLayout()
        loc_layout.addWidget(QLabel("Location:"))
        self.export_path = QLineEdit()
        self.export_path.setText(str(Path.home() / "Desktop"))
        loc_btn = QPushButton("📁 Browse")
        loc_btn.clicked.connect(self.browse_export_location)
        loc_layout.addWidget(self.export_path)
        loc_layout.addWidget(loc_btn)
        export_layout.addLayout(loc_layout)
        
        # Export button
        export_btn = QPushButton("💾 Export Data")
        export_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        export_btn.clicked.connect(self.export_data)
        export_layout.addWidget(export_btn)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        # ===== DISPLAY OPTIONS =====
        display_group = QGroupBox("Display")
        display_layout = QVBoxLayout()
        
        self.auto_scale_check = QCheckBox("Auto Scale Graphs")
        self.auto_scale_check.setChecked(True)
        display_layout.addWidget(self.auto_scale_check)
        
        self.show_mag_check = QCheckBox("Show Magnitude")
        self.show_mag_check.setChecked(True)
        display_layout.addWidget(self.show_mag_check)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        layout.addStretch()
        return layout
        
    def create_right_panel(self):
        """Create right panel with graphs and parameters"""
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Tab 1: Live Graphs
        self.live_tab = self.create_live_graphs_tab()
        self.tabs.addTab(self.live_tab, "📈 Live Data")
        
        # Tab 2: Time-Domain Parameters
        self.time_params_table = self.create_parameters_table()
        self.tabs.addTab(self.time_params_table, "⏱️ Time-Domain")
        
        # Tab 3: Frequency-Domain Parameters
        self.freq_params_table = self.create_parameters_table()
        self.tabs.addTab(self.freq_params_table, "📡 Frequency-Domain")
        
        # Tab 4: Correlation Parameters
        self.corr_params_table = self.create_parameters_table()
        self.tabs.addTab(self.corr_params_table, "🔗 Correlation")
        
        # Tab 5: All Parameters
        self.all_params_table = self.create_parameters_table()
        self.tabs.addTab(self.all_params_table, "📊 All Parameters")
        
        layout.addWidget(self.tabs)
        return layout
        
    def create_live_graphs_tab(self):
        """Create live graphs tab with pyqtgraph"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create plot
        self.plot = pg.PlotWidget()
        self.plot.setTitle("Real-Time Sensor Data")
        self.plot.setLabel('left', 'Acceleration (g)')
        self.plot.setLabel('bottom', 'Sample')
        self.plot.addLegend()
        
        # Plot lines
        self.line_s1_x = self.plot.plot(pen='r', name='S1-X')
        self.line_s1_y = self.plot.plot(pen='g', name='S1-Y')
        self.line_s1_z = self.plot.plot(pen='b', name='S1-Z')
        self.line_s2_x = self.plot.plot(pen='c', name='S2-X', style='--')
        self.line_s2_y = self.plot.plot(pen='m', name='S2-Y', style='--')
        self.line_s2_z = self.plot.plot(pen='y', name='S2-Z', style='--')
        
        layout.addWidget(self.plot)
        return widget
        
    def create_parameters_table(self):
        """Create a parameters table"""
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['Parameter', 'Value'])
        table.horizontalHeader().setStretchLastSection(True)
        table.setMaximumHeight(600)
        return table
        
    def setup_styles(self):
        """Setup application styles"""
        style = """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QGroupBox {
            color: #ffffff;
            border: 2px solid #3498db;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }
        QLabel {
            color: #ffffff;
        }
        QPushButton {
            border-radius: 5px;
            padding: 8px;
            font-weight: bold;
        }
        QComboBox, QSpinBox, QLineEdit {
            background-color: #2e2e2e;
            color: #ffffff;
            border: 1px solid #3498db;
            border-radius: 3px;
            padding: 5px;
        }
        QTableWidget {
            background-color: #2e2e2e;
            gridline-color: #3498db;
        }
        QHeaderView::section {
            background-color: #3498db;
            color: #ffffff;
            padding: 5px;
        }
        """
        QApplication.instance().setStyle('Fusion')
        QApplication.instance().setStyleSheet(style)
        
    def get_available_ports(self):
        """Get list of available serial ports"""
        ports = []
        for port, desc, hwid in serial.tools.list_ports.comports():
            ports.append(port)
        return ports if ports else ["No ports found"]
        
    def refresh_ports(self):
        """Refresh available ports"""
        self.port_combo.clear()
        self.port_combo.addItems(self.get_available_ports())
        
    def toggle_connection(self):
        """Toggle Arduino connection"""
        if not self.serial_thread:
            # Connect
            port = self.port_combo.currentText()
            if port == "No ports found":
                QMessageBox.warning(self, "Error", "No serial ports available")
                return
                
            self.serial_thread = SerialDataThread()
            self.serial_thread.set_port(port)
            self.serial_thread.data_received.connect(self.on_data_received)
            self.serial_thread.connection_status.connect(self.on_connection_status)
            self.serial_thread.error_occurred.connect(self.on_serial_error)
            self.serial_thread.start()
            
            self.connect_btn.setText("🔌 Disconnect")
            self.connect_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        else:
            # Disconnect
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.serial_thread = None
            
            self.connect_btn.setText("🔌 Connect")
            self.connect_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
            self.status_label.setText("Status: Disconnected")
            self.connection_label.setText("🔴 Disconnected")
            self.record_btn.setEnabled(False)
            
    def on_connection_status(self, connected):
        """Handle connection status change"""
        if connected:
            self.status_label.setText("Status: ✅ Connected")
            self.connection_label.setText("🟢 Connected")
            self.record_btn.setEnabled(True)
        else:
            self.status_label.setText("Status: ❌ Disconnected")
            self.connection_label.setText("🔴 Disconnected")
            self.record_btn.setEnabled(False)
            
    def on_data_received(self, values):
        """Handle incoming data from Arduino"""
        self.data_buffer.append(values)
        self.param_calculator.add_data(values)
        
        if self.recording:
            self.recorded_data.append(values)
            
    def on_serial_error(self, error):
        """Handle serial errors"""
        QMessageBox.critical(self, "Serial Error", error)
        self.serial_thread = None
        self.connect_btn.setText("🔌 Connect")
        self.connect_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        
    def toggle_recording(self):
        """Toggle data recording"""
        if not self.recording:
            # Start recording
            self.recording = True
            self.recorded_data = []
            self.recorded_params = []
            self.record_btn.setText("⏹️ Stop Recording")
            self.record_btn.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold;")
            self.progress_bar.setValue(0)
        else:
            # Stop recording
            self.recording = False
            self.record_btn.setText("🔴 Start Recording")
            self.record_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
            
            if len(self.recorded_data) > 0:
                QMessageBox.information(
                    self, 
                    "Recording Complete", 
                    f"Recorded {len(self.recorded_data)} samples.\nClick Export to save data."
                )
                
    def update_display(self):
        """Update displays with latest data"""
        # Update graphs
        if len(self.data_buffer) > 0:
            data = np.array(list(self.data_buffer))
            
            if data.shape[1] >= 6:
                x = np.arange(len(data))
                self.line_s1_x.setData(x, data[:, 0])
                self.line_s1_y.setData(x, data[:, 1])
                self.line_s1_z.setData(x, data[:, 2])
                self.line_s2_x.setData(x, data[:, 3])
                self.line_s2_y.setData(x, data[:, 4])
                self.line_s2_z.setData(x, data[:, 5])
                
        # Update parameters
        params = self.param_calculator.compute_parameters()
        self.update_parameter_tables(params)
        
        # Update recording info
        if self.recording:
            sample_count = len(self.recorded_data)
            self.sample_label.setText(f"Samples: {sample_count}")
            
            # Calculate recording time
            time_seconds = sample_count / 50  # Assuming 50Hz
            minutes, seconds = divmod(int(time_seconds), 60)
            hours, minutes = divmod(minutes, 60)
            self.time_label.setText(f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Update progress (assume 1000 samples = 100%)
            progress = min(100, (sample_count / 1000) * 100)
            self.progress_bar.setValue(int(progress))
            
    def update_parameter_tables(self, params):
        """Update all parameter tables"""
        # Time-domain parameters
        time_params = {k: v for k, v in params.items() if any(x in k for x in ['rms', 'peak', 'mean', 'std', 'crest', 'skew', 'kurt'])}
        self.fill_table(self.time_params_table, time_params)
        
        # Frequency-domain parameters
        freq_params = {k: v for k, v in params.items() if any(x in k for x in ['dominant', 'spectral', 'peak']) and 'freq' in k or 'power' in k}
        self.fill_table(self.freq_params_table, freq_params)
        
        # Correlation parameters
        corr_params = {k: v for k, v in params.items() if 'corr' in k}
        self.fill_table(self.corr_params_table, corr_params)
        
        # All parameters
        self.fill_table(self.all_params_table, params)
        
    def fill_table(self, table, params):
        """Fill parameter table"""
        table.setRowCount(len(params))
        
        for row, (key, value) in enumerate(params.items()):
            # Parameter name
            name_item = QTableWidgetItem(key)
            name_item.setForeground(QBrush(QColor(255, 255, 255)))
            table.setItem(row, 0, name_item)
            
            # Parameter value
            val_item = QTableWidgetItem(f"{value:.6f}")
            val_item.setForeground(QBrush(QColor(100, 200, 255)))
            table.setItem(row, 1, val_item)
            
    def browse_export_location(self):
        """Browse for export location"""
        folder = QFileDialog.getExistingDirectory(self, "Select Export Location")
        if folder:
            self.export_path.setText(folder)
            
    def export_data(self):
        """Export recorded data to CSV/JSON"""
        if len(self.recorded_data) == 0:
            QMessageBox.warning(self, "No Data", "No data to export. Record some data first.")
            return
            
        export_format = self.format_combo.currentText()
        export_path = Path(self.export_path.text())
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            if "CSV" in export_format or "Both" in export_format:
                # Export CSV WITHOUT timestamp
                csv_file = export_path / f"structural_health_{timestamp}.csv"
                
                with open(csv_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Write header: S1X, S1Y, S1Z, S2X, S2Y, S2Z
                    writer.writerow(['S1_X', 'S1_Y', 'S1_Z', 'S2_X', 'S2_Y', 'S2_Z'])
                    # Write data rows
                    for data in self.recorded_data:
                        writer.writerow(data[:6])
                        
                QMessageBox.information(self, "Success", f"CSV exported:\n{csv_file}")
                
            if "JSON" in export_format or "Both" in export_format:
                # Export JSON with parameters
                json_file = export_path / f"structural_health_{timestamp}_analysis.json"
                
                params = self.param_calculator.compute_parameters()
                export_data = {
                    "timestamp": datetime.now().isoformat(),
                    "samples": len(self.recorded_data),
                    "parameters": {k: float(v) for k, v in params.items()}
                }
                
                with open(json_file, 'w') as f:
                    json.dump(export_data, f, indent=2)
                    
                QMessageBox.information(self, "Success", f"JSON exported:\n{json_file}")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting data:\n{str(e)}")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Launch application"""
    app = QApplication(sys.argv)
    window = HexagonStructuralHealthUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
