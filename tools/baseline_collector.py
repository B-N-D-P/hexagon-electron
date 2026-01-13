#!/usr/bin/env python3
"""
Baseline data collection for ML model training.

Collects healthy structure vibration data for 3 days to create a baseline
that represents "normal" structural behavior.

Usage:
    python3 baseline_collector.py --stream ws://127.0.0.1:8000/ws/ingest --duration 3d
"""

import argparse
import asyncio
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import json
import numpy as np

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "services"))

from data_collect import ADXLSimulator, RotatingCSVWriter, QCMonitor, StreamingClient


class BaselineCollectionConfig:
    """Configuration for baseline collection."""
    
    def __init__(self, duration_str: str, output_dir: Path):
        """
        Parse duration string.
        
        Args:
            duration_str: Duration like "3d", "24h", "3600s"
            output_dir: Directory for baseline data
        """
        # Parse duration
        if duration_str.endswith('d'):
            self.duration_sec = int(duration_str[:-1]) * 86400
        elif duration_str.endswith('h'):
            self.duration_sec = int(duration_str[:-1]) * 3600
        elif duration_str.endswith('s'):
            self.duration_sec = int(duration_str[:-1])
        else:
            self.duration_sec = int(duration_str)
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_duration_formatted(self) -> str:
        """Get formatted duration."""
        hours = self.duration_sec / 3600
        if hours >= 24:
            return f"{hours / 24:.1f} days"
        return f"{hours:.1f} hours"


async def baseline_collection_loop(args):
    """Main baseline collection loop."""
    
    print("\n" + "="*80)
    print("📊 BASELINE DATA COLLECTION FOR ML TRAINING")
    print("="*80)
    
    config = BaselineCollectionConfig(args.duration, args.output_dir)
    
    print(f"\n📋 Configuration:")
    print(f"   Sampling rate: {args.fs} Hz")
    print(f"   Number of sensors: {args.num_sensors}")
    print(f"   Collection duration: {config.get_duration_formatted()}")
    print(f"   Output directory: {config.output_dir}")
    
    # Initialize components
    data_source = ADXLSimulator(args.fs, args.num_sensors)
    
    # Use a separate baseline CSV writer
    baseline_dir = config.output_dir / "baseline"
    baseline_dir.mkdir(exist_ok=True)
    
    csv_writer = RotatingCSVWriter(baseline_dir, args.num_sensors, 
                                   file_duration_sec=3600)  # Hourly rotation
    csv_writer.start_new_file(args.fs)
    
    qc_monitor = QCMonitor(args.fs)
    
    # Streaming if enabled
    streaming_client = None
    if args.stream and not args.dry_run:
        streaming_client = StreamingClient(args.stream, args.token)
        if not await streaming_client.connect():
            print("⚠ Streaming unavailable, continuing with local collection only")
            streaming_client = None
    
    print("\n" + "="*80)
    print(f"▶ Starting baseline collection... (press Ctrl+C to stop)")
    print("="*80 + "\n")
    
    start_time = time.time()
    end_time = start_time + config.duration_sec
    sample_count = 0
    dt = 1.0 / args.fs
    
    # Metadata for this collection session
    session_metadata = {
        'start_time': datetime.utcnow().isoformat(),
        'structure': args.structure_name,
        'sampling_rate': args.fs,
        'num_sensors': args.num_sensors,
        'planned_duration_sec': config.duration_sec,
        'files': []
    }
    
    try:
        while time.time() < end_time:
            # Get sample
            frame = data_source.get_sample()
            timestamp = datetime.utcnow()
            
            # Save to CSV
            csv_writer.write_sample(frame, timestamp)
            qc_monitor.update(frame, timestamp)
            
            # Stream if connected
            if streaming_client:
                should_flush = streaming_client.add_frame(frame, args.fs, timestamp)
                if should_flush:
                    await streaming_client.flush()
            
            sample_count += 1
            
            # Print status every 60 seconds
            elapsed = time.time() - start_time
            if sample_count % (args.fs * 60) == 0:
                remaining = config.duration_sec - elapsed
                progress = 100 * elapsed / config.duration_sec
                rate = sample_count / elapsed
                qc_summary = qc_monitor.get_summary()
                
                print(f"[{progress:5.1f}%] {elapsed:7.0f}s elapsed | "
                      f"Rate: {rate:6.1f} Hz | "
                      f"Remaining: {remaining:7.0f}s | "
                      f"Jitter: {qc_summary['avg_jitter_ms']:5.2f}ms | "
                      f"Clipping: {qc_summary['clipping_count']}")
            
            # Maintain sampling rate
            await asyncio.sleep(dt * 0.9)
    
    except KeyboardInterrupt:
        print("\n\n⏹ Collection interrupted by user")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    finally:
        # Final statistics
        elapsed = time.time() - start_time
        actual_rate = sample_count / elapsed if elapsed > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"✓ BASELINE COLLECTION COMPLETE")
        print(f"{'='*80}")
        print(f"\n📊 Statistics:")
        print(f"   Total samples: {sample_count}")
        print(f"   Actual duration: {elapsed:.1f}s ({elapsed/3600:.2f}h)")
        print(f"   Actual rate: {actual_rate:.1f} Hz")
        print(f"   Expected rate: {args.fs} Hz")
        
        qc_summary = qc_monitor.get_summary()
        print(f"   Avg jitter: {qc_summary['avg_jitter_ms']:.2f}ms")
        print(f"   Clipping events: {qc_summary['clipping_count']}")
        
        # Close files and connections
        csv_writer.close()
        
        if streaming_client:
            if streaming_client.get_pending_count() > 0:
                await streaming_client.flush()
            await streaming_client.disconnect()
        
        # Save session metadata
        session_metadata['end_time'] = datetime.utcnow().isoformat()
        session_metadata['actual_duration_sec'] = elapsed
        session_metadata['actual_rate'] = actual_rate
        session_metadata['total_samples'] = sample_count
        session_metadata['qc_summary'] = qc_summary
        
        metadata_file = baseline_dir / 'collection_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(session_metadata, f, indent=2)
        
        print(f"\n📁 Output:")
        print(f"   CSV files: {baseline_dir}")
        print(f"   Metadata: {metadata_file}")
        
        # Find CSV files
        csv_files = list(baseline_dir.glob("data_*.csv"))
        print(f"   CSV files created: {len(csv_files)}")
        
        print(f"\n✓ Ready for ML training!")
        print(f"   Next: python3 tools/train_ml_models.py --baseline-dir {baseline_dir}")
        print(f"{'='*80}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Collect baseline data for ML model training'
    )
    
    # Duration
    parser.add_argument(
        '--duration',
        type=str,
        default='3d',
        help='Collection duration (e.g., "3d", "24h", "3600s", default: 3d)'
    )
    
    # Output
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/baseline',
        help='Output directory for baseline data'
    )
    
    # Structure info
    parser.add_argument(
        '--structure-name',
        type=str,
        default='Iron Structure (3-Story)',
        help='Name of the structure being monitored'
    )
    
    # Streaming
    parser.add_argument(
        '--stream',
        type=str,
        default=None,
        help='Backend WebSocket URI for streaming'
    )
    parser.add_argument(
        '--token',
        type=str,
        default='dev-token',
        help='Authentication token'
    )
    
    # Hardware
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
    
    # Misc
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without saving'
    )
    
    args = parser.parse_args()
    
    # Run collection
    asyncio.run(baseline_collection_loop(args))


if __name__ == '__main__':
    main()
