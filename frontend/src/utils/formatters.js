export function formatCurrency(amount) {
  if (amount == null) return '₱0.00';
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency: 'PHP',
  }).format(Number(amount));
}

export function formatDate(isoString) {
  if (!isoString) return '—';
  return new Date(isoString).toLocaleDateString('en-PH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(isoString) {
  if (!isoString) return '—';
  return new Date(isoString).toLocaleString('en-PH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export function shortUUID(uuid) {
  if (!uuid) return '—';
  return uuid.substring(0, 8);
}

export function truncate(text, maxLen = 50) {
  if (!text) return '—';
  return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
}
