import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '';

const client = axios.create({
  baseURL: `${API_URL}/api/v1/tenant`,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config) => {
  const saved = localStorage.getItem('dormtel_tenant');
  if (saved) {
    try {
      const tenant = JSON.parse(saved);
      if (tenant.db_schema) {
        config.headers['X-Tenant-Schema'] = tenant.db_schema;
      }
    } catch {
      // ignore parse errors
    }
  }
  return config;
});

export default client;
