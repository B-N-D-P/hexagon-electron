import React from 'react';

function badge(sev) {
  if (sev >= 70) return 'bg-red-900 border-red-600 text-red-200';
  if (sev >= 40) return 'bg-yellow-900 border-yellow-600 text-yellow-200';
  return 'bg-green-900 border-green-600 text-green-200';
}

export default function MethodCard({ title, result }) {
  const severity = result?.severity_percentage ?? result?.severity ?? 0;
  const confidence = result?.confidence ?? 0;
  const damagedSensors = result?.damaged_sensors ?? [];

  return (
    <div className={`border rounded-lg p-4 ${badge(severity)}`}>
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-bold text-white">{title}</h4>
        <span className="text-xs px-2 py-1 rounded bg-black/20">
          Sev: {Number(severity).toFixed(1)}%
        </span>
      </div>

      <div className="text-sm text-gray-200 space-y-1">
        <div>Confidence: {(confidence * 100).toFixed(0)}%</div>
        <div>Damaged sensors: {damagedSensors.length ? damagedSensors.join(', ') : 'None'}</div>
      </div>
    </div>
  );
}
