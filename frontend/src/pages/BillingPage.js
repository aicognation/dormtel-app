import React, { useEffect, useState, useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import { Plus, Zap, CheckCircle, Send, RefreshCw, Upload, Download, Eye, ArrowLeft, Save } from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import FormField from '../components/ui/FormField';
import StatusBadge from '../components/ui/StatusBadge';
import {
  listBillings, submitMeterReading, generateBilling, approveBilling, distributeBilling,
  downloadMeterReadingTemplate, uploadMeterReadings, uploadDailyMeterSheet, listMeterReadings, previewBilling,
  getDailyMeterGrid, bulkUpsertMeterReadings,
} from '../api/billing';
import { generateStatements, listStatements, downloadStatement, sendStatementEmail } from '../api/statements';
import { listResidents } from '../api/residents';
import { listRooms } from '../api/onboarding';
import { BILLING_STATUSES } from '../utils/constants';
import { formatCurrency, formatDate, formatDateTime, shortUUID } from '../utils/formatters';

export default function BillingPage() {
  const [tab, setTab] = useState('billings');

  // Billings tab state
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: '', resident_id: '' });

  // Meter readings tab state
  const [meterReadings, setMeterReadings] = useState([]);
  const [meterLoading, setMeterLoading] = useState(false);

  // Daily grid state
  const [gridYear, setGridYear] = useState(new Date().getFullYear());
  const [gridMonth, setGridMonth] = useState(new Date().getMonth() + 1);
  const [gridBuilding, setGridBuilding] = useState('');
  const [gridData, setGridData] = useState(null);
  const [gridLoading, setGridLoading] = useState(false);
  const [editedCells, setEditedCells] = useState({});
  const [savingGrid, setSavingGrid] = useState(false);
  const [waterBill, setWaterBill] = useState('');
  const [showMiscCharges, setShowMiscCharges] = useState(true);
  const [showSummaryCols, setShowSummaryCols] = useState(true);

  // Preview billing tab state
  const [genForm, setGenForm] = useState({ billing_period: '', building: '', other_charges: '', total_water_bill: '' });
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Statements tab state
  const [statements, setStatements] = useState([]);
  const [statementsLoading, setStatementsLoading] = useState(false);
  const [showStatementModal, setShowStatementModal] = useState(false);
  const [statementForm, setStatementForm] = useState({
    billing_period: '',
    scope_type: 'resident',
    scope_target: '',
    total_water_bill: '',
    other_charges: '',
    regenerate: false,
    auto_send_email: false,
    email_subject: '',
    email_body: '',
  });
  const [residents, setResidents] = useState([]);
  const [statementGenerating, setStatementGenerating] = useState(false);

  // Rooms for meter reading modal
  const [rooms, setRooms] = useState([]);

  // Modals
  const [showMeter, setShowMeter] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [meterForm, setMeterForm] = useState({ building: '', room_id: '', resident_id: '', reading_date: '', electric_reading: '', water_reading: '' });
  const fileInputRef = useRef(null);
  const dailySheetInputRef = useRef(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.resident_id) params.resident_id = filters.resident_id;
      const result = await listBillings(params);
      setData(Array.isArray(result) ? result : []);
    } catch (err) {
      toast.error('Failed to load billings');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const fetchMeterReadings = useCallback(async () => {
    setMeterLoading(true);
    try {
      const result = await listMeterReadings({ limit: 500 });
      setMeterReadings(result);
    } catch {
      toast.error('Failed to load meter readings');
    } finally {
      setMeterLoading(false);
    }
  }, []);

  const fetchDailyGrid = useCallback(async () => {
    setGridLoading(true);
    try {
      const result = await getDailyMeterGrid({
        year: gridYear,
        month: gridMonth,
        building: gridBuilding || undefined,
      });
      setGridData(result);
      setEditedCells({});
    } catch {
      toast.error('Failed to load daily meter grid');
    } finally {
      setGridLoading(false);
    }
  }, [gridYear, gridMonth, gridBuilding]);

  const fetchRooms = useCallback(async () => {
    try {
      const result = await listRooms();
      setRooms(result || []);
    } catch {
      // silently fail
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (tab === 'meter-readings') {
      fetchDailyGrid();
    }
  }, [tab, fetchDailyGrid]);

  useEffect(() => {
    fetchRooms();
  }, [fetchRooms]);

  const fetchStatements = useCallback(async () => {
    setStatementsLoading(true);
    try {
      const result = await listStatements({ limit: 100 });
      setStatements(Array.isArray(result) ? result : []);
    } catch {
      toast.error('Failed to load statements');
      setStatements([]);
    } finally {
      setStatementsLoading(false);
    }
  }, []);

  const fetchResidents = useCallback(async () => {
    try {
      const result = await listResidents({ status: 'active' });
      setResidents(Array.isArray(result) ? result : []);
    } catch {
      // silently fail
    }
  }, []);

  useEffect(() => {
    if (tab === 'statements') {
      fetchStatements();
      if (residents.length === 0) fetchResidents();
    }
  }, [tab, fetchStatements, fetchResidents, residents.length]);

  const handleMeterSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        ...meterForm,
        room_id: meterForm.room_id || null,
        resident_id: meterForm.resident_id || null,
        electric_reading: meterForm.electric_reading ? Number(meterForm.electric_reading) : null,
        water_reading: meterForm.water_reading ? Number(meterForm.water_reading) : null,
      };
      const result = await submitMeterReading(payload);
      toast.success(`Meter reading submitted (variance: ${result?.variance_pct ?? 'N/A'}%)`);
      setShowMeter(false);
      setMeterForm({ building: '', room_id: '', resident_id: '', reading_date: '', electric_reading: '', water_reading: '' });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to submit meter reading';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handlePreview = async (e) => {
    e.preventDefault();
    setPreviewLoading(true);
    try {
      const payload = {
        billing_period: genForm.billing_period,
        building: genForm.building || undefined,
        other_charges: Number(genForm.other_charges || 0),
        total_water_bill: Number(genForm.total_water_bill || 0),
      };
      const result = await previewBilling(payload);
      setPreviewData(result);
      toast.success(`Preview ready for ${result.total_residents} residents`);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to generate preview';
      toast.error(msg);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleGenerate = async () => {
    setSubmitting(true);
    try {
      const payload = {
        billing_period: genForm.billing_period,
        building: genForm.building || undefined,
        other_charges: Number(genForm.other_charges || 0),
        total_water_bill: Number(genForm.total_water_bill || 0),
      };
      const result = await generateBilling(payload);
      toast.success(`Generated ${result.length} billing(s)`);
      setGenForm({ billing_period: '', building: '', other_charges: '', total_water_bill: '' });
      setPreviewData(null);
      setTab('billings');
      fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to generate billings';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleGenerateStatements = async (e) => {
    e.preventDefault();
    if (!statementForm.billing_period) {
      toast.error('Billing period is required');
      return;
    }
    setStatementGenerating(true);
    try {
      const payload = {
        billing_period: statementForm.billing_period,
        scope_type: statementForm.scope_type,
        scope_target: statementForm.scope_target || undefined,
        total_water_bill: Number(statementForm.total_water_bill || 0),
        other_charges: Number(statementForm.other_charges || 0),
        regenerate: statementForm.regenerate,
        auto_send_email: statementForm.auto_send_email,
        email_subject: statementForm.email_subject || undefined,
        email_body: statementForm.email_body || undefined,
      };
      const result = await generateStatements(payload);
      toast.success(`Generated ${result.generated} statement(s)${result.skipped ? `, skipped ${result.skipped}` : ''}`);
      setShowStatementModal(false);
      setStatementForm({
        billing_period: '',
        scope_type: 'resident',
        scope_target: '',
        total_water_bill: '',
        other_charges: '',
        regenerate: false,
        auto_send_email: false,
        email_subject: '',
        email_body: '',
      });
      fetchStatements();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to generate statements';
      toast.error(msg);
    } finally {
      setStatementGenerating(false);
    }
  };

  const handleDownloadStatement = async (statement) => {
    try {
      const res = await downloadStatement(statement.statement_id);
      const blob = new Blob([res], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = statement.file_name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error('Failed to download statement');
    }
  };

  const handleSendStatementEmail = async (statement) => {
    try {
      const result = await sendStatementEmail(statement.statement_id, {});
      if (result.status?.startsWith('sent_')) {
        toast.success('Statement email sent');
      } else {
        toast.error(`Email status: ${result.status}`);
      }
      fetchStatements();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to send statement email';
      toast.error(msg);
    }
  };

  const handleApprove = async (id) => {
    try {
      await approveBilling(id);
      toast.success('Billing approved');
      fetchData();
    } catch { /* interceptor */ }
  };

  const handleDistribute = async (id) => {
    try {
      await distributeBilling(id);
      toast.success('Billing distributed with payment link');
      fetchData();
    } catch { /* interceptor */ }
  };

  const handleDownloadTemplate = async () => {
    try {
      const res = await downloadMeterReadingTemplate();
      const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'meter_reading_template.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success('Template downloaded');
    } catch {
      toast.error('Failed to download template');
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const res = await uploadMeterReadings(file);
      toast.success(res.message || `Uploaded ${res.imported} readings`);
      e.target.value = '';
      if (tab === 'meter-readings') fetchDailyGrid();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to upload meter readings';
      toast.error(msg);
    }
  };

  const handleDailySheetUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const res = await uploadDailyMeterSheet(file);
      toast.success(res.message || `Uploaded daily sheet for ${res.building}`);
      e.target.value = '';
      // Auto-switch to meter-readings tab and refresh grid
      setTab('meter-readings');
      // Small delay to ensure tab switch, then fetch
      setTimeout(() => fetchDailyGrid(), 100);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to upload daily meter sheet';
      toast.error(msg);
    }
  };

  const handleCellChange = (residentId, dateKey, value) => {
    setEditedCells((prev) => ({
      ...prev,
      [`${residentId}|${dateKey}`]: { resident_id: residentId, reading_date: dateKey, electric_reading: value === '' ? null : Number(value) },
    }));
  };

  const handleSaveGrid = async () => {
    const edits = Object.values(editedCells);
    if (edits.length === 0) {
      toast('No changes to save');
      return;
    }
    setSavingGrid(true);
    try {
      // Build payload with building from grid context
      const payload = edits.map((e) => ({
        building: gridBuilding || 'DT01',
        resident_id: e.resident_id,
        reading_date: e.reading_date,
        electric_reading: e.electric_reading,
        water_reading: null,
      }));
      await bulkUpsertMeterReadings(payload);
      toast.success(`Saved ${payload.length} reading(s)`);
      setEditedCells({});
      fetchDailyGrid();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to save readings';
      toast.error(msg);
    } finally {
      setSavingGrid(false);
    }
  };

  const getDaysArray = () => {
    if (!gridData) return [];
    const days = [];
    for (let d = 1; d <= gridData.days_in_month; d++) {
      days.push(d);
    }
    return days;
  };

  const formatDateKey = (year, month, day) => {
    const m = String(month).padStart(2, '0');
    const d = String(day).padStart(2, '0');
    return `${year}-${m}-${d}`;
  };

  // Merge residents + vacant beds, grouped by room
  const getAllGridRows = () => {
    if (!gridData) return [];
    const allRows = [];
    const roomGroups = {};
    const roomOrder = [];
    (gridData.residents || []).forEach((r) => {
      const room = r.room_number || '??';
      if (!roomGroups[room]) { roomGroups[room] = []; roomOrder.push(room); }
      roomGroups[room].push({ ...r, _type: 'resident' });
    });
    (gridData.vacant_beds || []).forEach((vb) => {
      const room = vb.room_number || '??';
      if (!roomGroups[room]) { roomGroups[room] = []; roomOrder.push(room); }
      roomGroups[room].push({ ...vb, _type: 'vacant' });
    });
    roomOrder.sort((a, b) => {
      if (a === '??') return 1;
      if (b === '??') return -1;
      return a.localeCompare(b, undefined, { numeric: true });
    });
    roomOrder.forEach((room) => {
      const beds = roomGroups[room].sort((a, b) => {
        if (a._type !== b._type) return a._type === 'resident' ? -1 : 1;
        return (a.bed_letter || 'ZZ').localeCompare(b.bed_letter || 'ZZ');
      });
      beds.forEach((row, i) => {
        allRows.push({ ...row, _room: room, _isFirstInRoom: i === 0 });
      });
    });
    return allRows;
  };

  // Check if any resident has misc charges
  const hasMiscData = () => {
    if (!gridData) return false;
    return (gridData.residents || []).some((r) => r.misc_charges && Object.keys(r.misc_charges).length > 0);
  };

  // Check if any resident has import summary data
  const hasImportData = () => {
    if (!gridData) return false;
    return (gridData.residents || []).some((r) => r.total_electric_usage != null || r.elec_bill != null);
  };

  const billingColumns = [
    { key: 'billing_period', label: 'Period', render: (r) => <span className="font-medium">{r.billing_period}</span> },
    {
      key: 'resident_name',
      label: 'Resident',
      render: (r) => (
        <div className="flex flex-col">
          <span className="font-medium">{r.resident_name || shortUUID(r.resident_id)}</span>
          {r.bed_code && <span className="text-xs text-gray-500">{r.bed_code}</span>}
        </div>
      ),
    },
    { key: 'rent_amount', label: 'Rent', render: (r) => formatCurrency(r.rent_amount) },
    { key: 'electric_charge', label: 'Electric', render: (r) => formatCurrency(r.electric_charge) },
    { key: 'water_charge', label: 'Water', render: (r) => formatCurrency(r.water_charge) },
    { key: 'total_amount', label: 'Total', render: (r) => <span className="font-bold">{formatCurrency(r.total_amount)}</span> },
    { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    {
      key: 'actions',
      label: 'Actions',
      render: (r) => (
        <div className="flex gap-1">
          {(r.status === 'draft' || r.status === 'pending_review') && (
            <Button size="sm" variant="success" onClick={(e) => { e.stopPropagation(); handleApprove(r.id); }}>
              <CheckCircle className="w-3 h-3 mr-1" /> Approve
            </Button>
          )}
          {r.status === 'approved' && (
            <Button size="sm" variant="primary" onClick={(e) => { e.stopPropagation(); handleDistribute(r.id); }}>
              <Send className="w-3 h-3 mr-1" /> Distribute
            </Button>
          )}
        </div>
      ),
    },
  ];

  const meterColumns = [
    { key: 'building', label: 'Building', render: (r) => <span className="font-medium">{r.building}</span> },
    { key: 'room_number', label: 'Room', render: (r) => r.room_number ?? '-' },
    { key: 'resident_name', label: 'Resident', render: (r) => r.resident_name ?? '-' },
    { key: 'reading_date', label: 'Reading Date', render: (r) => formatDate(r.reading_date) },
    { key: 'electric_reading', label: 'Electric (kWh)', render: (r) => r.electric_reading ?? '-' },
    { key: 'water_reading', label: 'Water (m³)', render: (r) => r.water_reading ?? '-' },
    { key: 'variance_pct', label: 'Variance %', render: (r) => r.variance_pct != null ? `${Number(r.variance_pct).toFixed(2)}%` : '-' },
    { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status} /> },
  ];

  const previewColumns = [
    { key: 'resident_name', label: 'Resident', render: (r) => <span className="font-medium">{r.resident_name}</span> },
    { key: 'room_number', label: 'Room', render: (r) => r.room_number ?? '-' },
    { key: 'bed_code', label: 'Bed', render: (r) => r.bed_code ?? '-' },
    { key: 'rent_amount', label: 'Rent', render: (r) => formatCurrency(r.rent_amount) },
    { key: 'electric_charge', label: 'Electric', render: (r) => formatCurrency(r.electric_charge) },
    { key: 'water_charge', label: 'Water', render: (r) => formatCurrency(r.water_charge) },
    { key: 'other_charges', label: 'Other', render: (r) => formatCurrency(r.other_charges) },
    { key: 'total_amount', label: 'Total', render: (r) => <span className="font-bold">{formatCurrency(r.total_amount)}</span> },
  ];

  return (
    <div>
      <PageHeader
        title="Auto-Billing Engine"
        subtitle="Meter readings, billing generation, and distribution"
        actions={
          <div className="flex gap-2 flex-wrap">
            <Button variant="ghost" onClick={handleDownloadTemplate}>
              <Download className="w-4 h-4 mr-1" /> Template
            </Button>
            <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
              <Upload className="w-4 h-4 mr-1" /> Upload
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              onChange={handleFileUpload}
            />
            <Button variant="secondary" onClick={() => dailySheetInputRef.current?.click()}>
              <Upload className="w-4 h-4 mr-1" /> Daily Sheet
            </Button>
            <input
              ref={dailySheetInputRef}
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              onChange={handleDailySheetUpload}
            />
            <Button variant="secondary" onClick={() => setShowMeter(true)}>
              <Zap className="w-4 h-4 mr-1" /> Meter Reading
            </Button>
            <Button variant="secondary" onClick={() => { setTab('preview-billing'); setPreviewData(null); }}>
              <Plus className="w-4 h-4 mr-1" /> Preview Billing
            </Button>
            <Button onClick={() => { setTab('statements'); setShowStatementModal(true); }}>
              <Plus className="w-4 h-4 mr-1" /> Generate Statements
            </Button>
          </div>
        }
      />

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-4">
        {[
          { key: 'billings', label: 'Billings' },
          { key: 'meter-readings', label: 'Meter Readings' },
          { key: 'preview-billing', label: 'Preview Billing' },
          { key: 'statements', label: 'Statements' },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Billings Tab */}
      {tab === 'billings' && (
        <>
          <div className="flex flex-wrap gap-3 mb-4">
            <select
              value={filters.status}
              onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              {BILLING_STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
            <input
              type="text"
              placeholder="Filter by Resident ID..."
              value={filters.resident_id}
              onChange={(e) => setFilters((f) => ({ ...f, resident_id: e.target.value }))}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm w-64"
            />
            <Button variant="ghost" onClick={fetchData}><RefreshCw className="w-4 h-4" /></Button>
          </div>
          <DataTable columns={billingColumns} data={data} loading={loading} emptyMessage="No billings found" />
        </>
      )}

      {/* Meter Readings Tab */}
      {tab === 'meter-readings' && (
        <div className="space-y-4">
          {/* Controls */}
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Year</label>
              <input
                type="number"
                value={gridYear}
                onChange={(e) => setGridYear(Number(e.target.value))}
                className="rounded-md border border-gray-300 px-3 py-2 text-sm w-24"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Month</label>
              <select
                value={gridMonth}
                onChange={(e) => setGridMonth(Number(e.target.value))}
                className="rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>
                    {new Date(2000, i, 1).toLocaleString('default', { month: 'long' })}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Building</label>
              <select
                value={gridBuilding}
                onChange={(e) => setGridBuilding(e.target.value)}
                className="rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="">All</option>
                {Array.from(new Set((rooms || []).map((r) => r.building).filter(Boolean))).sort().map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </div>
            <Button variant="secondary" onClick={fetchDailyGrid}>
              <RefreshCw className="w-4 h-4 mr-1" /> Load Grid
            </Button>
            <Button onClick={handleSaveGrid} loading={savingGrid}>
              <Save className="w-4 h-4 mr-1" /> Save Changes
            </Button>
          </div>

          {/* Water Config */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h4 className="text-sm font-semibold text-blue-800 mb-2">Water Billing Configuration</h4>
            <div className="flex flex-wrap items-center gap-4">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Total SOGO Water Bill (₱)</label>
                <input
                  type="number"
                  value={waterBill}
                  onChange={(e) => setWaterBill(e.target.value)}
                  placeholder="e.g. 50000"
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm w-40"
                />
              </div>
              {gridData && gridData.residents.length > 0 && (
                <div className="text-sm text-gray-700">
                  <span className="font-medium">{gridData.residents.length}</span> active dormers
                  <span className="mx-2">|</span>
                  <span className="font-medium">
                    {gridData.residents.reduce((sum, r) => sum + r.days_in_month, 0)}
                  </span> total days
                </div>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Water charge per dormer = (Days stayed × Total Water Bill) ÷ Total days of all dormers
            </p>
          </div>

          {/* Import Status Banner */}
          {gridData?.import_info && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-3 text-sm">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
              <div className="flex-1">
                <span className="font-medium text-green-800">Daily sheet imported</span>
                <span className="text-green-700 ml-2">
                  {gridData.import_info.resident_count} residents from <b>{gridData.import_info.source_filename}</b>
                </span>
                <span className="text-green-600 ml-2 text-xs">
                  ({formatDateTime(gridData.import_info.imported_at)})
                </span>
              </div>
            </div>
          )}

          {/* Summary toggle */}
          {hasImportData() && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowSummaryCols(!showSummaryCols)}
                className="text-xs text-blue-600 hover:text-blue-800 underline"
              >
                {showSummaryCols ? 'Hide' : 'Show'} Computed Charges
              </button>
              <span className="text-xs text-gray-400">|</span>
              <span className="text-xs text-gray-500">
                {gridData.residents.length} active residents
                {(gridData.vacant_beds || []).length > 0 && `, ${gridData.vacant_beds.length} vacant beds`}
              </span>
            </div>
          )}

          {/* Enhanced Daily Grid */}
          {gridLoading ? (
            <div className="text-center py-8 text-gray-500">Loading grid...</div>
          ) : gridData && gridData.residents.length === 0 && !(gridData.vacant_beds || []).length ? (
            <div className="text-center py-8 text-gray-500">No active residents found for this period.</div>
          ) : gridData ? (
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="overflow-x-auto" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
                <table className="border-collapse text-xs w-full">
                  <thead className="sticky top-0 z-20">
                    <tr className="bg-slate-50">
                      {/* Zone 1: Identity (frozen left) */}
                      <th className="px-2 py-2.5 text-left font-semibold text-slate-600 border-r border-slate-200 border-b-2 border-b-slate-300 sticky left-0 bg-slate-50 z-30 w-[56px]">Room</th>
                      <th className="px-1.5 py-2.5 text-center font-semibold text-slate-600 border-r border-slate-200 border-b-2 border-b-slate-300 sticky left-[56px] bg-slate-50 z-30 w-[36px]">Bed</th>
                      <th className="px-2 py-2.5 text-left font-semibold text-slate-600 border-r-2 border-r-slate-300 border-b-2 border-b-slate-300 sticky left-[92px] bg-slate-50 z-30 min-w-[150px]">Name</th>
                      <th className="px-2 py-2.5 text-right font-semibold text-slate-600 border-r border-slate-200 border-b-2 border-b-slate-300 w-[68px]">Rate</th>
                      <th className="px-1.5 py-2.5 text-center font-semibold text-slate-600 border-r border-slate-200 border-b-2 border-b-slate-300 w-[70px]">Move In</th>
                      <th className="px-1.5 py-2.5 text-center font-semibold text-slate-600 border-r border-slate-200 border-b-2 border-b-slate-300 w-[70px]">Move Out</th>
                      <th className="px-1.5 py-2.5 text-center font-semibold text-slate-600 border-r-2 border-r-slate-300 border-b-2 border-b-slate-300 w-[36px]">Days</th>
                      {/* Zone 2: Date columns (scrollable) */}
                      {getDaysArray().map((d) => (
                        <th key={d} className="px-0.5 py-2.5 text-center font-medium text-slate-500 border-r border-gray-100 border-b-2 border-b-slate-300 min-w-[46px]">
                          {d}
                        </th>
                      ))}
                      {/* Zone 3: Summary columns (frozen right) */}
                      {showSummaryCols && (
                        <>
                          <th className="px-1.5 py-2.5 text-center font-semibold text-amber-700 border-l-2 border-l-amber-300 border-r border-amber-100 border-b-2 border-b-slate-300 bg-amber-50 min-w-[60px]">Total<br/>Usage</th>
                          <th className="px-1.5 py-2.5 text-center font-semibold text-amber-700 border-r border-amber-100 border-b-2 border-b-slate-300 bg-amber-50 min-w-[52px]">₱/kWh</th>
                          <th className="px-1.5 py-2.5 text-center font-semibold text-amber-700 border-r border-amber-100 border-b-2 border-b-slate-300 bg-amber-50 min-w-[64px]">Sub<br/>Total</th>
                          <th className="px-1.5 py-2.5 text-center font-semibold text-amber-700 border-r border-amber-100 border-b-2 border-b-slate-300 bg-amber-50 min-w-[52px]">VAT</th>
                          <th className="px-1.5 py-2.5 text-center font-semibold text-amber-700 border-r border-amber-100 border-b-2 border-b-slate-300 bg-amber-50 min-w-[64px]">Elec<br/>Bill</th>
                          <th className="px-1.5 py-2.5 text-center font-semibold text-teal-700 border-l border-l-teal-200 border-r border-teal-100 border-b-2 border-b-slate-300 bg-teal-50 min-w-[40px]">Days</th>
                          <th className="px-1.5 py-2.5 text-center font-semibold text-teal-700 border-r border-teal-100 border-b-2 border-b-slate-300 bg-teal-50 min-w-[52px]">Rate</th>
                          <th className="px-1.5 py-2.5 text-center font-semibold text-teal-700 border-r border-teal-100 border-b-2 border-b-slate-300 bg-teal-50 min-w-[64px]">Water<br/>Bill</th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {getAllGridRows().map((row, idx) => {
                      const isVacant = row._type === 'vacant';
                      const roomBg = row._isFirstInRoom ? 'bg-slate-800 text-white font-bold text-center' : 'bg-slate-700 text-transparent text-center';
                      const rowEven = idx % 2 === 0;
                      const baseBg = isVacant ? 'bg-gray-50' : (rowEven ? 'bg-white' : 'bg-slate-50/40');

                      return (
                        <tr key={row._type === 'resident' ? row.resident_id : `v-${row.bed_code}`} className="group">
                          {/* Room — grouped */}
                          <td className={`px-1 py-1 border-r border-slate-200 sticky left-0 z-10 ${roomBg}`}
                              style={row._isFirstInRoom ? { writingMode: 'horizontal-tb' } : {}}>
                            {row._isFirstInRoom ? row._room : ''}
                          </td>
                          {/* Bed */}
                          <td className={`px-1.5 py-1 text-center border-r border-slate-200 sticky left-[56px] z-10 font-medium ${isVacant ? 'bg-gray-50 text-gray-300' : (rowEven ? 'bg-white text-gray-600' : 'bg-slate-50/60 text-gray-600')}`}>
                            {row.bed_letter || '-'}
                          </td>
                          {/* Name */}
                          <td className={`px-2 py-1 border-r-2 border-r-slate-300 sticky left-[92px] z-10 whitespace-nowrap ${isVacant ? 'bg-gray-50 text-gray-300 italic' : (rowEven ? 'bg-white text-gray-800' : 'bg-slate-50/60 text-gray-800')}`}>
                            {isVacant ? 'VACANT' : row.resident_name}
                          </td>
                          {/* Rate */}
                          <td className={`px-2 py-1 text-right border-r border-gray-100 ${isVacant ? 'text-gray-200' : 'text-gray-600'} ${baseBg}`}>
                            {!isVacant && row.monthly_rate ? formatCurrency(row.monthly_rate) : '-'}
                          </td>
                          {/* Move In */}
                          <td className={`px-1.5 py-1 text-center border-r border-gray-100 ${isVacant ? 'text-gray-200' : 'text-gray-400'} ${baseBg}`}>
                            {!isVacant && row.move_in_date ? formatDate(row.move_in_date) : '-'}
                          </td>
                          {/* Move Out */}
                          <td className={`px-1.5 py-1 text-center border-r border-gray-100 ${isVacant ? 'text-gray-200' : 'text-gray-400'} ${baseBg}`}>
                            {!isVacant && row.move_out_date ? formatDate(row.move_out_date) : '-'}
                          </td>
                          {/* Days */}
                          <td className={`px-1.5 py-1 text-center border-r-2 border-r-slate-300 font-medium ${isVacant ? 'text-gray-200' : 'text-gray-700'} ${baseBg}`}>
                            {!isVacant ? (row.days_in_month || 0) : '-'}
                          </td>

                          {/* Date columns */}
                          {!isVacant ? getDaysArray().map((d) => {
                            const dateKey = formatDateKey(gridYear, gridMonth, d);
                            const cell = row.readings?.[dateKey];
                            const editKey = `${row.resident_id}|${dateKey}`;
                            const editedValue = editedCells[editKey]?.electric_reading;
                            const displayValue = editedValue !== undefined ? editedValue : (cell?.electric_reading ?? '');
                            const isEdited = editedValue !== undefined;

                            return (
                              <td key={d} className={`px-0.5 py-0.5 border-r border-gray-100 ${baseBg}`}>
                                <input
                                  type="number"
                                  value={displayValue}
                                  onChange={(e) => handleCellChange(row.resident_id, dateKey, e.target.value)}
                                  className={`w-full text-center text-[11px] px-0.5 py-0.5 rounded border ${
                                    isEdited ? 'border-amber-400 bg-amber-50 font-medium' : 'border-gray-200 focus:border-blue-400 focus:bg-blue-50'
                                  }`}
                                  placeholder=""
                                  step="0.01"
                                />
                              </td>
                            );
                          }) : getDaysArray().map((d) => (
                            <td key={d} className="px-0.5 py-1 border-r border-gray-100 bg-gray-50 text-center text-gray-200">-</td>
                          ))}

                          {/* Summary columns */}
                          {showSummaryCols && (
                            <>
                              <td className={`px-1.5 py-1 text-center border-l-2 border-l-amber-300 border-r border-amber-100 font-medium ${isVacant ? 'bg-gray-50 text-gray-200' : 'bg-amber-50/50 text-gray-800'}`}>
                                {!isVacant && row.total_electric_usage != null ? Number(row.total_electric_usage).toFixed(1) : '-'}
                              </td>
                              <td className={`px-1.5 py-1 text-center border-r border-amber-100 ${isVacant ? 'bg-gray-50 text-gray-200' : 'bg-amber-50/50 text-gray-600'}`}>
                                {!isVacant && row.peso_kwh != null ? Number(row.peso_kwh).toFixed(2) : '-'}
                              </td>
                              <td className={`px-1.5 py-1 text-right border-r border-amber-100 ${isVacant ? 'bg-gray-50 text-gray-200' : 'bg-amber-50/50 text-gray-800'}`}>
                                {!isVacant && row.sub_total != null ? Number(row.sub_total).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'}
                              </td>
                              <td className={`px-1.5 py-1 text-right border-r border-amber-100 ${isVacant ? 'bg-gray-50 text-gray-200' : 'bg-amber-50/50 text-gray-600'}`}>
                                {!isVacant && row.total_with_vat != null ? Number(row.total_with_vat).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'}
                              </td>
                              <td className={`px-1.5 py-1 text-right border-r border-amber-100 font-semibold ${isVacant ? 'bg-gray-50 text-gray-200' : 'bg-amber-50/50 text-gray-900'}`}>
                                {!isVacant && row.elec_bill != null ? Number(row.elec_bill).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'}
                              </td>
                              <td className={`px-1.5 py-1 text-center border-l border-l-teal-200 border-r border-teal-100 ${isVacant ? 'bg-gray-50 text-gray-200' : 'bg-teal-50/50 text-gray-700'}`}>
                                {!isVacant && row.water_days != null ? row.water_days : '-'}
                              </td>
                              <td className={`px-1.5 py-1 text-right border-r border-teal-100 ${isVacant ? 'bg-gray-50 text-gray-200' : 'bg-teal-50/50 text-gray-600'}`}>
                                {!isVacant && row.water_rate != null ? Number(row.water_rate).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'}
                              </td>
                              <td className={`px-1.5 py-1 text-right border-r border-teal-100 font-semibold ${isVacant ? 'bg-gray-50 text-gray-200' : 'bg-teal-50/50 text-gray-900'}`}>
                                {!isVacant && row.water_bill != null ? Number(row.water_bill).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'}
                              </td>
                            </>
                          )}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

          {/* Misc Charges Sub-table */}
          {hasMiscData() && (
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => setShowMiscCharges(!showMiscCharges)}
                className="w-full flex items-center justify-between px-4 py-2 bg-amber-50 hover:bg-amber-100 transition-colors text-sm font-medium text-amber-800"
              >
                <span>Misc Charges (from daily sheet)</span>
                <span className="text-xs">{showMiscCharges ? '▼ Collapse' : '▶ Expand'}</span>
              </button>
              {showMiscCharges && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="bg-amber-50/70">
                        <th className="px-2 py-2 text-left font-semibold text-slate-600 border-r border-amber-200 w-[56px]">Room</th>
                        <th className="px-1.5 py-2 text-center font-semibold text-slate-600 border-r border-amber-200 w-[36px]">Bed</th>
                        <th className="px-2 py-2 text-left font-semibold text-slate-600 border-r-2 border-r-amber-300 min-w-[150px]">Name</th>
                        {['laundry_dorm', 'laundry', 'drinking_water', 'ice_cream', 'coffee', 'honesty_store', 'lost_keycard', 'ref_rental'].map((key) => (
                          <th key={key} className="px-2 py-2 text-center font-semibold text-amber-700 border-r border-amber-100 min-w-[70px]">
                            {key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(gridData.residents || [])
                        .filter((r) => r.misc_charges && Object.keys(r.misc_charges).length > 0)
                        .map((r, i) => (
                          <tr key={r.resident_id} className={i % 2 === 0 ? 'bg-white' : 'bg-amber-50/20'}>
                            <td className="px-2 py-1 border-r border-amber-100 font-medium text-gray-700">{r.room_number || '-'}</td>
                            <td className="px-1.5 py-1 text-center border-r border-amber-100 text-gray-600">{r.bed_letter || '-'}</td>
                            <td className="px-2 py-1 border-r-2 border-r-amber-300 whitespace-nowrap text-gray-800">{r.resident_name}</td>
                            {['laundry_dorm', 'laundry', 'drinking_water', 'ice_cream', 'coffee', 'honesty_store', 'lost_keycard', 'ref_rental'].map((key) => (
                              <td key={key} className="px-2 py-1 text-right border-r border-amber-100 text-gray-700">
                                {r.misc_charges?.[key] ? Number(r.misc_charges[key]).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Raw Meter Readings Table (optional, for reference) */}
          <div className="pt-4">
            <div className="flex justify-between items-center mb-2">
              <h4 className="text-sm font-semibold text-gray-700">Recent Uploaded Readings</h4>
              <Button variant="ghost" size="sm" onClick={fetchMeterReadings}><RefreshCw className="w-3 h-3" /></Button>
            </div>
            <DataTable columns={meterColumns} data={meterReadings} loading={meterLoading} emptyMessage="No meter readings found" />
          </div>
        </div>
      )}

      {/* Preview Billing Tab */}
      {tab === 'preview-billing' && (
        <div className="space-y-6">
          {!previewData ? (
            <div className="max-w-xl">
              <h3 className="text-lg font-semibold mb-4">Generate Billing Preview</h3>
              <p className="text-sm text-gray-500 mb-4">
                Enter the billing period. Electric is computed from per-resident daily meter readings. Water is computed from days stayed × rate derived from the total SOGO water bill.
              </p>
              <form onSubmit={handlePreview} className="space-y-4">
                <FormField label="Billing Period" name="billing_period" required value={genForm.billing_period}
                  onChange={(e) => setGenForm({ ...genForm, billing_period: e.target.value })} placeholder="e.g. 2026-05" />
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Building (optional)</label>
                  <select
                    value={genForm.building}
                    onChange={(e) => setGenForm({ ...genForm, building: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  >
                    <option value="">All buildings</option>
                    {Array.from(new Set((rooms || []).map((r) => r.building).filter(Boolean))).sort().map((b) => (
                      <option key={b} value={b}>{b}</option>
                    ))}
                  </select>
                </div>
                <FormField label="Total SOGO Water Bill (₱)" name="total_water_bill" type="number" value={genForm.total_water_bill}
                  onChange={(e) => setGenForm({ ...genForm, total_water_bill: e.target.value })}
                  placeholder="Total water consumption billed by SOGO" />
                <FormField label="Other Charges (₱)" name="other_charges" type="number" value={genForm.other_charges}
                  onChange={(e) => setGenForm({ ...genForm, other_charges: e.target.value })} />
                <div className="flex gap-2 pt-2">
                  <Button variant="secondary" type="button" onClick={() => setTab('billings')}>Cancel</Button>
                  <Button type="submit" loading={previewLoading}>
                    <Eye className="w-4 h-4 mr-1" /> Preview Billing
                  </Button>
                </div>
              </form>
            </div>
          ) : (
            <div>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold">Billing Preview</h3>
                  <p className="text-sm text-gray-500">
                    Period: <span className="font-medium">{previewData.billing_period}</span> | Building: <span className="font-medium">{previewData.building || 'All'}</span> | Residents: <span className="font-medium">{previewData.total_residents}</span>
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={() => setPreviewData(null)}>
                    <ArrowLeft className="w-4 h-4 mr-1" /> Back
                  </Button>
                  <Button onClick={handleGenerate} loading={submitting}>
                    <CheckCircle className="w-4 h-4 mr-1" /> Generate & Save
                  </Button>
                </div>
              </div>

              {/* Summary Cards */}
              {previewData.summary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  <div className="bg-white border rounded-md p-3">
                    <p className="text-xs text-gray-500">Total Rent</p>
                    <p className="text-lg font-semibold">{formatCurrency(previewData.summary.total_rent)}</p>
                  </div>
                  <div className="bg-white border rounded-md p-3">
                    <p className="text-xs text-gray-500">Total Electric</p>
                    <p className="text-lg font-semibold">{formatCurrency(previewData.summary.total_electric)}</p>
                  </div>
                  <div className="bg-white border rounded-md p-3">
                    <p className="text-xs text-gray-500">Total Water</p>
                    <p className="text-lg font-semibold">{formatCurrency(previewData.summary.total_water)}</p>
                  </div>
                  <div className="bg-white border rounded-md p-3">
                    <p className="text-xs text-gray-500">Grand Total</p>
                    <p className="text-lg font-semibold text-blue-600">{formatCurrency(previewData.summary.grand_total)}</p>
                  </div>
                </div>
              )}

              {/* Water computation summary */}
              {previewData.summary && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4 text-sm">
                  <p className="text-blue-800">
                    <span className="font-medium">Water computation:</span>{' '}
                    Total days: <span className="font-medium">{previewData.summary.total_days}</span>{' '}
                    | Rate per day: <span className="font-medium">₱{Number(previewData.summary.water_rate_per_day).toFixed(2)}</span>
                  </p>
                </div>
              )}

              <DataTable columns={previewColumns} data={previewData.rows} loading={false} emptyMessage="No residents found" />
            </div>
          )}
        </div>
      )}

      {/* Statements Tab */}
      {tab === 'statements' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold">Billing Statements</h3>
              <p className="text-sm text-gray-500">Generated PDF statements with resident, room, floor, or property scope.</p>
            </div>
            <Button onClick={() => setShowStatementModal(true)}>
              <Plus className="w-4 h-4 mr-1" /> Generate Statements
            </Button>
          </div>
          <DataTable
            columns={[
              { key: 'billing_period', label: 'Period', render: (r) => <span className="font-medium">{r.billing_period}</span> },
              {
                key: 'resident_name',
                label: 'Resident',
                render: (r) => (
                  <div className="flex flex-col">
                    <span className="font-medium">{r.resident_name}</span>
                    <span className="text-xs text-gray-500">{r.scope_type}{r.scope_target ? `: ${r.scope_target}` : ''}</span>
                  </div>
                ),
              },
              { key: 'total_amount', label: 'Total', render: (r) => formatCurrency(r.total_amount) },
              { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status} /> },
              { key: 'email_status', label: 'Email', render: (r) => r.email_status || '—' },
              { key: 'created_at', label: 'Generated', render: (r) => formatDateTime(r.created_at) },
              {
                key: 'actions',
                label: 'Actions',
                render: (r) => (
                  <div className="flex gap-1">
                    <Button size="sm" variant="secondary" onClick={() => handleDownloadStatement(r)}>
                      <Download className="w-3 h-3 mr-1" /> Download
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => handleSendStatementEmail(r)}>
                      <Send className="w-3 h-3 mr-1" /> Send
                    </Button>
                  </div>
                ),
              },
            ]}
            data={statements}
            loading={statementsLoading}
            emptyMessage="No statements generated yet"
          />
        </div>
      )}

      {/* Statement Generate Modal */}
      <Modal isOpen={showStatementModal} onClose={() => setShowStatementModal(false)} title="Generate Billing Statements">
        <form onSubmit={handleGenerateStatements} className="space-y-4">
          <FormField
            label="Billing Period"
            name="billing_period"
            required
            value={statementForm.billing_period}
            onChange={(e) => setStatementForm({ ...statementForm, billing_period: e.target.value })}
            placeholder="e.g. 2026-06"
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Scope</label>
            <select
              value={statementForm.scope_type}
              onChange={(e) => setStatementForm({ ...statementForm, scope_type: e.target.value, scope_target: '' })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="resident">Resident</option>
              <option value="room">Room</option>
              <option value="floor">Floor</option>
              <option value="property">Property / Building</option>
            </select>
          </div>
          {statementForm.scope_type === 'resident' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Resident</label>
              <select
                required
                value={statementForm.scope_target}
                onChange={(e) => setStatementForm({ ...statementForm, scope_target: e.target.value })}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="">Select resident...</option>
                {residents.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.full_name} {r.room_number ? `(${r.room_number}${r.bed_code ? ` / ${r.bed_code}` : ''})` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}
          {statementForm.scope_type === 'room' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Room</label>
              <select
                required
                value={statementForm.scope_target}
                onChange={(e) => setStatementForm({ ...statementForm, scope_target: e.target.value })}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="">Select room...</option>
                {rooms.map((r) => (
                  <option key={r.id} value={r.id}>{r.room_number} ({r.building})</option>
                ))}
              </select>
            </div>
          )}
          {statementForm.scope_type === 'floor' && (
            <FormField
              label="Floor Prefix"
              name="floor_prefix"
              required
              value={statementForm.scope_target}
              onChange={(e) => setStatementForm({ ...statementForm, scope_target: e.target.value })}
              placeholder="e.g. A1 for rooms A101-A109"
            />
          )}
          {statementForm.scope_type === 'property' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Property / Building</label>
              <select
                value={statementForm.scope_target}
                onChange={(e) => setStatementForm({ ...statementForm, scope_target: e.target.value })}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="">All properties</option>
                {Array.from(new Set((rooms || []).map((r) => r.building).filter(Boolean))).sort().map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
                {Array.from(new Set((rooms || []).map((r) => r.property_code).filter(Boolean))).sort().map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          )}
          <FormField
            label="Total SOGO Water Bill (₱)"
            name="total_water_bill"
            type="number"
            value={statementForm.total_water_bill}
            onChange={(e) => setStatementForm({ ...statementForm, total_water_bill: e.target.value })}
            placeholder="Total water bill to split by days stayed"
          />
          <FormField
            label="Other Charges (₱)"
            name="other_charges"
            type="number"
            value={statementForm.other_charges}
            onChange={(e) => setStatementForm({ ...statementForm, other_charges: e.target.value })}
          />
          <div className="flex items-center gap-2">
            <input
              id="regenerate"
              type="checkbox"
              checked={statementForm.regenerate}
              onChange={(e) => setStatementForm({ ...statementForm, regenerate: e.target.checked })}
              className="rounded border-gray-300"
            />
            <label htmlFor="regenerate" className="text-sm text-gray-700">Regenerate if statement already exists</label>
          </div>
          <div className="flex items-center gap-2">
            <input
              id="auto_send_email"
              type="checkbox"
              checked={statementForm.auto_send_email}
              onChange={(e) => setStatementForm({ ...statementForm, auto_send_email: e.target.checked })}
              className="rounded border-gray-300"
            />
            <label htmlFor="auto_send_email" className="text-sm text-gray-700">Auto-send statements via email</label>
          </div>
          {statementForm.auto_send_email && (
            <>
              <FormField
                label="Email Subject (optional)"
                name="email_subject"
                value={statementForm.email_subject}
                onChange={(e) => setStatementForm({ ...statementForm, email_subject: e.target.value })}
                placeholder="Default: DormTel Statement of Account"
              />
              <FormField
                label="Email Body (optional)"
                name="email_body"
                type="textarea"
                value={statementForm.email_body}
                onChange={(e) => setStatementForm({ ...statementForm, email_body: e.target.value })}
                placeholder="Default message will be used if blank"
              />
            </>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setShowStatementModal(false)}>Cancel</Button>
            <Button type="submit" loading={statementGenerating}>Generate Statements</Button>
          </div>
        </form>
      </Modal>

      {/* Meter Reading Modal */}
      <Modal isOpen={showMeter} onClose={() => setShowMeter(false)} title="Submit Meter Reading">
        <form onSubmit={handleMeterSubmit} className="space-y-4">
          <FormField label="Building" name="building" required value={meterForm.building}
            onChange={(e) => setMeterForm({ ...meterForm, building: e.target.value })} placeholder="e.g. DT01" />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Room (optional)</label>
            <select
              name="room_id"
              value={meterForm.room_id}
              onChange={(e) => setMeterForm({ ...meterForm, room_id: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">-- Select Room --</option>
              {rooms.map((room) => (
                <option key={room.id} value={room.id}>{room.room_number} ({room.building})</option>
              ))}
            </select>
          </div>
          <FormField label="Reading Date" name="reading_date" type="date" required value={meterForm.reading_date}
            onChange={(e) => setMeterForm({ ...meterForm, reading_date: e.target.value })} />
          <FormField label="Electric Reading (kWh)" name="electric_reading" type="number" value={meterForm.electric_reading}
            onChange={(e) => setMeterForm({ ...meterForm, electric_reading: e.target.value })} />
          <FormField label="Water Reading (m³)" name="water_reading" type="number" value={meterForm.water_reading}
            onChange={(e) => setMeterForm({ ...meterForm, water_reading: e.target.value })} />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setShowMeter(false)}>Cancel</Button>
            <Button type="submit" loading={submitting}>Submit Reading</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
