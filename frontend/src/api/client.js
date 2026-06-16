import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_API_URL || '';

const client = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('dt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';
    if (error.response?.status === 401) {
      localStorage.removeItem('dt_token');
      window.location.href = '/login';
    } else {
      toast.error(message);
    }
    return Promise.reject(error);
  }
);

export default client;

// Health check uses root path, not /api/v1
export async function fetchHealth() {
  const res = await axios.get(`${API_BASE}/health`);
  return res.data;
}
