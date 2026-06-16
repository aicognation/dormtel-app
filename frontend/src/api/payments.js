import client from './client';

export function getDSR() {
  return client.get('/payments/dsr');
}

export function getUnmatched() {
  return client.get('/payments/unmatched');
}

export function listPayments(params = {}) {
  return client.get('/payments/list', { params });
}

export function reconcilePayments(paymentIds = null) {
  return client.post('/payments/reconcile', paymentIds ? { payment_ids: paymentIds } : {});
}

export function matchPayment(id, data) {
  return client.post(`/payments/${id}/match`, data);
}

export function simulateWebhook(data) {
  return client.post('/payments/webhook', data);
}

export function getDormerLedger(residentId) {
  return client.get(`/payments/ledger/${residentId}`);
}

export function getAllLedgers(params = {}) {
  return client.get('/payments/ledgers', { params });
}
