import React, { useEffect, useState, useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import {
  QrCode, Plus, RotateCcw, Loader2, Download, Megaphone,
  Copy, Check, CalendarDays, MapPin, Users, Sparkles, Link2,
} from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import FormField from '../components/ui/FormField';
import Button from '../components/ui/Button';
import { createInquiry } from '../api/inquiries';
import { listCampaigns, createCampaign } from '../api/qrCampaigns';
import { useProperty } from '../contexts/PropertyContext';
import { formatDateTime } from '../utils/formatters';

const TENANT_PORTAL_URL = process.env.REACT_APP_TENANT_PORTAL_URL || 'https://dormtel.bayanaihan.net';

const PROPERTIES = [
  { value: 'DT01', label: 'Recto Branch' },
  { value: 'DT02', label: 'Sta. Mesa Branch' },
];

const propertyLabel = (code) => PROPERTIES.find((p) => p.value === code)?.label || code;

const SOURCES = [
  { value: 'walkin', label: 'Walk-in' },
  { value: 'phone', label: 'Phone' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'referral', label: 'Referral' },
];

const STATUS_OPTIONS = [
  { value: '', label: 'Select status...' },
  { value: 'student', label: 'Student' },
  { value: 'working', label: 'Working Professional' },
  { value: 'reviewee', label: 'Reviewee' },
  { value: 'backpacker', label: 'Backpacker' },
];

const LENGTH_OPTIONS = [
  { value: '', label: 'Select length...' },
  { value: '1_month', label: '1 Month' },
  { value: '2_months', label: '2 Months' },
  { value: '3_months', label: '3 Months' },
  { value: '6_months', label: '6 Months' },
  { value: '1_year', label: '1 Year' },
  { value: 'indefinite', label: 'Indefinite / Until Exam' },
];

const INITIAL_FORM = {
  source: 'walkin',
  prospect_name: '',
  prospect_phone: '',
  prospect_email: '',
  school: '',
  course: '',
  review_center: '',
  status_detail: '',
  desired_move_in_date: '',
  length_of_stay: '',
  content: '',
};

const INITIAL_CAMPAIGN = { title: '', property_code: '', start_date: '', end_date: '', notes: '' };

const localToday = () => {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
};

const campaignState = (c) => {
  const t = localToday();
  if (c.start_date && t < c.start_date) return 'upcoming';
  if (c.end_date && t > c.end_date) return 'expired';
  return 'active';
};

const CAMPAIGN_STATE_STYLES = {
  active: 'bg-green-100 text-green-800',
  upcoming: 'bg-sky-100 text-sky-800',
  expired: 'bg-gray-100 text-gray-600',
};

export default function QrInquiryPage() {
  const { propertyCode } = useProperty();
  const activeProperty = propertyCode || 'DT01';

  const [activeTab, setActiveTab] = useState('qr');
  const [form, setForm] = useState({ ...INITIAL_FORM, property_code: activeProperty });
  const [submitting, setSubmitting] = useState(false);

  // Campaigns
  const [campaigns, setCampaigns] = useState([]);
  const [loadingCampaigns, setLoadingCampaigns] = useState(true);
  const [campForm, setCampForm] = useState({ ...INITIAL_CAMPAIGN, property_code: activeProperty });
  const [creatingCampaign, setCreatingCampaign] = useState(false);
  const [activeQr, setActiveQr] = useState(null); // { campaign, data, imageUrl }
  const [copied, setCopied] = useState(false);
  const downloadRef = useRef(null);

  const fetchCampaigns = useCallback(async () => {
    setLoadingCampaigns(true);
    try {
      const result = await listCampaigns();
      setCampaigns(Array.isArray(result) ? result : []);
    } catch (err) {
      setCampaigns([]);
    } finally {
      setLoadingCampaigns(false);
    }
  }, [propertyCode]);

  useEffect(() => { fetchCampaigns(); }, [fetchCampaigns]);

  const qrForCampaign = (campaign) => {
    const schema = localStorage.getItem('dt_schema') || 'demo';
    const data = `${TENANT_PORTAL_URL}/inquiry?cid=${campaign.id}&schema=${encodeURIComponent(schema)}`;
    return {
      campaign,
      data,
      imageUrl: `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(data)}`,
    };
  };

  const handleCreateCampaign = async (e) => {
    e.preventDefault();
    if (!campForm.title.trim()) {
      toast.error('Give the campaign a title — e.g. "August Promo — Recto"');
      return;
    }
    if (campForm.start_date && campForm.end_date && campForm.start_date > campForm.end_date) {
      toast.error('Start date must be on or before the end date');
      return;
    }
    setCreatingCampaign(true);
    try {
      const campaign = await createCampaign({
        title: campForm.title.trim(),
        property_code: campForm.property_code,
        start_date: campForm.start_date || null,
        end_date: campForm.end_date || null,
        notes: campForm.notes.trim() || null,
      });
      setActiveQr(qrForCampaign(campaign));
      setCampForm({ ...INITIAL_CAMPAIGN, property_code: activeProperty });
      toast.success('Campaign created — QR code ready');
      await fetchCampaigns();
    } catch (err) {
      // client interceptor already toasted the message
    } finally {
      setCreatingCampaign(false);
    }
  };

  const handleCopyLink = async (url) => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      toast.success('Form link copied');
      setTimeout(() => setCopied(false), 1800);
    } catch {
      toast.error('Could not copy — select and copy the link manually');
    }
  };

  const handleDownloadQr = async () => {
    if (!activeQr) return;
    try {
      const res = await fetch(activeQr.imageUrl);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = downloadRef.current;
      const slug = activeQr.campaign.title.replace(/[^a-z0-9]+/gi, '_').replace(/^_+|_+$/g, '');
      a.href = url;
      a.download = `DormTel_QR_${slug || 'campaign'}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('QR code downloaded');
    } catch {
      toast.error('Download failed — right-click the QR image and save it instead');
    }
  };

  // ----- Manual inquiry -----
  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createInquiry({
        ...form,
        source: (form.source || '').toLowerCase(),
        property_code: form.property_code || activeProperty,
        inquiry_form_data: {
          status_detail: form.status_detail || null,
          submitted_via: 'staff_manual',
        },
      });
      toast.success('Inquiry created successfully');
      setForm({ ...INITIAL_FORM, property_code: activeProperty });
    } catch (err) {
      // handled by interceptor
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => setForm({ ...INITIAL_FORM, property_code: activeProperty });

  const tabs = [
    { id: 'qr', label: 'QR Campaigns', icon: QrCode },
    { id: 'new', label: 'New Inquiry', icon: Plus },
    { id: 'records', label: 'Inquiry Records', icon: Users },
  ];

  return (
    <div>
      <div className="flex items-start justify-between">
        <PageHeader
          title="QR Inquiry"
          subtitle="Generate trackable campaign QR codes and log inquiries"
        />
        <Button onClick={() => setActiveTab('qr')}>
          <QrCode className="w-4 h-4 mr-2" />
          New Campaign QR
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 border-b border-gray-200 mb-6">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === id
                ? 'border-brand-gold text-brand-navy'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Icon className="w-4 h-4 mr-2" />
            {label}
          </button>
        ))}
      </div>

      {/* ============ QR CAMPAIGNS TAB ============ */}
      {activeTab === 'qr' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* Campaign creator */}
            <div className="lg:col-span-3 bg-white rounded-lg border border-gray-200 p-5">
              <div className="flex items-center gap-2.5 mb-1">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-gold/20 text-brand-navy">
                  <Megaphone size={18} />
                </span>
                <div>
                  <h3 className="text-base font-bold text-gray-900">Create a QR Campaign</h3>
                  <p className="text-xs text-gray-500">Every QR code is tied to a campaign, so each lead traces back to the exact marketing effort and property.</p>
                </div>
              </div>

              <form onSubmit={handleCreateCampaign} className="mt-4 space-y-4">
                <FormField
                  label="Campaign Title" required
                  value={campForm.title}
                  onChange={(e) => setCampForm({ ...campForm, title: e.target.value })}
                  placeholder='e.g. "August Promo — Recto" or "DT02 Open House 2026"'
                />
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <FormField
                    label="Property" type="select" required
                    value={campForm.property_code}
                    onChange={(e) => setCampForm({ ...campForm, property_code: e.target.value })}
                    options={PROPERTIES}
                  />
                  <FormField
                    label="Valid From" type="date"
                    value={campForm.start_date}
                    onChange={(e) => setCampForm({ ...campForm, start_date: e.target.value })}
                  />
                  <FormField
                    label="Valid Until" type="date"
                    value={campForm.end_date}
                    onChange={(e) => setCampForm({ ...campForm, end_date: e.target.value })}
                  />
                </div>
                <FormField
                  label="Notes (optional)" type="textarea"
                  value={campForm.notes}
                  onChange={(e) => setCampForm({ ...campForm, notes: e.target.value })}
                  placeholder="Where will this QR be posted? e.g. Lobby standee, UE bulletin board..."
                />
                <div className="flex justify-end">
                  <Button type="submit" loading={creatingCampaign}>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Create Campaign & Generate QR
                  </Button>
                </div>
              </form>
            </div>

            {/* QR panel */}
            <div className="lg:col-span-2">
              {activeQr ? (
                <div className="bg-brand-navy rounded-lg p-5 text-white relative overflow-hidden">
                  <div className="absolute -right-8 -top-8 w-32 h-32 rounded-full bg-brand-gold/15" />
                  <div className="absolute -left-6 -bottom-10 w-28 h-28 rounded-full bg-white/5" />
                  <div className="relative">
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-brand-gold">QR Ready</p>
                    <h3 className="text-lg font-bold leading-tight mt-0.5">{activeQr.campaign.title}</h3>
                    <p className="flex items-center flex-wrap gap-x-1.5 gap-y-1 text-xs text-white/70 mt-1">
                      <span className="inline-flex items-center gap-1">
                        <MapPin size={12} className="text-brand-gold" />
                        {propertyLabel(activeQr.campaign.property_code)} · {activeQr.campaign.property_code}
                      </span>
                      {(activeQr.campaign.start_date || activeQr.campaign.end_date) && (
                        <span className="inline-flex items-center gap-1">
                          <CalendarDays size={12} />
                          {activeQr.campaign.start_date || '…'} → {activeQr.campaign.end_date || '…'}
                        </span>
                      )}
                    </p>

                    <div className="mt-4 bg-white rounded-lg p-3 w-fit mx-auto">
                      <img src={activeQr.imageUrl} alt="Campaign QR code" className="w-44 h-44" />
                    </div>

                    <div className="mt-3 rounded bg-white/10 border border-white/15 px-3 py-2">
                      <p className="text-[10px] font-semibold uppercase tracking-wide text-white/50">QR scans open</p>
                      <p className="text-[11px] text-white/85 break-all leading-relaxed">{activeQr.data}</p>
                    </div>

                    <div className="flex gap-2 mt-4">
                      <button
                        onClick={handleDownloadQr}
                        className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-brand-gold px-3 py-2.5 text-xs font-bold text-brand-navy transition hover:brightness-105"
                      >
                        <Download size={14} /> Download PNG
                      </button>
                      <button
                        onClick={() => handleCopyLink(activeQr.data)}
                        className="flex-1 flex items-center justify-center gap-1.5 rounded-lg border border-white/25 bg-white/10 px-3 py-2.5 text-xs font-bold text-white transition hover:bg-white/20"
                      >
                        {copied ? <Check size={14} className="text-brand-gold" /> : <Copy size={14} />}
                        {copied ? 'Copied' : 'Copy Link'}
                      </button>
                    </div>
                    <button
                      onClick={() => setActiveQr(null)}
                      className="w-full mt-2 text-[11px] text-white/50 hover:text-white/80 transition-colors"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              ) : (
                <div className="h-full min-h-[280px] flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50/60 p-6 text-center">
                  <QrCode className="w-10 h-10 text-gray-300" />
                  <p className="mt-3 text-sm font-semibold text-gray-600">No QR generated yet</p>
                  <p className="mt-1 text-xs text-gray-400 max-w-[220px]">
                    Create a campaign on the left and its scannable QR code appears here — ready to print and post.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Campaigns table */}
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-gray-900">Campaigns — {propertyLabel(activeProperty)}</h3>
                <p className="text-xs text-gray-500 mt-0.5">Reprint any QR below — a campaign's link never changes, so leads always trace back correctly.</p>
              </div>
              <button onClick={fetchCampaigns} className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors" title="Refresh">
                <RotateCcw size={15} className={loadingCampaigns ? 'animate-spin' : ''} />
              </button>
            </div>

            {loadingCampaigns ? (
              <div className="flex items-center justify-center py-12 text-gray-400">
                <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading campaigns...
              </div>
            ) : campaigns.length === 0 ? (
              <div className="py-12 text-center">
                <Megaphone className="w-8 h-8 text-gray-300 mx-auto" />
                <p className="mt-2 text-sm text-gray-500">No campaigns yet for this property.</p>
                <p className="text-xs text-gray-400">Create your first one above to start tracking QR leads.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[11px] uppercase tracking-wide text-gray-400 border-b border-gray-100">
                      <th className="px-5 py-3 font-semibold">Campaign</th>
                      <th className="px-3 py-3 font-semibold">Property</th>
                      <th className="px-3 py-3 font-semibold">Validity</th>
                      <th className="px-3 py-3 font-semibold text-center">Leads</th>
                      <th className="px-3 py-3 font-semibold text-center">New</th>
                      <th className="px-3 py-3 font-semibold text-center">Converted</th>
                      <th className="px-3 py-3 font-semibold">Created</th>
                      <th className="px-5 py-3 font-semibold text-right">QR</th>
                    </tr>
                  </thead>
                  <tbody>
                    {campaigns.map((c) => {
                      const state = campaignState(c);
                      return (
                        <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50/70 transition-colors">
                          <td className="px-5 py-3">
                            <p className="font-semibold text-gray-900">{c.title}</p>
                            {c.notes && <p className="text-[11px] text-gray-400 mt-0.5 max-w-[240px] truncate" title={c.notes}>{c.notes}</p>}
                          </td>
                          <td className="px-3 py-3">
                            <span className="inline-flex items-center gap-1 rounded-full bg-brand-navy/10 px-2 py-0.5 text-[11px] font-bold text-brand-navy">
                              <MapPin size={10} /> {c.property_code}
                            </span>
                          </td>
                          <td className="px-3 py-3">
                            <p className="text-xs text-gray-600">{c.start_date || '—'} → {c.end_date || '—'}</p>
                            <span className={`inline-block mt-1 rounded-full px-2 py-0.5 text-[10px] font-bold capitalize ${CAMPAIGN_STATE_STYLES[state]}`}>{state}</span>
                          </td>
                          <td className="px-3 py-3 text-center">
                            <span className="inline-flex items-center justify-center min-w-[28px] rounded-md bg-gray-100 px-1.5 py-0.5 text-xs font-bold text-gray-700">{c.leads_count}</span>
                          </td>
                          <td className="px-3 py-3 text-center">
                            <span className={`inline-flex items-center justify-center min-w-[28px] rounded-md px-1.5 py-0.5 text-xs font-bold ${c.new_count > 0 ? 'bg-blue-100 text-blue-700' : 'bg-gray-50 text-gray-400'}`}>{c.new_count}</span>
                          </td>
                          <td className="px-3 py-3 text-center">
                            <span className={`inline-flex items-center justify-center min-w-[28px] rounded-md px-1.5 py-0.5 text-xs font-bold ${c.converted_count > 0 ? 'bg-green-100 text-green-700' : 'bg-gray-50 text-gray-400'}`}>{c.converted_count}</span>
                          </td>
                          <td className="px-3 py-3">
                            <p className="text-xs text-gray-700">{c.created_by_name || '—'}</p>
                            <p className="text-[11px] text-gray-400">{formatDateTime(c.created_at)}</p>
                          </td>
                          <td className="px-5 py-3">
                            <div className="flex items-center justify-end gap-1">
                              <button
                                onClick={() => setActiveQr(qrForCampaign(c))}
                                className="flex items-center gap-1 rounded-lg bg-brand-navy px-2.5 py-1.5 text-[11px] font-bold text-white transition hover:bg-brand-navy/90"
                                title="Show QR code"
                              >
                                <QrCode size={13} /> QR
                              </button>
                              <button
                                onClick={() => handleCopyLink(qrForCampaign(c).data)}
                                className="p-1.5 rounded-lg text-gray-400 hover:text-brand-navy hover:bg-gray-100 transition-colors"
                                title="Copy form link"
                              >
                                <Link2 size={14} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ============ NEW INQUIRY TAB ============ */}
      {activeTab === 'new' && (
        <div className="max-w-2xl">
          <form onSubmit={handleCreate} className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                label="Source" type="select" required
                value={form.source}
                onChange={(e) => setForm({ ...form, source: e.target.value })}
                options={SOURCES}
              />
              <FormField
                label="Property" type="select" required
                value={form.property_code}
                onChange={(e) => setForm({ ...form, property_code: e.target.value })}
                options={PROPERTIES}
              />
            </div>
            <FormField
              label="Prospect Name" required
              value={form.prospect_name}
              onChange={(e) => setForm({ ...form, prospect_name: e.target.value })}
              placeholder="Full name"
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                label="Phone" type="tel"
                value={form.prospect_phone}
                onChange={(e) => setForm({ ...form, prospect_phone: e.target.value })}
                placeholder="09XX XXX XXXX"
              />
              <FormField
                label="Email" type="email"
                value={form.prospect_email}
                onChange={(e) => setForm({ ...form, prospect_email: e.target.value })}
                placeholder="name@email.com"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                label="School / University"
                value={form.school}
                onChange={(e) => setForm({ ...form, school: e.target.value })}
                placeholder="e.g. UE, PUP, UST"
              />
              <FormField
                label="Course / Program"
                value={form.course}
                onChange={(e) => setForm({ ...form, course: e.target.value })}
                placeholder="e.g. Nursing"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                label="Review Center"
                value={form.review_center}
                onChange={(e) => setForm({ ...form, review_center: e.target.value })}
                placeholder="If reviewee"
              />
              <FormField
                label="Status" type="select"
                value={form.status_detail}
                onChange={(e) => setForm({ ...form, status_detail: e.target.value })}
                options={STATUS_OPTIONS}
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                label="Desired Move-in Date" type="date"
                value={form.desired_move_in_date}
                onChange={(e) => setForm({ ...form, desired_move_in_date: e.target.value })}
              />
              <FormField
                label="Expected Length of Stay" type="select"
                value={form.length_of_stay}
                onChange={(e) => setForm({ ...form, length_of_stay: e.target.value })}
                options={LENGTH_OPTIONS}
              />
            </div>
            <FormField
              label="Inquiry Details" type="textarea" required
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              placeholder="What are they asking about? Rates, room types, rules..."
            />
            <div className="flex justify-end gap-3 pt-2">
              <Button type="button" variant="secondary" onClick={handleReset}>
                <RotateCcw className="w-4 h-4 mr-2" /> Reset
              </Button>
              <Button type="submit" loading={submitting}>
                <Plus className="w-4 h-4 mr-2" /> Create Inquiry
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* ============ RECORDS TAB ============ */}
      {activeTab === 'records' && (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <Users className="w-10 h-10 text-gray-300 mx-auto" />
          <h3 className="mt-3 text-sm font-semibold text-gray-700">Inquiry records live in Inquiry Management</h3>
          <p className="mt-1 text-xs text-gray-400 max-w-sm mx-auto">
            All inquiries — staff-logged and public QR leads — are managed, responded to, and converted from the Inquiry Management page. QR-originated leads are also summarized on the QR Leads page.
          </p>
          <div className="flex justify-center gap-3 mt-4">
            <Button variant="secondary" onClick={() => { window.location.href = '/inquiries'; }}>
              Open Inquiry Management
            </Button>
            <Button onClick={() => { window.location.href = '/qr-leads'; }}>
              Open QR Leads
            </Button>
          </div>
        </div>
      )}

      <a ref={downloadRef} className="hidden" href="#download" aria-hidden="true">download</a>
    </div>
  );
}
