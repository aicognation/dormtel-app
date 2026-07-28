import React, { useState, useEffect, useMemo, useCallback } from 'react';
import toast from 'react-hot-toast';
import { Download, Search, Users, CalendarDays, FileSpreadsheet, Loader2 } from 'lucide-react';
import Modal from '../ui/Modal';
import Button from '../ui/Button';
import { generateMeterTemplate, getMeterTemplateRoster } from '../../api/billing';

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

function todayISO() {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${m}-${day}`;
}

function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(new Blob([blob], { type: XLSX_MIME }));
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

export default function GenerateTemplateModal({ isOpen, onClose, propertyCode }) {
  const [tab, setTab] = useState('adhoc');

  // Ad-hoc wizard state
  const [roster, setRoster] = useState([]);
  const [rosterLoading, setRosterLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(() => new Set());

  // Daily state
  const [dailyDate, setDailyDate] = useState(todayISO());
  const [dailyCount, setDailyCount] = useState(null);

  // Monthly state
  const now = new Date();
  const [mMonth, setMMonth] = useState(now.getMonth() + 1);
  const [mYear, setMYear] = useState(now.getFullYear());
  const [monthlyCount, setMonthlyCount] = useState(null);

  const [generating, setGenerating] = useState(false);

  // Load the current-active roster for the ad-hoc picker whenever the modal opens
  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    setRosterLoading(true);
    getMeterTemplateRoster({})
      .then((res) => { if (!cancelled) setRoster(res.residents || []); })
      .catch(() => { if (!cancelled) setRoster([]); })
      .finally(() => { if (!cancelled) setRosterLoading(false); });
    return () => { cancelled = true; };
  }, [isOpen]);

  // Live count for the Daily tab
  useEffect(() => {
    if (!isOpen || tab !== 'daily' || !dailyDate) return;
    let cancelled = false;
    getMeterTemplateRoster({ for_date: dailyDate })
      .then((res) => { if (!cancelled) setDailyCount(res.count); })
      .catch(() => { if (!cancelled) setDailyCount(null); });
    return () => { cancelled = true; };
  }, [isOpen, tab, dailyDate]);

  // Live count for the Monthly tab
  useEffect(() => {
    if (!isOpen || tab !== 'monthly') return;
    let cancelled = false;
    getMeterTemplateRoster({ month: mMonth, year: mYear })
      .then((res) => { if (!cancelled) setMonthlyCount(res.count); })
      .catch(() => { if (!cancelled) setMonthlyCount(null); });
    return () => { cancelled = true; };
  }, [isOpen, tab, mMonth, mYear]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return roster;
    return roster.filter((r) =>
      (r.full_name || '').toLowerCase().includes(q) ||
      (r.room_number || '').toLowerCase().includes(q) ||
      (r.bed_code || '').toLowerCase().includes(q)
    );
  }, [roster, search]);

  const grouped = useMemo(() => {
    const map = new Map();
    for (const r of filtered) {
      const key = r.room_number || '—';
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(r);
    }
    return [...map.entries()].sort((a, b) => String(a[0]).localeCompare(String(b[0]), undefined, { numeric: true }));
  }, [filtered]);

  const toggle = useCallback((id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }, []);

  const selectAll = () => setSelected(new Set(filtered.map((r) => r.id)));
  const clearAll = () => setSelected(new Set());

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      let payload;
      let filename;
      if (tab === 'adhoc') {
        if (selected.size === 0) {
          toast.error('Select at least one resident for the ad-hoc template.');
          return;
        }
        payload = { type: 'adhoc', resident_ids: [...selected] };
        filename = `METER_READINGS_ADHOC_${propertyCode}_${todayISO()}.xlsx`;
      } else if (tab === 'daily') {
        payload = { type: 'daily', date: dailyDate };
        filename = `METER_READINGS_DAILY_${propertyCode}_${dailyDate}.xlsx`;
      } else {
        payload = { type: 'monthly', month: Number(mMonth), year: Number(mYear) };
        filename = `DORMERS_ELEC_WATER_${MONTHS[mMonth - 1].toUpperCase()}_${mYear}_${propertyCode}.xlsx`;
      }
      const blob = await generateMeterTemplate(payload);
      downloadBlob(blob, filename);
      toast.success('Template downloaded — fill in the yellow cells, then upload it.');
      onClose();
    } catch {
      // The API interceptor already surfaced the specific error message.
    } finally {
      setGenerating(false);
    }
  };

  const yearOptions = [];
  for (let y = now.getFullYear(); y >= now.getFullYear() - 3; y--) yearOptions.push(y);

  const tabBtn = (key, label, icon) => (
    <button
      onClick={() => setTab(key)}
      className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
        tab === key ? 'bg-[#1F3A5F] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
    >
      {icon} {label}
    </button>
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Generate Meter Reading Template" size="lg">
      <div className="flex gap-2 mb-4 flex-wrap">
        {tabBtn('adhoc', 'Ad-hoc', <Users className="w-4 h-4" />)}
        {tabBtn('daily', 'Daily', <CalendarDays className="w-4 h-4" />)}
        {tabBtn('monthly', 'Monthly', <FileSpreadsheet className="w-4 h-4" />)}
      </div>

      {tab === 'adhoc' && (
        <div>
          <p className="text-sm text-gray-600 mb-3">
            Pick the residents to include. The template has one row per selected resident — fill in a reading date and value for each.
          </p>
          <div className="relative mb-3">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, room, or bed…"
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1F3A5F]"
            />
          </div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">{selected.size} selected</span>
            <div className="flex gap-2">
              <button onClick={selectAll} className="text-xs font-semibold text-[#1F3A5F] hover:underline">Select all ({filtered.length})</button>
              <button onClick={clearAll} className="text-xs font-semibold text-gray-500 hover:underline">Clear</button>
            </div>
          </div>
          <div className="border border-gray-200 rounded-lg max-h-72 overflow-y-auto divide-y divide-gray-100">
            {rosterLoading && (
              <div className="flex items-center justify-center py-8 text-gray-400 text-sm">
                <Loader2 className="w-4 h-4 animate-spin mr-2" /> Loading residents…
              </div>
            )}
            {!rosterLoading && grouped.length === 0 && (
              <div className="py-8 text-center text-gray-400 text-sm">No residents match your search.</div>
            )}
            {!rosterLoading && grouped.map(([room, residents]) => (
              <div key={room}>
                <div className="px-3 py-1.5 bg-gray-50 text-xs font-bold text-gray-500 sticky top-0">ROOM {room}</div>
                {residents.map((r) => (
                  <label key={r.id} className="flex items-center gap-3 px-3 py-2 hover:bg-blue-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selected.has(r.id)}
                      onChange={() => toggle(r.id)}
                      className="w-4 h-4 accent-[#1F3A5F]"
                    />
                    <span className="flex-1 text-sm text-gray-800">{r.full_name}</span>
                    <span className="text-xs text-gray-400">Bed {r.bed_letter || '—'}</span>
                  </label>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'daily' && (
        <div>
          <p className="text-sm text-gray-600 mb-3">
            One row per resident <strong>active on the chosen date</strong>, with the Reading Date pre-filled. Ideal for recording today's readings.
          </p>
          <label className="block text-sm font-medium text-gray-700 mb-1">Reading date</label>
          <input
            type="date"
            value={dailyDate}
            onChange={(e) => setDailyDate(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1F3A5F]"
          />
          <div className="mt-3 text-sm text-gray-600">
            {dailyCount === null ? 'Checking…' : (
              <>Includes <strong className="text-[#1F3A5F]">{dailyCount}</strong> resident(s) active on {dailyDate}.</>
            )}
          </div>
        </div>
      )}

      {tab === 'monthly' && (
        <div>
          <p className="text-sm text-gray-600 mb-3">
            A full grid — one row per resident who was there that month, one column per day. Use this to load a <strong>past month's</strong> readings (residents who have since moved out are included).
          </p>
          <div className="flex gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Month</label>
              <select
                value={mMonth}
                onChange={(e) => setMMonth(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1F3A5F]"
              >
                {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
              <select
                value={mYear}
                onChange={(e) => setMYear(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1F3A5F]"
              >
                {yearOptions.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
          </div>
          <div className="mt-3 text-sm text-gray-600">
            {monthlyCount === null ? 'Checking…' : (
              <>Includes <strong className="text-[#1F3A5F]">{monthlyCount}</strong> resident(s) active in {MONTHS[mMonth - 1]} {mYear}.</>
            )}
          </div>
        </div>
      )}

      <div className="flex justify-end gap-2 mt-5">
        <Button variant="ghost" onClick={onClose}>Cancel</Button>
        <Button variant="primary" onClick={handleGenerate} disabled={generating}>
          {generating ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Download className="w-4 h-4 mr-1" />}
          {generating ? 'Generating…' : 'Generate & Download'}
        </Button>
      </div>
    </Modal>
  );
}
