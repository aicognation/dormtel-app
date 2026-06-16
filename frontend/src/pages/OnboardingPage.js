import React, { useEffect, useState, useCallback, useMemo } from 'react';
import toast from 'react-hot-toast';
import { Plus, RefreshCw, Eye, BedSingle, ArrowUpDown, Building2, DoorOpen, UserCircle, GraduationCap, Home } from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import FormField from '../components/ui/FormField';
import StatusBadge from '../components/ui/StatusBadge';
import { listRooms, createReservation } from '../api/onboarding';
import { getConvertibleInquiries } from '../api/inquiries';
import { ID_TYPES } from '../utils/constants';
import { formatCurrency } from '../utils/formatters';
import ViewTenantsModal from '../components/onboarding/ViewTenantsModal';

export default function OnboardingPage() {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showReserve, setShowReserve] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [viewTenantsRoom, setViewTenantsRoom] = useState(null);
  const [inquiries, setInquiries] = useState([]);
  const [loadingInquiries, setLoadingInquiries] = useState(false);

  // Filters
  const [filterProperty, setFilterProperty] = useState('');
  const [filterBuilding, setFilterBuilding] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterBedType, setFilterBedType] = useState('');
  const [sortBy, setSortBy] = useState('room_number');
  const [sortDir, setSortDir] = useState('asc');

  const [form, setForm] = useState({
    inquiry_id: '', full_name: '', email: '', phone: '', monthly_rate: '',
    id_type: '', id_number: '', bed_id: '', move_in_date: '', move_out_date: '',
    school: '', course: '', review_center: '', exam_date: '', is_first_time_dormer: true,
    address: '', deposit_paid: '',
  });

  const fetchRooms = useCallback(async () => {
    setLoading(true);
    try {
      const result = await listRooms();
      setRooms(result);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchInquiries = useCallback(async () => {
    setLoadingInquiries(true);
    try {
      const result = await getConvertibleInquiries();
      setInquiries(result);
    } catch {
      setInquiries([]);
    } finally {
      setLoadingInquiries(false);
    }
  }, []);

  useEffect(() => { fetchRooms(); }, [fetchRooms]);

  // Auto-open reservation modal if coming from Inquiry conversion
  useEffect(() => {
    const inquiryId = localStorage.getItem('dormtel_convert_inquiry_id');
    if (inquiryId) {
      localStorage.removeItem('dormtel_convert_inquiry_id');
      fetchInquiries().then(() => {
        setShowReserve(true);
        // Wait for inquiries to load then select
        setTimeout(() => handleInquiryChange(inquiryId), 300);
      });
    }
  }, []);

  const buildings = useMemo(() => {
    const set = new Set(rooms.map((r) => r.building).filter(Boolean));
    return Array.from(set);
  }, [rooms]);

  const properties = useMemo(() => {
    const set = new Set(rooms.map((r) => r.property_code).filter(Boolean));
    return Array.from(set);
  }, [rooms]);

  const bedTypes = useMemo(() => {
    const set = new Set();
    rooms.forEach((r) => r.beds?.forEach((b) => { if (b.bed_type) set.add(b.bed_type); }));
    return Array.from(set);
  }, [rooms]);

  const availableRooms = useMemo(() => {
    return rooms.filter((r) => r.beds?.some((b) => b.status === 'available'));
  }, [rooms]);

  const filteredRooms = useMemo(() => {
    let data = [...rooms];

    if (filterProperty) data = data.filter((r) => r.property_code === filterProperty);
    if (filterBuilding) data = data.filter((r) => r.building === filterBuilding);
    if (filterStatus) data = data.filter((r) => r.status === filterStatus);
    if (filterBedType) {
      data = data.filter((r) => r.beds?.some((b) => b.bed_type === filterBedType));
    }

    data.sort((a, b) => {
      let valA, valB;
      if (sortBy === 'room_number') {
        valA = a.room_number;
        valB = b.room_number;
      } else if (sortBy === 'occupancy') {
        valA = a.occupied_count / (a.capacity || 1);
        valB = b.occupied_count / (b.capacity || 1);
      } else if (sortBy === 'rate') {
        valA = a.min_rate || 0;
        valB = b.min_rate || 0;
      } else {
        valA = a[sortBy];
        valB = b[sortBy];
      }
      if (valA < valB) return sortDir === 'asc' ? -1 : 1;
      if (valA > valB) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });

    return data;
  }, [rooms, filterProperty, filterBuilding, filterStatus, filterBedType, sortBy, sortDir]);

  const handleInquiryChange = (inquiryId) => {
    if (!inquiryId) {
      setForm((prev) => ({
        ...prev, inquiry_id: '', full_name: '', email: '', phone: '',
        school: '', course: '', review_center: '', exam_date: '', is_first_time_dormer: true,
      }));
      return;
    }
    const inquiry = inquiries.find((i) => i.id === inquiryId);
    if (!inquiry) return;
    setForm((prev) => ({
      ...prev,
      inquiry_id: inquiryId,
      full_name: inquiry.prospect_name || '',
      email: inquiry.prospect_email || '',
      phone: inquiry.prospect_phone || '',
      school: inquiry.school || '',
      course: inquiry.course || '',
      review_center: inquiry.review_center || '',
      exam_date: inquiry.exam_date || '',
      is_first_time_dormer: inquiry.first_time_dormer ?? true,
    }));
  };

  const handleReserve = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        monthly_rate: Number(form.monthly_rate),
        bed_id: form.bed_id || undefined,
        deposit_paid: form.deposit_paid ? Number(form.deposit_paid) : 0,
        inquiry_id: form.inquiry_id || undefined,
      };
      const result = await createReservation(payload);
      const bed = selectedRoom?.beds?.find((b) => b.id === form.bed_id);
      const roomInfo = selectedRoom ? ` — Room ${selectedRoom.room_number}${bed ? `, ${bed.bed_code}` : ''}` : '';
      toast.success(`Reservation created for ${result.full_name}${roomInfo}`);
      setShowReserve(false);
      setSelectedRoom(null);
      setForm({
        inquiry_id: '', full_name: '', email: '', phone: '', monthly_rate: '',
        id_type: '', id_number: '', bed_id: '', move_in_date: '', move_out_date: '',
        school: '', course: '', review_center: '', exam_date: '', is_first_time_dormer: true,
        address: '', deposit_paid: '',
      });
      fetchRooms();
    } finally {
      setSubmitting(false);
    }
  };

  const openReserveModal = (room) => {
    setSelectedRoom(room);
    const firstAvailable = room.beds?.find((b) => b.status === 'available');
    setForm({
      inquiry_id: '', full_name: '', email: '', phone: '', monthly_rate: '',
      id_type: '', id_number: '', bed_id: firstAvailable?.id || '', move_in_date: '', move_out_date: '',
      school: '', course: '', review_center: '', exam_date: '', is_first_time_dormer: true,
      address: '', deposit_paid: '',
    });
    if (firstAvailable?.rate_per_bed) {
      setForm((prev) => ({ ...prev, monthly_rate: firstAvailable.rate_per_bed }));
    } else if (room.min_rate) {
      setForm((prev) => ({ ...prev, monthly_rate: room.min_rate }));
    }
    fetchInquiries();
    setShowReserve(true);
  };

  const openNewReservationModal = () => {
    setSelectedRoom(null);
    setForm({
      inquiry_id: '', full_name: '', email: '', phone: '', monthly_rate: '',
      id_type: '', id_number: '', bed_id: '', move_in_date: '', move_out_date: '',
      school: '', course: '', review_center: '', exam_date: '', is_first_time_dormer: true,
      address: '', deposit_paid: '',
    });
    fetchInquiries();
    setShowReserve(true);
  };

  const toggleSort = (key) => {
    if (sortBy === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(key);
      setSortDir('asc');
    }
  };

  const occupancyBoxes = (room) => {
    const boxes = [];
    for (let i = 0; i < room.capacity; i++) {
      const bed = room.beds?.[i];
      let colorClass = 'bg-white border-gray-300';
      if (bed) {
        if (bed.status === 'occupied') colorClass = 'bg-green-500 border-green-600';
        else if (bed.status === 'reserved') colorClass = 'bg-yellow-400 border-yellow-500';
        else colorClass = 'bg-white border-gray-300';
      }
      boxes.push(
        <div
          key={i}
          className={`w-4 h-4 rounded-sm border ${colorClass}`}
          title={bed ? `${bed.bed_code}: ${bed.status}` : 'N/A'}
        />
      );
    }
    return (
      <div className="flex items-center gap-1">
        <div className="flex flex-wrap gap-0.5 max-w-[140px]">{boxes}</div>
        <span className="text-xs text-gray-500 ml-1">
          {room.occupied_count}/{room.capacity}
        </span>
      </div>
    );
  };

  const roomColumns = [
    { key: 'room_number', label: 'Room #', render: (r) => <span className="font-semibold">{r.room_number}</span> },
    { key: 'building', label: 'Building' },
    { key: 'property_code', label: 'Property' },
    { key: 'capacity', label: 'Capacity' },
    {
      key: 'occupancy',
      label: (
        <button className="flex items-center gap-1 uppercase" onClick={() => toggleSort('occupancy')}>
          Occupancy <ArrowUpDown className="w-3 h-3" />
        </button>
      ),
      render: occupancyBoxes,
    },
    {
      key: 'rate',
      label: (
        <button className="flex items-center gap-1 uppercase" onClick={() => toggleSort('rate')}>
          Rate/Bed <ArrowUpDown className="w-3 h-3" />
        </button>
      ),
      render: (r) => {
        if (r.min_rate === r.max_rate || !r.max_rate) return formatCurrency(r.min_rate);
        return `${formatCurrency(r.min_rate)} - ${formatCurrency(r.max_rate)}`;
      },
    },
    { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    {
      key: 'actions',
      label: 'Actions',
      render: (r) => (
        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={(e) => { e.stopPropagation(); openReserveModal(r); }}
            disabled={r.status === 'full' && !r.beds?.some((b) => b.status === 'available')}
          >
            <BedSingle className="w-3 h-3 mr-1" /> Reserve
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={(e) => { e.stopPropagation(); setViewTenantsRoom(r); }}
          >
            <Eye className="w-3 h-3 mr-1" /> Tenants
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Digital Onboarding"
        subtitle="Manage reservations, rooms, and move-in activation"
        actions={
          <Button onClick={openNewReservationModal}>
            <Plus className="w-4 h-4 mr-1" /> New Reservation
          </Button>
        }
      />

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 mb-4">
        <div className="flex flex-wrap gap-3 items-end">
          <FormField
            label="Property"
            name="filterProperty"
            type="select"
            value={filterProperty}
            onChange={(e) => setFilterProperty(e.target.value)}
            options={[{ value: '', label: 'All Properties' }, ...properties.map((p) => ({ value: p, label: p }))]}
            className="min-w-[140px]"
          />
          <FormField
            label="Building"
            name="filterBuilding"
            type="select"
            value={filterBuilding}
            onChange={(e) => setFilterBuilding(e.target.value)}
            options={[{ value: '', label: 'All Buildings' }, ...buildings.map((b) => ({ value: b, label: b }))]}
            className="min-w-[140px]"
          />
          <FormField
            label="Room Status"
            name="filterStatus"
            type="select"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            options={[
              { value: '', label: 'All Statuses' },
              { value: 'available', label: 'Available' },
              { value: 'full', label: 'Full' },
              { value: 'maintenance', label: 'Maintenance' },
            ]}
            className="min-w-[140px]"
          />
          <FormField
            label="Bed Type"
            name="filterBedType"
            type="select"
            value={filterBedType}
            onChange={(e) => setFilterBedType(e.target.value)}
            options={[{ value: '', label: 'All Bed Types' }, ...bedTypes.map((t) => ({ value: t, label: t.replace(/_/g, ' ') }))]}
            className="min-w-[160px]"
          />
          <div className="flex-1" />
          <Button variant="ghost" size="sm" onClick={fetchRooms}><RefreshCw className="w-4 h-4" /></Button>
        </div>
      </div>

      <DataTable
        columns={roomColumns}
        data={filteredRooms}
        loading={loading}
        emptyMessage="No rooms match your filters"
      />

      {/* Create Reservation Modal */}
      <Modal isOpen={showReserve} onClose={() => setShowReserve(false)} title={selectedRoom ? `Reserve — Room ${selectedRoom.room_number}` : 'New Reservation'} size="xl">
        <form onSubmit={handleReserve} className="space-y-4">

          {/* Inquiry Selector */}
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <UserCircle className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-semibold text-blue-800">Link to Inquiry (optional)</span>
            </div>
            <FormField
              name="inquiry_id"
              type="select"
              value={form.inquiry_id}
              onChange={(e) => handleInquiryChange(e.target.value)}
              options={[
                { value: '', label: loadingInquiries ? 'Loading inquiries...' : 'Select an inquiry or leave blank for walk-in' },
                ...inquiries.map((i) => ({
                  value: i.id,
                  label: `${i.prospect_name || 'Unnamed'} — ${i.source} (${i.lead_score ?? 0} pts)`,
                })),
              ]}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Room selection when no room pre-selected */}
            {!selectedRoom && (
              <div className="sm:col-span-2">
                <FormField
                  label="Select Room"
                  name="room_select"
                  type="select"
                  required
                  value={selectedRoom?.id || ''}
                  onChange={(e) => {
                    const room = availableRooms.find((r) => r.id === e.target.value);
                    setSelectedRoom(room || null);
                    if (room) {
                      const firstAvailable = room.beds?.find((b) => b.status === 'available');
                      setForm((prev) => ({
                        ...prev,
                        bed_id: firstAvailable?.id || '',
                        monthly_rate: firstAvailable?.rate_per_bed || room.min_rate || '',
                      }));
                    }
                  }}
                  options={[
                    { value: '', label: 'Choose a room...' },
                    ...availableRooms.map((r) => ({
                      value: r.id,
                      label: `Room ${r.room_number} — ${r.building} / ${r.property_code} (${r.available_count || 0} beds avail)`,
                    })),
                  ]}
                />
              </div>
            )}

            {/* Room details card */}
            {selectedRoom && (
              <div className="sm:col-span-2 bg-brand-navy/5 border border-brand-navy/10 rounded-lg p-3 flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <DoorOpen className="w-4 h-4 text-brand-navy" />
                  <span className="font-semibold text-brand-navy">Room {selectedRoom.room_number}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-gray-500" />
                  <span>{selectedRoom.building} / {selectedRoom.property_code}</span>
                </div>
                <div className="text-gray-600">
                  Capacity: <span className="font-medium">{selectedRoom.capacity}</span> beds
                </div>
                <div className="text-gray-600">
                  Available: <span className="font-medium">{selectedRoom.beds?.filter((b) => b.status === 'available').length || 0}</span> beds
                </div>
                <div className="text-gray-600">
                  Rate: <span className="font-medium">{formatCurrency(selectedRoom.min_rate)}</span>{selectedRoom.max_rate && selectedRoom.max_rate !== selectedRoom.min_rate ? ` - ${formatCurrency(selectedRoom.max_rate)}` : ''}
                </div>
              </div>
            )}

            {/* Visual Bed Selector */}
            {selectedRoom && selectedRoom.beds && (
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Select Bed</label>
                <div className="flex flex-wrap gap-2">
                  {selectedRoom.beds.map((bed) => {
                    const isAvailable = bed.status === 'available';
                    const isSelected = form.bed_id === bed.id;
                    const statusColors = {
                      available: isSelected ? 'bg-brand-navy text-white border-brand-navy' : 'bg-white text-gray-700 border-gray-300 hover:border-brand-navy hover:text-brand-navy',
                      reserved: 'bg-yellow-50 text-yellow-700 border-yellow-300 cursor-not-allowed',
                      occupied: 'bg-green-50 text-green-700 border-green-300 cursor-not-allowed',
                    };
                    return (
                      <button
                        key={bed.id}
                        type="button"
                        disabled={!isAvailable}
                        onClick={() => {
                          if (isAvailable) {
                            setForm((prev) => ({
                              ...prev,
                              bed_id: bed.id,
                              monthly_rate: bed.rate_per_bed || prev.monthly_rate,
                            }));
                          }
                        }}
                        className={`px-3 py-2 rounded-lg border-2 text-sm font-medium transition-colors ${statusColors[bed.status] || statusColors.available}`}
                        title={`${bed.bed_code} — ${bed.bed_type?.replace(/_/g, ' ') || 'Standard'} — ${bed.status}`}
                      >
                        <div className="text-xs uppercase tracking-wide opacity-75">{bed.bed_code}</div>
                        <div className="text-xs">{formatCurrency(bed.rate_per_bed)}</div>
                      </button>
                    );
                  })}
                </div>
                <div className="flex gap-3 mt-2 text-xs text-gray-500">
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm border border-gray-300 bg-white inline-block" /> Available</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm border border-yellow-400 bg-yellow-50 inline-block" /> Reserved</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm border border-green-300 bg-green-50 inline-block" /> Occupied</span>
                </div>
              </div>
            )}

            <FormField label="Full Name *" name="full_name" required value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            <FormField label="Email *" name="email" type="email" required value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <FormField label="Phone *" name="phone" required value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="09XX-XXX-XXXX" />
            <FormField label="Monthly Rate (₱) *" name="monthly_rate" type="number" required value={form.monthly_rate}
              onChange={(e) => setForm({ ...form, monthly_rate: e.target.value })} />
            <FormField label="Deposit Paid (₱)" name="deposit_paid" type="number" value={form.deposit_paid}
              onChange={(e) => setForm({ ...form, deposit_paid: e.target.value })} />
            <FormField label="ID Type" name="id_type" type="select" value={form.id_type}
              onChange={(e) => setForm({ ...form, id_type: e.target.value })} options={ID_TYPES} />
            <FormField label="ID Number" name="id_number" value={form.id_number}
              onChange={(e) => setForm({ ...form, id_number: e.target.value })} />

            <div className="sm:col-span-2 border-t border-gray-200 pt-3 mt-1">
              <div className="flex items-center gap-2 mb-3">
                <GraduationCap className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-semibold text-gray-700">Student Information</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="School" name="school" value={form.school}
                  onChange={(e) => setForm({ ...form, school: e.target.value })} />
                <FormField label="Course" name="course" value={form.course}
                  onChange={(e) => setForm({ ...form, course: e.target.value })} />
                <FormField label="Review Center" name="review_center" value={form.review_center}
                  onChange={(e) => setForm({ ...form, review_center: e.target.value })} />
                <FormField label="Exam Date" name="exam_date" type="date" value={form.exam_date}
                  onChange={(e) => setForm({ ...form, exam_date: e.target.value })} />
              </div>
            </div>

            <div className="sm:col-span-2 border-t border-gray-200 pt-3">
              <div className="flex items-center gap-2 mb-3">
                <Home className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-semibold text-gray-700">Address & Other Details</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Address" name="address" value={form.address}
                  onChange={(e) => setForm({ ...form, address: e.target.value })} />
                <FormField label="First Time Dormer?" name="is_first_time_dormer" type="select"
                  value={String(form.is_first_time_dormer)}
                  onChange={(e) => setForm({ ...form, is_first_time_dormer: e.target.value === 'true' })}
                  options={[{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }]} />
              </div>
            </div>

            <FormField label="Move-in Date *" name="move_in_date" type="date" required value={form.move_in_date}
              onChange={(e) => setForm({ ...form, move_in_date: e.target.value })} />
            <FormField label="Move-out Date *" name="move_out_date" type="date" required value={form.move_out_date}
              onChange={(e) => setForm({ ...form, move_out_date: e.target.value })} />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setShowReserve(false)}>Cancel</Button>
            <Button type="submit" loading={submitting}>Create Reservation</Button>
          </div>
        </form>
      </Modal>

      {/* View Tenants Modal */}
      <ViewTenantsModal
        isOpen={!!viewTenantsRoom}
        onClose={() => setViewTenantsRoom(null)}
        roomId={viewTenantsRoom?.id}
        roomNumber={viewTenantsRoom?.room_number}
      />
    </div>
  );
}
