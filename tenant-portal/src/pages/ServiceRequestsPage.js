import React, { useState, useEffect, useCallback } from 'react';
import { useTenant } from '../context/TenantContext';
import { getServiceRequests, createServiceRequest } from '../api/tenant';
import { formatDateTime } from '../utils/formatters';
import {
  Wrench, Zap, Wind, Bug, Wifi, Droplets, KeyRound, Sparkles, Refrigerator, HelpCircle,
  Plus, ChevronDown, ChevronUp, CheckCircle2,
} from 'lucide-react';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import StatusBadge from '../components/ui/StatusBadge';
import Modal from '../components/ui/Modal';
import Button from '../components/ui/Button';
import toast from 'react-hot-toast';

const categories = [
  { id: 'plumbing', label: 'Plumbing', icon: Wrench, color: 'bg-blue-500' },
  { id: 'electrical', label: 'Electrical', icon: Zap, color: 'bg-amber-500' },
  { id: 'aircon', label: 'Aircon', icon: Wind, color: 'bg-cyan-500' },
  { id: 'pest_control', label: 'Pest Control', icon: Bug, color: 'bg-red-500' },
  { id: 'wifi', label: 'WiFi', icon: Wifi, color: 'bg-purple-500' },
  { id: 'water_supply', label: 'Water', icon: Droplets, color: 'bg-blue-400' },
  { id: 'lock_key', label: 'Lock / Key', icon: KeyRound, color: 'bg-gray-600' },
  { id: 'cleaning', label: 'Cleaning', icon: Sparkles, color: 'bg-emerald-500' },
  { id: 'appliance', label: 'Appliance', icon: Refrigerator, color: 'bg-orange-500' },
  { id: 'other', label: 'Other', icon: HelpCircle, color: 'bg-gray-400' },
];

const priorities = ['low', 'medium', 'high', 'urgent'];

export default function ServiceRequestsPage() {
  const { tenant } = useTenant();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [expanded, setExpanded] = useState(null);
  const [form, setForm] = useState({ category: '', subject: '', description: '', location: '', priority: 'medium' });
  const [submitting, setSubmitting] = useState(false);

  const loadData = useCallback(() => {
    if (!tenant?.id) return;
    setLoading(true);
    getServiceRequests(tenant.id)
      .then(({ data }) => setRequests(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [tenant?.id]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async () => {
    if (!form.category || !form.subject) {
      toast.error('Select a category and enter a subject');
      return;
    }
    if (!tenant?.id) return;
    setSubmitting(true);
    try {
      await createServiceRequest(tenant.id, form);
      toast.success('Request submitted!');
      setShowModal(false);
      setForm({ category: '', subject: '', description: '', location: '', priority: 'medium' });
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit');
    } finally {
      setSubmitting(false);
    }
  };

  const getCategoryIcon = (cat) => {
    const c = categories.find((x) => x.id === cat);
    return c || categories[categories.length - 1];
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-gray-900">My Service Requests</h2>
        <Button variant="accent" className="flex items-center gap-1 text-sm px-3 py-2.5 min-h-[44px]" onClick={() => setShowModal(true)}>
          <Plus size={16} /> New Request
        </Button>
      </div>

      {/* Request List */}
      {requests.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <Wrench size={40} className="mx-auto mb-3 opacity-50" />
          <p className="text-sm">No service requests yet</p>
          <p className="text-xs mt-1">Tap "New Request" to submit one</p>
        </div>
      ) : (
        <div className="space-y-2">
          {requests.map((sr) => {
            const cat = getCategoryIcon(sr.category);
            const Icon = cat.icon;
            return (
              <div key={sr.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
                <button
                  onClick={() => setExpanded(expanded === sr.id ? null : sr.id)}
                  className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 transition-colors"
                >
                  <div className={`w-10 h-10 ${cat.color} rounded-xl flex items-center justify-center flex-shrink-0`}>
                    <Icon size={20} className="text-white" />
                  </div>
                  <div className="flex-1 text-left min-w-0">
                    <p className="text-sm font-semibold text-gray-900 truncate">{sr.subject}</p>
                    <p className="text-xs text-gray-500">{formatDateTime(sr.submitted_at)}</p>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <StatusBadge status={sr.status} />
                    {expanded === sr.id ? <ChevronUp size={14} className="text-gray-400" /> : <ChevronDown size={14} className="text-gray-400" />}
                  </div>
                </button>
                {expanded === sr.id && (
                  <div className="px-3 pb-3 border-t border-gray-50 space-y-2 pt-2">
                    {sr.description && <p className="text-sm text-gray-600">{sr.description}</p>}
                    <div className="flex gap-4 text-xs text-gray-500">
                      <span>Category: <span className="capitalize">{(sr.category || '').replace('_', ' ')}</span></span>
                      <span>Priority: <StatusBadge status={sr.priority} /></span>
                    </div>
                    {sr.location && <p className="text-xs text-gray-500">Location: {sr.location}</p>}
                    {sr.resolution_notes && (
                      <div className="bg-emerald-50 rounded-lg p-2 flex items-start gap-2">
                        <CheckCircle2 size={14} className="text-emerald-500 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-xs font-semibold text-emerald-700">Resolution</p>
                          <p className="text-xs text-emerald-600">{sr.resolution_notes}</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* New Request Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="New Service Request">
        <div className="space-y-4">
          {/* Category Picker */}
          <div>
            <p className="text-sm font-semibold text-gray-700 mb-2">Category</p>
            <div className="grid grid-cols-5 gap-2">
              {categories.map(({ id, label, icon: Icon, color }) => (
                <button
                  key={id}
                  onClick={() => setForm({ ...form, category: id })}
                  className={`flex flex-col items-center gap-1 p-2 rounded-xl border-2 transition-all ${
                    form.category === id ? 'border-brand-navy bg-brand-navy/5' : 'border-gray-100'
                  }`}
                >
                  <div className={`w-8 h-8 ${color} rounded-lg flex items-center justify-center`}>
                    <Icon size={14} className="text-white" />
                  </div>
                  <span className="text-[11px] text-gray-600 leading-tight text-center">{label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Subject */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Subject</label>
            <input
              type="text"
              value={form.subject}
              onChange={(e) => setForm({ ...form, subject: e.target.value })}
              placeholder="e.g., Aircon not cooling"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Describe the issue in detail..."
              rows={3}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy resize-none"
            />
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Location</label>
            <input
              type="text"
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
              placeholder={`Room ${tenant.room_number || ''}`}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy"
            />
          </div>

          {/* Priority */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Priority</label>
            <div className="flex gap-2">
              {priorities.map((p) => (
                <button
                  key={p}
                  onClick={() => setForm({ ...form, priority: p })}
                  className={`flex-1 py-2.5 rounded-xl text-xs font-medium border-2 capitalize transition-all min-h-[44px] ${
                    form.priority === p ? 'border-brand-navy bg-brand-navy text-white' : 'border-gray-100 text-gray-600'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <Button variant="accent" className="w-full" onClick={handleSubmit} disabled={submitting}>
            {submitting ? 'Submitting...' : 'Submit Request'}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
