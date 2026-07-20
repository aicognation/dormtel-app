import client from './client';

export function listCampaigns() {
  return client.get('/qr-campaigns/');
}

export function createCampaign(data) {
  return client.post('/qr-campaigns/', data);
}

export function getCampaignLeads(id) {
  return client.get(`/qr-campaigns/${id}/leads`);
}
