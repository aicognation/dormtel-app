import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import client from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [staff, setStaff] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadStaff = useCallback(async () => {
    const token = localStorage.getItem('dt_token');
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const data = await client.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setStaff(data);
    } catch {
      localStorage.removeItem('dt_token');
      localStorage.removeItem('dt_schema');
      setStaff(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStaff();
  }, [loadStaff]);

  const login = async (email, password, schema = 'demo') => {
    const data = await client.post('/auth/login', { email, password, schema });
    localStorage.setItem('dt_token', data.access_token);
    localStorage.setItem('dt_schema', schema);
    setStaff(data.staff);
    return data;
  };

  const logout = () => {
    localStorage.removeItem('dt_token');
    localStorage.removeItem('dt_schema');
    setStaff(null);
    window.location.href = '/login';
  };

  const token = () => localStorage.getItem('dt_token');
  const schema = () => localStorage.getItem('dt_schema') || 'demo';

  const value = {
    staff,
    isAuthenticated: !!staff,
    isManager: staff?.role === 'manager',
    isAdmin: staff?.role === 'manager' || staff?.role === 'admin',
    loading,
    login,
    logout,
    token,
    schema,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
