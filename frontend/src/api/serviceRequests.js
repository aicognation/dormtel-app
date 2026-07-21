import client from './client';

export function listServiceRequests(params = {}) {
  return client.get('/service-requests/', { params });
}

export function updateServiceRequestStatus(id, data) {
  return client.patch(`/service-requests/${id}/status`, data);
}

export function assignServiceRequest(id, data) {
  return client.post(`/service-requests/${id}/assign`, data);
}

export function createServiceRequest(data) {
  return client.post('/service-requests/', data);
}
