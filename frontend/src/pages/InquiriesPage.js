import React, { useEffect, useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import { Plus, Send, AlertTriangle, RefreshCw, BedSingle, Megaphone } from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import FormField from '../components/ui/FormField';
import StatusBadge from '../components/ui/StatusBadge';
import { listInquiries, createInquiry, respondToInquiry, respondToInquiryManual, escalateInquiry } from '../api/inquiries';
import { listCampaigns } from '../api/qrCampaigns';
import { INQUIRY_SOURCES, INQUIRY_STATUSES } from '../utils/constants';
import { formatDateTime, truncate } from '../utils/formatters';
import { useProperty } from '../contexts/PropertyContext';

export default function InquiriesPage() {
  const { propertyCode } = useProperty();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: '', source: '', campaign: '' });
  const [campaigns, setCampaigns] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ source: 'facebook', prospect_name: '', prospect_email: '', prospect_phone: '', content: '', external_id: '', school: '', course: '', review_center: '' });
  const [submitting, setSubmitting] = useState(false);
  const [convertInquiry, setConvertInquiry] = useState(null);
  const [responseModal, setResponseModal] = useState(null);
  const [responseText, setResponseText] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.source) params.source = filters.source;
      if (filters.campaign) params.campaign_id = filters.campaign;
      const result = await listInquiries(params);
      setData(Array.isArray(result) ? result : []);
    } catch (err) {
      toast.error('Failed to load inquiries');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [filters, propertyCode]);

  useEffect(() => { fetchData(); }, [fetchData]);

  useEffect(() => {
    listCampaigns()
      .then((result) => setCampaigns(Array.isArray(result) ? result : []))
      .catch(() => setCampaigns([]));
  }, [propertyCode]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createInquiry({
        ...form,
        source: (form.source || '').toLowerCase(),
        property_code: propertyCode,
      });
      toast.success('Inquiry created successfully');
      setShowCreate(false);
      setForm({ source: 'facebook', prospect_name: '', prospect_email: '', prospect_phone: '', content: '', external_id: '', school: '', course: '', review_center: '' });
      await fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to create inquiry';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRespond = async (id) => {
    try {
      const result = await respondToInquiry(id);
      toast.success(`Auto-response sent: "${truncate(result?.auto_response, 60)}"`);
      await fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to send auto-response';
      toast.error(msg);
    }
  };

  const handleEscalate = async (id) => {
    try {
      await escalateInquiry(id);
      toast.success('Inquiry escalated');
      await fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to escalate inquiry';
      toast.error(msg);
    }
  };

  const handleConvertClick = (inquiry) => {
    setConvertInquiry(inquiry);
  };

  const openResponseModal = (inquiry) => {
    setResponseModal(inquiry);
    setResponseText(inquiry.response || '');
  };

  const handleManualResponse = async (e) => {
    e.preventDefault();
    if (!responseModal || !responseText.trim()) return;
    setSubmitting(true);
    try {
      await respondToInquiryManual(responseModal.id, responseText.trim());
      toast.success('Response sent to tenant');
      setResponseModal(null);
      setResponseText('');
      await fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to send response';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const columns = [
    { key: 'source', label: 'Source', render: (row) => <span className="capitalize font-medium">{row.source}</span> },
    { key: 'campaign_title', label: 'Campaign', render: (row) => (
      row.campaign_title
        ? <span className="inline-flex items-center gap-1 rounded-full bg-brand-gold/20 px-2 py-0.5 text-[11px] font-bold text-brand-navy" title="Came in via this QR campaign"><Megaphone className="w-3 h-3" /> {row.campaign_title}</span>
        : <span className="text-gray-300">—</span>
    ) },
    { key: 'prospect_name', label: 'Name', render: (row) => <span className="font-medium">{row.prospect_name || '—'}</span> },
    { key: 'school', label: 'School / Company', render: (row) => <span className="text-gray-700">{row.school || '—'}</span> },
    { key: 'course', label: 'Course', render: (row) => <span className="text-gray-700">{row.course || '—'}</span> },
    { key: 'review_center', label: 'Review Center', render: (row) => <span className="text-gray-700">{row.review_center || '—'}</span> },
    { key: 'content', label: 'Content', render: (row) => (
      <span title={row.content} className="cursor-default">{truncate(row.content, 40)}</span>
    ) },
    {
      key: 'sentiment_score',
      label: 'Sentiment',
      render: (row) => {
        const score = Number(row.sentiment_score || 0);
        const color = score >= 0.7 ? 'text-green-600' : score >= 0.4 ? 'text-yellow-600' : 'text-red-600';
        return <span className={`font-semibold ${color}`}>{score.toFixed(2)}</span>;
      },
    },
    {
      key: 'lead_score',
      label: 'Lead',
      render: (row) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded bg-brand-navy/10 text-brand-navy text-xs font-bold">
          {row.lead_score ?? 0}
        </span>
      ),
    },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge status={row.status} /> },
    { key: 'created_at', label: 'Created', render: (row) => formatDateTime(row.created_at) },
    {
      key: 'actions',
      label: 'Actions',
      render: (row) => (
        <div className="flex flex-wrap gap-1">
          {row.resident_id && (
            <Button size="sm" variant="secondary" onClick={(e) => { e.stopPropagation(); openResponseModal(row); }}>
              <Send className="w-3 h-3 mr-1" /> Reply
            </Button>
          )}
          {row.status === 'new' && (
            <Button size="sm" variant="success" onClick={(e) => { e.stopPropagation(); handleRespond(row.id); }}>
              <Send className="w-3 h-3 mr-1" /> Auto-Respond
            </Button>
          )}
          {(row.status === 'new' || row.status === 'responded') && (
            <Button size="sm" variant="danger" onClick={(e) => { e.stopPropagation(); handleEscalate(row.id); }}>
              <AlertTriangle className="w-3 h-3 mr-1" /> Escalate
            </Button>
          )}
          {row.status !== 'converted' && row.status !== 'closed' && (
            <Button size="sm" variant="primary" onClick={(e) => { e.stopPropagation(); handleConvertClick(row); }}>
              <BedSingle className="w-3 h-3 mr-1" /> Convert
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Smart Inquiry Hub"
        subtitle="Manage inquiries, auto-respond, and escalate"
        actions={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="w-4 h-4 mr-1" /> New Inquiry
          </Button>
        }
      />

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={filters.status}
          onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {INQUIRY_STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <select
          value={filters.source}
          onChange={(e) => setFilters((f) => ({ ...f, source: e.target.value }))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">All Sources</option>
          {INQUIRY_SOURCES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <select
          value={filters.campaign}
          onChange={(e) => setFilters((f) => ({ ...f, campaign: e.target.value }))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">All Campaigns</option>
          {campaigns.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
        </select>
        <Button variant="ghost" onClick={fetchData}><RefreshCw className="w-4 h-4" /></Button>
      </div>

      <DataTable columns={columns} data={data} loading={loading} emptyMessage="No inquiries found" />

      {/* Create Modal */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create New Inquiry">
        <form onSubmit={handleCreate} className="space-y-4">
          <FormField
            label="Source" name="source" type="select" required
            value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })}
            options={INQUIRY_SOURCES}
          />
          <FormField
            label="Name" name="prospect_name" type="text"
            value={form.prospect_name} onChange={(e) => setForm({ ...form, prospect_name: e.target.value })}
            placeholder="Prospect name"
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField
              label="Email" name="prospect_email" type="text"
              value={form.prospect_email} onChange={(e) => setForm({ ...form, prospect_email: e.target.value })}
              placeholder="Prospect email"
            />
            <FormField
              label="Phone" name="prospect_phone" type="text"
              value={form.prospect_phone} onChange={(e) => setForm({ ...form, prospect_phone: e.target.value })}
              placeholder="e.g. 09XXXXXXXXX"
            />
          </div>
          <FormField
            label="School / Company" name="school" type="text"
            value={form.school} onChange={(e) => setForm({ ...form, school: e.target.value })}
            placeholder="e.g. University of Santo Tomas, ABC Corp"
          />
          <FormField
            label="Course" name="course" type="text"
            value={form.course} onChange={(e) => setForm({ ...form, course: e.target.value })}
            placeholder="e.g. Nursing, Civil Engineering"
          />
          <FormField
            label="Review Center" name="review_center" type="text"
            value={form.review_center} onChange={(e) => setForm({ ...form, review_center: e.target.value })}
            placeholder="e.g. Review Masters, CBRC"
          />
          <FormField
            label="Content" name="content" type="textarea" required
            value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })}
            placeholder="Inquiry message or description..."
          />
          <FormField
            label="External ID" name="external_id" type="text"
            value={form.external_id} onChange={(e) => setForm({ ...form, external_id: e.target.value })}
            placeholder="Optional reference (e.g. FB message ID)"
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button type="submit" loading={submitting}>Create Inquiry</Button>
          </div>
        </form>
      </Modal>

      {/* Manual Response Modal */}
      <Modal isOpen={!!responseModal} onClose={() => { setResponseModal(null); setResponseText(''); }} title="Reply to Tenant Inquiry">
        {responseModal && (
          <form onSubmit={handleManualResponse} className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-3 text-sm">
              <p className="font-semibold text-gray-800">{responseModal.prospect_name || 'Tenant'}</p>
              {responseModal.content && (
                <p className="text-gray-600 mt-1 italic">"{truncate(responseModal.content, 120)}"</p>
              )}
            </div>
            <FormField
              label="Your Response"
              name="response"
              type="textarea"
              required
              value={responseText}
              onChange={(e) => setResponseText(e.target.value)}
              placeholder="Type your response to the tenant..."
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={() => { setResponseModal(null); setResponseText(''); }}>Cancel</Button>
              <Button type="submit" loading={submitting}>Send Response</Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Convert to Reservation Modal */}
      <Modal isOpen={!!convertInquiry} onClose={() => setConvertInquiry(null)} title="Convert Inquiry to Reservation">
        {convertInquiry && (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm">
              <p className="font-semibold text-blue-800 mb-1">{convertInquiry.prospect_name || 'Unnamed Prospect'}</p>
              <p className="text-blue-700">Source: <span className="capitalize">{convertInquiry.source}</span></p>
              {convertInquiry.prospect_email && <p className="text-blue-700">Email: {convertInquiry.prospect_email}</p>}
              {convertInquiry.prospect_phone && <p className="text-blue-700">Phone: {convertInquiry.prospect_phone}</p>}
              {convertInquiry.school && <p className="text-blue-700">School: {convertInquiry.school}</p>}
              {convertInquiry.desired_move_in_date && <p className="text-blue-700">Desired Move-in: {convertInquiry.desired_move_in_date}</p>}
            </div>
            <p className="text-sm text-gray-600">
              Proceed to the Onboarding page to create a reservation. The inquiry details will be pre-filled automatically.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" type="button" onClick={() => setConvertInquiry(null)}>Cancel</Button>
              <Button
                onClick={() => {
                  localStorage.setItem('dormtel_convert_inquiry_id', convertInquiry.id);
                  window.location.href = '/onboarding';
                }}
              >
                <BedSingle className="w-4 h-4 mr-1" /> Go to Onboarding
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
