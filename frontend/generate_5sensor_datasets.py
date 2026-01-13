#!/usr/bin/env python3
import csv
import math
import random

def create_3axis_dataset(filename, include_damage=False):
    """Generate 3-axis data with 5 sensors (12 columns + timestamp)"""
    
    headers = ['timestamp', 
               'sensor1_x', 'sensor1_y', 'sensor1_z',
               'sensor2_x', 'sensor2_y', 'sensor2_z',
               'sensor3_x', 'sensor3_y', 'sensor3_z',
               'sensor4_x', 'sensor4_y', 'sensor4_z',
               'sensor5_x', 'sensor5_y', 'sensor5_z']
    
    # Write CSV manually to guarantee Unix newlines and full length
    lines = []
    lines.append(','.join(headers))

    total_samples = 5120
    for t in range(total_samples):
        timestamp = t
        freq1 = 0.02
        freq2 = 0.03
        noise_scale = 0.05
        row = [timestamp]
        for sensor in range(5):
            phase_offset = sensor * 2 * math.pi / 5
            base_x = 0.3 * math.sin(2 * math.pi * freq1 * t + phase_offset)
            base_y = 0.25 * math.cos(2 * math.pi * freq2 * t + phase_offset)
            base_z = 9.81 + 0.15 * math.sin(2 * math.pi * freq1 * t)
            if include_damage and t > 300:
                damage_factor = (t - 300) / 212.0
                damage_x = damage_factor * 0.5 * math.sin(2 * math.pi * 0.1 * t)
                damage_y = damage_factor * 0.4 * math.cos(2 * math.pi * 0.12 * t)
                damage_z = damage_factor * 0.3 * math.sin(2 * math.pi * 0.08 * t)
                base_x += damage_x
                base_y += damage_y
                base_z += damage_z
            noise_x = random.gauss(0, noise_scale)
            noise_y = random.gauss(0, noise_scale)
            noise_z = random.gauss(0, noise_scale)
            row.extend([
                round(base_x + noise_x, 4),
                round(base_y + noise_y, 4),
                round(base_z + noise_z, 4)
            ])
        lines.append(','.join(str(x) for x in row))

    with open(filename, 'w', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')

    # simple verification
    try:
        with open(filename, 'r') as _f:
            _line_count = sum(1 for _ in _f) - 1
    except Exception:
        _line_count = -1
    print(f"Created {filename} with {_line_count} samples and 5 sensors")

if __name__ == "__main__":
    # Create dataset 1: Normal 3-axis data
    create_3axis_dataset("test_data_3axis_5sensors.csv", include_damage=False)
    
    # Create dataset 2: 3-axis data with damage patterns
    create_3axis_dataset("test_data_with_damage_5sensors.csv", include_damage=True)
