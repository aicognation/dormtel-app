import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useProperty } from '../contexts/PropertyContext';
import client from '../api/client';
import { Search, Users, Filter, Pencil, Trash2, Eye, Plus, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { listRooms } from '../api/onboarding';

export default function ResidentsPage() {
  const { isAdmin } = useAuth();
  const { propertyCode } = useProperty();
  const [residents, setResidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [rooms, setRooms] = useState([]);
  const [form, setForm] = useState({
    full_name: '', email: '', phone: '', status: 'active', notes: '',
    id_type: '', id_number: '', address: '', school: '', course: '',
    review_center: '', monthly_rate: '', move_in_date: '', move_out_date: '',
    contract_end_date: '', bed_id: '',
  });

  const fetchResidents = async () => {
    setLoading(true);
    try {
      const data = await client.get('/residents');
      setResidents(Array.isArray(data) ? data : []);
    } catch {
      toast.error('Failed to load residents');
      setResidents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResidents();
  }, [propertyCode]);

  useEffect(() => {
    const fetchRooms = async () => {
      try {
        const result = await listRooms();
        setRooms(Array.isArray(result) ? result : []);
      } catch {
        // silently fail; bed selection is optional
      }
    };
    fetchRooms();
  }, [propertyCode]);

  const filtered = residents.filter((r) => {
    const s = search.toLowerCase();
    const matchesSearch =
      (r.full_name || '').toLowerCase().includes(s) ||
      (r.email || '').toLowerCase().includes(s) ||
      (r.phone || '').includes(s) ||
      (r.bed_code || '').toLowerCase().includes(s) ||
      (r.room_number || '').toLowerCase().includes(s) ||
      (r.id_number || '').toLowerCase().includes(s) ||
      (r.school || '').toLowerCase().includes(s) ||
      (r.address || '').toLowerCase().includes(s);
    const matchesStatus = statusFilter === 'all' || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const openCreate = () => {
    setEditing(null);
    setForm({
      full_name: '', email: '', phone: '', status: 'active', notes: '',
      id_type: '', id_number: '', address: '', school: '', course: '',
      review_center: '', monthly_rate: '', move_in_date: '', move_out_date: '',
      contract_end_date: '', bed_id: '',
    });
    setModalOpen(true);
  };

  const openEdit = (r) => {
    setEditing(r);
    setForm({
      full_name: r.full_name || '',
      email: r.email || '',
      phone: r.phone || '',
      status: r.status || 'active',
      notes: r.notes || '',
      id_type: r.id_type || '',
      id_number: r.id_number || '',
      address: r.address || '',
      school: r.school || '',
      course: r.course || '',
      review_center: r.review_center || '',
      monthly_rate: r.monthly_rate || '',
      move_in_date: r.move_in_date || '',
      move_out_date: r.move_out_date || '',
      contract_end_date: r.contract_end_date || '',
      bed_id: r.bed_id || '',
    });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...form,
        monthly_rate: form.monthly_rate ? Number(form.monthly_rate) : 0,
        bed_id: form.bed_id || undefined,
      };
      if (editing) {
        await client.patch(`/residents/${editing.id}`, payload);
        toast.success('Resident updated');
      } else {
        await client.post('/residents', { ...payload, monthly_rate: payload.monthly_rate || 0 });
        toast.success('Resident created');
      }
      setModalOpen(false);
      fetchResidents();
    } catch (err) {
      const msg = err.response?.data?.detail || `Failed to ${editing ? 'update' : 'create'} resident`;
      toast.error(msg);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to deactivate this resident?')) return;
    try {
      await client.delete(`/residents/${id}`);
      toast.success('Resident deactivated');
      fetchResidents();
    } catch {
      // handled by interceptor
    }
  };

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

  const formatDate = (d) => {
    if (!d) return '-';
    return new Date(d).toLocaleDateString('en-PH');
  };

  const formatMoney = (v) => {
    if (v === null || v === undefined) return '-';
    return `₱${Number(v).toLocaleString()}`;
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Users className="w-6 h-6 text-brand-navy" />
          Residents
        </h1>
        {isAdmin && (
          <button
            onClick={openCreate}
            className="inline-flex items-center gap-2 bg-brand-navy text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-navy/90"
          >
            <Plus className="w-4 h-4" />
            Add Resident
          </button>
        )}
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name, email, phone, bed, room, ID, school..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-gray-300 rounded-lg text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-navy"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="reserved">Reserved</option>
            <option value="prospect">Prospect</option>
            <option value="inactive">Inactive</option>
            <option value="moved_out">Moved Out</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading residents...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No residents found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 font-medium">
                <tr>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Room No.</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Room Type</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Bed</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Name</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Contact</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Address</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Location</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Email</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">ID Type</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">ID Number</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Source</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Dormer Type</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">School / Review Center</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Course / Exam</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">1 Mo. Advance</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">PR No.</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Security Dep.</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">PR No.</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Utility Dep.</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">PR No.</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Lease Term</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Rate</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Move In</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Move Out</th>
                  <th className="px-3 py-3 text-left whitespace-nowrap">Status</th>
                  <th className="px-3 py-3 text-right whitespace-nowrap">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <td className="px-3 py-3 whitespace-nowrap">
                      <span className="font-medium text-gray-900">{r.room_number || '-'}</span>
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700 capitalize">
                      {r.bed_type?.replace(/_/g, ' ') || '-'}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700">
                      {r.bed_code || '-'}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap">
                      <p className="font-medium text-gray-900">{r.full_name}</p>
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700">
                      {r.phone || '-'}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700 max-w-[120px] truncate" title={r.address}>
                      {r.address || '-'}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-500">
                      -
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700">
                      {r.email || '-'}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700 capitalize">
                      {r.id_type?.replace(/_/g, ' ') || '-'}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700">
                      {r.id_number || '-'}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-500">
                      -
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap">
                      {r.is_first_time_dormer ? (
                        <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full">New</span>
                      ) : (
                        <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">Returning</span>
                      )}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700 max-w-[140px] truncate" title={r.school || r.review_center}>
                      {r.school || r.review_center || '-'}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700 max-w-[120px] truncate" title={r.course}>
                      {r.course || '-'}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700">
                      {formatMoney(r.deposit_paid)}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-500">
                      -
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700">
                      {formatMoney(r.deposit_paid)}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-500">
                      -
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-500">
                      -
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-500">
                      -
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700">
                      {formatDate(r.contract_end_date)}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700">
                      {formatMoney(r.monthly_rate)}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700">
                      {formatDate(r.move_in_date)}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-gray-700">
                      {formatDate(r.move_out_date)}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap">
                      {statusBadge(r.status)}
                    </td>
                    <td className="px-3 py-3 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => openEdit(r)}
                          className="p-1.5 text-gray-500 hover:text-brand-navy hover:bg-gray-100 rounded"
                          title="Edit"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        {isAdmin && (
                          <button
                            onClick={() => handleDelete(r.id)}
                            className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"
                            title="Deactivate"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                {editing ? 'Edit Resident' : 'Add Resident'}
              </h3>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                  <input
                    required
                    value={form.full_name}
                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    required
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input
                    required
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Rate</label>
                  <input
                    type="number"
                    value={form.monthly_rate}
                    onChange={(e) => setForm({ ...form, monthly_rate: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ID Type</label>
                  <select
                    value={form.id_type}
                    onChange={(e) => setForm({ ...form, id_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  >
                    <option value="">Select...</option>
                    <option value="passport">Passport</option>
                    <option value="drivers_license">Driver's License</option>
                    <option value="national_id">National ID</option>
                    <option value="school_id">School ID</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ID Number</label>
                  <input
                    value={form.id_number}
                    onChange={(e) => setForm({ ...form, id_number: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                  <input
                    value={form.address}
                    onChange={(e) => setForm({ ...form, address: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">School / Review Center</label>
                  <input
                    value={form.school}
                    onChange={(e) => setForm({ ...form, school: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Course / Exam</label>
                  <input
                    value={form.course}
                    onChange={(e) => setForm({ ...form, course: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Review Center</label>
                  <input
                    value={form.review_center}
                    onChange={(e) => setForm({ ...form, review_center: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select
                    value={form.status}
                    onChange={(e) => setForm({ ...form, status: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  >
                    <option value="prospect">Prospect</option>
                    <option value="reserved">Reserved</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="moved_out">Moved Out</option>
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Bed / Room</label>
                  <select
                    value={form.bed_id}
                    onChange={(e) => setForm({ ...form, bed_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  >
                    <option value="">No bed assigned</option>
                    {rooms.map((room) => (
                      <optgroup key={room.id} label={`${room.room_number}${room.building ? ` (${room.building})` : ''}`}>
                        {(room.beds || []).map((bed) => (
                          <option key={bed.id} value={bed.id}>
                            {bed.bed_code} — {bed.bed_type?.replace(/_/g, ' ') || 'bed'} — {bed.status}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Move-in Date</label>
                  <input
                    type="date"
                    value={form.move_in_date}
                    onChange={(e) => setForm({ ...form, move_in_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Move-out Date</label>
                  <input
                    type="date"
                    value={form.move_out_date}
                    onChange={(e) => setForm({ ...form, move_out_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Contract End Date</label>
                  <input
                    type="date"
                    value={form.contract_end_date}
                    onChange={(e) => setForm({ ...form, contract_end_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  rows={3}
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-navy"
                  placeholder="Internal notes about this resident..."
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-brand-navy rounded-lg hover:bg-brand-navy/90"
                >
                  {editing ? 'Save Changes' : 'Create Resident'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
