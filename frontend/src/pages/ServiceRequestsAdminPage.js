import React, { useEffect, useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import { RefreshCw, UserCheck, Plus } from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import FormField from '../components/ui/FormField';
import { listServiceRequests, updateServiceRequestStatus, assignServiceRequest, createServiceRequest } from '../api/serviceRequests';
import { listResidents } from '../api/residents';
import { listStaff } from '../api/auth';
import { SERVICE_REQUEST_STATUSES, SERVICE_REQUEST_CATEGORIES, SERVICE_REQUEST_PRIORITIES } from '../utils/constants';
import { formatDateTime, truncate, shortUUID } from '../utils/formatters';
import { useProperty } from '../contexts/PropertyContext';

export default function ServiceRequestsAdminPage() {
  const { propertyCode } = useProperty();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: '', category: '', priority: '' });
  const [submitting, setSubmitting] = useState(false);
  const [resolveModal, setResolveModal] = useState(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [assignModal, setAssignModal] = useState(null);
  const [assigneeId, setAssigneeId] = useState('');
  const [staffList, setStaffList] = useState([]);
  const [loadingStaff, setLoadingStaff] = useState(false);

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [residents, setResidents] = useState([]);
  const [loadingResidents, setLoadingResidents] = useState(false);
  const [createForm, setCreateForm] = useState({
    resident_id: '',
    category: '',
    subject: '',
    description: '',
    location: '',
    priority: 'medium',
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.category) params.category = filters.category;
      if (filters.priority) params.priority = filters.priority;
      const result = await listServiceRequests(params);
      setData(Array.isArray(result) ? result : []);
    } catch (err) {
      toast.error('Failed to load service requests');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [filters, propertyCode]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleStatusChange = async (row, newStatus) => {
    if (newStatus === 'resolved') {
      setResolveModal({ id: row.id, currentStatus: row.status });
      return;
    }

    try {
      await updateServiceRequestStatus(row.id, { status: newStatus });
      toast.success(`Status updated to ${newStatus.replace(/_/g, ' ')}`);
      fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to update status';
      toast.error(msg);
    }
  };

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    if (!resolveModal) return;
    setSubmitting(true);
    try {
      await updateServiceRequestStatus(resolveModal.id, { status: 'resolved', resolution_notes: resolutionNotes });
      toast.success('Status updated to resolved');
      setResolveModal(null);
      setResolutionNotes('');
      fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to resolve service request';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const openAssignModal = async (row) => {
    setAssignModal(row);
    setAssigneeId(row.assigned_to || '');
    if (staffList.length === 0) {
      setLoadingStaff(true);
      try {
        const result = await listStaff();
        setStaffList(Array.isArray(result) ? result : []);
      } catch {
        toast.error('Failed to load staff list');
      } finally {
        setLoadingStaff(false);
      }
    }
  };

  const openCreateModal = async () => {
    setCreateModalOpen(true);
    if (residents.length === 0) {
      setLoadingResidents(true);
      try {
        const result = await listResidents({ status: 'active' });
        setResidents(Array.isArray(result) ? result : []);
      } catch {
        toast.error('Failed to load residents');
      } finally {
        setLoadingResidents(false);
      }
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!createForm.resident_id || !createForm.category || !createForm.subject) return;
    setSubmitting(true);
    try {
      await createServiceRequest({
        resident_id: createForm.resident_id,
        category: createForm.category,
        subject: createForm.subject,
        description: createForm.description,
        location: createForm.location,
        priority: createForm.priority,
      });
      toast.success('Service request created');
      setCreateModalOpen(false);
      setCreateForm({
        resident_id: '',
        category: '',
        subject: '',
        description: '',
        location: '',
        priority: 'medium',
      });
      fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to create service request';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAssignSubmit = async (e) => {
    e.preventDefault();
    if (!assignModal || !assigneeId) return;
    setSubmitting(true);
    try {
      await assignServiceRequest(assignModal.id, { assigned_to: assigneeId });
      toast.success('Service request assigned');
      setAssignModal(null);
      setAssigneeId('');
      fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to assign service request';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const priorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'text-red-600 font-bold';
      case 'high': return 'text-orange-600 font-semibold';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const columns = [
    {
      key: 'created_at',
      label: 'Date',
      render: (r) => formatDateTime(r.created_at),
    },
    {
      key: 'resident_name',
      label: 'Resident',
      render: (r) => (
        <div className="flex flex-col">
          <span className="font-medium">{r.resident_name || shortUUID(r.resident_id)}</span>
          {(r.room_number || r.bed_code) && (
            <span className="text-xs text-gray-500">{r.room_number} {r.bed_code ? `(${r.bed_code})` : ''}</span>
          )}
        </div>
      ),
    },
    {
      key: 'category',
      label: 'Category',
      render: (r) => <span className="capitalize">{r.category?.replace(/_/g, ' ') || '—'}</span>,
    },
    {
      key: 'subject',
      label: 'Subject',
      render: (r) => (
        <span title={r.subject} className="cursor-default">{truncate(r.subject, 35)}</span>
      ),
    },
    {
      key: 'priority',
      label: 'Priority',
      render: (r) => <span className={`capitalize ${priorityColor(r.priority)}`}>{r.priority || '—'}</span>,
    },
    {
      key: 'status',
      label: 'Status',
      render: (r) => (
        <select
          value={r.status}
          onChange={(e) => handleStatusChange(r, e.target.value)}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs capitalize"
          onClick={(e) => e.stopPropagation()}
        >
          {SERVICE_REQUEST_STATUSES.filter((s) => s.value).map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
      ),
    },
    {
      key: 'location',
      label: 'Location',
      render: (r) => <span className="text-sm text-gray-600">{r.location || '—'}</span>,
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (r) => (
        <div className="flex flex-wrap gap-1">
          <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); openAssignModal(r); }}>
            <UserCheck className="w-3 h-3 mr-1" /> Assign
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Service Requests"
        subtitle="Manage maintenance, repairs, and resident service requests"
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={fetchData}>
              <RefreshCw className="w-4 h-4 mr-1" /> Refresh
            </Button>
            <Button onClick={openCreateModal}>
              <Plus className="w-4 h-4 mr-1" /> Add Request
            </Button>
          </div>
        }
      />

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={filters.status}
          onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {SERVICE_REQUEST_STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <select
          value={filters.category}
          onChange={(e) => setFilters((f) => ({ ...f, category: e.target.value }))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {SERVICE_REQUEST_CATEGORIES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <select
          value={filters.priority}
          onChange={(e) => setFilters((f) => ({ ...f, priority: e.target.value }))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {SERVICE_REQUEST_PRIORITIES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <Button variant="ghost" onClick={fetchData}><RefreshCw className="w-4 h-4" /></Button>
      </div>

      <DataTable columns={columns} data={data} loading={loading} emptyMessage="No service requests found" />

      {/* Resolve Modal */}
      <Modal isOpen={!!resolveModal} onClose={() => { setResolveModal(null); setResolutionNotes(''); }} title="Resolve Service Request">
        {resolveModal && (
          <form onSubmit={handleResolveSubmit} className="space-y-4">
            <p className="text-sm text-gray-600">
              You are marking this service request as <strong>resolved</strong>. Please enter resolution notes below.
            </p>
            <FormField
              label="Resolution Notes"
              name="resolution_notes"
              type="textarea"
              required
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Describe how the issue was resolved..."
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={() => { setResolveModal(null); setResolutionNotes(''); }}>Cancel</Button>
              <Button type="submit" loading={submitting}>Mark Resolved</Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Create Modal */}
      <Modal isOpen={createModalOpen} onClose={() => setCreateModalOpen(false)} title="Create Service Request">
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Resident</label>
            <select
              required
              value={createForm.resident_id}
              onChange={(e) => setCreateForm({ ...createForm, resident_id: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">{loadingResidents ? 'Loading residents...' : 'Select resident...'}</option>
              {residents.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.full_name} {r.room_number ? `(${r.room_number}${r.bed_code ? ` / ${r.bed_code}` : ''})` : ''}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select
              required
              value={createForm.category}
              onChange={(e) => setCreateForm({ ...createForm, category: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">Select category...</option>
              {[
                { value: 'plumbing', label: 'Plumbing' },
                { value: 'electrical', label: 'Electrical' },
                { value: 'aircon', label: 'Aircon' },
                { value: 'pest_control', label: 'Pest Control' },
                { value: 'wifi', label: 'WiFi' },
                { value: 'water_supply', label: 'Water Supply' },
                { value: 'lock_key', label: 'Lock / Key' },
                { value: 'cleaning', label: 'Cleaning' },
                { value: 'appliance', label: 'Appliance' },
                { value: 'other', label: 'Other' },
              ].map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <FormField
            label="Subject"
            name="subject"
            required
            value={createForm.subject}
            onChange={(e) => setCreateForm({ ...createForm, subject: e.target.value })}
            placeholder="Short summary of the request"
          />
          <FormField
            label="Description"
            name="description"
            type="textarea"
            value={createForm.description}
            onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
            placeholder="Detailed description of the concern or request"
          />
          <FormField
            label="Location"
            name="location"
            value={createForm.location}
            onChange={(e) => setCreateForm({ ...createForm, location: e.target.value })}
            placeholder="e.g. Room A101"
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <select
              value={createForm.priority}
              onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              {SERVICE_REQUEST_PRIORITIES.filter((p) => p.value).map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setCreateModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={submitting}>Create Request</Button>
          </div>
        </form>
      </Modal>

      {/* Assign Modal */}
      <Modal isOpen={!!assignModal} onClose={() => { setAssignModal(null); setAssigneeId(''); }} title="Assign Service Request">
        {assignModal && (
          <form onSubmit={handleAssignSubmit} className="space-y-4">
            <p className="text-sm text-gray-600">
              Assigning service request for <strong>{assignModal.subject}</strong>
            </p>
            {loadingStaff ? (
              <p className="text-sm text-gray-500">Loading staff list...</p>
            ) : staffList.length > 0 ? (
              <FormField
                label="Assign To"
                name="assigned_to"
                type="select"
                required
                value={assigneeId}
                onChange={(e) => setAssigneeId(e.target.value)}
                options={[
                  { value: '', label: 'Select staff member...' },
                  ...staffList.map((s) => ({ value: s.id, label: `${s.full_name} (${s.role})` })),
                ]}
              />
            ) : (
              <FormField
                label="Assign To (Staff UUID)"
                name="assigned_to"
                type="text"
                required
                value={assigneeId}
                onChange={(e) => setAssigneeId(e.target.value)}
                placeholder="Enter staff UUID"
              />
            )}
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={() => { setAssignModal(null); setAssigneeId(''); }}>Cancel</Button>
              <Button type="submit" loading={submitting} disabled={!assigneeId}>Assign</Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
