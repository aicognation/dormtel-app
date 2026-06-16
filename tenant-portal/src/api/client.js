import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '';

const client = axios.create({
  baseURL: `${API_URL}/api/v1/tenant`,
  headers: { 'Content-Type': 'application/json' },
});

export default client;
