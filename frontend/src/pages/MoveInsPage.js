import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { Home, Calendar, Search, User } from 'lucide-react';

export default function MoveInsPage() {
  const [period, setPeriod] = useState('current');
  const [residents, setResidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchMoveIns = async () => {
    setLoading(true);
    try {
      const data = await client.get(`/moveins?period=${period}`);
      setResidents(data);
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMoveIns();
  }, [period]);

  const filtered = residents.filter((r) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      (r.full_name || '').toLowerCase().includes(s) ||
      (r.email || '').toLowerCase().includes(s) ||
      (r.bed_code || '').toLowerCase().includes(s) ||
      (r.room_number || '').toLowerCase().includes(s)
    );
  });

  const statusBadge = (s) => {
    const colors = {
      prospect: 'bg-gray-100 text-gray-700',
      reserved: 'bg-blue-100 text-blue-700',
      active: 'bg-green-100 text-green-700',
      inactive: 'bg-yellow-100 text-yellow-700',
      moved_out: 'bg-red-100 text-red-700',
    };
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colors[s] || colors.prospect}`}>
        {s?.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Home className="w-6 h-6 text-brand-navy" />
          Move-ins
        </h1>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex gap-2">
          {['past', 'current', 'future'].map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                period === p
                  ? 'bg-brand-navy text-white'
                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
        <div className="relative flex-1 sm:max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy"
          />
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading move-ins...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No move-ins found for this period.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 font-medium">
                <tr>
                  <th className="px-4 py-3 text-left">Resident</th>
                  <th className="px-4 py-3 text-left">Contact</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Bed / Room</th>
                  <th className="px-4 py-3 text-left">Move-in Date</th>
                  <th className="px-4 py-3 text-left">Contract End</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600">
                          <User className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{r.full_name}</p>
                          <p className="text-xs text-gray-500">{r.school || ''}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-gray-700">{r.email}</p>
                      <p className="text-xs text-gray-500">{r.phone}</p>
                    </td>
                    <td className="px-4 py-3">{statusBadge(r.status)}</td>
                    <td className="px-4 py-3">
                      <p className="text-gray-700">{r.bed_code || '-'}</p>
                      <p className="text-xs text-gray-500">{r.room_number || ''} {r.building || ''}</p>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5 text-gray-700">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        {r.move_in_date || '-'}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-700">
                      {r.contract_end_date || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
