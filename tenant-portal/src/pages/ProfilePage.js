import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTenant } from '../context/TenantContext';
import { getProfile } from '../api/tenant';
import { formatCurrency, formatDate } from '../utils/formatters';
import {
  User, Mail, Phone, CreditCard, MapPin, Home, Calendar, Banknote,
  LogOut as LogOutIcon, ChevronRight, FileText,
} from 'lucide-react';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import StatusBadge from '../components/ui/StatusBadge';

function InfoRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-3 py-2.5">
      <Icon size={18} className="text-gray-400 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-sm font-semibold text-gray-900 truncate">{value || '-'}</p>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const { tenant, logout } = useTenant();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!tenant?.id) return;
    getProfile(tenant.id)
      .then(({ data }) => setProfile(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [tenant?.id]);

  const handleLogout = () => {
    logout();
  };

  if (loading) return <LoadingSpinner />;
  if (!profile) return <p className="text-center text-gray-500 py-8">Unable to load profile</p>;

  return (
    <div className="space-y-4">
      {/* Profile Header */}
      <div className="bg-white rounded-2xl p-5 shadow-sm text-center">
        <div className="w-16 h-16 bg-brand-navy rounded-full flex items-center justify-center mx-auto mb-3">
          <span className="text-2xl font-bold text-white">
            {profile.full_name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
          </span>
        </div>
        <h2 className="text-lg font-bold text-gray-900">{profile.full_name}</h2>
        <StatusBadge status={profile.status} />
      </div>

      {/* Personal Info */}
      <div className="bg-white rounded-2xl p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-500 mb-1 uppercase tracking-wider">Personal Info</h3>
        <div className="divide-y divide-gray-50">
          <InfoRow icon={Mail} label="Email" value={profile.email} />
          <InfoRow icon={Phone} label="Phone" value={profile.phone} />
          <InfoRow icon={CreditCard} label="ID" value={profile.id_type ? `${profile.id_type} - ${profile.id_number}` : null} />
        </div>
      </div>

      {/* Room Details */}
      <div className="bg-white rounded-2xl p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-500 mb-1 uppercase tracking-wider">Room Details</h3>
        <div className="divide-y divide-gray-50">
          <InfoRow icon={Home} label="Room" value={profile.room_number} />
          <InfoRow icon={MapPin} label="Building" value={profile.building} />
          <InfoRow icon={User} label="Bed Number" value={profile.bed_number} />
        </div>
      </div>

      {/* Contract Info */}
      <div className="bg-white rounded-2xl p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-500 mb-1 uppercase tracking-wider">Contract</h3>
        <div className="divide-y divide-gray-50">
          <InfoRow icon={Calendar} label="Move-in Date" value={formatDate(profile.move_in_date)} />
          <InfoRow icon={Banknote} label="Monthly Rate" value={formatCurrency(profile.monthly_rate)} />
          <InfoRow icon={Banknote} label="Deposit Paid" value={profile.deposit_paid ? formatCurrency(profile.deposit_paid) : 'Not recorded'} />
          <InfoRow icon={FileText} label="Account Balance" value={formatCurrency(profile.ledger_balance)} />
        </div>
      </div>

      {/* Quick Links */}
      <button
        onClick={() => navigate('/tenant/moveout')}
        className="w-full bg-white rounded-2xl p-4 shadow-sm flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <LogOutIcon size={20} className="text-gray-500" />
          <span className="text-sm font-semibold text-gray-700">Move-Out</span>
        </div>
        <ChevronRight size={18} className="text-gray-300" />
      </button>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full bg-red-50 text-red-600 rounded-2xl p-4 text-sm font-semibold text-center hover:bg-red-100 transition-colors"
      >
        Sign Out
      </button>
    </div>
  );
}
