#!/usr/bin/env python3
import os, math, random, csv
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / 'test_datasets'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Utility to write 3-axis CSV: timestamp + 5 sensors x (x,y,z)
def write_3axis_csv(path: Path, total_samples=4096, fs=1000.0, damage=None):
    headers = ['timestamp',
               'sensor1_x','sensor1_y','sensor1_z',
               'sensor2_x','sensor2_y','sensor2_z',
               'sensor3_x','sensor3_y','sensor3_z',
               'sensor4_x','sensor4_y','sensor4_z',
               'sensor5_x','sensor5_y','sensor5_z']
    with open(path, 'w', newline='\n') as f:
        w = csv.writer(f)
        w.writerow(headers)
        for t in range(total_samples):
            timestamp = t
            freq1 = 2.0   # Hz
            freq2 = 3.0   # Hz
            noise_scale = 0.02
            row = [timestamp]
            for s in range(5):
                ph = s * 2*math.pi/5
                bx = 0.30 * math.sin(2*math.pi*freq1*t/fs + ph)
                by = 0.25 * math.cos(2*math.pi*freq2*t/fs + ph)
                bz = 9.81 + 0.15 * math.sin(2*math.pi*freq1*t/fs)
                # apply scenario-specific damage function
                if damage is not None:
                    dx, dy, dz = damage(t, s, fs)
                    bx += dx; by += dy; bz += dz
                nx = random.gauss(0, noise_scale)
                ny = random.gauss(0, noise_scale)
                nz = random.gauss(0, noise_scale)
                row.extend([round(bx+nx, 5), round(by+ny, 5), round(bz+nz, 5)])
            w.writerow(row)

# Damage functions
# 1) global stiffness loss: add low-freq drift + reduce amplitude
def damage_global(t, s, fs):
    # amplitude reduction applied via baseline function will reflect in spectral content
    hf = 12.0
    return (0.03*math.sin(2*math.pi*hf*t/fs),
            -0.02*math.cos(2*math.pi*(hf+1.2)*t/fs),
            0.02*math.sin(2*math.pi*(hf-0.8)*t/fs))

# 2) localized sensor anomaly at sensor k (e.g., 2 or 4)
def make_localized_damage(sensor_idx=2):
    def f(t, s, fs):
        if s != sensor_idx:
            return (0.0, 0.0, 0.0)
        # bursty anomaly after 1s
        if t < int(1.0*fs):
            return (0.0, 0.0, 0.0)
        hf = 18.0
        amp = 0.25
        return (amp*math.sin(2*math.pi*hf*t/fs), 0.2*math.cos(2*math.pi*(hf+0.7)*t/fs), 0.15*math.sin(2*math.pi*(hf-0.9)*t/fs))
    return f

# 3) repaired closer to baseline
def make_repair_from_damage(damage_fn, factor=0.3):
    def f(t, s, fs):
        dx,dy,dz = damage_fn(t,s,fs)
        return (factor*dx, factor*dy, factor*dz)
    return f

if __name__ == '__main__':
    # Repair quality scenario (original, damaged, repaired)
    original = OUT_DIR / 'rq_original_5s3axis.csv'
    damaged  = OUT_DIR / 'rq_damaged_5s3axis.csv'
    repaired = OUT_DIR / 'rq_repaired_5s3axis.csv'

    # baseline (no damage)
    write_3axis_csv(original, total_samples=4096)
    # damaged (global + localized at sensor 2)
    def rq_damage(t,s,fs):
        g = damage_global(t,s,fs)
        l = make_localized_damage(sensor_idx=2)(t,s,fs)
        return (g[0]+l[0], g[1]+l[1], g[2]+l[2])
    write_3axis_csv(damaged, total_samples=4096, damage=rq_damage)
    # repaired (partial recovery)
    write_3axis_csv(repaired, total_samples=4096, damage=make_repair_from_damage(rq_damage, factor=0.3))

    # Comparative scenario (damaged -> repaired)
    comp_damaged  = OUT_DIR / 'comp_damaged_5s3axis.csv'
    comp_repaired = OUT_DIR / 'comp_repaired_5s3axis.csv'
    write_3axis_csv(comp_damaged, total_samples=4096, damage=rq_damage)
    write_3axis_csv(comp_repaired, total_samples=4096, damage=make_repair_from_damage(rq_damage, factor=0.4))

    # Localization scenario (baseline vs current with localized damage at sensor 4)
    loc_baseline = OUT_DIR / 'loc_baseline_5s3axis.csv'
    loc_current  = OUT_DIR / 'loc_current_5s3axis.csv'
    write_3axis_csv(loc_baseline, total_samples=4096)
    write_3axis_csv(loc_current,  total_samples=4096, damage=make_localized_damage(sensor_idx=4))

    print('\nGenerated test datasets in:', OUT_DIR)
    for p in [original, damaged, repaired, comp_damaged, comp_repaired, loc_baseline, loc_current]:
        print(' -', p)
