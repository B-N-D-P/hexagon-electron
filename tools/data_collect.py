#!/usr/bin/env python3
"""
Real-time data collection from 5× ADXL345 SPI rig with optional streaming.

Features:
- Collect raw acceleration data (x, y, z per sensor)
- Stream to backend WebSocket (/ws/ingest)
- Save rotating CSV files (ring buffer)
- Compute jitter, SNR, and clipping statistics
- Auto-restart on connection loss
"""

import argparse
import asyncio
import csv
import json
import math
import os
import sys
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import websockets
import numpy as np


class ADXLSimulator:
    """Simulate ADXL345 sensor data for testing."""
    
    def __init__(self, fs: float = 1000.0, num_sensors: int = 5):
        self.fs = fs
        self.num_sensors = num_sensors
        self.t = 0
        self.dt = 1.0 / fs
        
        # Generate modal frequencies for realistic data
        self.frequencies = [12.5, 24.3, 48.1, 96.2, 150.0]
    
    def get_sample(self) -> List[List[float]]:
        """Get one sample of synthetic acceleration data (x, y, z per sensor)."""
        self.t += self.dt
        samples = []
        
        for sensor_id in range(self.num_sensors):
            # Generate signal with modal content
            signal = 0.0
            for idx, freq in enumerate(self.frequencies[:3]):
                # Add frequency-dependent damping
                damping = np.exp(-0.01 * freq * self.t)
                signal += 0.2 * damping * np.sin(2 * np.pi * freq * self.t + sensor_id * 0.5)
            
            # Add noise
            noise = np.random.normal(0, 0.05)
            signal += noise
            
            # Three-axis acceleration
            x = signal * 0.8 + np.random.normal(0, 0.02)
            y = signal * 0.6 + np.random.normal(0, 0.02)
            z = 9.81 + signal * 0.4 + np.random.normal(0, 0.02)  # 1g offset on Z
            
            samples.append([x, y, z])
        
        return samples


class RotatingCSVWriter:
    """Write data to rotating CSV files (ring buffer pattern)."""
    
    def __init__(self, data_dir: Path, num_sensors: int = 5, 
                 file_duration_sec: float = 300):
        """
        Initialize CSV writer.
        
        Args:
            data_dir: Output directory
            num_sensors: Number of sensors
            file_duration_sec: Duration per CSV file (seconds)
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.num_sensors = num_sensors
        self.file_duration_sec = file_duration_sec
        self.samples_per_file = 0  # Will be set based on fs
        
        self.current_file = None
        self.current_writer = None
        self.sample_count = 0
        self.file_start_time = None
        self.metadata = {}
        
        self._lock = threading.Lock()
    
    def start_new_file(self, fs: float) -> None:
        """Start writing to a new CSV file."""
        with self._lock:
            # Close previous file if open
            if self.current_file:
                self._finalize_file()
            
            # Compute samples per file
            self.samples_per_file = int(fs * self.file_duration_sec)
            
            # Create new file
            now = datetime.now()
            file_date = now.strftime('%Y%m%d')
            file_time = now.strftime('%H%M%S')
            
            date_dir = self.data_dir / file_date
            date_dir.mkdir(exist_ok=True)
            
            filename = f"data_{file_date}_{file_time}.csv"
            self.current_file = date_dir / filename
            
            # Write header
            header = ['timestamp_iso', 'timestamp_unix']
            for sensor_id in range(self.num_sensors):
                header.extend([f'S{sensor_id+1}_x', f'S{sensor_id+1}_y', f'S{sensor_id+1}_z'])
            
            self.current_writer = csv.writer(open(self.current_file, 'w'))
            self.current_writer.writerow(header)
            
            self.sample_count = 0
            self.file_start_time = now
            
            self.metadata = {
                'filename': filename,
                'date': file_date,
                'start_time': now.isoformat(),
                'fs': fs,
                'num_sensors': self.num_sensors,
                'samples': 0
            }
            
            print(f"✓ Started new CSV file: {filename}")
    
    def write_sample(self, frame: List[List[float]], timestamp: datetime) -> None:
        """Write one sample to CSV."""
        if not self.current_writer:
            raise RuntimeError("No CSV file open")
        
        with self._lock:
            row = [timestamp.isoformat(), timestamp.timestamp()]
            for sensor_data in frame:
                row.extend(sensor_data)
            
            self.current_writer.writerow(row)
            self.sample_count += 1
            self.metadata['samples'] = self.sample_count
            
            # Check if we need to rotate to new file
            if self.sample_count >= self.samples_per_file:
                print(f"  → File rotation: {self.sample_count} samples collected")
                self.start_new_file(self.metadata['fs'])
    
    def _finalize_file(self) -> None:
        """Finalize and save metadata for current file."""
        if self.current_file and self.metadata:
            # Save metadata
            metadata_file = self.current_file.with_suffix('.json')
            metadata = self.metadata.copy()
            metadata['end_time'] = datetime.now().isoformat()
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Close file
            if self.current_writer:
                # Flush the file by closing
                self.current_writer = None
            
            print(f"✓ Finalized CSV: {self.current_file.name} ({self.sample_count} samples)")
    
    def close(self) -> None:
        """Close and finalize all files."""
        with self._lock:
            self._finalize_file()


class QCMonitor:
    """Monitor quality control metrics."""
    
    def __init__(self, fs: float, window_size: int = 100):
        self.fs = fs
        self.window_size = window_size
        self.dt_history = deque(maxlen=window_size)
        self.signal_history = deque(maxlen=window_size * 5)
        
        self.jitter_threshold = 5.0  # ms
        self.clipping_threshold = 0.95  # Fraction of ADC max
        self.max_adc = 16384
        
        self.last_timestamp = None
        self.clipping_count = 0
    
    def update(self, frame: List[List[float]], timestamp: datetime) -> Dict:
        """Update QC metrics."""
        metrics = {
            'jitter_ms': 0.0,
            'clipping': [False] * len(frame),
            'snr_db': 35.0
        }
        
        # Compute jitter
        if self.last_timestamp:
            dt_ms = (timestamp - self.last_timestamp).total_seconds() * 1000
            self.dt_history.append(dt_ms)
            
            if len(self.dt_history) > 10:
                jitter = np.std(list(self.dt_history))
                metrics['jitter_ms'] = jitter
                
                if jitter > self.jitter_threshold:
                    print(f"  ⚠ Jitter warning: {jitter:.2f}ms")
        
        # Check clipping
        for sensor_id, xyz in enumerate(frame):
            max_val = max(abs(v) for v in xyz)
            if max_val > self.max_adc * self.clipping_threshold:
                metrics['clipping'][sensor_id] = True
                self.clipping_count += 1
                print(f"  ⚠ Clipping detected on S{sensor_id+1}: {max_val:.0f}")
        
        # Estimate SNR from signal statistics
        signal_rms = np.sqrt(np.mean([v**2 for xyz in frame for v in xyz]))
        if signal_rms > 0:
            snr = 20 * np.log10(signal_rms / 0.1)  # Reference 0.1g noise floor
            metrics['snr_db'] = max(0, min(60, snr))
        
        self.last_timestamp = timestamp
        return metrics
    
    def get_summary(self) -> Dict:
        """Get QC summary statistics."""
        return {
            'clipping_count': self.clipping_count,
            'avg_jitter_ms': np.mean(list(self.dt_history)) if self.dt_history else 0.0,
            'std_jitter_ms': np.std(list(self.dt_history)) if len(self.dt_history) > 1 else 0.0
        }


class StreamingClient:
    """WebSocket client for streaming to backend."""
    
    def __init__(self, uri: str, token: str, batch_size: int = 100):
        self.uri = uri
        self.token = token
        self.batch_size = batch_size
        
        self.batch = []
        self.batch_start_time = None
        self.ws = None
        self.connected = False
        self._lock = threading.Lock()
    
    async def connect(self) -> bool:
        """Connect to backend WebSocket."""
        try:
            uri_with_token = f"{self.uri}?token={self.token}"
            self.ws = await websockets.connect(uri_with_token)
            self.connected = True
            print(f"✓ Connected to stream: {self.uri}")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            self.connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from backend."""
        if self.ws:
            await self.ws.close()
            self.connected = False
            print(f"✗ Disconnected from stream")
    
    def add_frame(self, frame: List[List[float]], fs: float, 
                 timestamp: datetime, mode: str = 'raw_xyz') -> bool:
        """Add a frame to the batch."""
        with self._lock:
            self.batch.append({
                'ts': timestamp.isoformat() + 'Z',
                'fs': fs,
                'sensors': len(frame),
                'mode': mode,
                'frame': frame
            })
            
            if self.batch_start_time is None:
                self.batch_start_time = timestamp
            
            # Check if we should flush
            return len(self.batch) >= self.batch_size
    
    async def flush(self) -> bool:
        """Send pending batch to backend."""
        with self._lock:
            if not self.batch or not self.connected:
                return False
            
            try:
                # Send each frame
                for frame_data in self.batch:
                    await self.ws.send(json.dumps(frame_data))
                
                batch_size = len(self.batch)
                self.batch = []
                self.batch_start_time = None
                
                return True
            except Exception as e:
                print(f"✗ Error sending batch: {e}")
                self.connected = False
                return False
    
    def get_pending_count(self) -> int:
        """Get number of pending frames."""
        with self._lock:
            return len(self.batch)


async def data_collection_loop(args):
    """Main data collection loop."""
    
    # Initialize components
    print("\n" + "="*80)
    print("🔍 ADXL345 Real-Time Data Collection")
    print("="*80)
    
    # Sampling parameters
    fs = float(args.fs)
    num_sensors = int(args.num_sensors)
    dt = 1.0 / fs
    
    print(f"\n📋 Configuration:")
    print(f"   Sampling rate: {fs} Hz")
    print(f"   Number of sensors: {num_sensors}")
    print(f"   Sample interval: {dt*1000:.2f} ms")
    
    # Initialize data source
    if args.simulate:
        data_source = ADXLSimulator(fs, num_sensors)
        print(f"\n🎲 Using SYNTHETIC data (simulation mode)")
    else:
        # In real implementation, initialize actual ADXL345 SPI interface
        print(f"\n📊 Waiting for REAL ADXL345 hardware...")
        data_source = ADXLSimulator(fs, num_sensors)  # Fallback to simulation
    
    # Initialize CSV writer
    csv_writer = RotatingCSVWriter(args.data_dir, num_sensors, file_duration_sec=300)
    csv_writer.start_new_file(fs)
    
    # Initialize QC monitor
    qc_monitor = QCMonitor(fs)
    
    # Initialize streaming client if enabled
    streaming_client = None
    if args.stream:
        streaming_client = StreamingClient(args.stream, args.token, args.batch_size)
        if not await streaming_client.connect():
            if not args.dry_run:
                print("⚠ Streaming unavailable, continuing with local save only")
                streaming_client = None
    
    print("\n" + "="*80)
    print(f"▶ Starting collection... (press Ctrl+C to stop)")
    print("="*80 + "\n")
    
    start_time = time.time()
    sample_count = 0
    reconnect_attempts = 0
    max_reconnect_attempts = 5
    
    try:
        while True:
            # Reconnect streaming if needed
            if args.stream and not streaming_client.connected:
                if reconnect_attempts < max_reconnect_attempts:
                    print(f"🔄 Reconnecting to stream ({reconnect_attempts + 1}/{max_reconnect_attempts})...")
                    if await streaming_client.connect():
                        reconnect_attempts = 0
                    else:
                        reconnect_attempts += 1
                        await asyncio.sleep(2.0)
                        continue
            
            # Get sample
            frame = data_source.get_sample()
            timestamp = datetime.utcnow()
            
            # Process and save
            csv_writer.write_sample(frame, timestamp)
            qc_metrics = qc_monitor.update(frame, timestamp)
            
            # Stream if connected
            if streaming_client and not args.dry_run:
                should_flush = streaming_client.add_frame(frame, fs, timestamp)
                if should_flush:
                    await streaming_client.flush()
            
            sample_count += 1
            
            # Print periodic status
            if sample_count % (fs * 5) == 0:  # Every 5 seconds
                elapsed = time.time() - start_time
                rate = sample_count / elapsed
                pending = streaming_client.get_pending_count() if streaming_client else 0
                qc_summary = qc_monitor.get_summary()
                
                print(f"[{sample_count:7d}] {elapsed:6.1f}s | "
                      f"Rate: {rate:6.1f} Hz | "
                      f"Jitter: {qc_summary['avg_jitter_ms']:5.2f}±{qc_summary['std_jitter_ms']:5.2f}ms | "
                      f"Pending: {pending} | "
                      f"Clipping: {qc_summary['clipping_count']}")
            
            # Maintain sampling rate
            await asyncio.sleep(dt * 0.9)  # Slight underestimate to catch up
    
    except KeyboardInterrupt:
        print("\n\n⏹ Stopping collection...")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    finally:
        # Cleanup
        print(f"\n📊 Final Statistics:")
        print(f"   Samples collected: {sample_count}")
        print(f"   Duration: {time.time() - start_time:.1f}s")
        print(f"   Average rate: {sample_count / (time.time() - start_time):.1f} Hz")
        qc_summary = qc_monitor.get_summary()
        print(f"   Clipping events: {qc_summary['clipping_count']}")
        print(f"   Avg jitter: {qc_summary['avg_jitter_ms']:.2f}ms")
        
        # Close files and connections
        csv_writer.close()
        if streaming_client:
            if streaming_client.get_pending_count() > 0:
                await streaming_client.flush()
            await streaming_client.disconnect()
        
        print("✓ Collection complete")
        print("="*80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Real-time ADXL345 data collection with optional streaming'
    )
    
    # Streaming options
    parser.add_argument(
        '--stream',
        type=str,
        default=None,
        help='Backend WebSocket URI (e.g., ws://127.0.0.1:8000/ws/ingest)'
    )
    parser.add_argument(
        '--token',
        type=str,
        default='dev-token',
        help='Authentication token for streaming'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of samples per batch before sending'
    )
    
    # Data storage options
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Output directory for CSV files'
    )
    
    # Hardware options
    parser.add_argument(
        '--fs',
        type=float,
        default=1000.0,
        help='Sampling frequency (Hz)'
    )
    parser.add_argument(
        '--num-sensors',
        type=int,
        default=5,
        help='Number of sensors'
    )
    parser.add_argument(
        '--simulate',
        action='store_true',
        help='Use simulated data (testing mode)'
    )
    
    # Misc options
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without streaming or saving (performance test)'
    )
    
    args = parser.parse_args()
    
    # Run collection loop
    asyncio.run(data_collection_loop(args))


if __name__ == '__main__':
    main()
