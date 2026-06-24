import client from './client';

export function generateStatements(data) {
  return client.post('/statements/generate', data);
}

export function listStatements(params = {}) {
  return client.get('/statements', { params });
}

export function downloadStatement(statementId) {
  return client.get(`/statements/${statementId}/download`, { responseType: 'blob' });
}

export function sendStatementEmail(statementId, data) {
  return client.post(`/statements/${statementId}/send-email`, data);
}
