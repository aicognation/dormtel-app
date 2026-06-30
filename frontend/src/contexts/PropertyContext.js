import React, { createContext, useContext, useState, useCallback } from 'react';

const PropertyContext = createContext(null);

const PROPERTIES = {
  DT01: { code: 'DT01', name: 'Recto Branch' },
  DT02: { code: 'DT02', name: 'Sta. Mesa Branch' },
};

export function PropertyProvider({ children }) {
  const [propertyCode, setPropertyCode] = useState(() => localStorage.getItem('dt_property') || null);

  const property = propertyCode ? PROPERTIES[propertyCode] : null;

  const selectProperty = useCallback((code) => {
    localStorage.setItem('dt_property', code);
    setPropertyCode(code);
  }, []);

  const clearProperty = useCallback(() => {
    localStorage.removeItem('dt_property');
    setPropertyCode(null);
  }, []);

  return (
    <PropertyContext.Provider value={{ propertyCode, property, selectProperty, clearProperty, properties: PROPERTIES }}>
      {children}
    </PropertyContext.Provider>
  );
}

export function useProperty() {
  const ctx = useContext(PropertyContext);
  if (!ctx) throw new Error('useProperty must be used within PropertyProvider');
  return ctx;
}
