import React, { useEffect, useRef } from 'react';

interface CorrelationHeatmapProps {
  parameters: any;
}

const CorrelationHeatmap: React.FC<CorrelationHeatmapProps> = ({ parameters }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || !parameters) return;

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    // Create correlation matrix
    const correlationData = [
      [1.0, parameters.correlation?.cross_correlation || 0],
      [parameters.correlation?.cross_correlation || 0, 1.0],
    ];

    const size = 100;
    const padding = 20;

    // Clear canvas
    ctx.fillStyle = '#0a0e27';
    ctx.fillRect(0, 0, canvasRef.current.width, canvasRef.current.height);

    // Draw heatmap
    for (let i = 0; i < correlationData.length; i++) {
      for (let j = 0; j < correlationData[i].length; j++) {
        const value = correlationData[i][j];
        const hue = (1 - value) * 240; // Blue (240) to Red (0)
        const color = `hsl(${hue}, 100%, 50%)`;

        ctx.fillStyle = color;
        ctx.fillRect(padding + j * size, padding + i * size, size, size);

        // Draw value text
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 16px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(
          value.toFixed(2),
          padding + j * size + size / 2,
          padding + i * size + size / 2
        );
      }
    }

    // Draw labels
    const labels = ['Sensor 1', 'Sensor 2'];
    ctx.fillStyle = '#a0a0a0';
    ctx.font = '12px Arial';
    ctx.textAlign = 'right';

    for (let i = 0; i < labels.length; i++) {
      ctx.fillText(labels[i], padding - 5, padding + i * size + size / 2);
      ctx.textAlign = 'center';
      ctx.fillText(labels[i], padding + i * size + size / 2, padding - 5);
    }

    // Draw border
    ctx.strokeStyle = '#a0a0a0';
    ctx.lineWidth = 2;
    ctx.strokeRect(padding, padding, size * 2, size * 2);
  }, [parameters]);

  return (
    <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
      <canvas
        ref={canvasRef}
        width={300}
        height={300}
        style={{
          maxWidth: '100%',
          borderRadius: '8px',
        }}
      ></canvas>
    </div>
  );
};

export default CorrelationHeatmap;
