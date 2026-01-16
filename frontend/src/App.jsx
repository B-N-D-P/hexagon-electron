import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

import Header from './components/Header';
import Upload from './pages/Upload';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import SensorSetup from './pages/SensorSetup';
import LiveMonitoring from './pages/LiveMonitoring';
import RealtimeDashboard from './components/Dashboard';

export default function App() {
  const [currentAnalysisId, setCurrentAnalysisId] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);

  return (
    <Router>
      <div className="min-h-screen bg-gray-900">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route 
              path="/" 
              element={
                <Upload 
                  onAnalysisStart={setCurrentAnalysisId}
                  onAnalysisComplete={setAnalysisResults}
                />
              } 
            />
            <Route 
              path="/realtime" 
              element={<RealtimeDashboard />} 
            />
            <Route 
              path="/dashboard/:analysisId" 
              element={<Dashboard />} 
            />
            <Route 
              path="/analysis/:analysisId" 
              element={<Analysis />} 
            />
            <Route 
              path="/sensor-setup" 
              element={<SensorSetup />} 
            />
            <Route 
              path="/live-monitoring" 
              element={<LiveMonitoring />} 
            />
          </Routes>
        </main>
        <ToastContainer 
          position="bottom-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />
      </div>
    </Router>
  );
}
