import React, { useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface FFTSpectrumProps {
  data: any;
}

const FFTSpectrum: React.FC<FFTSpectrumProps> = ({ data }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<ChartJS | null>(null);

  useEffect(() => {
    if (!data || !data.sensor_1 || !data.sensor_1.frequency_domain) return;

    const freqDomain1 = data.sensor_1.frequency_domain;
    const freqDomain2 = data.sensor_2?.frequency_domain;

    const frequencies = Array.from({ length: 50 }, (_, i) => i);
    const magnitudes1 = Array(50).fill(0);
    const magnitudes2 = Array(50).fill(0);

    if (!canvasRef.current) return;

    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }
    
    {
      const ctx = canvasRef.current.getContext('2d');
      if (!ctx) return;

      chartRef.current = new ChartJS(ctx, {
        type: 'bar',
        data: {
          labels: frequencies,
          datasets: [
            {
              label: 'Sensor 1',
              data: magnitudes1,
              backgroundColor: 'rgba(0, 217, 255, 0.7)',
              borderColor: '#00d9ff',
              borderWidth: 1,
            },
            {
              label: 'Sensor 2',
              data: magnitudes2,
              backgroundColor: 'rgba(181, 55, 242, 0.7)',
              borderColor: '#b537f2',
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
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
              title: {
                display: true,
                text: 'Magnitude',
                color: '#a0a0a0',
              },
            },
            x: {
              grid: { color: 'rgba(255, 255, 255, 0.1)' },
              ticks: { color: '#a0a0a0' },
              title: {
                display: true,
                text: 'Frequency (Hz)',
                color: '#a0a0a0',
              },
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

export default FFTSpectrum;
