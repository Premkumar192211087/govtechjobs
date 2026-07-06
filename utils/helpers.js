/**
 * Helper utilities — date formatting, text parsing, status logic
 */

/**
 * Format a date string for display (e.g., "15 Jul 2025")
 */
function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return 'N/A';
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
}

/**
 * Calculate days remaining until a date
 */
function daysRemaining(dateStr) {
  if (!dateStr) return null;
  const target = new Date(dateStr);
  const now = new Date();
  const diffMs = target.getTime() - now.getTime();
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
}

/**
 * Determine job status based on dates
 */
function computeStatus(job) {
  const now = new Date();
  if (job.application_start_date && new Date(job.application_start_date) > now) {
    return 'upcoming';
  }
  if (job.application_last_date && new Date(job.application_last_date) < now) {
    if (job.exam_date && new Date(job.exam_date) > now) return 'exam_scheduled';
    if (job.exam_date && new Date(job.exam_date) < now) return 'result';
    return 'closed';
  }
  return 'active';
}

/**
 * Generate a URL-friendly slug
 */
function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

/**
 * Truncate text with ellipsis
 */
function truncate(text, maxLen = 100) {
  if (!text || text.length <= maxLen) return text;
  return text.substring(0, maxLen) + '...';
}

/**
 * Parse pay scale text into CPC level number
 */
function parsePayLevel(payScale) {
  if (!payScale) return null;
  const match = payScale.match(/level\s*(\d+)/i);
  return match ? parseInt(match[1]) : null;
}

/**
 * Map domain codes to display labels
 */
const domainLabels = {
  software_it: '🖥️ Software/IT',
  telecom: '📡 Telecom/Networking',
  cybersecurity: '🔒 Cybersecurity',
  data_analytics: '📊 Data/Analytics',
  non_it: '🏛️ Non-IT Government',
  banking: '🏦 Banking/Finance',
  psu: '⚡ PSU/Engineering',
  teaching: '🎓 Teaching/Research'
};

/**
 * Map status codes to display labels
 */
const statusLabels = {
  active: '🟢 Apply Now',
  upcoming: '🟡 Coming Soon',
  exam_scheduled: '🔵 Exam Scheduled',
  result: '🟠 Result Out',
  closed: '🔴 Closed'
};

module.exports = {
  formatDate,
  daysRemaining,
  computeStatus,
  slugify,
  truncate,
  parsePayLevel,
  domainLabels,
  statusLabels
};
