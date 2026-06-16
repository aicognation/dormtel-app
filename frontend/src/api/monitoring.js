import client from './client';

export async function getDailyMonitoring(params = {}) {
  return client.get('/monitoring/daily', { params });
}

export async function getCurrentOccupancy(params = {}) {
  return client.get('/monitoring/occupancy', { params });
}
