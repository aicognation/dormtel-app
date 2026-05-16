import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-blue-700 text-white p-4">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <h1 className="text-xl font-bold">Dormtel Automation</h1>
            <div className="space-x-4">
              <Link to="/" className="hover:underline">Dashboard</Link>
            </div>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto p-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
