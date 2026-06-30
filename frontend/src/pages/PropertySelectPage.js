import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Loader2 } from 'lucide-react';
import { useProperty } from '../contexts/PropertyContext';
import client from '../api/client';

export default function PropertySelectPage() {
  const navigate = useNavigate();
  const { selectProperty, properties } = useProperty();

  const [availableProperties, setAvailableProperties] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selecting, setSelecting] = useState(null);

  useEffect(() => {
    async function fetchProperties() {
      try {
        const data = await client.get('/auth/properties');
        setAvailableProperties(data);
      } catch {
        // Fallback to static list if endpoint not ready
        setAvailableProperties(Object.values(properties));
      } finally {
        setLoading(false);
      }
    }
    fetchProperties();
  }, [properties]);

  const handleSelect = async (code) => {
    setSelecting(code);
    try {
      const data = await client.post('/auth/select-property', { property_code: code });
      if (data?.access_token) {
        localStorage.setItem('dt_token', data.access_token);
      }
      selectProperty(code);
      navigate('/');
    } catch {
      // Error toast handled by client interceptor
      setSelecting(null);
    }
  };

  const propertyList = availableProperties
    ? Array.isArray(availableProperties)
      ? availableProperties
      : Object.values(availableProperties)
    : [];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-brand-navy px-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 bg-brand-gold/20 rounded-lg flex items-center justify-center">
          <Building2 className="w-6 h-6 text-brand-gold" />
        </div>
        <span className="text-white text-xl font-bold tracking-wide">DormTel</span>
      </div>

      <h1 className="text-white text-2xl sm:text-3xl font-bold mt-6 mb-2">Select Your Property</h1>
      <p className="text-white/50 text-sm mb-10">Choose the branch you want to manage for this session.</p>

      {loading ? (
        <div className="flex items-center gap-2 text-white/60">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Loading properties...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 w-full max-w-2xl">
          {propertyList.map((prop) => {
            const code = prop.code || prop.property_code;
            const name = prop.name || prop.property_name;
            const isSelecting = selecting === code;

            return (
              <button
                key={code}
                onClick={() => handleSelect(code)}
                disabled={!!selecting}
                className="group relative flex flex-col items-center justify-center bg-white/5 hover:bg-white/10 border border-white/10 hover:border-brand-gold/50 rounded-2xl p-8 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSelecting ? (
                  <Loader2 className="w-8 h-8 text-brand-gold animate-spin mb-3" />
                ) : (
                  <div className="w-14 h-14 rounded-xl bg-brand-gold/10 group-hover:bg-brand-gold/20 flex items-center justify-center mb-4 transition-colors">
                    <Building2 className="w-8 h-8 text-brand-gold" />
                  </div>
                )}
                <span className="text-white text-xl font-bold mb-1">{code}</span>
                <span className="text-white/60 text-sm">{name}</span>
              </button>
            );
          })}
        </div>
      )}

      <p className="text-white/30 text-xs mt-10">
        To switch properties, sign out and sign back in.
      </p>
    </div>
  );
}
