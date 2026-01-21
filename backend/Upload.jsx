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
  const [fs, setFs] = useState(100); // IAI Hardware: 100 samples per second
  const [maxModes, setMaxModes] = useState(5);
  
  // ML456 baseline prediction state
  const [ml456Available, setMl456Available] = useState(false);
  const [predictingBaseline, setPredictingBaseline] = useState(false);
  const [mlPrediction, setMlPrediction] = useState(null);
  
  // Check ML456 availability on mount
  React.useEffect(() => {
    const checkML456 = async () => {
      try {
        const response = await api.get('/health');
        setMl456Available(response.data.ml456_available === true);
      } catch (error) {
        setMl456Available(false);
      }
    };
    checkML456();
  }, []);
  
  // Predict baseline using ML456
  const predictBaseline = async () => {
    if (!files.damaged) {
      toast.error('Please upload damaged file first');
      return;
    }
    
    try {
      setPredictingBaseline(true);
      toast.info('🔮 Predicting baseline using ML... This may take 10-20 seconds');
      
      const response = await api.post(`/api/v1/predict_baseline?file_id=${files.damaged}`);
      
      if (response.data.success) {
        setMlPrediction(response.data);
        toast.success(`✅ Baseline predicted! Confidence: ${(response.data.confidence * 100).toFixed(1)}%`);
        
        // Show warning if confidence is low
        if (response.data.confidence < 0.5) {
          toast.warning(response.data.warning, { autoClose: 10000 });
        }
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to predict baseline';
      toast.error(`Baseline prediction failed: ${errorMsg}`);
      setMlPrediction(null);
    } finally {
      setPredictingBaseline(false);
    }
  };

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

    if (analysisType === 'damage_specification') {
      if (!files.damaged) {
        toast.error('Damaged structure file is required for damage classification');
        return;
      }
    }

    // Handle Damage Specification separately - it has a different API
    if (analysisType === 'damage_specification') {
      try {
        setAnalyzing(true);
        const response = await api.post('/api/v1/classify-damage', {
          file_id: files.damaged
        });
        
        setAnalyzing(false);
        
        // Show results in a toast notification
        const result = response.data;
        toast.success(`Damage Detected: ${result.prediction} (${result.confidence.toFixed(1)}% confidence)`, {
          autoClose: 8000
        });
        
        // Log full result for debugging
        console.log('Damage Classification Result:', result);
        
        // You could also navigate to a results page or show a modal here
        // For now, we'll just show the result in console and toast
        
        return;
      } catch (error) {
        setAnalyzing(false);
        const errorMsg = error.response?.data?.detail || error.message || 'Classification failed';
        toast.error(`Damage classification failed: ${errorMsg}`);
        console.error('Classification error:', error);
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
        max_freq: 49.0, // Safe limit: 98% of Nyquist for 100 Hz sampling rate
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

              <label className="flex items-center p-3 rounded border border-gray-700 cursor-pointer hover:bg-gray-700" 
                     style={{ borderColor: analysisType === 'baseline_calculation' ? '#ffffff' : undefined, backgroundColor: analysisType === 'baseline_calculation' ? '#374151' : undefined }}>
                <input
                  type="radio"
                  name="analysisType"
                  value="baseline_calculation"
                  checked={analysisType === 'baseline_calculation'}
                  onChange={(e) => setAnalysisType(e.target.value)}
                  className="w-4 h-4"
                />
                <div className="ml-3">
                  <p className="text-white font-medium text-sm">🤖 Baseline Calculation (ML)</p>
                  <p className="text-xs text-gray-400">Predict baseline from damaged data using hybrid model</p>
                </div>
              </label>

              <label className="flex items-center p-3 rounded border border-gray-700 cursor-pointer hover:bg-gray-700" 
                     style={{ borderColor: analysisType === 'damage_specification' ? '#ffffff' : undefined, backgroundColor: analysisType === 'damage_specification' ? '#374151' : undefined }}>
                <input
                  type="radio"
                  name="analysisType"
                  value="damage_specification"
                  checked={analysisType === 'damage_specification'}
                  onChange={(e) => setAnalysisType(e.target.value)}
                  className="w-4 h-4"
                />
                <div className="ml-3 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-white font-medium text-sm">🔍 Damage Specification (AI)</p>
                    <span className="px-2 py-0.5 text-xs bg-green-600 text-white rounded-full">NEW</span>
                    <span className="px-2 py-0.5 text-xs bg-purple-600 text-white rounded-full">98.28%</span>
                  </div>
                  <p className="text-xs text-gray-400">Classify damage type: healthy, deformation, bolt damage, missing beam, brace damage</p>
                </div>
              </label>
            </div>
          </div>

          {/* File Upload Section */}
          <div className="space-y-4">
            {/* Baseline Calculation Mode - Only needs damaged file */}
            {analysisType === 'baseline_calculation' && (
              <div>
                <div className="mb-4 p-4 bg-gradient-to-r from-blue-900/40 to-purple-900/40 border border-blue-500 rounded-lg">
                  <div className="flex items-start gap-3">
                    <div className="text-3xl">🤖</div>
                    <div>
                      <h3 className="text-lg font-bold text-white mb-2">ML Baseline Prediction</h3>
                      <p className="text-sm text-gray-300 mb-2">
                        Upload your damaged/current structure data, and our hybrid ML model will predict what the baseline (healthy) state should be.
                      </p>
                      <ul className="text-xs text-gray-400 space-y-1">
                        <li>✓ Trained on 51 real structural samples</li>
                        <li>✓ 10 different damage scenarios</li>
                        <li>✓ Hybrid model (frequency + time domain)</li>
                        <li>✓ Confidence score: 35-60%</li>
                      </ul>
                    </div>
                  </div>
                </div>
                
                <label className="block text-sm font-semibold text-white mb-2">
                  Current/Damaged Structure *
                </label>
                <FileUploader 
                  onFileSelect={(file) => handleFileSelect('damaged', file)}
                  disabled={uploading}
                  fileId={files.damaged}
                  metadata={fileMetadata.damaged}
                />
                
                {files.damaged && (
                  <div className="mt-4 p-4 bg-green-900/30 border border-green-500 rounded-lg">
                    <p className="text-sm text-green-300 mb-3">
                      ✅ Ready to predict baseline! Click the button below to start ML prediction.
                    </p>
                    <button
                      onClick={predictBaseline}
                      disabled={predictingBaseline}
                      className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 text-white rounded-lg text-sm font-bold transition-all transform hover:scale-105 disabled:scale-100"
                    >
                      {predictingBaseline ? '🔮 Predicting Baseline... (10-20s)' : '🤖 Predict Baseline with ML'}
                    </button>
                  </div>
                )}
                
                {/* ML Prediction Result */}
                {mlPrediction && (
                  <div className="mt-4 p-5 bg-gradient-to-r from-yellow-900/40 to-orange-900/40 border-2 border-yellow-500 rounded-lg">
                    <div className="flex items-start gap-3">
                      <div className="text-2xl">✨</div>
                      <div className="flex-1">
                        <p className="text-lg font-bold text-yellow-300 mb-3">
                          🎯 Baseline Predicted Successfully!
                        </p>
                        <div className="grid grid-cols-2 gap-3 mb-3">
                          <div className="bg-gray-900/50 p-3 rounded">
                            <p className="text-xs text-gray-400 mb-1">Confidence</p>
                            <p className="text-xl font-bold text-white">{(mlPrediction.confidence * 100).toFixed(1)}%</p>
                            <p className="text-xs text-gray-400">({mlPrediction.confidence_level})</p>
                          </div>
                          <div className="bg-gray-900/50 p-3 rounded">
                            <p className="text-xs text-gray-400 mb-1">Method</p>
                            <p className="text-xl font-bold text-white capitalize">{mlPrediction.method}</p>
                          </div>
                          <div className="bg-gray-900/50 p-3 rounded">
                            <p className="text-xs text-gray-400 mb-1">Features</p>
                            <p className="text-xl font-bold text-white">{mlPrediction.predicted_baseline_features.length}</p>
                          </div>
                          <div className="bg-gray-900/50 p-3 rounded">
                            <p className="text-xs text-gray-400 mb-1">Status</p>
                            <p className="text-lg font-bold text-green-400">✓ Ready</p>
                          </div>
                        </div>
                        {mlPrediction.warning && (
                          <div className="bg-orange-900/40 border border-orange-500 p-3 rounded mb-3">
                            <p className="text-xs text-orange-200 leading-relaxed">
                              ⚠️ {mlPrediction.warning}
                            </p>
                          </div>
                        )}
                        {mlPrediction.recommendation && (
                          <div className="bg-blue-900/40 border border-blue-500 p-3 rounded mb-3">
                            <p className="text-xs text-blue-200 leading-relaxed whitespace-pre-line">
                              💡 {mlPrediction.recommendation}
                            </p>
                          </div>
                        )}
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              // Download full prediction data as JSON (includes all metadata)
                              const dataStr = JSON.stringify(mlPrediction, null, 2);
                              const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
                              const exportFileDefaultName = `predicted_baseline_full_${new Date().getTime()}.json`;
                              const linkElement = document.createElement('a');
                              linkElement.setAttribute('href', dataUri);
                              linkElement.setAttribute('download', exportFileDefaultName);
                              linkElement.click();
                              toast.success('Full prediction data downloaded as JSON!');
                            }}
                            className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition-colors"
                          >
                            📥 Download JSON
                          </button>
                          <button
                            onClick={async () => {
                              try {
                                // Request CSV format from backend
                                const response = await api.get(`/api/v1/download_baseline_csv?file_id=${files.damaged}`, {
                                  responseType: 'blob'
                                });
                                
                                // Create download link
                                const url = window.URL.createObjectURL(new Blob([response.data]));
                                const link = document.createElement('a');
                                link.href = url;
                                link.setAttribute('download', `predicted_baseline_${new Date().getTime()}.csv`);
                                document.body.appendChild(link);
                                link.click();
                                link.remove();
                                
                                toast.success('✅ Baseline CSV downloaded! Ready to upload for analysis.', {
                                  autoClose: 5000
                                });
                                toast.info('💡 You can now use this CSV as "Original (Baseline)" in Repair Quality analysis!', {
                                  autoClose: 8000
                                });
                              } catch (error) {
                                toast.error('CSV download failed. Downloading JSON instead...');
                                // Fallback: download features array as simple JSON
                                const dataStr = JSON.stringify(mlPrediction.predicted_baseline_features, null, 2);
                                const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
                                const exportFileDefaultName = `predicted_baseline_features_${new Date().getTime()}.json`;
                                const linkElement = document.createElement('a');
                                linkElement.setAttribute('href', dataUri);
                                linkElement.setAttribute('download', exportFileDefaultName);
                                linkElement.click();
                              }
                            }}
                            className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm font-medium transition-colors"
                          >
                            📥 Download CSV
                          </button>
                          <button
                            onClick={() => setMlPrediction(null)}
                            className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium transition-colors"
                          >
                            🔄 Reset
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Damage Specification Mode - AI Damage Classification */}
            {analysisType === 'damage_specification' && (
              <div>
                <div className="mb-4 p-4 bg-gradient-to-r from-blue-900/40 to-purple-900/40 border border-blue-500 rounded-lg">
                  <div className="flex items-start gap-3">
                    <div className="text-3xl">🔍</div>
                    <div>
                      <h3 className="text-lg font-bold text-white mb-2">AI Damage Classification</h3>
                      <p className="text-sm text-gray-300 mb-2">
                        Upload your damaged structure data, and our AI model will identify the specific type of structural damage with high accuracy.
                      </p>
                      <ul className="text-xs text-gray-400 space-y-1">
                        <li>✓ Trained on 230 real structural samples</li>
                        <li>✓ 5 different damage types detected</li>
                        <li>✓ Random Forest ML model (98.28% accuracy)</li>
                        <li>✓ Detects: healthy, deformation, bolt damage, missing beam, brace damage</li>
                      </ul>
                    </div>
                  </div>
                </div>
                
                <label className="block text-sm font-semibold text-white mb-2">
                  Current/Damaged Structure *
                </label>
                <FileUploader 
                  onFileSelect={(file) => handleFileSelect('damaged', file)}
                  disabled={uploading}
                  fileId={files.damaged}
                  metadata={fileMetadata.damaged}
                />
              </div>
            )}
            
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
                
                {/* ML456 Baseline Prediction */}
                {!files.original && files.damaged && ml456Available && (
                  <div className="mt-3 p-4 bg-blue-900/30 border border-blue-500 rounded-lg">
                    <div className="flex items-start gap-3">
                      <Info className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-blue-300 mb-2">
                          💡 Don't have baseline data?
                        </p>
                        <p className="text-xs text-gray-300 mb-3">
                          We can predict it using ML trained on real structural data!
                        </p>
                        <button
                          onClick={predictBaseline}
                          disabled={predictingBaseline || !files.damaged}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded text-sm font-medium transition-colors"
                        >
                          {predictingBaseline ? '🔮 Predicting...' : '🤖 Predict Baseline with ML'}
                        </button>
                        <p className="text-xs text-gray-400 mt-2">
                          Confidence: 35-60% • Trained on 51 samples • 10 damage scenarios
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* ML Prediction Result */}
                {mlPrediction && (
                  <div className="mt-3 p-4 bg-yellow-900/30 border border-yellow-500 rounded-lg">
                    <div className="flex items-start gap-3">
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-yellow-300 mb-2">
                          ⚠️ ML-Predicted Baseline
                        </p>
                        <div className="space-y-2 text-xs">
                          <p className="text-gray-300">
                            <span className="font-semibold">Confidence:</span> {(mlPrediction.confidence * 100).toFixed(1)}% ({mlPrediction.confidence_level})
                          </p>
                          <p className="text-gray-300">
                            <span className="font-semibold">Method:</span> {mlPrediction.method}
                          </p>
                          <p className="text-gray-300">
                            <span className="font-semibold">Features:</span> {mlPrediction.predicted_baseline_features.length} predicted
                          </p>
                          {mlPrediction.warning && (
                            <p className="text-yellow-200 mt-2 text-xs italic">
                              {mlPrediction.warning}
                            </p>
                          )}
                          <button
                            onClick={() => setMlPrediction(null)}
                            className="mt-2 text-xs text-red-400 hover:text-red-300 underline"
                          >
                            Clear Prediction
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
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

            {/* Damaged Structure upload - NOT shown in baseline_calculation mode */}
            {analysisType !== 'baseline_calculation' && (
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
            )}

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
