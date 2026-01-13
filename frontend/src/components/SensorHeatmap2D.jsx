import React from 'react';

function scoreColor(score) {
  // score in [0,1]
  const s = Math.max(0, Math.min(1, score || 0));
  // blue (healthy) -> yellow -> red
  const r = Math.round(255 * s);
  const g = Math.round(200 * (1 - Math.abs(s - 0.5) * 2));
  const b = Math.round(255 * (1 - s));
  return `rgb(${r},${g},${b})`;
}

export default function SensorHeatmap2D({ sensorLayout, sensorScores }) {
  const sensors = sensorLayout?.sensors || [];
  if (!sensors.length) {
    return (
      <div className="text-gray-300 text-sm">
        No sensor layout available.
      </div>
    );
  }

  // Find bounds in x,y for scaling
  const xs = sensors.map(s => s.absolute_coordinate?.[0] ?? 0);
  const ys = sensors.map(s => s.absolute_coordinate?.[1] ?? 0);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);

  const w = 700;
  const h = 350;
  const pad = 40;

  const sx = (x) => {
    if (maxX - minX < 1e-9) return w / 2;
    return pad + ((x - minX) / (maxX - minX)) * (w - 2 * pad);
  };
  const sy = (y) => {
    if (maxY - minY < 1e-9) return h / 2;
    // invert y so bigger y is up
    return h - (pad + ((y - minY) / (maxY - minY)) * (h - 2 * pad));
  };

  return (
    <div className="w-full overflow-x-auto">
      <svg width={w} height={h} className="bg-slate-900 rounded-lg border border-slate-700">
        {/* axes */}
        <line x1={pad} y1={h-pad} x2={w-pad} y2={h-pad} stroke="#475569" />
        <line x1={pad} y1={pad} x2={pad} y2={h-pad} stroke="#475569" />
        <text x={pad} y={pad-10} fill="#94a3b8" fontSize="12">Y</text>
        <text x={w-pad+10} y={h-pad+4} fill="#94a3b8" fontSize="12">X</text>

        {sensors.map((s) => {
          const sid = s.sensor_id;
          const coord = s.absolute_coordinate || [0,0,0];
          const x = sx(coord[0]);
          const y = sy(coord[1]);
          const score = sensorScores?.[sid] ?? 0;
          const color = scoreColor(score);

          return (
            <g key={sid}>
              <circle cx={x} cy={y} r={12} fill={color} stroke="#0f172a" strokeWidth={2} />
              <text x={x} y={y+4} textAnchor="middle" fill="#0f172a" fontSize="11" fontWeight="700">
                {sid}
              </text>
              <text x={x+16} y={y-10} fill="#e2e8f0" fontSize="11">
                {`S${sid}: ${(score*100).toFixed(0)}%`}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="text-xs text-gray-400 mt-2">
        Color scale: blue = healthy, red = high damage probability (from Phase-2 consensus).
      </div>
    </div>
  );
}
