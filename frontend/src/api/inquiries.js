import client from './client';

export function listInquiries(params = {}) {
  return client.get('/inquiries/', { params });
}

export function getInquiry(id) {
  return client.get(`/inquiries/${id}`);
}

export function createInquiry(data) {
  return client.post('/inquiries/', data);
}

export function respondToInquiry(id) {
  return client.post(`/inquiries/${id}/respond`);
}

export function respondToInquiryManual(id, response) {
  return client.patch(`/inquiries/${id}/respond`, { response });
}

export function escalateInquiry(id) {
  return client.post(`/inquiries/${id}/escalate`);
}

export function getConvertibleInquiries() {
  return client.get('/inquiries/convertible');
}
