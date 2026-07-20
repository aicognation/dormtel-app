import React, { useEffect, useState, useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import {
  Megaphone, RefreshCw, X, Phone, Mail, CalendarDays, GraduationCap,
  Send, AlertTriangle, BedSingle, QrCode, MapPin, UserCheck, Inbox,
  TrendingUp, BellRing, CheckCheck, ScanLine, Clock,
} from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import Button from '../components/ui/Button';
import StatusBadge from '../components/ui/StatusBadge';
import { listInquiries, respondToInquiry, escalateInquiry } from '../api/inquiries';
import { listCampaigns } from '../api/qrCampaigns';
import { useProperty } from '../contexts/PropertyContext';
import { formatDateTime } from '../utils/formatters';

const POLL_INTERVAL_MS = 45000;
const LAST_SEEN_KEY = 'dt_qr_leads_last_seen';

const STATUS_DETAIL_LABELS = {
  student: 'Student',
  working: 'Working Professional',
  reviewee: 'Reviewee',
  backpacker: 'Backpacker / Traveller',
};

const LENGTH_LABELS = {
  '1_month': '1 Month', '2_months': '2 Months', '3_months': '3 Months',
  '6_months': '6 Months', '1_year': '1 Year', indefinite: 'Indefinite / Until Exam',
};

const PROPERTIES = [
  { value: 'DT01', label: 'Recto Branch' },
  { value: 'DT02', label: 'Sta. Mesa Branch' },
];
const propertyLabel = (code) => PROPERTIES.find((p) => p.value === code)?.label || code;

const isQrLead = (i) => Boolean(i.campaign_id) || i.inquiry_form_data?.submitted_via === 'public_qr_form';

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function QrLeadsPage() {
  const navigate = useNavigate();
  const { propertyCode } = useProperty();

  const [leads, setLeads] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [campaignFilter, setCampaignFilter] = useState('all');
  const [selected, setSelected] = useState(null);
  const [acting, setActing] = useState(false);
  const [unread, setUnread] = useState(0);
  const [lastPoll, setLastPoll] = useState(null);

  const knownIds = useRef(new Set());
  const firstLoad = useRef(true);

  const fetchAll = useCallback(async (silent = false) => {
    try {
      const [inq, camps] = await Promise.all([
        listInquiries({ via_qr: true }),
        listCampaigns(),
      ]);
      const list = Array.isArray(inq) ? inq : [];
      const campList = Array.isArray(camps) ? camps : [];
      setCampaigns(campList);

      if (firstLoad.current) {
        firstLoad.current = false;
        list.forEach((l) => knownIds.current.add(l.id));
        const lastSeen = localStorage.getItem(LAST_SEEN_KEY);
        if (lastSeen) {
          setUnread(list.filter((l) => l.created_at > lastSeen && l.status === 'new').length);
        }
      } else {
        const fresh = list.filter((l) => !knownIds.current.has(l.id));
        if (fresh.length > 0) {
          fresh.forEach((l) => knownIds.current.add(l.id));
          fresh.slice(0, 3).forEach((l) => {
            toast(`New QR lead: ${l.prospect_name || 'Unnamed'}${l.campaign_title ? ` — ${l.campaign_title}` : ''}`, {
              icon: '📥',
              duration: 6000,
            });
          });
          setUnread((u) => u + fresh.length);
        }
      }

      setLeads(list);
      setLastPoll(new Date());
      if (!silent) setLoading(false);
    } catch (err) {
      if (!silent) {
        setLoading(false);
      }
    }
  }, [propertyCode]);

  useEffect(() => {
    setLoading(true);
    firstLoad.current = true;
    knownIds.current = new Set();
    fetchAll();
    const timer = setInterval(() => fetchAll(true), POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [fetchAll]);

  const markAllSeen = () => {
    localStorage.setItem(LAST_SEEN_KEY, new Date().toISOString());
    setUnread(0);
    toast.success('All leads marked as seen');
  };

  const filtered = campaignFilter === 'all'
    ? leads
    : leads.filter((l) => l.campaign_id === campaignFilter);

  const stats = {
    total: filtered.length,
    new: filtered.filter((l) => l.status === 'new').length,
    responded: filtered.filter((l) => l.status === 'responded').length,
    converted: filtered.filter((l) => l.status === 'converted').length,
  };
  const conversionRate = stats.total > 0 ? Math.round((stats.converted / stats.total) * 100) : 0;

  const handleRespond = async (lead) => {
    setActing(true);
    try {
      const result = await respondToInquiry(lead.id);
      toast.success('Auto-response logged — lead marked as responded');
      setSelected((s) => (s && s.id === lead.id ? { ...s, status: 'responded', response: result?.auto_response } : s));
      await fetchAll(true);
    } catch (err) { /* toasted */ } finally {
      setActing(false);
    }
  };

  const handleEscalate = async (lead) => {
    setActing(true);
    try {
      await escalateInquiry(lead.id);
      toast.success('Lead escalated — checkpoint created');
      setSelected((s) => (s && s.id === lead.id ? { ...s, status: 'escalated' } : s));
      await fetchAll(true);
    } catch (err) { /* toasted */ } finally {
      setActing(false);
    }
  };

  const handleConvert = (lead) => {
    localStorage.setItem('dormtel_convert_inquiry_id', lead.id);
    navigate('/onboarding');
  };

  const statCards = [
    { label: 'Total QR Leads', value: stats.total, icon: Inbox, chip: 'bg-brand-navy/10 text-brand-navy' },
    { label: 'New / Untouched', value: stats.new, icon: BellRing, chip: 'bg-blue-100 text-blue-700', pulse: stats.new > 0 },
    { label: 'Responded', value: stats.responded, icon: Send, chip: 'bg-amber-100 text-amber-700' },
    { label: 'Converted', value: stats.converted, icon: UserCheck, chip: 'bg-green-100 text-green-700' },
    { label: 'Conversion Rate', value: `${conversionRate}%`, icon: TrendingUp, chip: 'bg-brand-gold/25 text-brand-navy' },
  ];

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PageHeader
          title="QR Leads"
          subtitle="Every inquiry that came in through a public QR campaign form"
        />
        <div className="flex items-center gap-2">
          <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-green-200 bg-green-50 px-3 py-1.5 text-[11px] font-semibold text-green-700">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
            Live · checks every 45s{lastPoll ? ` · updated ${timeAgo(lastPoll.toISOString())}` : ''}
          </span>
          <Button variant="secondary" onClick={() => { setLoading(true); fetchAll(); }}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </Button>
          <Button onClick={markAllSeen} disabled={unread === 0}>
            <CheckCheck className="w-4 h-4 mr-2" /> Mark seen{unread > 0 ? ` (${unread})` : ''}
          </Button>
        </div>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mt-5">
        {statCards.map(({ label, value, icon: Icon, chip, pulse }) => (
          <div key={label} className="relative bg-white rounded-lg border border-gray-200 px-4 py-3.5 overflow-hidden transition-shadow hover:shadow-md">
            <div className="flex items-center justify-between">
              <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${chip}`}>
                <Icon size={15} strokeWidth={2.4} />
              </span>
              {pulse && <span className="absolute top-2.5 right-2.5 h-2 w-2 rounded-full bg-blue-500 animate-pulse" />}
            </div>
            <p className="mt-2.5 text-2xl font-extrabold text-gray-900 leading-none">{value}</p>
            <p className="mt-1 text-[11px] font-medium text-gray-500">{label}</p>
          </div>
        ))}
      </div>

      {/* Campaign filter chips */}
      <div className="flex flex-wrap items-center gap-2 mt-5">
        <span className="text-[11px] font-bold uppercase tracking-wide text-gray-400 mr-1">Campaign:</span>
        <button
          onClick={() => setCampaignFilter('all')}
          className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
            campaignFilter === 'all'
              ? 'bg-brand-navy text-white'
              : 'bg-white border border-gray-200 text-gray-600 hover:border-gray-300'
          }`}
        >
          All campaigns ({leads.length})
        </button>
        {campaigns.map((c) => (
          <button
            key={c.id}
            onClick={() => setCampaignFilter(c.id)}
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
              campaignFilter === c.id
                ? 'bg-brand-navy text-white'
                : 'bg-white border border-gray-200 text-gray-600 hover:border-gray-300'
            }`}
          >
            <Megaphone size={11} />
            {c.title}
            <span className={`rounded-full px-1.5 text-[10px] font-bold ${campaignFilter === c.id ? 'bg-white/20' : 'bg-gray-100 text-gray-500'}`}>
              {c.leads_count}
            </span>
          </button>
        ))}
      </div>

      {/* Leads table */}
      <div className="bg-white rounded-lg border border-gray-200 mt-4">
        {loading ? (
          <div className="flex items-center justify-center py-16 text-gray-400">
            <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading QR leads...
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center">
            <ScanLine className="w-10 h-10 text-gray-200 mx-auto" />
            <p className="mt-3 text-sm font-semibold text-gray-600">No QR leads yet</p>
            <p className="mt-1 text-xs text-gray-400 max-w-xs mx-auto">
              Generate a campaign QR on the QR Inquiry page, print it, and leads will appear here the moment someone scans and submits.
            </p>
            <Button className="mt-4" onClick={() => navigate('/qr-inquiry')}>
              <QrCode className="w-4 h-4 mr-2" /> Create a Campaign QR
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wide text-gray-400 border-b border-gray-100">
                  <th className="px-5 py-3 font-semibold">Received</th>
                  <th className="px-3 py-3 font-semibold">Campaign</th>
                  <th className="px-3 py-3 font-semibold">Prospect</th>
                  <th className="px-3 py-3 font-semibold">Contact</th>
                  <th className="px-3 py-3 font-semibold">Profile</th>
                  <th className="px-3 py-3 font-semibold text-center">Lead</th>
                  <th className="px-3 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold text-right">Open</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((l) => {
                  const detail = l.inquiry_form_data?.status_detail;
                  const viaCampaign = Boolean(l.campaign_id);
                  return (
                    <tr
                      key={l.id}
                      onClick={() => setSelected(l)}
                      className="border-b border-gray-50 cursor-pointer hover:bg-brand-gold/5 transition-colors"
                    >
                      <td className="px-5 py-3 whitespace-nowrap">
                        <p className="text-xs font-semibold text-gray-800">{timeAgo(l.created_at)}</p>
                        <p className="text-[11px] text-gray-400">{formatDateTime(l.created_at)}</p>
                      </td>
                      <td className="px-3 py-3">
                        {l.campaign_title ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-brand-gold/20 px-2 py-0.5 text-[11px] font-bold text-brand-navy" title={viaCampaign ? 'Tracked via campaign QR' : ''}>
                            <Megaphone size={10} /> {l.campaign_title}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-semibold text-gray-500">
                            <ScanLine size={10} /> Public QR form
                          </span>
                        )}
                        <p className="mt-1 inline-flex items-center gap-1 text-[10px] text-gray-400">
                          <MapPin size={9} /> {l.property_code}
                        </p>
                      </td>
                      <td className="px-3 py-3">
                        <p className="font-semibold text-gray-900">{l.prospect_name || '—'}</p>
                        {l.school && <p className="text-[11px] text-gray-400">{l.school}</p>}
                      </td>
                      <td className="px-3 py-3">
                        {l.prospect_phone && (
                          <p className="flex items-center gap-1 text-xs text-gray-700"><Phone size={11} className="text-gray-400" /> {l.prospect_phone}</p>
                        )}
                        {l.prospect_email && (
                          <p className="flex items-center gap-1 text-[11px] text-gray-400 mt-0.5"><Mail size={10} /> {l.prospect_email}</p>
                        )}
                        {!l.prospect_phone && !l.prospect_email && <span className="text-gray-300">—</span>}
                      </td>
                      <td className="px-3 py-3">
                        <p className="text-xs text-gray-700">{STATUS_DETAIL_LABELS[detail] || '—'}</p>
                        {l.desired_move_in_date && (
                          <p className="flex items-center gap-1 text-[11px] text-gray-400 mt-0.5">
                            <CalendarDays size={10} /> {l.desired_move_in_date}
                            {l.length_of_stay ? ` · ${LENGTH_LABELS[l.length_of_stay] || l.length_of_stay}` : ''}
                          </p>
                        )}
                      </td>
                      <td className="px-3 py-3 text-center">
                        <span className="inline-flex items-center justify-center min-w-[30px] rounded-md bg-brand-navy/10 px-1.5 py-0.5 text-xs font-bold text-brand-navy">
                          {l.lead_score ?? 0}
                        </span>
                      </td>
                      <td className="px-3 py-3"><StatusBadge status={l.status} /></td>
                      <td className="px-5 py-3 text-right">
                        <span className="text-[11px] font-bold text-brand-navy opacity-0 group-hover:opacity-100">View →</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ============ Detail drawer ============ */}
      {selected && (
        <div className="fixed inset-0 z-50">
          <div className="absolute inset-0 bg-brand-navy/40 dt-fade" onClick={() => setSelected(null)} />
          <div className="absolute right-0 top-0 h-full w-full max-w-md bg-white shadow-2xl dt-drawer-panel flex flex-col">
            {/* Drawer header */}
            <div className="relative overflow-hidden bg-brand-navy px-5 py-4 text-white">
              <div className="absolute -right-6 -top-8 w-28 h-28 rounded-full bg-brand-gold/15" />
              <div className="relative flex items-start justify-between">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-brand-gold">QR Lead</p>
                  <h3 className="text-lg font-bold leading-tight mt-0.5">{selected.prospect_name || 'Unnamed prospect'}</h3>
                  <p className="flex items-center gap-1.5 text-xs text-white/70 mt-1">
                    <Clock size={11} /> {formatDateTime(selected.created_at)} · {timeAgo(selected.created_at)}
                  </p>
                </div>
                <button onClick={() => setSelected(null)} className="p-1.5 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors">
                  <X size={18} />
                </button>
              </div>
              <div className="relative mt-2.5"><StatusBadge status={selected.status} /></div>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              {/* QR trace */}
              <section className="rounded-lg border border-brand-gold/40 bg-brand-gold/10 p-3.5">
                <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-brand-navy">
                  <QrCode size={12} /> QR Trace — where this lead came from
                </p>
                <div className="mt-2 space-y-1.5 text-xs text-gray-700">
                  <p className="flex items-center gap-1.5">
                    <Megaphone size={12} className="text-brand-navy" />
                    <span className="font-semibold">{selected.campaign_title || 'Public QR form (pre-campaign)'}</span>
                  </p>
                  <p className="flex items-center gap-1.5">
                    <MapPin size={12} className="text-brand-navy" />
                    {propertyLabel(selected.property_code)} · {selected.property_code}
                  </p>
                  <p className="flex items-center gap-1.5">
                    <ScanLine size={12} className="text-brand-navy" />
                    Submitted via {selected.inquiry_form_data?.submitted_via === 'public_qr_form' ? 'public QR form' : selected.inquiry_form_data?.submitted_via || 'QR flow'}
                    {selected.inquiry_form_data?.qr_label ? ` · "${selected.inquiry_form_data.qr_label}"` : ''}
                  </p>
                  <p className="flex items-center gap-1.5 capitalize">
                    <TrendingUp size={12} className="text-brand-navy" />
                    Source: {selected.source}
                  </p>
                </div>
              </section>

              {/* Contact */}
              <section>
                <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-gray-400 mb-2">Contact</p>
                <div className="space-y-1.5 text-sm">
                  {selected.prospect_phone && (
                    <p className="flex items-center gap-2 text-gray-800"><Phone size={14} className="text-gray-400" /> <span className="font-semibold">{selected.prospect_phone}</span></p>
                  )}
                  {selected.prospect_email && (
                    <p className="flex items-center gap-2 text-gray-800"><Mail size={14} className="text-gray-400" /> {selected.prospect_email}</p>
                  )}
                  {!selected.prospect_phone && !selected.prospect_email && <p className="text-xs text-gray-400">No contact details provided</p>}
                </div>
              </section>

              {/* Profile */}
              <section>
                <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-gray-400 mb-2">Profile</p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 text-xs">
                  <div>
                    <p className="text-gray-400">Currently a</p>
                    <p className="font-semibold text-gray-800 mt-0.5">{STATUS_DETAIL_LABELS[selected.inquiry_form_data?.status_detail] || '—'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">School / University</p>
                    <p className="font-semibold text-gray-800 mt-0.5">{selected.school || '—'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Course</p>
                    <p className="font-semibold text-gray-800 mt-0.5">{selected.course || '—'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Review Center</p>
                    <p className="font-semibold text-gray-800 mt-0.5">{selected.review_center || '—'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Desired move-in</p>
                    <p className="font-semibold text-gray-800 mt-0.5">{selected.desired_move_in_date || '—'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Length of stay</p>
                    <p className="font-semibold text-gray-800 mt-0.5">{LENGTH_LABELS[selected.length_of_stay] || selected.length_of_stay || '—'}</p>
                  </div>
                </div>
              </section>

              {/* Message */}
              <section>
                <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-gray-400 mb-2">Message</p>
                <p className="rounded-lg bg-gray-50 border border-gray-100 p-3 text-sm text-gray-700 leading-relaxed italic">
                  "{selected.content || 'No message provided'}"
                </p>
              </section>

              {/* Scores */}
              <section className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-gray-200 p-3 text-center">
                  <p className="text-xl font-extrabold text-brand-navy">{selected.lead_score ?? 0}</p>
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400 mt-0.5">Lead Score</p>
                </div>
                <div className="rounded-lg border border-gray-200 p-3 text-center">
                  <p className="text-xl font-extrabold text-brand-navy">{Number(selected.sentiment_score || 0).toFixed(2)}</p>
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400 mt-0.5">Sentiment</p>
                </div>
              </section>

              {selected.response && (
                <section>
                  <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-gray-400 mb-2">Staff Response</p>
                  <p className="rounded-lg bg-blue-50 border border-blue-100 p-3 text-sm text-blue-900 leading-relaxed">{selected.response}</p>
                </section>
              )}
            </div>

            {/* Drawer actions */}
            <div className="border-t border-gray-100 px-5 py-3.5 space-y-2 bg-gray-50/60">
              <div className="flex gap-2">
                {selected.status === 'new' && (
                  <Button size="sm" variant="success" onClick={() => handleRespond(selected)} loading={acting} className="flex-1">
                    <Send className="w-3.5 h-3.5 mr-1" /> Auto-Respond
                  </Button>
                )}
                {(selected.status === 'new' || selected.status === 'responded') && (
                  <Button size="sm" variant="danger" onClick={() => handleEscalate(selected)} loading={acting} className="flex-1">
                    <AlertTriangle className="w-3.5 h-3.5 mr-1" /> Escalate
                  </Button>
                )}
              </div>
              {selected.status !== 'converted' && selected.status !== 'closed' && (
                <Button onClick={() => handleConvert(selected)} className="w-full">
                  <BedSingle className="w-4 h-4 mr-2" /> Convert to Reservation
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
