import React, { useEffect, useState } from 'react';
import Modal from '../ui/Modal';
import DataTable from '../ui/DataTable';
import client from '../../api/client';
import StatusBadge from '../ui/StatusBadge';

export default function DormersModal({ isOpen, onClose, mode = 'active' }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  const isAll = mode === 'all';
  const title = isAll ? 'Listed Residents' : 'Active Dormers';
  const emptyMessage = isAll ? 'No residents found' : 'No active dormers found';

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    client.get(isAll ? '/residents' : '/residents?status=active&current_only=true')
      .then((res) => {
        setData(res || []);
      })
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [isOpen, isAll]);

  const columns = [
    { key: 'full_name', label: 'Name' },
    { key: 'email', label: 'Email' },
    { key: 'phone', label: 'Phone' },
    { key: 'bed_code', label: 'Bed' },
    { key: 'room_number', label: 'Room' },
    { key: 'building', label: 'Building' },
    { key: 'monthly_rate', label: 'Rate', render: (r) => `₱${Number(r.monthly_rate).toLocaleString()}` },
    { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status} /> },
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="xl">
      <DataTable columns={columns} data={data} loading={loading} emptyMessage={emptyMessage} />
    </Modal>
  );
}
