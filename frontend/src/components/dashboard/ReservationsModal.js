import React, { useEffect, useState } from 'react';
import Modal from '../ui/Modal';
import DataTable from '../ui/DataTable';
import { listInquiries } from '../../api/inquiries';
import { formatDate } from '../../utils/formatters';
import StatusBadge from '../ui/StatusBadge';

export default function ReservationsModal({ isOpen, onClose }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    listInquiries({})
      .then((res) => {
        // Filter to show only inquiries that look like reservations or recent ones
        setData(res || []);
      })
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [isOpen]);

  const columns = [
    { key: 'prospect_name', label: 'Name' },
    { key: 'prospect_phone', label: 'Phone' },
    { key: 'source', label: 'Source', render: (r) => <span className="capitalize">{r.source}</span> },
    { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'desired_move_in_date', label: 'Move-in Date', render: (r) => formatDate(r.desired_move_in_date) },
    { key: 'created_at', label: 'Created', render: (r) => formatDate(r.created_at) },
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Reservations / Inquiries" size="lg">
      <DataTable columns={columns} data={data} loading={loading} emptyMessage="No reservations found" />
    </Modal>
  );
}
