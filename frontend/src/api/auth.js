import client from './client';

export function listStaff() {
  return client.get('/auth/staff');
}

export function getCurrentStaff() {
  return client.get('/auth/me');
}
