import React, { createContext, useContext, useState, useEffect } from 'react';

const TenantContext = createContext(null);

export function TenantProvider({ children }) {
  const [tenant, setTenant] = useState(() => {
    const saved = localStorage.getItem('dormtel_tenant');
    return saved ? JSON.parse(saved) : null;
  });

  useEffect(() => {
    if (tenant) {
      localStorage.setItem('dormtel_tenant', JSON.stringify(tenant));
    } else {
      localStorage.removeItem('dormtel_tenant');
    }
  }, [tenant]);

  const login = (tenantData) => setTenant(tenantData);
  const logout = () => setTenant(null);

  return (
    <TenantContext.Provider value={{ tenant, login, logout }}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  const ctx = useContext(TenantContext);
  if (!ctx) throw new Error('useTenant must be used within TenantProvider');
  return ctx;
}
