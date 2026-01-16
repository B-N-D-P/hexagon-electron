import React, { useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface LiveWaveformProps {
  data: any;
}

const LiveWaveform: React.FC<LiveWaveformProps> = ({ data }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<ChartJS | null>(null);
  const dataRef = useRef<any>([]);

  useEffect(() => {
    if (!data || !data.sensor_1 || !data.sensor_1.axes) return;

    const axes = data.sensor_1.axes;
    const xData = axes.x || [];
    const yData = axes.y || [];
    const zData = axes.z || [];

    // Keep only last 500 samples for visualization
    const maxSamples = 500;
    const startIdx = Math.max(0, xData.length - maxSamples);
    const displayX = xData.slice(startIdx);
    const displayY = yData.slice(startIdx);
    const displayZ = zData.slice(startIdx);
    const timeLabels = Array.from({ length: displayX.length }, (_, i) => i);

    if (!canvasRef.current) return;

    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }
    
    {
      const ctx = canvasRef.current.getContext('2d');
      if (!ctx) return;

      chartRef.current = new ChartJS(ctx, {
        type: 'line',
        data: {
          labels: timeLabels,
          datasets: [
            {
              label: 'X-Axis',
              data: displayX,
              borderColor: '#ff4757',
              backgroundColor: 'rgba(255, 71, 87, 0.1)',
              tension: 0.1,
              pointRadius: 0,
              borderWidth: 2,
            },
            {
              label: 'Y-Axis',
              data: displayY,
              borderColor: '#2ed573',
              backgroundColor: 'rgba(46, 213, 115, 0.1)',
              tension: 0.1,
              pointRadius: 0,
              borderWidth: 2,
            },
            {
              label: 'Z-Axis',
              data: displayZ,
              borderColor: '#00d9ff',
              backgroundColor: 'rgba(0, 217, 255, 0.1)',
              tension: 0.1,
              pointRadius: 0,
              borderWidth: 2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'top',
              labels: {
                color: '#a0a0a0',
                font: { size: 12 },
              },
            },
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: { color: 'rgba(255, 255, 255, 0.1)' },
              ticks: { color: '#a0a0a0' },
            },
            x: {
              grid: { color: 'rgba(255, 255, 255, 0.1)' },
              ticks: { color: '#a0a0a0' },
            },
          },
        },
      });
    }
  }, [data]);

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <canvas ref={canvasRef}></canvas>
    </div>
  );
};

export default LiveWaveform;
