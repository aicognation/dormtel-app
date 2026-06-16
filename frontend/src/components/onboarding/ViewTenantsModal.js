import React, { useEffect, useState } from 'react';
import Modal from '../ui/Modal';
import { getRoomTenants } from '../../api/onboarding';
import { formatCurrency } from '../../utils/formatters';
import StatusBadge from '../ui/StatusBadge';

export default function ViewTenantsModal({ isOpen, onClose, roomId, roomNumber }) {
  const [beds, setBeds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isOpen || !roomId) return;
    setLoading(true);
    getRoomTenants(roomId)
      .then((res) => setBeds(res || []))
      .catch(() => setBeds([]))
      .finally(() => setLoading(false));
  }, [isOpen, roomId]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Room ${roomNumber} - Tenants`} size="lg">
      {loading ? (
        <div className="py-8 text-center text-gray-500">Loading tenants...</div>
      ) : (
        <div className="space-y-3">
          {beds.map((bed) => (
            <div key={bed.id} className="flex items-center justify-between border rounded-lg p-3 bg-white">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                  bed.status === 'occupied' ? 'bg-green-100 text-green-700' :
                  bed.status === 'reserved' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-500'
                }`}>
                  {bed.bed_code.slice(-1)}
                </div>
                <div>
                  <div className="text-sm font-semibold text-gray-900">
                    {bed.resident ? bed.resident.full_name : 'Vacant'}
                  </div>
                  <div className="text-xs text-gray-500">
                    {bed.bed_type ? bed.bed_type.replace(/_/g, ' ') : 'Standard'} · {formatCurrency(bed.rate_per_bed)}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={bed.status} />
                {bed.resident && (
                  <span className="text-xs text-gray-500">{bed.resident.id.slice(0,8)}</span>
                )}
              </div>
            </div>
          ))}
          {beds.length === 0 && (
            <div className="text-center text-gray-500 py-4">No bed data for this room.</div>
          )}
        </div>
      )}
    </Modal>
  );
}
