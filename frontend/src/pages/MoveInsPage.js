import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { Home, Calendar, Search, User, ChevronDown, ChevronUp, GraduationCap, Building2, FileText, Tag, Clock } from 'lucide-react';

function ResidentDetailCard({ r }) {
  return (
    <div className="bg-gray-50 border-t border-gray-200 p-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
        <div className="space-y-2">
          <h4 className="font-semibold text-gray-700 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5" /> Identification
          </h4>
          <p className="text-gray-600"><span className="text-gray-400">Type:</span> {r.id_type || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Number:</span> {r.id_number || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Address:</span> {r.address || '—'}</p>
        </div>
        <div className="space-y-2">
          <h4 className="font-semibold text-gray-700 flex items-center gap-1.5">
            <GraduationCap className="w-3.5 h-3.5" /> Academic / Professional
          </h4>
          <p className="text-gray-600"><span className="text-gray-400">School:</span> {r.school || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Course:</span> {r.course || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Review Center:</span> {r.review_center || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Board Exam:</span> {r.board_exam_type || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Exam Date:</span> {r.exam_date || '—'}</p>
        </div>
        <div className="space-y-2">
          <h4 className="font-semibold text-gray-700 flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5" /> Profile
          </h4>
          <p className="text-gray-600"><span className="text-gray-400">Source:</span> {r.source || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Location:</span> {r.location || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Dormer Type:</span> {r.dormer_type ? r.dormer_type.replace('_', ' ') : '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">First Time:</span> {r.is_first_time_dormer ? 'Yes' : 'No'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Lease Term:</span> {r.lease_term_months ? `${r.lease_term_months} month(s)` : '—'}</p>
        </div>
        <div className="space-y-2">
          <h4 className="font-semibold text-gray-700 flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5" /> Accommodation
          </h4>
          <p className="text-gray-600"><span className="text-gray-400">Room Type:</span> {r.room_type || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Bed Type:</span> {r.bed_type || '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Monthly Rate:</span> {r.monthly_rate ? `₱${Number(r.monthly_rate).toLocaleString()}` : '—'}</p>
          <p className="text-gray-600"><span className="text-gray-400">Deposit Paid:</span> {r.deposit_paid ? `₱${Number(r.deposit_paid).toLocaleString()}` : '—'}</p>
        </div>
        <div className="space-y-2 sm:col-span-2 lg:col-span-2">
          <h4 className="font-semibold text-gray-700 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" /> Dates
          </h4>
          <div className="flex flex-wrap gap-x-6 gap-y-1">
            <p className="text-gray-600"><span className="text-gray-400">Move-in:</span> {r.move_in_date || '—'}</p>
            <p className="text-gray-600"><span className="text-gray-400">Move-out:</span> {r.move_out_date || '—'}</p>
            <p className="text-gray-600"><span className="text-gray-400">Contract End:</span> {r.contract_end_date || '—'}</p>
            <p className="text-gray-600"><span className="text-gray-400">Created:</span> {r.created_at ? new Date(r.created_at).toLocaleDateString('en-PH') : '—'}</p>
          </div>
        </div>
      </div>
      {r.notes && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-sm text-gray-600"><span className="text-gray-400">Notes:</span> {r.notes}</p>
        </div>
      )}
    </div>
  );
}

export default function MoveInsPage() {
  const [period, setPeriod] = useState('current');
  const [residents, setResidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [expandedId, setExpandedId] = useState(null);

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
      (r.phone || '').includes(s) ||
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

  const toggleExpand = (id) => {
    setExpandedId((prev) => (prev === id ? null : id));
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
                  <th className="px-4 py-3 text-left w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((r) => (
                  <React.Fragment key={r.id}>
                    <tr
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => toggleExpand(r.id)}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600">
                            <User className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{r.full_name}</p>
                            <p className="text-xs text-gray-500">
                              {r.dormer_type ? r.dormer_type.replace('_', ' ') : ''}
                              {r.dormer_type && r.school ? ' · ' : ''}
                              {r.school || ''}
                            </p>
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
                      <td className="px-4 py-3">
                        {expandedId === r.id ? (
                          <ChevronUp className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        )}
                      </td>
                    </tr>
                    {expandedId === r.id && (
                      <tr>
                        <td colSpan={7} className="p-0">
                          <ResidentDetailCard r={r} />
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
