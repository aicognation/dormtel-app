import React, { useState, useMemo, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  CalendarDays, Clock, Send, User, GraduationCap, Home,
  ChevronDown, Loader2, MapPin, ShieldCheck, Megaphone,
} from 'lucide-react';

const API_URL = process.env.REACT_APP_API_URL || '';

const BRANCH_LABELS = { DT01: 'Recto Branch', DT02: 'Sta. Mesa Branch' };

const STATUS_OPTIONS = [
  { value: 'student', label: 'Student' },
  { value: 'working', label: 'Working Professional' },
  { value: 'reviewee', label: 'Reviewee' },
  { value: 'backpacker', label: 'Backpacker / Traveller' },
];

const LENGTH_OPTIONS = [
  { value: '1_month', label: '1 Month' },
  { value: '2_months', label: '2 Months' },
  { value: '3_months', label: '3 Months' },
  { value: '6_months', label: '6 Months' },
  { value: '1_year', label: '1 Year' },
  { value: 'indefinite', label: 'Indefinite / Until Exam' },
];

const SOURCE_OPTIONS = [
  { value: 'walkin', label: 'Walk-in' },
  { value: 'phone', label: 'Phone' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'referral', label: 'Referral' },
  { value: 'website', label: 'Website' },
];

const INITIAL = {
  prospect_name: '',
  prospect_phone: '',
  prospect_email: '',
  status_detail: 'student',
  school: '',
  course: '',
  review_center: '',
  desired_move_in_date: '',
  length_of_stay: '',
  source: 'walkin',
  content: '',
};

const localToday = () => {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
};

const prettyDate = (iso) => {
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  if (!y || !m || !d) return iso;
  return new Date(y, m - 1, d).toLocaleDateString('en-PH', { month: 'long', day: 'numeric', year: 'numeric' });
};

function Field({ label, required, children }) {
  return (
    <label className="block">
      <span className="block text-[13px] font-semibold text-slate-700 mb-1.5">
        {label} {required && <span className="text-red-500">*</span>}
      </span>
      {children}
    </label>
  );
}

const inputClass =
  'w-full rounded-lg border border-slate-300 bg-white px-3.5 py-3 text-[15px] text-slate-900 placeholder-slate-400 outline-none transition focus:border-brand-navy focus:ring-2 focus:ring-brand-navy/20';

function SelectField({ value, onChange, options, placeholder }) {
  return (
    <div className="relative">
      <select value={value} onChange={onChange} className={`${inputClass} appearance-none pr-10`}>
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      <ChevronDown size={16} className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
    </div>
  );
}

function SectionTitle({ icon: Icon, children }) {
  return (
    <div className="flex items-center gap-2.5 mb-4">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gold-light text-brand-navy">
        <Icon size={16} strokeWidth={2.4} />
      </span>
      <h3 className="text-[12px] font-bold uppercase tracking-[0.14em] text-brand-navy">{children}</h3>
    </div>
  );
}

export default function PublicInquiryPage() {
  const [params] = useSearchParams();
  const cid = params.get('cid') || '';
  const schema = params.get('schema') || '';

  const [campaign, setCampaign] = useState(null);
  const [campaignLoading, setCampaignLoading] = useState(Boolean(cid));
  const [campaignError, setCampaignError] = useState(false);

  useEffect(() => {
    if (!cid) return;
    const headers = {};
    if (schema === 'demo' || schema === 'pilot') headers['X-Tenant-Schema'] = schema;
    axios
      .get(`${API_URL}/api/v1/qr-campaigns/public/${cid}`, { headers })
      .then((res) => setCampaign(res.data))
      .catch(() => setCampaignError(true))
      .finally(() => setCampaignLoading(false));
  }, [cid, schema]);

  // Campaign QRs resolve everything from the campaign record; legacy QRs pass params directly
  const branch = campaign ? campaign.property_code : (params.get('branch') || 'DT01');
  const branchLabel = BRANCH_LABELS[branch] || branch;
  const heading = campaign ? campaign.title : (params.get('label') || branchLabel);
  const start = campaign ? (campaign.start_date || '') : (params.get('start') || '');
  const end = campaign ? (campaign.end_date || '') : (params.get('end') || '');

  const [form, setForm] = useState({ ...INITIAL });
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const validity = useMemo(() => {
    const t = localToday();
    if (start && t < start) return 'upcoming';
    if (end && t > end) return 'expired';
    return 'open';
  }, [start, end]);

  const set = (name) => (e) => setForm((p) => ({ ...p, [name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.prospect_name.trim() || !form.prospect_phone.trim()) {
      toast.error('Please fill in your name and cellphone number.');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        prospect_name: form.prospect_name.trim(),
        prospect_phone: form.prospect_phone.trim(),
        prospect_email: form.prospect_email.trim() || null,
        school: form.school.trim() || null,
        course: form.course.trim() || null,
        review_center: form.review_center.trim() || null,
        desired_move_in_date: form.desired_move_in_date || null,
        length_of_stay: form.length_of_stay || null,
        source: form.source,
        content: form.content.trim() || `Inquiry from ${form.prospect_name.trim()} via ${heading} QR form`,
        property_code: branch,
        campaign_id: cid || null,
        inquiry_form_data: {
          status_detail: form.status_detail,
          submitted_via: 'public_qr_form',
          qr_label: heading,
          qr_campaign_id: cid || null,
          qr_start: start,
          qr_end: end,
        },
      };
      const headers = {};
      if (schema === 'demo' || schema === 'pilot') headers['X-Tenant-Schema'] = schema;
      await axios.post(`${API_URL}/api/v1/inquiries/`, payload, { headers });
      setDone(true);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Something went wrong — please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="pi-page min-h-screen">
      {/* ---- Header band ---- */}
      <header className="pi-band relative overflow-hidden bg-brand-navy pb-16 pt-8 text-white">
        <div className="relative mx-auto max-w-xl px-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-display text-2xl font-bold leading-none tracking-tight">
                Dorm<span className="text-brand-gold">Tel</span>
              </p>
              <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.28em] text-white/60">
                My Dorm &middot; My Home
              </p>
            </div>
            <span className="flex items-center gap-1.5 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-[11px] font-semibold">
              <ShieldCheck size={13} className="text-brand-gold" /> Official Inquiry Form
            </span>
          </div>

          <div className="mt-8">
            <p className="flex items-center gap-1.5 text-[12px] font-semibold uppercase tracking-[0.18em] text-brand-gold">
              <MapPin size={13} /> {branchLabel} &middot; {branch}
            </p>
            {campaign && (
              <span className="mt-2.5 inline-flex items-center gap-1.5 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-[11px] font-semibold text-white/85">
                <Megaphone size={12} className="text-brand-gold" /> Official Campaign
              </span>
            )}
            <h1 className="font-display mt-1.5 text-[32px] font-bold leading-tight tracking-tight">
              {heading}
            </h1>
            <p className="mt-2 max-w-sm text-[14px] leading-relaxed text-white/75">
              Kuha ka na ng slot! Fill out this quick form and our team will reach out with rates, room options, and tour schedules.
            </p>
            {(start || end) && (
              <span className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-brand-gold px-3 py-1.5 text-[11.5px] font-bold text-brand-navy-dark">
                <CalendarDays size={13} />
                Valid {prettyDate(start)} &ndash; {prettyDate(end)}
              </span>
            )}
          </div>
        </div>
      </header>

      {/* ---- Body ---- */}
      <main className="relative z-10 mx-auto -mt-9 max-w-xl px-5 pb-16">
        {campaignLoading && (
          <div className="pi-rise rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-lg shadow-slate-900/5">
            <Loader2 size={28} className="mx-auto animate-spin text-brand-navy" />
            <p className="mt-3 text-sm font-semibold text-slate-700">Loading campaign details...</p>
          </div>
        )}

        {!campaignLoading && campaignError && (
          <div className="pi-rise rounded-2xl border border-red-200 bg-white p-7 text-center shadow-lg shadow-slate-900/5">
            <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600">
              <Clock size={26} />
            </span>
            <h2 className="font-display mt-4 text-xl font-bold text-slate-900">This QR code isn&rsquo;t recognized</h2>
            <p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-slate-500">
              The campaign linked to this code may have been removed. Please scan the latest QR code at our branch or message us on Facebook to inquire.
            </p>
          </div>
        )}

        {!campaignLoading && !campaignError && validity === 'expired' && (
          <div className="pi-rise rounded-2xl border border-amber-200 bg-white p-7 text-center shadow-lg shadow-slate-900/5">
            <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-amber-100 text-amber-600">
              <Clock size={26} />
            </span>
            <h2 className="font-display mt-4 text-xl font-bold text-slate-900">This QR code has expired</h2>
            <p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-slate-500">
              It was valid until <span className="font-semibold text-slate-700">{prettyDate(end)}</span>. Please scan the latest QR code posted at our branch, or message us on Facebook to inquire.
            </p>
          </div>
        )}

        {!campaignLoading && !campaignError && validity === 'upcoming' && (
          <div className="pi-rise rounded-2xl border border-sky-200 bg-white p-7 text-center shadow-lg shadow-slate-900/5">
            <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-sky-100 text-sky-600">
              <CalendarDays size={26} />
            </span>
            <h2 className="font-display mt-4 text-xl font-bold text-slate-900">This QR code isn&rsquo;t active yet</h2>
            <p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-slate-500">
              It becomes valid on <span className="font-semibold text-slate-700">{prettyDate(start)}</span>. Please come back then or ask our front desk for assistance.
            </p>
          </div>
        )}

        {!campaignLoading && !campaignError && validity === 'open' && done && (
          <div className="pi-rise rounded-2xl border border-emerald-200 bg-white p-8 text-center shadow-lg shadow-slate-900/5">
            <svg viewBox="0 0 52 52" className="mx-auto h-20 w-20">
              <circle cx="26" cy="26" r="24" fill="none" stroke="#10b981" strokeWidth="2.5" className="pi-check-circle" />
              <path fill="none" stroke="#10b981" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" d="M14 27l8 8 16-17" className="pi-check-mark" />
            </svg>
            <h2 className="font-display mt-4 text-2xl font-bold text-slate-900">
              Salamat, {form.prospect_name.trim().split(' ')[0]}!
            </h2>
            <p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-slate-500">
              Your inquiry for <span className="font-semibold text-slate-700">{heading}</span> has been received. Our team will contact you at <span className="font-semibold text-slate-700">{form.prospect_phone.trim()}</span> shortly.
            </p>
            <div className="mx-auto mt-6 max-w-xs rounded-xl bg-slate-50 p-4 text-left text-[13px] text-slate-600">
              <p className="font-semibold text-slate-800">What happens next?</p>
              <p className="mt-1.5 leading-relaxed">A branch staff will confirm your preferred move-in date and share current rates and available rooms{form.desired_move_in_date ? ` for ${prettyDate(form.desired_move_in_date)}` : ''}.</p>
            </div>
          </div>
        )}

        {!campaignLoading && !campaignError && validity === 'open' && !done && (
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Section: Your Information */}
            <section className="pi-rise rounded-2xl border border-slate-200 bg-white p-5 shadow-lg shadow-slate-900/5" style={{ animationDelay: '60ms' }}>
              <SectionTitle icon={User}>Your Information</SectionTitle>
              <div className="space-y-4">
                <Field label="Full Name" required>
                  <input className={inputClass} value={form.prospect_name} onChange={set('prospect_name')} placeholder="Juan Dela Cruz" autoComplete="name" />
                </Field>
                <Field label="Cellphone Number" required>
                  <input className={inputClass} type="tel" value={form.prospect_phone} onChange={set('prospect_phone')} placeholder="09XX XXX XXXX" autoComplete="tel" />
                </Field>
                <Field label="Email">
                  <input className={inputClass} type="email" value={form.prospect_email} onChange={set('prospect_email')} placeholder="you@example.com" autoComplete="email" />
                </Field>
              </div>
            </section>

            {/* Section: Academic / Professional */}
            <section className="pi-rise rounded-2xl border border-slate-200 bg-white p-5 shadow-lg shadow-slate-900/5" style={{ animationDelay: '140ms' }}>
              <SectionTitle icon={GraduationCap}>Academic / Professional</SectionTitle>
              <div className="space-y-4">
                <Field label="I am currently a...">
                  <SelectField value={form.status_detail} onChange={set('status_detail')} options={STATUS_OPTIONS} />
                </Field>
                <Field label="School / University">
                  <input className={inputClass} value={form.school} onChange={set('school')} placeholder="e.g. UE, PUP, UST" />
                </Field>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <Field label="Course / Program">
                    <input className={inputClass} value={form.course} onChange={set('course')} placeholder="e.g. Nursing" />
                  </Field>
                  <Field label="Review Center">
                    <input className={inputClass} value={form.review_center} onChange={set('review_center')} placeholder="If reviewee" />
                  </Field>
                </div>
              </div>
            </section>

            {/* Section: Stay Preferences */}
            <section className="pi-rise rounded-2xl border border-slate-200 bg-white p-5 shadow-lg shadow-slate-900/5" style={{ animationDelay: '220ms' }}>
              <SectionTitle icon={Home}>Stay Preferences</SectionTitle>
              <div className="space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <Field label="Desired Move-in Date">
                    <input className={inputClass} type="date" value={form.desired_move_in_date} onChange={set('desired_move_in_date')} />
                  </Field>
                  <Field label="Expected Length of Stay">
                    <SelectField value={form.length_of_stay} onChange={set('length_of_stay')} options={LENGTH_OPTIONS} placeholder="Select..." />
                  </Field>
                </div>
                <Field label="How did you hear about us?">
                  <SelectField value={form.source} onChange={set('source')} options={SOURCE_OPTIONS} />
                </Field>
                <Field label="Questions or Special Requests">
                  <textarea
                    className={`${inputClass} resize-none`}
                    rows={3}
                    value={form.content}
                    onChange={set('content')}
                    placeholder="Room preferences, budget, questions about rules..."
                  />
                </Field>
              </div>
            </section>

            <button
              type="submit"
              disabled={submitting}
              className="pi-rise group flex w-full items-center justify-center gap-2 rounded-xl bg-brand-gold px-6 py-4 text-[15px] font-bold text-brand-navy-dark shadow-lg shadow-brand-gold/30 transition hover:brightness-105 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.99] disabled:opacity-70 disabled:hover:translate-y-0"
              style={{ animationDelay: '300ms' }}
            >
              {submitting ? (
                <><Loader2 size={18} className="animate-spin" /> Submitting...</>
              ) : (
                <><Send size={17} className="transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" /> Submit Inquiry</>
              )}
            </button>
            <p className="pi-rise text-center text-[11.5px] leading-relaxed text-slate-400" style={{ animationDelay: '340ms' }}>
              By submitting, you agree to be contacted by DormTel {branchLabel} regarding your inquiry.
            </p>
          </form>
        )}

        <p className="mt-10 text-center text-[11px] font-medium uppercase tracking-[0.2em] text-slate-400">
          DormTel Automation &middot; CUCED Initiated
        </p>
      </main>
    </div>
  );
}
