import client from './client';

export function listRooms() {
  return client.get('/onboarding/rooms');
}

export function createReservation(data) {
  return client.post('/onboarding/reservations', data);
}

export function generatePaymentLink(residentId) {
  return client.post(`/onboarding/reservations/${residentId}/payment-link`);
}

export function activateMoveIn(residentId) {
  return client.post(`/onboarding/moveins/${residentId}/activate`);
}

export function getRoomTenants(roomId) {
  return client.get(`/onboarding/rooms/${roomId}/tenants`);
}
