import React, { useEffect, useRef } from 'react';

interface GaugePanelProps {
  parameters: any;
}

const GaugePanel: React.FC<GaugePanelProps> = ({ parameters }) => {
  const gaugeRefs = useRef<{
    peak: HTMLCanvasElement | null;
    rms: HTMLCanvasElement | null;
    freq: HTMLCanvasElement | null;
  }>({
    peak: null,
    rms: null,
    freq: null,
  });

  // Fix canvas DPI scaling on mount
  useEffect(() => {
    Object.values(gaugeRefs.current).forEach(canvas => {
      if (canvas) {
        const dpr = window.devicePixelRatio || 1;
        canvas.width = 200 * dpr;
        canvas.height = 200 * dpr;
        canvas.style.width = '200px';
        canvas.style.height = '200px';
        const ctx = canvas.getContext('2d');
        if (ctx) ctx.scale(dpr, dpr);
      }
    });
  }, []);

  const drawGauge = (
    canvas: HTMLCanvasElement | null,
    value: number,
    max: number,
    label: string,
    unit: string,
    color: string
  ) => {
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 10;

    // Clear canvas
    ctx.fillStyle = '#0a0e27';
    ctx.fillRect(0, 0, width, height);

    // Draw background circle
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    ctx.stroke();

    // Draw gauge arc
    const startAngle = Math.PI;
    const endAngle = Math.PI * 2;
    const currentAngle = startAngle + ((endAngle - startAngle) * Math.min(value / max, 1));

    ctx.strokeStyle = color;
    ctx.lineWidth = 8;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius - 4, startAngle, currentAngle);
    ctx.stroke();

    // Draw needle
    const needleLength = radius - 20;
    const needleX = centerX + needleLength * Math.cos(currentAngle);
    const needleY = centerY + needleLength * Math.sin(currentAngle);

    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(needleX, needleY);
    ctx.stroke();

    // Draw center circle
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(centerX, centerY, 6, 0, Math.PI * 2);
    ctx.fill();

    // Draw labels
    ctx.fillStyle = '#a0a0a0';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';

    // Min/Max labels
    ctx.fillText('0', centerX - radius + 10, centerY + 15);
    ctx.fillText(max.toFixed(1), centerX + radius - 10, centerY + 15);

    // Value
    ctx.fillStyle = color;
    ctx.font = 'bold 20px Arial';
    ctx.fillText(`${value.toFixed(2)} ${unit}`, centerX, centerY - 20);

    // Label
    ctx.fillStyle = '#a0a0a0';
    ctx.font = '14px Arial';
    ctx.fillText(label, centerX, height - 10);
  };

  useEffect(() => {
    if (!parameters) return;

    const s1 = parameters.sensor_1 || {};
    const timeDomain = s1.time_domain || {};

    const peak = timeDomain.peak || 0;
    const rms = timeDomain.rms || 0;
    const domFreq = s1.frequency_domain?.dominant_frequency || 0;

    drawGauge(gaugeRefs.current.peak, Math.min(peak, 20), 20, 'Peak Acceleration', 'g', '#ff4757');
    drawGauge(gaugeRefs.current.rms, Math.min(rms, 10), 10, 'RMS Value', 'g', '#2ed573');
    drawGauge(
      gaugeRefs.current.freq,
      Math.min(domFreq, 50),
      50,
      'Dominant Frequency',
      'Hz',
      '#00d9ff'
    );
  }, [parameters]);

  return (
    <div className="gauge-panel">
      <div className="gauge-container">
        <canvas
          ref={(el) => (gaugeRefs.current.peak = el)}
          width={200}
          height={200}
        ></canvas>
      </div>
      <div className="gauge-container">
        <canvas
          ref={(el) => (gaugeRefs.current.rms = el)}
          width={200}
          height={200}
        ></canvas>
      </div>
      <div className="gauge-container">
        <canvas
          ref={(el) => (gaugeRefs.current.freq = el)}
          width={200}
          height={200}
        ></canvas>
      </div>
    </div>
  );
};

export default GaugePanel;
