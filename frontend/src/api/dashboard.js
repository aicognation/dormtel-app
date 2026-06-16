import client from './client';

export function getDashboardStats(period = 'monthly') {
  return client.get('/dashboard/stats', { params: { period } });
}

export function getDashboardEvents(type, year, month) {
  return client.get('/dashboard/events', { params: { type, year, month } });
}
