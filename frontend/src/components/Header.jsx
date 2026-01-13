import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, Activity, Hexagon, Radio } from 'lucide-react';

export default function Header() {
  return (
    <header className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 border-b-2 border-blue-600 sticky top-0 z-50 shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Left: Logo and Branding */}
          <Link to="/" className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-2 rounded-lg flex items-center justify-center">
              <Hexagon size={24} className="text-white" />
            </div>
            <div>
              <div className="text-blue-400 font-bold text-xs tracking-widest">HEXAGON</div>
              <h1 className="text-white font-bold text-lg">Structural Health</h1>
            </div>
          </Link>
          
          {/* Center: Navigation */}
          <nav className="flex items-center gap-8">
            <Link to="/sensor-setup" className="text-gray-300 hover:text-blue-400 transition text-sm font-medium">Sensor Setup</Link>
            <Link to="/live-monitoring" className="flex items-center gap-2 text-gray-300 hover:text-red-400 transition text-sm font-medium">
              <Radio size={16} className="animate-pulse" /> Live Monitor
            </Link>
            <a href="#docs" className="text-gray-300 hover:text-blue-400 transition text-sm font-medium">Docs</a>
          </nav>

          {/* Right: Status Indicator */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-3 py-1 bg-gray-700 rounded-full">
              <Activity size={16} className="text-green-400 animate-pulse" />
              <span className="text-xs text-gray-300">System Active</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
