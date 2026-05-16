import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    axios.get(`${API}/health`).then(r => setHealth(r.data)).catch(() => setHealth({ status: 'error' }));
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800">Operations Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-500">API Status</p>
          <p className={`text-lg font-bold ${health?.status === 'ok' ? 'text-green-600' : 'text-red-600'}`}>
            {health?.status === 'ok' ? 'Online' : 'Offline'}
          </p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-500">Service</p>
          <p className="text-lg font-bold text-gray-800">{health?.service || '—'}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-500">Version</p>
          <p className="text-lg font-bold text-gray-800">1.0.0</p>
        </div>
      </div>
      <div className="bg-white p-4 rounded shadow">
        <h3 className="font-semibold text-gray-700 mb-2">Modules</h3>
        <ul className="list-disc list-inside text-gray-600">
          <li>Smart Inquiry Hub</li>
          <li>Digital Onboarding</li>
          <li>Auto-Billing Engine</li>
          <li>Payment Gateway & Reconciliation</li>
          <li>Move-Out Settlement</li>
        </ul>
      </div>
    </div>
  );
}
