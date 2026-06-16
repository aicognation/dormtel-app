import client from './client';

export async function listFaqs(params = {}) {
  return client.get('/faqs', { params });
}

export async function listFaqCategories() {
  return client.get('/faqs/categories');
}

export async function createFaq(payload) {
  return client.post('/faqs', payload);
}
