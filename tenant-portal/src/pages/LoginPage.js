import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTenant } from '../context/TenantContext';
import { tenantLogin } from '../api/tenant';
import { Home, Mail, Phone, BedDouble } from 'lucide-react';
import toast from 'react-hot-toast';
import Button from '../components/ui/Button';

export default function LoginPage() {
  const [mode, setMode] = useState('email');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [bedCode, setBedCode] = useState('');
  const [dbSchema, setDbSchema] = useState('pilot');
  const [loading, setLoading] = useState(false);
  const { login } = useTenant();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const value = mode === 'email' ? email.trim() : mode === 'phone' ? phone.trim() : bedCode.trim();
    if (!value) return;
    setLoading(true);
    try {
      const { data } = await tenantLogin(
        mode === 'email' ? value : null,
        mode === 'phone' ? value : null,
        mode === 'room' ? value : null,
        dbSchema
      );
      login(data);
      toast.success(`Welcome, ${data.full_name}!`);
      navigate('/tenant');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Account not found');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-navy to-brand-navy-dark flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-brand-gold rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <Home size={32} className="text-brand-navy" />
          </div>
          <h1 className="text-2xl font-bold text-white">DormTel</h1>
          <p className="text-brand-gold text-sm mt-1">My Dorm, My Home</p>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-xl">
          <h2 className="text-lg font-bold text-gray-900 mb-1">Tenant Login</h2>
          <p className="text-sm text-gray-500 mb-6">Sign in with your email, mobile number, or room code</p>

          {/* Mode Toggle */}
          <div className="flex bg-gray-100 rounded-xl p-1 mb-4">
            <button
              type="button"
              onClick={() => setMode('email')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-all ${
                mode === 'email' ? 'bg-white text-brand-navy shadow-sm' : 'text-gray-500'
              }`}
            >
              <Mail size={14} /> Email
            </button>
            <button
              type="button"
              onClick={() => setMode('phone')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-all ${
                mode === 'phone' ? 'bg-white text-brand-navy shadow-sm' : 'text-gray-500'
              }`}
            >
              <Phone size={14} /> Mobile
            </button>
            <button
              type="button"
              onClick={() => setMode('room')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-all ${
                mode === 'room' ? 'bg-white text-brand-navy shadow-sm' : 'text-gray-500'
              }`}
            >
              <BedDouble size={14} /> Room
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'email' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                <div className="relative">
                  <Mail size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your.email@example.com"
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy focus:border-transparent"
                    required
                  />
                </div>
              </div>
            ) : mode === 'phone' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mobile Number</label>
                <div className="relative">
                  <Phone size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="09XXXXXXXXX"
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy focus:border-transparent"
                    required
                  />
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Room + Bed Code</label>
                <div className="relative">
                  <BedDouble size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    value={bedCode}
                    onChange={(e) => setBedCode(e.target.value.toUpperCase())}
                    placeholder="e.g. 101A"
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy focus:border-transparent"
                    required
                  />
                </div>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Property</label>
              <select
                value={dbSchema}
                onChange={(e) => setDbSchema(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy focus:border-transparent"
              >
                <option value="pilot">Pilot Property</option>
                <option value="demo">Demo Property</option>
              </select>
            </div>
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-4 p-3 bg-brand-gold/10 rounded-xl border border-brand-gold/30">
            <p className="text-xs text-gray-600">
              <span className="font-semibold">Demo:</span> juan.delacruz@email.com or Room: A101A (select Demo Property)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
