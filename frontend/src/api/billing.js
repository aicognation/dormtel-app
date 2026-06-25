import client from './client';

export function listBillings(params = {}) {
  return client.get('/billings/', { params });
}

export function submitMeterReading(data) {
  return client.post('/billings/meter-readings', data);
}

export function bulkUpsertMeterReadings(data) {
  return client.post('/billings/meter-readings/bulk-upsert', data);
}

export function generateBilling(data) {
  return client.post('/billings/generate', data);
}

export function approveBilling(id) {
  return client.post(`/billings/${id}/approve`);
}

export function distributeBilling(id) {
  return client.post(`/billings/${id}/distribute`);
}

export function downloadMeterReadingTemplate() {
  return client.get('/billings/meter-readings/template', {
    responseType: 'blob',
  });
}

export function uploadMeterReadings(file) {
  const formData = new FormData();
  formData.append('file', file);
  return client.post('/billings/meter-readings/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export function uploadDailyMeterSheet(file) {
  const formData = new FormData();
  formData.append('file', file);
  return client.post('/billings/meter-readings/upload-daily-sheet', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export function listMeterReadings(params = {}) {
  return client.get('/billings/meter-readings', { params });
}

export function getDailyMeterGrid(params) {
  return client.get('/billings/meter-readings/daily-grid', { params });
}

export function previewBilling(data) {
  return client.post('/billings/preview', data);
}

export function getBillingImportStatus(params) {
  return client.get('/billings/import-status', { params });
}
