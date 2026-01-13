import React, { useState, useRef } from 'react';
import { Upload, Check, AlertCircle, FileText } from 'lucide-react';

export default function FileUploader({ onFileSelect, disabled, fileId, metadata }) {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setDragActive(e.type === 'dragenter' || e.type === 'dragover');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (!disabled && e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.csv') || file.name.endsWith('.xlsx')) {
        onFileSelect(file);
      }
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`relative border-2 border-dashed rounded p-6 text-center cursor-pointer transition ${
        disabled
          ? 'bg-gray-700 border-gray-600 opacity-50 cursor-not-allowed'
          : dragActive
          ? 'bg-gray-700 border-white'
          : fileId
          ? 'bg-gray-700 border-green-500'
          : 'bg-gray-800 border-gray-700 hover:border-white'
      }`}
    >
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleChange}
        accept=".csv,.xlsx"
        className="hidden"
        disabled={disabled}
      />

      {fileId && metadata ? (
        <div className="flex items-center justify-center gap-3">
          <Check size={24} className="text-green-500" />
          <div className="text-left">
            <p className="font-semibold text-white">{metadata.filename}</p>
            <p className="text-sm text-gray-400">
              {metadata.num_samples} samples · {metadata.num_sensors} sensors · {metadata.duration_sec.toFixed(2)}s
            </p>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center gap-2">
          <Upload size={32} className={disabled ? 'text-gray-500' : 'text-gray-300'} />
          <p className="font-semibold text-white">Drop CSV file here</p>
          <p className="text-sm text-gray-400">or click to select</p>
          <p className="text-xs text-gray-500 mt-2">CSV, XLSX (max 50 MB)</p>
        </div>
      )}
    </div>
  );
}
