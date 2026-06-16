import React, { useEffect, useState } from 'react';
import Modal from '../ui/Modal';
import DataTable from '../ui/DataTable';
import { listBillings } from '../../api/billing';
import { formatCurrency, formatDate } from '../../utils/formatters';
import StatusBadge from '../ui/StatusBadge';

export default function PendingBillsModal({ isOpen, onClose }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    listBillings({})
      .then((res) => {
        const pending = (res || []).filter((b) =>
          ['pending_review', 'approved', 'distributed', 'overdue'].includes(b.status)
        );
        setData(pending);
      })
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [isOpen]);

  const columns = [
    { key: 'billing_period', label: 'Period' },
    {
      key: 'resident_name',
      label: 'Resident',
      render: (r) => (
        <div className="flex flex-col">
          <span className="font-medium">{r.resident_name || '—'}</span>
          {r.bed_code && (
            <span className="text-xs text-gray-500">{r.bed_code}</span>
          )}
        </div>
      ),
    },
    { key: 'total_amount', label: 'Amount', render: (r) => formatCurrency(r.total_amount) },
    { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'created_at', label: 'Created', render: (r) => formatDate(r.created_at) },
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Pending Bills" size="lg">
      <DataTable columns={columns} data={data} loading={loading} emptyMessage="No pending bills" />
    </Modal>
  );
}
