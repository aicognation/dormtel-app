export const STATUS_COLORS = {
  // Green statuses
  active: 'bg-green-100 text-green-800',
  approved: 'bg-green-100 text-green-800',
  paid: 'bg-green-100 text-green-800',
  matched: 'bg-green-100 text-green-800',
  completed: 'bg-green-100 text-green-800',
  ok: 'bg-green-100 text-green-800',
  verified: 'bg-green-100 text-green-800',

  // Yellow statuses
  pending: 'bg-yellow-100 text-yellow-800',
  pending_review: 'bg-yellow-100 text-yellow-800',
  draft: 'bg-yellow-100 text-yellow-800',
  reserved: 'bg-yellow-100 text-yellow-800',

  // Red statuses
  overdue: 'bg-red-100 text-red-800',
  rejected: 'bg-red-100 text-red-800',
  error: 'bg-red-100 text-red-800',
  unreconciled: 'bg-red-100 text-red-800',

  // Blue statuses
  new: 'bg-blue-100 text-blue-800',
  responded: 'bg-blue-100 text-blue-800',
  distributed: 'bg-blue-100 text-blue-800',

  // Purple statuses
  escalated: 'bg-purple-100 text-purple-800',
  clearance: 'bg-purple-100 text-purple-800',
  refund_pending: 'bg-purple-100 text-purple-800',
  requested: 'bg-purple-100 text-purple-800',
  in_progress: 'bg-purple-100 text-purple-800',

  // Blue statuses
  submitted: 'bg-blue-100 text-blue-800',
  acknowledged: 'bg-blue-100 text-blue-800',

  // Green statuses
  resolved: 'bg-green-100 text-green-800',

  // Gray fallback
  moved_out: 'bg-gray-100 text-gray-800',
  closed: 'bg-gray-100 text-gray-800',
};

export const INQUIRY_SOURCES = [
  { value: 'facebook', label: 'Facebook' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'walkin', label: 'Walk-in' },
  { value: 'phone', label: 'Phone' },
  { value: 'email', label: 'Email' },
  { value: 'referral', label: 'Referral' },
];

export const INQUIRY_STATUSES = [
  { value: '', label: 'All Statuses' },
  { value: 'new', label: 'New' },
  { value: 'responded', label: 'Responded' },
  { value: 'escalated', label: 'Escalated' },
  { value: 'converted', label: 'Converted' },
  { value: 'closed', label: 'Closed' },
];

export const BILLING_STATUSES = [
  { value: '', label: 'All Statuses' },
  { value: 'draft', label: 'Draft' },
  { value: 'pending_review', label: 'Pending Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'distributed', label: 'Distributed' },
  { value: 'paid', label: 'Paid' },
  { value: 'overdue', label: 'Overdue' },
];

export const MOVEOUT_STATUSES = [
  { value: '', label: 'All Statuses' },
  { value: 'requested', label: 'Requested' },
  { value: 'clearance', label: 'Clearance' },
  { value: 'refund_pending', label: 'Refund Pending' },
  { value: 'completed', label: 'Completed' },
];

export const PAYMENT_METHODS = [
  { value: 'gcash', label: 'GCash' },
  { value: 'maya', label: 'Maya' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'cash', label: 'Cash' },
  { value: 'salary_deduction', label: 'Salary Deduction' },
];

export const SERVICE_REQUEST_STATUSES = [
  { value: '', label: 'All Statuses' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'acknowledged', label: 'Acknowledged' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
];

export const SERVICE_REQUEST_CATEGORIES = [
  { value: '', label: 'All Categories' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'repair', label: 'Repair' },
  { value: 'cleaning', label: 'Cleaning' },
  { value: 'plumbing', label: 'Plumbing' },
  { value: 'electrical', label: 'Electrical' },
  { value: 'hvac', label: 'HVAC' },
  { value: 'furniture', label: 'Furniture' },
  { value: 'pest_control', label: 'Pest Control' },
  { value: 'security', label: 'Security' },
  { value: 'noise_complaint', label: 'Noise Complaint' },
  { value: 'other', label: 'Other' },
];

export const SERVICE_REQUEST_PRIORITIES = [
  { value: '', label: 'All Priorities' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

export const ID_TYPES = [
  { value: 'national_id', label: 'National ID' },
  { value: 'drivers_license', label: "Driver's License" },
  { value: 'passport', label: 'Passport' },
  { value: 'company_id', label: 'Company ID' },
  { value: 'sss', label: 'SSS ID' },
  { value: 'philhealth', label: 'PhilHealth ID' },
];
