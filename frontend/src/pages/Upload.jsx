import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { Upload as UploadIcon, FileUp, Play, Info } from 'lucide-react';
import FileUploader from '../components/FileUploader';
import api from '../services/api';

export default function Upload() {
  const navigate = useNavigate();
  const [files, setFiles] = useState({
    original: null,
    damaged: null,
    repaired: null,
  });
  const [fileMetadata, setFileMetadata] = useState({});
  const [analysisType, setAnalysisType] = useState('repair_quality');
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [fs, setFs] = useState(1000);
  const [maxModes, setMaxModes] = useState(5);

  const handleFileSelect = async (fileType, file) => {
    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/v1/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setFiles(prev => ({
        ...prev,
        [fileType]: response.data.file_id,
      }));

      setFileMetadata(prev => ({
        ...prev,
        [fileType]: response.data,
      }));

      toast.success(`${fileType.charAt(0).toUpperCase() + fileType.slice(1)} file uploaded successfully!`);
    } catch (error) {
      const errorMsg = error.message || error.originalError?.response?.data?.detail || 'Unknown error';
      toast.error(`Failed to upload ${fileType} file: ${errorMsg}`);
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleAnalysisStart = async (e) => {
    e.preventDefault();

    // Validate inputs
    if (!files.damaged) {
      toast.error('Damaged file is required');
      return;
    }

    if (analysisType === 'repair_quality') {
      if (!files.original || !files.repaired) {
        toast.error('Original and Repaired files are required for repair quality analysis');
        return;
      }
    }

    if (analysisType === 'localization') {
      if (!files.original || !files.damaged) {
        toast.error('Baseline (healthy) and Current (damaged) files are required for 2-sensor localization');
        return;
      }
    }


    try {
      setAnalyzing(true);
      setAnalysisProgress(0);

      const analysisRequest = {
        original_file_id: files.original,
        damaged_file_id: files.damaged,
        repaired_file_id: files.repaired,
        analysis_type: analysisType,
        fs: parseFloat(fs),
        max_modes: parseInt(maxModes),
        min_freq: 1.0,
        max_freq: 450.0,
      };

      // Start analysis
      const startResponse = await api.post('/api/v1/analyze', analysisRequest);
      const analysisId = startResponse.data.analysis_id;

      toast.info('Analysis started... This may take a moment.');

      // Poll for results
      let pollAttempts = 0;
      const maxPollAttempts = 600; // 10 minutes with 1s interval
      
      const pollInterval = setInterval(async () => {
        pollAttempts++;
        
        try {
          const resultResponse = await api.get(`/api/v1/results/${analysisId}`);

          if (resultResponse.data.status === 'processing') {
            setAnalysisProgress(resultResponse.data.progress || 0);
          } else if (resultResponse.data.status === 'completed') {
            clearInterval(pollInterval);
            setAnalyzing(false);
            toast.success('Analysis completed!');
            navigate(`/dashboard/${analysisId}`);
          } else if (resultResponse.data.status === 'failed') {
            clearInterval(pollInterval);
            setAnalyzing(false);
            toast.error(`Analysis failed: ${resultResponse.data.error || 'Unknown error'}`);
          }
        } catch (error) {
          console.error('Poll error:', error);
          // Continue polling on error, as the analysis might still be running
        }
        
        // Timeout after max attempts
        if (pollAttempts >= maxPollAttempts) {
          clearInterval(pollInterval);
          setAnalyzing(false);
          toast.error('Analysis timeout. Please check results later.');
        }
      }, 1000);
    } catch (error) {
      const errorMsg = error.message || error.originalError?.response?.data?.detail || 'Unknown error';
      toast.error(`Failed to start analysis: ${errorMsg}`);
      setAnalyzing(false);
      console.error('Analysis error:', error);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-white mb-4">
          Structural Repair Analysis
        </h1>
        <p className="text-gray-400">
          Upload accelerometer data and run analysis
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        {/* Upload Section */}
        <div className="lg:col-span-2 space-y-6">
          {/* Analysis Type Selection */}
          <div className="bg-gray-800 rounded p-6 border border-gray-700">
            <h2 className="text-white font-semibold mb-4">Analysis Type</h2>
            <div className="space-y-2">
              <label className="flex items-center p-3 rounded border border-gray-700 cursor-pointer hover:bg-gray-700" 
                     style={{ borderColor: analysisType === 'repair_quality' ? '#ffffff' : undefined, backgroundColor: analysisType === 'repair_quality' ? '#374151' : undefined }}>
                <input
                  type="radio"
                  name="analysisType"
                  value="repair_quality"
                  checked={analysisType === 'repair_quality'}
                  onChange={(e) => setAnalysisType(e.target.value)}
                  className="w-4 h-4"
                />
                <div className="ml-3">
                  <p className="text-white font-medium text-sm">Repair Quality</p>
                  <p className="text-xs text-gray-400">Original → Damaged → Repaired</p>
                </div>
              </label>

              <label className="flex items-center p-3 rounded border border-gray-700 cursor-pointer hover:bg-gray-700" 
                     style={{ borderColor: analysisType === 'comparative' ? '#ffffff' : undefined, backgroundColor: analysisType === 'comparative' ? '#374151' : undefined }}>
                <input
                  type="radio"
                  name="analysisType"
                  value="comparative"
                  checked={analysisType === 'comparative'}
                  onChange={(e) => setAnalysisType(e.target.value)}
                  className="w-4 h-4"
                />
                <div className="ml-3">
                  <p className="text-white font-medium text-sm">Comparative</p>
                  <p className="text-xs text-gray-400">Damaged vs Repaired</p>
                </div>
              </label>

              <label className="flex items-center p-3 rounded border border-gray-700 cursor-pointer hover:bg-gray-700" 
                     style={{ borderColor: analysisType === 'localization' ? '#ffffff' : undefined, backgroundColor: analysisType === 'localization' ? '#374151' : undefined }}>
                <input
                  type="radio"
                  name="analysisType"
                  value="localization"
                  checked={analysisType === 'localization'}
                  onChange={(e) => setAnalysisType(e.target.value)}
                  className="w-4 h-4"
                />
                <div className="ml-3">
                  <p className="text-white font-medium text-sm">Localization (2-Sensor)</p>
                  <p className="text-xs text-gray-400">Locate damage between sensors</p>
                </div>
              </label>
            </div>
          </div>

          {/* File Upload Section */}
          <div className="space-y-4">
            {analysisType === 'repair_quality' && (
              <div>
                <label className="block text-sm font-semibold text-white mb-2">
                  Original (Baseline) Structure *
                </label>
                <FileUploader 
                  onFileSelect={(file) => handleFileSelect('original', file)}
                  disabled={uploading}
                  fileId={files.original}
                  metadata={fileMetadata.original}
                />
              </div>
            )}

            {analysisType === 'localization' && (
              <div>
                <label className="block text-sm font-semibold text-white mb-2">
                  Baseline (Healthy) Structure *
                </label>
                <FileUploader 
                  onFileSelect={(file) => handleFileSelect('original', file)}
                  disabled={uploading}
                  fileId={files.original}
                  metadata={fileMetadata.original}
                />
              </div>
            )}


            <div>
              <label className="block text-sm font-semibold text-white mb-2">
                {analysisType === 'localization' ? 'Current Structure (to localize damage) *' : analysisType === 'comparative' ? 'Damaged Structure *' : 'Damaged Structure *'}
              </label>
              <FileUploader 
                onFileSelect={(file) => handleFileSelect('damaged', file)}
                disabled={uploading}
                fileId={files.damaged}
                metadata={fileMetadata.damaged}
              />
            </div>

            {(analysisType === 'repair_quality' || analysisType === 'comparative') && (
              <div>
                <label className="block text-sm font-semibold text-white mb-2">Repaired Structure *</label>
                <FileUploader 
                  onFileSelect={(file) => handleFileSelect('repaired', file)}
                  disabled={uploading}
                  fileId={files.repaired}
                  metadata={fileMetadata.repaired}
                />
              </div>
            )}
          </div>
        </div>

        {/* Parameters Sidebar */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 h-fit">
          <h3 className="text-xl font-bold text-white mb-4">Analysis Parameters</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Sampling Rate (Hz)
              </label>
              <input
                type="number"
                value={fs}
                onChange={(e) => setFs(e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Max Modes to Extract
              </label>
              <input
                type="number"
                value={maxModes}
                onChange={(e) => setMaxModes(e.target.value)}
                min="1"
                max="10"
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div className="bg-blue-900 bg-opacity-30 border border-blue-700 rounded p-3 text-sm text-blue-200">
              <p className="flex items-start gap-2">
                <Info size={16} className="mt-0.5 flex-shrink-0" />
                <span>Adjust parameters based on your data characteristics and required precision</span>
              </p>
            </div>

            <button
              onClick={handleAnalysisStart}
              disabled={analyzing || uploading || !files.damaged}
              className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play size={20} />
              {analyzing ? 'Analyzing...' : 'Run Analysis'}
            </button>

            {analyzing && (
              <div className="space-y-2">
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${analysisProgress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-400 text-center">{analysisProgress}% Complete</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Info Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h4 className="font-bold text-white mb-2 flex items-center gap-2">
            <FileUp size={20} className="text-green-400" />
            Supported Formats
          </h4>
          <ul className="text-sm text-gray-400 space-y-1">
            <li>✓ CSV files (comma-separated)</li>
            <li>✓ Single-axis (4-5 columns)</li>
            <li>✓ 3-axis 4 sensors (12 columns)</li>
            <li>✓ 3-axis 5 sensors (15 columns)</li>
            <li>✓ Max 50 MB per file</li>
          </ul>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h4 className="font-bold text-white mb-2 flex items-center gap-2">
            <UploadIcon size={20} className="text-blue-400" />
            Data Requirements
          </h4>
          <ul className="text-sm text-gray-400 space-y-1">
            <li>✓ Min 512 samples</li>
            <li>✓ ≤ 1 Hz frequency resolution</li>
            <li>✓ Consistent sampling rate</li>
            <li>✓ No NaN or infinite values</li>
          </ul>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h4 className="font-bold text-white mb-2 flex items-center gap-2">
            <UploadIcon size={20} className="text-purple-400" />
            Analysis Output
          </h4>
          <ul className="text-sm text-gray-400 space-y-1">
            <li>✓ Modal parameters</li>
            <li>✓ Quality assessment</li>
            <li>✓ 2-sensor damage localization</li>
            <li>✓ Professional reports</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
