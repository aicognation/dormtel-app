import client from './client';

export function listResidents(params = {}) {
  return client.get('/residents', { params });
}

export function getResident(id) {
  return client.get(`/residents/${id}`);
}

export function createResident(data) {
  return client.post('/residents', data);
}

export function updateResident(id, data) {
  return client.patch(`/residents/${id}`, data);
}

export function deactivateResident(id) {
  return client.delete(`/residents/${id}`);
}
