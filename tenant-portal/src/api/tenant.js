import client from './client';

export const tenantLogin = (email, phone, bedCode, dbSchema = 'demo') =>
  client.post('/login', { email, phone, bed_code: bedCode, db_schema: dbSchema });

export const getDashboard = (id) => client.get(`/dashboard/${id}`);

export const getBillings = (id, status) => {
  const params = status ? { status } : {};
  return client.get(`/billings/${id}`, { params });
};

export const getPayments = (id) => client.get(`/payments/${id}`);

export const makePayment = (id, data) => client.post(`/payments/${id}/pay`, data);

export const getServiceRequests = (id, status) => {
  const params = status ? { status } : {};
  return client.get(`/service-requests/${id}`, { params });
};

export const createServiceRequest = (id, data) => client.post(`/service-requests/${id}`, data);

export const getMoveOut = (id) => client.get(`/moveout/${id}`);

export const createMoveOut = (id, data) => client.post(`/moveout/${id}`, data);

export const getProfile = (id) => client.get(`/profile/${id}`);

export const getAnnouncements = () => client.get('/announcements');

export const getInquiries = (id) => client.get(`/inquiries/${id}`);

export const createInquiry = (id, data) => client.post(`/inquiry/${id}`, data);
