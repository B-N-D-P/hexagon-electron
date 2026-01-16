import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import SensorHeatmap2D from '../components/SensorHeatmap2D';
import { Download, Eye, MapPin, TrendingUp, AlertTriangle } from 'lucide-react';
import api from '../services/api';

export default function Dashboard() {
  const { analysisId } = useParams();
  const navigate = useNavigate();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchResults();
  }, [analysisId]);

  const fetchResults = async () => {
    try {
      const response = await api.get(`/api/v1/results/${analysisId}`);
      if (response.data.status === 'completed') {
        setResults(response.data);
        setLoading(false);
      } else {
        setTimeout(fetchResults, 2000);
      }
    } catch (error) {
      toast.error('Failed to fetch results');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading analysis results...</p>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="text-center text-red-400">
        <p>No results available</p>
      </div>
    );
  }

  // Prepare chart data
  const frequencyData = results.modal_data?.original?.frequencies?.map((freq, idx) => ({
    mode: `Mode ${idx + 1}`,
    original: freq,
    damaged: results.modal_data?.damaged?.frequencies?.[idx] || 0,
    repaired: results.modal_data?.repaired?.frequencies?.[idx] || 0,
  })) || [];

  const qualityData = [
    {
      metric: 'Frequency Recovery',
      value: results.quality_breakdown?.frequency_recovery ? results.quality_breakdown.frequency_recovery * 100 : 0
    },
    {
      metric: 'Mode Shape',
      value: results.quality_breakdown?.mode_shape_match ? results.quality_breakdown.mode_shape_match * 100 : 0
    },
    {
      metric: 'Damping',
      value: results.quality_breakdown?.damping_recovery ? results.quality_breakdown.damping_recovery * 100 : 0
    },
    {
      metric: 'Overall',
      value: results.quality_score ? results.quality_score * 100 : 0
    },
  ];

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">Analysis Results</h1>
        <p className="text-gray-400">ID: {analysisId}</p>
      </div>

      {/* Quality Score Card */}
      <div className="bg-gray-800 rounded p-8 mb-8 border border-gray-700">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <p className="text-gray-400 mb-2">
              {results.analysis_type === 'localization' ? 'Q Index Score' : 'Overall Quality Score'}
            </p>
            <p className="text-5xl font-bold text-white">
              {results.analysis_type === 'localization'
                ? ((results.q_index?.q || 0) * 100).toFixed(1) + '%'
                : (results.quality_score ? (results.quality_score * 100).toFixed(1) : 'N/A') + '%'
              }
            </p>
            <p className="text-sm text-gray-400 mt-2">
              {results.analysis_type === 'localization'
                ? results.damage_location?.severity || 'Analysis Complete'
                : results.quality_interpretation || 'Complete'
              }
            </p>
          </div>

          {results.damage_location && (
            <div className="text-center border-l border-gray-600 pl-6">
              <p className="text-gray-400 mb-2 flex items-center justify-center gap-2">
                <MapPin size={18} />
                Damage Location
              </p>
              <p className="text-2xl font-bold text-white">
                Detected
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Confidence: {(results.damage_confidence * 100).toFixed(0)}% · Q: {(((results.q_index?.q || 0) * 100)).toFixed(1)}%
              </p>
            </div>
          )}

          <div className="text-center border-l border-gray-600 pl-6">
            <p className="text-gray-400 mb-2">Analysis Type</p>
            <p className="text-2xl font-bold text-white capitalize">
              {results.analysis_type?.replace(/_/g, ' ')}
            </p>
            <p className="text-sm text-blue-200 mt-2">Complete</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-8 border-b border-slate-700 overflow-x-auto">
        {['overview', 'frequencies', 'quality', 'damping', 'timeDomain', 'fft', 'energy', 'modeShapes', 'mac', 'freqShift', 'damage', 'export'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 font-semibold transition capitalize whitespace-nowrap text-sm ${
              activeTab === tab
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {tab === 'timeDomain' ? 'Time Domain' : tab === 'freqShift' ? 'Freq Shift' : tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="space-y-8">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-4">Frequency Comparison (Hz)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={frequencyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                  <XAxis dataKey="mode" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" label={{ value: 'Frequency (Hz)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                    formatter={(value) => value ? value.toFixed(2) : '0'}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }} />
                  <Line type="monotone" dataKey="original" stroke="#3b82f6" strokeWidth={2.5} strokeDasharray="0" dot={{ fill: '#3b82f6', r: 6 }} activeDot={{ r: 8 }} name="Original" />
                  <Line type="monotone" dataKey="damaged" stroke="#ef4444" strokeWidth={2.5} strokeDasharray="5,5" dot={{ fill: '#ef4444', r: 6 }} activeDot={{ r: 8 }} name="Damaged" />
                  <Line type="monotone" dataKey="repaired" stroke="#10b981" strokeWidth={2.5} strokeDasharray="10,5" dot={{ fill: '#10b981', r: 6 }} activeDot={{ r: 8 }} name="Repaired" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-gray-800 rounded p-6 border border-gray-700">
              <h3 className="text-xl font-bold text-white mb-4">Quality Metrics</h3>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={qualityData}>
                  <PolarGrid stroke="#475569" />
                  <PolarAngleAxis dataKey="metric" stroke="#94a3b8" />
                  <PolarRadiusAxis stroke="#94a3b8" domain={[0, 100]} />
                  <Radar name="Score %" dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Frequencies Tab */}
        {activeTab === 'frequencies' && (
          <div className="bg-gray-800 rounded p-6 border border-gray-700">
            <h3 className="text-xl font-bold text-white mb-4">Natural Frequencies (Hz)</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={frequencyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="mode" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }} />
                <Legend />
                <Line type="monotone" dataKey="original" stroke="#3b82f6" strokeWidth={2.5} strokeDasharray="0" dot={{ fill: '#3b82f6', r: 5 }} name="Original" />
                <Line type="monotone" dataKey="damaged" stroke="#ef4444" strokeWidth={2.5} strokeDasharray="5,5" dot={{ fill: '#ef4444', r: 5 }} name="Damaged" />
                <Line type="monotone" dataKey="repaired" stroke="#10b981" strokeWidth={2.5} strokeDasharray="10,5" dot={{ fill: '#10b981', r: 5 }} name="Repaired" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Quality Tab */}
        {activeTab === 'quality' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-800 rounded p-6 border border-gray-700">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <TrendingUp className="text-green-400" />
                Repair Quality Breakdown
              </h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-gray-400">Frequency Recovery</span>
                    <span className="text-green-400 font-bold">{((results.quality_breakdown?.frequency_recovery || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{ width: `${(results.quality_breakdown?.frequency_recovery || 0) * 100}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-gray-400">Mode Shape Match</span>
                    <span className="text-blue-400 font-bold">{((results.quality_breakdown?.mode_shape_match || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(results.quality_breakdown?.mode_shape_match || 0) * 100}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-gray-400">Damping Recovery</span>
                    <span className="text-purple-400 font-bold">{((results.quality_breakdown?.damping_recovery || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div className="bg-purple-500 h-2 rounded-full" style={{ width: `${(results.quality_breakdown?.damping_recovery || 0) * 100}%` }}></div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded p-6 border border-gray-700">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Eye className="text-blue-400" />
                Assessment
              </h3>
              <div className="space-y-3">
                <p className="text-gray-300">{results.quality_interpretation}</p>
                <div className="bg-blue-900 bg-opacity-30 border border-blue-700 rounded p-4 text-sm text-blue-200">
                  <p className="font-semibold mb-2">Recommendations:</p>
                  <ul className="space-y-1 text-xs">
                    <li>✓ Structure is suitable for normal operating loads</li>
                    <li>✓ Schedule follow-up inspection in 6 months</li>
                    <li>✓ Document repair in maintenance records</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Damping Ratio Tab */}
        {activeTab === 'damping' && (
          results.enhanced_graphs?.damping_comparison ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                <h3 className="text-xl font-bold text-white mb-4">Damping Ratio Comparison (%)</h3>
                <ResponsiveContainer width="100%" height={360}>
                  <BarChart data={results.enhanced_graphs.damping_comparison.damping_data || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                    <XAxis dataKey="mode" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }} />
                    <Legend />
                    <Bar dataKey="original" fill="#3b82f6" />
                    <Bar dataKey="damaged" fill="#ef4444" />
                    <Bar dataKey="repaired" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                <h3 className="text-xl font-bold text-white mb-4">Damping Fit Quality (R²)</h3>
                <ResponsiveContainer width="100%" height={360}>
                  <BarChart data={results.enhanced_graphs.damping_comparison.damping_fit_quality || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                    <XAxis dataKey="mode" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" domain={[0,1]} />
                    <Legend />
                    <Bar dataKey="original" fill="#60a5fa" />
                    <Bar dataKey="damaged" fill="#fca5a5" />
                    <Bar dataKey="repaired" fill="#6ee7b7" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 text-center">
              <p className="text-gray-400">Damping comparison data not available for this analysis type.</p>
            </div>
          )
        )}

        {/* Time Domain Tab - Vibration Acceleration vs Time */}
        {activeTab === 'timeDomain' && (
          results.enhanced_graphs?.time_domain ? (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-4">Vibration Acceleration vs Time</h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={results.enhanced_graphs.time_domain.time_domain || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                  <XAxis
                    dataKey="time"
                    stroke="#94a3b8"
                    label={{ value: 'Time (s)', position: 'insideBottomRight', offset: -5 }}
                  />
                  <YAxis
                    stroke="#94a3b8"
                    label={{ value: 'Acceleration (g)', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                    formatter={(value) => value ? value.toFixed(3) : '0'}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }} />
                  <Line type="monotone" dataKey="baseline" stroke="#06b6d4" strokeWidth={2} dot={false} isAnimationActive={false} name="Baseline" />
                  <Line type="monotone" dataKey="damaged" stroke="#ef4444" strokeWidth={2} dot={false} isAnimationActive={false} name="Damaged" />
                  <Line type="monotone" dataKey="repaired" stroke="#10b981" strokeWidth={2} dot={false} isAnimationActive={false} name="Repaired" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 text-center">
              <p className="text-gray-400">Time domain data not available for this analysis type.</p>
            </div>
          )
        )}

        {/* FFT Spectrum Tab */}
        {activeTab === 'fft' && (
          results.enhanced_graphs?.fft_spectrum ? (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-4">Power Spectral Density (Welch)</h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={results.enhanced_graphs.fft_spectrum.fft_spectrum || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                  <XAxis
                    dataKey="frequency"
                    stroke="#94a3b8"
                    label={{ value: 'Frequency (Hz)', position: 'insideBottomRight', offset: -5 }}
                  />
                  <YAxis
                    stroke="#94a3b8"
                    label={{ value: 'Magnitude (linear)', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                    formatter={(value) => value ? value.toFixed(2) : '0'}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }} />
                  <Line type="monotone" dataKey="baseline" stroke="#06b6d4" strokeWidth={2} dot={false} isAnimationActive={false} name="Baseline" />
                  <Line type="monotone" dataKey="damaged" stroke="#ef4444" strokeWidth={2} dot={false} isAnimationActive={false} name="Damaged" />
                  <Line type="monotone" dataKey="repaired" stroke="#10b981" strokeWidth={2} dot={false} isAnimationActive={false} name="Repaired" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 text-center">
              <p className="text-gray-400">FFT spectrum data not available for this analysis type.</p>
            </div>
          )
        )}

        {/* Energy Distribution Tab */}
        {activeTab === 'energy' && (
          results.enhanced_graphs?.energy_distribution ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                <h3 className="text-xl font-bold text-white mb-4">Cumulative Energy Distribution (%)</h3>
                <ResponsiveContainer width="100%" height={360}>
                  <LineChart data={results.enhanced_graphs.energy_distribution.energy_cumulative || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                    <XAxis dataKey="mode" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" domain={[0, 100]} />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }} />
                    <Legend />
                    <Line type="monotone" dataKey="original" stroke="#3b82f6" strokeWidth={2} />
                    <Line type="monotone" dataKey="damaged" stroke="#ef4444" strokeWidth={2} />
                    <Line type="monotone" dataKey="repaired" stroke="#10b981" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                <h3 className="text-xl font-bold text-white mb-4">Per-Mode Energy (arb. units)</h3>
                <ResponsiveContainer width="100%" height={360}>
                  <BarChart data={results.enhanced_graphs.energy_distribution.energy_per_mode || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                    <XAxis dataKey="mode" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }} />
                    <Legend />
                    <Bar dataKey="original" fill="#3b82f6" />
                    <Bar dataKey="damaged" fill="#ef4444" />
                    <Bar dataKey="repaired" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 text-center">
              <p className="text-gray-400">Energy distribution data not available for this analysis type.</p>
            </div>
          )
        )}

        {/* Mode Shapes Tab */}
        {activeTab === 'modeShapes' && (
          results.enhanced_graphs?.mode_shapes ? (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-4">Mode Shapes (Modes 1-3)</h3>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {['mode_1','mode_2','mode_3'].map((mkey) => (
                  results.enhanced_graphs.mode_shapes.mode_shapes?.[mkey] ? (
                    <div key={mkey} className="bg-slate-900 rounded p-4 border border-slate-700">
                      <h4 className="text-white font-semibold mb-2">{mkey.replace('_',' ').toUpperCase()}</h4>
                      <ResponsiveContainer width="100%" height={260}>
                        <LineChart data={results.enhanced_graphs.mode_shapes.mode_shapes[mkey]}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                          <XAxis dataKey="sensor" stroke="#94a3b8" />
                          <YAxis stroke="#94a3b8" domain={[-1,1]} />
                          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }} />
                          <Legend />
                          <Line type="monotone" dataKey="original" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
                          <Line type="monotone" dataKey="damaged" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} />
                          <Line type="monotone" dataKey="repaired" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div key={mkey} className="bg-slate-900 rounded p-4 border border-slate-700 text-gray-500">No data</div>
                  )
                ))}
              </div>
            </div>
          ) : (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 text-center">
              <p className="text-gray-400">Mode shapes not available.</p>
            </div>
          )
        )}

        {/* MAC Matrix Tab */}
        {activeTab === 'mac' && (
          results.enhanced_graphs?.mac_matrix ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-4">MAC: Original vs Damaged</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-gray-300">
                  <thead className="border-b border-slate-600">
                    <tr>
                      <th className="px-4 py-2 text-left">Mode</th>
                      {results.enhanced_graphs.mac_matrix.original_vs_damaged[0]?.map((_, idx) => (
                        <th key={idx} className="px-4 py-2 text-right">M{idx + 1}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {results.enhanced_graphs.mac_matrix.original_vs_damaged?.map((row, ridx) => (
                      <tr key={ridx} className="border-b border-slate-700">
                        <td className="px-4 py-2 font-semibold">M{ridx + 1}</td>
                        {row.map((val, cidx) => (
                          <td key={cidx} className="px-4 py-2 text-right">
                            <span className={val > 0.8 ? 'bg-green-900 px-2 py-1 rounded' : val > 0.5 ? 'bg-yellow-900 px-2 py-1 rounded' : ''}>
                              {(val * 100).toFixed(0)}%
                            </span>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-4">MAC: Original vs Repaired</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-gray-300">
                  <thead className="border-b border-slate-600">
                    <tr>
                      <th className="px-4 py-2 text-left">Mode</th>
                      {results.enhanced_graphs.mac_matrix.original_vs_repaired[0]?.map((_, idx) => (
                        <th key={idx} className="px-4 py-2 text-right">M{idx + 1}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {results.enhanced_graphs.mac_matrix.original_vs_repaired?.map((row, ridx) => (
                      <tr key={ridx} className="border-b border-slate-700">
                        <td className="px-4 py-2 font-semibold">M{ridx + 1}</td>
                        {row.map((val, cidx) => (
                          <td key={cidx} className="px-4 py-2 text-right">
                            <span className={val > 0.8 ? 'bg-green-900 px-2 py-1 rounded' : val > 0.5 ? 'bg-yellow-900 px-2 py-1 rounded' : ''}>
                              {(val * 100).toFixed(0)}%
                            </span>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            </div>
          ) : (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 text-center">
              <p className="text-gray-400">MAC matrix data not available for this analysis type.</p>
            </div>
          )
        )}

        {/* Frequency Shift Tab */}
        {activeTab === 'freqShift' && (
          results.enhanced_graphs?.frequency_shifts ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-4">Frequency Shift: Original → Damaged (%)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={results.enhanced_graphs.frequency_shifts.damaged_shift}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                  <XAxis dataKey="mode" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }} />
                  <Bar dataKey="shift_percent" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-4">Frequency Shift: Original → Repaired (%)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={results.enhanced_graphs.frequency_shifts.repaired_shift}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                  <XAxis dataKey="mode" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }} />
                  <Bar dataKey="shift_percent" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            </div>
          ) : (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 text-center">
              <p className="text-gray-400">Frequency shift data not available for this analysis type.</p>
            </div>
          )
        )}

        {/* Damage Localization Tab */}
        {activeTab === 'damage' && results.damage_location && (
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <MapPin className="text-red-400" />
              Damage Localization
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-slate-700 rounded p-4">
                <p className="text-gray-400 text-sm mb-1">From Origin (x,y,z)</p>
                <p className="text-lg font-bold text-white">
                  ({results.damage_location?.x?.toFixed(2)}, {results.damage_location?.y?.toFixed(2)}, {results.damage_location?.z?.toFixed(2)}) m
                </p>
                <p className="text-xs text-gray-300">dist: {results.damage_location?.distance_from_origin?.toFixed(2)} m</p>
              </div>
              <div className="bg-slate-700 rounded p-4">
                <p className="text-gray-400 text-sm mb-1">Component</p>
                <p className="text-lg font-bold text-white">{results.damage_component || 'N/A'}</p>
                <p className="text-xs text-gray-300">Sensor: {results.damage_primary_sensor || 'N/A'}</p>
              </div>
              <div className="bg-slate-700 rounded p-4">
                <p className="text-gray-400 text-sm mb-1">Severity / Confidence</p>
                <p className="text-lg font-bold text-white">{(results.damage_severity || 0).toFixed(1)}%</p>
                <p className="text-2xl font-bold text-green-400">{(results.damage_confidence * 100).toFixed(0)}%</p>
              </div>
            </div>

            <div className="flex gap-3 mb-6">
              <button
                onClick={() => navigate(`/damage-localization/${analysisId}`)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                View Full Localization Report
              </button>
            </div>

            <div className="bg-gradient-to-r from-red-900 to-orange-900 bg-opacity-30 border border-red-700 rounded p-6">
              <p className="text-white font-semibold mb-2 flex items-center gap-2">
                <AlertTriangle size={20} />
                Inspection Recommendation
              </p>
              <p className="text-gray-300 text-sm mb-6">
                Use the Full Localization Report to see per-method evidence (Spatial/Wavelet/MAC) and the sensor heatmap.
              </p>
              {results.sensor_layout && (
                <div>
                  <h4 className="text-white font-semibold mb-3">Sensor Heatmap (Consensus)</h4>
                  <SensorHeatmap2D sensorLayout={results.sensor_layout} sensorScores={results.sensor_damage_scores} />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Export Tab */}
        {activeTab === 'export' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <button
              onClick={() => {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                window.location.href = `${apiUrl}/api/v1/results/${analysisId}/download/json`;
              }}
              className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-blue-500 transition flex items-center justify-between group cursor-pointer"
            >
              <div>
                <h3 className="text-lg font-bold text-white mb-1">📊 JSON Report</h3>
                <p className="text-gray-400 text-sm">Full analysis data in JSON format</p>
              </div>
              <Download size={28} className="text-blue-400 group-hover:scale-110 transition" />
            </button>

            <button
              onClick={() => {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                window.location.href = `${apiUrl}/api/v1/results/${analysisId}/download/pdf`;
              }}
              className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-blue-500 transition flex items-center justify-between group cursor-pointer"
            >
              <div>
                <h3 className="text-lg font-bold text-white mb-1">📄 Standard PDF</h3>
                <p className="text-gray-400 text-sm">Single page professional report</p>
              </div>
              <Download size={28} className="text-blue-400 group-hover:scale-110 transition" />
            </button>

            <button
              onClick={() => {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                window.location.href = `${apiUrl}/api/v1/results/${analysisId}/download/comprehensive-pdf`;
              }}
              className="bg-slate-800 rounded-lg p-6 border border-cyan-500 hover:border-cyan-400 transition flex items-center justify-between group cursor-pointer"
            >
              <div>
                <h3 className="text-lg font-bold text-cyan-400 mb-1">⭐ Comprehensive PDF</h3>
                <p className="text-gray-400 text-sm">2+ pages with ALL graphs & metrics</p>
              </div>
              <Download size={28} className="text-cyan-400 group-hover:scale-110 transition" />
            </button>

            <button
              onClick={() => {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                window.location.href = `${apiUrl}/api/v1/results/${analysisId}/download/enhanced-html`;
              }}
              className="bg-slate-800 rounded-lg p-6 border border-green-500 hover:border-green-400 transition flex items-center justify-between group cursor-pointer"
            >
              <div>
                <h3 className="text-lg font-bold text-green-400 mb-1">🎨 Interactive HTML</h3>
                <p className="text-gray-400 text-sm">Hexagon chart + interactive graphs</p>
              </div>
              <Download size={28} className="text-green-400 group-hover:scale-110 transition" />
            </button>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-12 flex gap-4 justify-center">
        <button
          onClick={() => navigate('/')}
          className="px-8 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-lg transition"
        >
          New Analysis
        </button>
        <button
          onClick={() => window.print()}
          className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition flex items-center gap-2"
        >
          <Download size={18} />
          Print Report
        </button>
      </div>
    </div>
  );
}
