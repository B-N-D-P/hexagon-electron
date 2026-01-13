import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Save, Edit2 } from 'lucide-react';
import api from '../services/api';

export default function SensorSetup() {
  const navigate = useNavigate();
  const [sensors, setSensors] = useState([
    { id: 1, name: 'Sensor 1', x: 5, y: 0, z: 2.5 },
    { id: 2, name: 'Sensor 2', x: 5, y: 5, z: 2.5 },
  ]);
  const [loading, setLoading] = useState(false);

  const updateSensor = (id, field, value) => {
    setSensors(sensors.map(s => s.id === id ? { ...s, [field]: field === 'name' ? value : parseFloat(value) || 0 } : s));
  };

  const saveSensors = async () => {
    setLoading(true);
    try {
      const response = await api.post('/api/v1/save-sensor-positions', {
        sensors: sensors.map(s => ({
          id: s.id,
          name: s.name,
          x: s.x,
          y: s.y,
          z: s.z
        }))
      });

      if (response.data.status === 'success') {
        alert('✓ Sensor positions saved! Ready for analysis.');
        navigate('/');
      }
    } catch (error) {
      alert(`Error: ${error.response?.data?.message || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Sensor Configuration
        </h1>
        <p className="text-gray-400">
          Define 2 sensor positions (X, Y, Z) - 3-axis each (6 columns total)
        </p>
      </div>

      <div className="bg-gray-800 rounded p-6 border border-gray-700">
        <div className="space-y-4">
          {sensors.map((sensor) => (
            <div key={sensor.id} className="bg-gray-700 rounded p-4 border border-gray-600">
              <div className="mb-3">
                <label className="block text-sm text-gray-400 mb-2">Name</label>
                <input
                  type="text"
                  value={sensor.name}
                  onChange={(e) => updateSensor(sensor.id, 'name', e.target.value)}
                  className="w-full bg-gray-600 border border-gray-500 rounded px-3 py-1 text-white focus:outline-none focus:border-white"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">X</label>
                  <input
                    type="number"
                    value={sensor.x}
                    onChange={(e) => updateSensor(sensor.id, 'x', e.target.value)}
                    className="w-full bg-gray-600 border border-gray-500 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-white"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Y</label>
                  <input
                    type="number"
                    value={sensor.y}
                    onChange={(e) => updateSensor(sensor.id, 'y', e.target.value)}
                    className="w-full bg-gray-600 border border-gray-500 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-white"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Z</label>
                  <input
                    type="number"
                    value={sensor.z}
                    onChange={(e) => updateSensor(sensor.id, 'z', e.target.value)}
                    className="w-full bg-gray-600 border border-gray-500 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-white"
                    step="0.1"
                  />
                </div>
              </div>

              <div className="mt-2 text-xs text-gray-400">
                ({sensor.x.toFixed(2)}, {sensor.y.toFixed(2)}, {sensor.z.toFixed(2)})
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={saveSensors}
          disabled={loading}
          className="w-full mt-6 bg-white text-gray-900 font-semibold py-2 px-4 rounded hover:bg-gray-100 disabled:bg-gray-500"
        >
          {loading ? 'Saving...' : 'Save Sensor Positions'}
        </button>
      </div>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
        <div className="bg-gray-800 rounded p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-1">2</h3>
          <p className="text-gray-400 text-sm">Sensors (XYZ)</p>
        </div>
        <div className="bg-gray-800 rounded p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-1">6</h3>
          <p className="text-gray-400 text-sm">Data Columns</p>
        </div>
        <div className="bg-gray-800 rounded p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-1">✓</h3>
          <p className="text-gray-400 text-sm">Ready for Analysis</p>
        </div>
      </div>
    </div>
  );
}
