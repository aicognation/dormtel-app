import client from './client';

export function listMoveOuts(params = {}) {
  return client.get('/moveouts/', { params });
}

export function createMoveOut(data) {
  return client.post('/moveouts/', data);
}

export function generateClearance(id) {
  return client.post(`/moveouts/${id}/clearance`);
}

export function finalizeMoveOut(id) {
  return client.post(`/moveouts/${id}/finalize`);
}

export function completeMoveOut(id) {
  return client.post(`/moveouts/${id}/complete`);
}

export function extendMoveOut(id, data) {
  return client.post(`/moveouts/${id}/extend`, data);
}
