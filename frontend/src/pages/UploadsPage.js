import React, { useEffect, useState, useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import { RefreshCw, Upload, CheckCircle, XCircle, AlertTriangle, FileText, Users, Hash, Search, Download, Zap } from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import FormField from '../components/ui/FormField';
import GenerateTemplateModal from '../components/dashboard/GenerateTemplateModal';
import TemplatePreviewModal from '../components/dashboard/TemplatePreviewModal';
import { listUploads, getUploadStats, getUploadDetail, uploadMeterReadings, uploadDailyMeterSheet, validateMeterReadingTemplate, validateDailySheetTemplate, submitMeterReading } from '../api/billing';
import { formatDateTime } from '../utils/formatters';
import { useProperty } from '../contexts/PropertyContext';

const STATUS_COLORS = {
  accepted: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-200' },
  rejected: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-200' },
  partial: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-200' },
};

function StatusBadge({ status }) {
  const colors = STATUS_COLORS[status] || { bg: 'bg-gray-100', text: 'text-gray-800', border: 'border-gray-200' };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${colors.bg} ${colors.text} border ${colors.border}`}>
      {status || 'unknown'}
    </span>
  );
}

function KpiCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-xs text-gray-500 font-medium">{label}</p>
        <p className="text-xl font-bold text-gray-900">{value ?? '—'}</p>
      </div>
    </div>
  );
}

export default function UploadsPage() {
  const { propertyCode } = useProperty();

  // Stats
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);

  // Uploads list
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  // Filters
  const [filterProperty, setFilterProperty] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterDateFrom, setFilterDateFrom] = useState('');
  const [filterDateTo, setFilterDateTo] = useState('');
  const [filterFilename, setFilterFilename] = useState('');

  // Detail modal
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Upload actions state
  const [showGenerateTemplate, setShowGenerateTemplate] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [validationLoading, setValidationLoading] = useState(false);
  const [pendingUploadFile, setPendingUploadFile] = useState(null);
  const [pendingUploadType, setPendingUploadType] = useState(null);
  const [showMeter, setShowMeter] = useState(false);
  const [meterForm, setMeterForm] = useState({ building: '', room_id: '', resident_id: '', reading_date: '', electric_reading: '', water_reading: '' });
  const [submitting, setSubmitting] = useState(false);
  const fileInputRef = useRef(null);
  const dailySheetInputRef = useRef(null);

  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const result = await getUploadStats({ property_code: filterProperty || undefined });
      setStats(result);
    } catch {
      toast.error('Failed to load upload stats');
    } finally {
      setStatsLoading(false);
    }
  }, [filterProperty]);

  const fetchUploads = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (filterProperty) params.property_code = filterProperty;
      if (filterStatus) params.status = filterStatus;
      if (filterDateFrom) params.date_from = filterDateFrom;
      if (filterDateTo) params.date_to = filterDateTo;
      if (filterFilename) params.filename = filterFilename;

      const result = await listUploads(params);
      setUploads(Array.isArray(result) ? result : (result?.items || []));
      setTotalCount(result?.total ?? result?.length ?? 0);
    } catch {
      toast.error('Failed to load uploads');
      setUploads([]);
    } finally {
      setLoading(false);
    }
  }, [page, filterProperty, filterStatus, filterDateFrom, filterDateTo, filterFilename]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  useEffect(() => {
    fetchUploads();
  }, [fetchUploads]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [filterProperty, filterStatus, filterDateFrom, filterDateTo, filterFilename]);

  const handleRowClick = async (row) => {
    setDetailOpen(true);
    setDetailLoading(true);
    setDetailData(null);
    try {
      const result = await getUploadDetail(row.id);
      setDetailData(result);
    } catch {
      toast.error('Failed to load upload detail');
    } finally {
      setDetailLoading(false);
    }
  };

  const rejectionRate = stats?.total_uploads > 0
    ? ((stats.rejected / stats.total_uploads) * 100).toFixed(1) + '%'
    : '0%';

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    e.target.value = '';
    setValidationLoading(true);
    try {
      const result = await validateMeterReadingTemplate(file);
      setValidationResult(result);
      setPendingUploadFile(file);
      setPendingUploadType('standard');
      setShowPreviewModal(true);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to validate file';
      toast.error(msg);
    } finally {
      setValidationLoading(false);
    }
  };

  const handleDailySheetUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    e.target.value = '';
    setValidationLoading(true);
    try {
      const result = await validateDailySheetTemplate(file);
      setValidationResult(result);
      setPendingUploadFile(file);
      setPendingUploadType('daily_sheet');
      setShowPreviewModal(true);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to validate file';
      toast.error(msg);
    } finally {
      setValidationLoading(false);
    }
  };

  const handleProceedWithUpload = async () => {
    if (!pendingUploadFile) return;
    setSubmitting(true);
    try {
      if (pendingUploadType === 'standard') {
        const res = await uploadMeterReadings(pendingUploadFile);
        if ((res.imported ?? 0) === 0) {
          toast.error(
            `No readings were imported (${res.skipped ?? 0} row(s) skipped). ` +
            'Fill in the Reading Date (YYYY-MM-DD) and at least one reading value ' +
            '(Electric or Water) for each row, then upload again.',
            { duration: 9000 }
          );
        } else {
          toast.success(res.message || `Uploaded ${res.imported} readings`);
        }
        if (res.errors && res.errors.length > 0) {
          res.errors.forEach((err) => toast.error(err, { duration: 6000 }));
        }
      } else {
        const res = await uploadDailyMeterSheet(pendingUploadFile);
        if ((res.residents_imported ?? 0) === 0) {
          toast.error(
            'No residents matched this file. Make sure the correct property is selected ' +
            'and the file lists that property\'s residents.',
            { duration: 9000 }
          );
        } else if ((res.daily_readings_imported ?? 0) === 0) {
          toast.error(
            `Matched ${res.residents_imported} resident(s) but imported 0 daily readings. ` +
            'The date columns are empty — type the meter value for each day ' +
            '(the yellow cells) before uploading.',
            { duration: 9000 }
          );
        } else {
          toast.success(res.message || `Uploaded daily sheet for ${res.building}`);
        }
        if (res.errors && res.errors.length > 0) {
          res.errors.forEach((err) => toast.error(err, { duration: 6000 }));
        }
      }
      setShowPreviewModal(false);
      setPendingUploadFile(null);
      setValidationResult(null);
      // Refresh uploads list and stats
      fetchUploads();
      fetchStats();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Upload failed';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

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
      // Refresh uploads list and stats
      fetchUploads();
      fetchStats();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to submit meter reading';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const columns = [
    {
      key: 'created_at',
      label: 'Date',
      render: (r) => <span className="text-sm">{formatDateTime(r.created_at)}</span>,
    },
    {
      key: 'source_filename',
      label: 'Filename',
      render: (r) => (
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
          <span className="text-sm font-medium truncate max-w-[200px]" title={r.source_filename}>
            {r.source_filename || '—'}
          </span>
        </div>
      ),
    },
    {
      key: 'property_code',
      label: 'Property',
      render: (r) => <span className="text-sm font-medium">{r.property_code || '—'}</span>,
    },
    {
      key: 'uploaded_by',
      label: 'Uploader',
      render: (r) => <span className="text-sm">{r.uploaded_by_name || r.uploaded_by || '—'}</span>,
    },
    {
      key: 'upload_type',
      label: 'Type',
      render: (r) => <span className="text-sm">{r.upload_type || '—'}</span>,
    },
    {
      key: 'billing_period',
      label: 'Period',
      render: (r) => <span className="text-sm">{r.billing_period || r.period_label || '—'}</span>,
    },
    {
      key: 'status',
      label: 'Status',
      render: (r) => <StatusBadge status={r.status} />,
    },
    {
      key: 'total_residents',
      label: 'Residents',
      render: (r) => <span className="text-sm">{r.total_residents ?? '—'}</span>,
    },
    {
      key: 'total_readings',
      label: 'Readings',
      render: (r) => <span className="text-sm">{r.total_readings ?? '—'}</span>,
    },
    {
      key: 'result_summary',
      label: 'Result',
      render: (r) => (
        <span className="text-sm text-gray-600 truncate max-w-[150px]" title={r.result_summary || ''}>
          {r.result_summary || (r.status === 'accepted' ? 'OK' : r.status === 'rejected' ? 'Failed' : '—')}
        </span>
      ),
    },
  ];

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div>
      <PageHeader
        title="Upload Monitor"
        subtitle="Track meter reading uploads, validation results, and import history"
        actions={
          <Button variant="ghost" onClick={() => { fetchStats(); fetchUploads(); }}>
            <RefreshCw className="w-4 h-4 mr-1" /> Refresh
          </Button>
        }
      />

      {/* Upload Actions */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 mb-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Upload Meter Readings</h3>
        <div className="flex flex-wrap gap-2">
          <Button variant="ghost" size="sm" onClick={() => setShowGenerateTemplate(true)}>
            <Download className="w-4 h-4 mr-1" /> Generate Template
          </Button>
          <Button variant="secondary" size="sm" onClick={() => fileInputRef.current?.click()}>
            <Upload className="w-4 h-4 mr-1" /> Ad-hoc / Daily Upload
          </Button>
          <input ref={fileInputRef} type="file" accept=".xlsx,.xls" className="hidden" onChange={handleFileUpload} />
          <Button variant="secondary" size="sm" onClick={() => dailySheetInputRef.current?.click()}>
            <Upload className="w-4 h-4 mr-1" /> Monthly Grid Upload
          </Button>
          <input ref={dailySheetInputRef} type="file" accept=".xlsx,.xls" className="hidden" onChange={handleDailySheetUpload} />
          <Button variant="secondary" size="sm" onClick={() => setShowMeter(true)}>
            <Zap className="w-4 h-4 mr-1" /> Single Meter Reading
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        <KpiCard
          icon={Upload}
          label="Total Uploads"
          value={statsLoading ? '...' : stats?.total_uploads ?? 0}
          color="bg-[#1F3A5F]"
        />
        <KpiCard
          icon={CheckCircle}
          label="Accepted"
          value={statsLoading ? '...' : stats?.accepted ?? 0}
          color="bg-green-600"
        />
        <KpiCard
          icon={XCircle}
          label="Rejected"
          value={statsLoading ? '...' : stats?.rejected ?? 0}
          color="bg-red-600"
        />
        <KpiCard
          icon={AlertTriangle}
          label="Rejection Rate"
          value={statsLoading ? '...' : rejectionRate}
          color="bg-yellow-500"
        />
        <KpiCard
          icon={Hash}
          label="Total Readings"
          value={statsLoading ? '...' : stats?.total_readings ?? 0}
          color="bg-blue-600"
        />
        <KpiCard
          icon={Users}
          label="Total Residents"
          value={statsLoading ? '...' : stats?.total_residents ?? 0}
          color="bg-purple-600"
        />
      </div>

      {/* Filters Row */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Property</label>
            <select
              value={filterProperty}
              onChange={(e) => setFilterProperty(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1F3A5F]"
            >
              <option value="">All</option>
              <option value="DT01">DT01</option>
              <option value="DT02">DT02</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Status</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1F3A5F]"
            >
              <option value="">All</option>
              <option value="accepted">Accepted</option>
              <option value="rejected">Rejected</option>
              <option value="partial">Partial</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">From</label>
            <input
              type="date"
              value={filterDateFrom}
              onChange={(e) => setFilterDateFrom(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1F3A5F]"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">To</label>
            <input
              type="date"
              value={filterDateTo}
              onChange={(e) => setFilterDateTo(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1F3A5F]"
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">Filename</label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={filterFilename}
                onChange={(e) => setFilterFilename(e.target.value)}
                placeholder="Search by filename..."
                className="w-full pl-9 pr-3 py-2 rounded-md border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#1F3A5F]"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <DataTable
        columns={columns}
        data={uploads}
        loading={loading}
        emptyMessage="No uploads yet"
        onRowClick={handleRowClick}
      />

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-gray-500">
            Showing {((page - 1) * pageSize) + 1}–{Math.min(page * pageSize, totalCount)} of {totalCount}
          </p>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const startPage = Math.max(1, Math.min(page - 2, totalPages - 4));
              const pageNum = startPage + i;
              if (pageNum > totalPages) return null;
              return (
                <Button
                  key={pageNum}
                  variant={pageNum === page ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setPage(pageNum)}
                >
                  {pageNum}
                </Button>
              );
            })}
            <Button
              variant="ghost"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      <Modal
        isOpen={detailOpen}
        onClose={() => { setDetailOpen(false); setDetailData(null); }}
        title="Upload Detail"
        size="lg"
      >
        {detailLoading ? (
          <div className="flex items-center justify-center py-12 text-gray-400">
            <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading detail...
          </div>
        ) : detailData ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-gray-500 font-medium">Filename</p>
                <p className="text-sm font-semibold text-gray-900">{detailData.source_filename || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 font-medium">Property</p>
                <p className="text-sm font-semibold text-gray-900">{detailData.property_code || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 font-medium">Uploader</p>
                <p className="text-sm text-gray-900">{detailData.uploaded_by_name || detailData.uploaded_by || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 font-medium">Upload Type</p>
                <p className="text-sm text-gray-900">{detailData.upload_type || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 font-medium">Period</p>
                <p className="text-sm text-gray-900">{detailData.billing_period || detailData.period_label || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 font-medium">Status</p>
                <StatusBadge status={detailData.status} />
              </div>
              <div>
                <p className="text-xs text-gray-500 font-medium">Uploaded At</p>
                <p className="text-sm text-gray-900">{formatDateTime(detailData.created_at)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 font-medium">Residents / Readings</p>
                <p className="text-sm text-gray-900">
                  {detailData.total_residents ?? '—'} residents / {detailData.total_readings ?? '—'} readings
                </p>
              </div>
            </div>

            {detailData.result_summary && (
              <div>
                <p className="text-xs text-gray-500 font-medium mb-1">Result Summary</p>
                <p className="text-sm text-gray-700 bg-gray-50 rounded-md p-3">{detailData.result_summary}</p>
              </div>
            )}

            {detailData.issues && detailData.issues.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 font-medium mb-2">Issues ({detailData.issues.length})</p>
                <div className="border border-gray-200 rounded-lg divide-y divide-gray-100 max-h-60 overflow-y-auto">
                  {detailData.issues.map((issue, i) => (
                    <div key={i} className="px-3 py-2 text-sm">
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium mr-2 ${
                        issue.severity === 'error' ? 'bg-red-100 text-red-700' :
                        issue.severity === 'warning' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {issue.severity || 'info'}
                      </span>
                      <span className="text-gray-700">{issue.message || issue}</span>
                      {issue.row != null && <span className="text-gray-400 ml-2 text-xs">(row {issue.row})</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400 text-sm">Could not load upload detail.</div>
        )}
      </Modal>

      <GenerateTemplateModal
        isOpen={showGenerateTemplate}
        onClose={() => setShowGenerateTemplate(false)}
        propertyCode={propertyCode}
      />

      <TemplatePreviewModal
        isOpen={showPreviewModal}
        onClose={() => setShowPreviewModal(false)}
        onProceed={handleProceedWithUpload}
        validationResult={validationResult}
        uploadType={pendingUploadType}
        loading={submitting}
      />

      {/* Meter Reading Modal */}
      <Modal isOpen={showMeter} onClose={() => setShowMeter(false)} title="Submit Meter Reading">
        <form onSubmit={handleMeterSubmit} className="space-y-4">
          <FormField label="Building" name="building" required value={meterForm.building}
            onChange={(e) => setMeterForm({ ...meterForm, building: e.target.value })} placeholder="e.g. DT01" />
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
