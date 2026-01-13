import React from 'react';
import { useParams } from 'react-router-dom';

export default function Analysis() {
  const { analysisId } = useParams();

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-4xl font-bold text-white mb-8">Detailed Analysis</h1>
      <div className="bg-slate-800 rounded-lg p-8 border border-slate-700">
        <p className="text-gray-300">Detailed analysis view for {analysisId}</p>
        <p className="text-gray-400 text-sm mt-2">Modal parameters, FFT spectra, and mode shapes will be displayed here.</p>
      </div>
    </div>
  );
}
