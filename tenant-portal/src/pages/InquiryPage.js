import React, { useState, useEffect, useCallback } from 'react';
import { useTenant } from '../context/TenantContext';
import { getInquiries, createInquiry } from '../api/tenant';
import { formatDateTime } from '../utils/formatters';
import {
  MessageSquare, HelpCircle, AlertTriangle, CheckCircle2, Send,
  Plus, ChevronDown, ChevronUp,
} from 'lucide-react';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import StatusBadge from '../components/ui/StatusBadge';
import Modal from '../components/ui/Modal';
import Button from '../components/ui/Button';
import toast from 'react-hot-toast';

const types = [
  { id: 'question', label: 'Question', icon: HelpCircle, color: 'bg-blue-500', description: 'Ask about policies, facilities, etc.' },
  { id: 'complaint', label: 'Complaint', icon: AlertTriangle, color: 'bg-red-500', description: 'Report an issue or concern' },
];

const getTypeMeta = (type) => types.find((t) => t.id === type) || { icon: MessageSquare, color: 'bg-gray-400', label: 'Inquiry' };

export default function InquiryPage() {
  const { tenant } = useTenant();
  const [inquiries, setInquiries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [expanded, setExpanded] = useState(null);
  const [inquiryType, setInquiryType] = useState('');
  const [content, setContent] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = useCallback(() => {
    if (!tenant?.id) return;
    setLoading(true);
    getInquiries(tenant.id)
      .then(({ data }) => setInquiries(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [tenant?.id]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async () => {
    if (!inquiryType || !content.trim()) {
      toast.error('Select a type and enter your message');
      return;
    }
    if (!tenant?.id) return;
    setSubmitting(true);
    try {
      await createInquiry(tenant.id, { content: content.trim(), inquiry_type: inquiryType });
      toast.success('Inquiry submitted successfully!');
      setShowModal(false);
      setInquiryType('');
      setContent('');
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit inquiry');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare size={20} className="text-brand-navy" />
          <h2 className="text-lg font-bold text-gray-900">My Inquiries</h2>
        </div>
        <Button variant="accent" className="flex items-center gap-1 text-xs px-3 py-2" onClick={() => setShowModal(true)}>
          <Plus size={16} /> New Inquiry
        </Button>
      </div>

      {/* Inquiry List */}
      {inquiries.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <MessageSquare size={40} className="mx-auto mb-3 opacity-50" />
          <p className="text-sm">No inquiries yet</p>
          <p className="text-xs mt-1">Tap "New Inquiry" to ask a question</p>
        </div>
      ) : (
        <div className="space-y-2">
          {inquiries.map((inq) => {
            const meta = getTypeMeta(inq.inquiry_type);
            const Icon = meta.icon;
            return (
              <div key={inq.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
                <button
                  onClick={() => setExpanded(expanded === inq.id ? null : inq.id)}
                  className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 transition-colors"
                >
                  <div className={`w-10 h-10 ${meta.color} rounded-xl flex items-center justify-center flex-shrink-0`}>
                    <Icon size={20} className="text-white" />
                  </div>
                  <div className="flex-1 text-left min-w-0">
                    <p className="text-sm font-semibold text-gray-900 truncate">
                      {inq.inquiry_type ? meta.label : 'Inquiry'}
                    </p>
                    <p className="text-xs text-gray-500">{formatDateTime(inq.created_at)}</p>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <StatusBadge status={inq.status} />
                    {expanded === inq.id ? <ChevronUp size={14} className="text-gray-400" /> : <ChevronDown size={14} className="text-gray-400" />}
                  </div>
                </button>
                {expanded === inq.id && (
                  <div className="px-3 pb-3 border-t border-gray-50 space-y-2 pt-2">
                    {inq.content && <p className="text-sm text-gray-600">{inq.content}</p>}
                    {inq.inquiry_type && (
                      <div className="flex gap-4 text-xs text-gray-500">
                        <span>Type: <span className="capitalize">{inq.inquiry_type}</span></span>
                      </div>
                    )}
                    {inq.response && (
                      <div className="bg-emerald-50 rounded-lg p-2 flex items-start gap-2">
                        <CheckCircle2 size={14} className="text-emerald-500 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-xs font-semibold text-emerald-700">Admin Response</p>
                          <p className="text-xs text-emerald-600">{inq.response}</p>
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

      {/* New Inquiry Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="New Inquiry">
        <div className="space-y-4">
          <p className="text-sm text-gray-500">
            Submit a question or complaint directly to the DormTel management team.
          </p>

          {/* Type Selector */}
          <div className="grid grid-cols-2 gap-3">
            {types.map(({ id, label, icon: Icon, color, description }) => (
              <button
                key={id}
                onClick={() => setInquiryType(id)}
                className={`bg-white rounded-xl p-4 shadow-sm border-2 transition-all text-left ${
                  inquiryType === id ? 'border-brand-navy' : 'border-transparent hover:border-gray-200'
                }`}
              >
                <div className={`w-10 h-10 ${color} rounded-lg flex items-center justify-center mb-2`}>
                  <Icon size={20} className="text-white" />
                </div>
                <p className={`text-sm font-semibold ${inquiryType === id ? 'text-brand-navy' : 'text-gray-900'}`}>
                  {label}
                </p>
                <p className="text-[10px] text-gray-500 mt-0.5">{description}</p>
              </button>
            ))}
          </div>

          {/* Content */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Your Message</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Describe your question or complaint in detail..."
              rows={5}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy resize-none"
            />
            <p className="text-[10px] text-gray-400 mt-1">
              Your inquiry will be sent to the DormTel admin team and appear in the Inquiry Management dashboard.
            </p>
          </div>

          <Button variant="accent" className="w-full flex items-center justify-center gap-2" onClick={handleSubmit} disabled={submitting}>
            <Send size={16} />
            {submitting ? 'Sending...' : 'Submit Inquiry'}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
