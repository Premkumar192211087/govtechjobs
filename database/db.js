/**
 * Database layer with in-memory fallback for local development.
 * When DATABASE_URL is configured, uses PostgreSQL via node-postgres.
 * Otherwise, uses an in-memory store seeded with demo data.
 */

const logger = require('../utils/logger');

let pool = null;
let useInMemory = true;

// In-memory data store
let memoryStore = {
  jobs: [],
  cutoffs: [],
  portals: [],
  scrapeLogs: []
};

/**
 * Initialize database connection
 */
async function initDatabase() {
  if (process.env.DATABASE_URL) {
    try {
      const { Pool } = require('pg');
      pool = new Pool({ connectionString: process.env.DATABASE_URL, ssl: { rejectUnauthorized: false } });
      await pool.query('SELECT 1');
      useInMemory = false;
      logger.info('Database', 'Connected to PostgreSQL');
      return;
    } catch (err) {
      logger.warn('Database', 'PostgreSQL unavailable, falling back to in-memory', { error: err.message });
    }
  }

  logger.info('Database', 'Using in-memory database with seed data');
  useInMemory = true;
  seedData();
}

/**
 * Seed the in-memory store with realistic demo data
 */
function seedData() {
  memoryStore.jobs = [];
  memoryStore.cutoffs = [];

  // Load portals from config
  const { portals: portalConfig } = require('../config/portals');
  memoryStore.portals = portalConfig.map((p, i) => ({
    id: i + 1,
    name: p.name,
    short_name: p.shortName,
    url: p.url,
    description: p.description,
    category: p.category,
    exams_covered: p.exams,
    it_roles_available: p.itRoles,
    last_scraped: null,
    scrape_status: 'pending',
    is_active: true
  }));

  logger.info('Database', `Portals list initialized with ${memoryStore.portals.length} portals. Real-time scrapers will populate jobs.`);
}

/**
 * Save a scraped job notification to the database (in-memory or Postgres)
 */
async function saveJob(job) {
  if (useInMemory) {
    const exists = memoryStore.jobs.some(j => 
      j.exam_name === job.exam_name && 
      j.organization === job.organization && 
      j.notification_date === job.notification_date
    );
    if (!exists) {
      job.id = memoryStore.jobs.length + 1;
      job.created_at = new Date().toISOString();
      job.updated_at = new Date().toISOString();
      memoryStore.jobs.push(job);
      logger.info('Database', `Saved new job to memory: ${job.exam_name} (${job.organization})`);
    }
  } else {
    try {
      const query = `
        INSERT INTO jobs (
          exam_name, organization, organization_full, post_name, job_domain, 
          vacancies, qualification, experience_required, age_limit, application_fee, 
          pay_scale, location, notification_date, application_start_date, application_last_date, 
          exam_date, status, apply_link, portal_url, notification_pdf_url, 
          portal_instructions, source_url, total_marks, created_at, updated_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, NOW(), NOW())
        ON CONFLICT (exam_name, organization, notification_date) 
        DO UPDATE SET
          post_name = EXCLUDED.post_name,
          vacancies = EXCLUDED.vacancies,
          application_last_date = EXCLUDED.application_last_date,
          status = EXCLUDED.status,
          apply_link = EXCLUDED.apply_link,
          updated_at = NOW()
        RETURNING id;
      `;
      const values = [
        job.exam_name, job.organization, job.organization_full, job.post_name, job.job_domain,
        job.vacancies, job.qualification, job.experience_required, job.age_limit, job.application_fee,
        job.pay_scale, job.location, job.notification_date, job.application_start_date, job.application_last_date,
        job.exam_date, job.status, job.apply_link, job.portal_url, job.notification_pdf_url,
        job.portal_instructions, job.source_url, job.total_marks
      ];
      const res = await pool.query(query, values);
      logger.info('Database', `Saved new job to Postgres: ${job.exam_name} (${job.organization})`);
      return res.rows[0]?.id;
    } catch (err) {
      logger.error('Database', 'Error saving job to Postgres', { error: err.message });
    }
  }
}


// ============================================================
// Query interface (works for both PG and in-memory)
// ============================================================

/**
 * Get jobs with filtering, searching, and pagination
 */
async function getJobs(filters = {}) {
  const { domain, organization, status, qualification, experience, search, page = 1, limit = 20 } = filters;

  let jobs = [...memoryStore.jobs];

  // Apply filters
  if (domain) {
    jobs = jobs.filter(j => j.job_domain === domain);
  }
  if (organization) {
    jobs = jobs.filter(j => j.organization.toLowerCase() === organization.toLowerCase());
  }
  if (status) {
    jobs = jobs.filter(j => j.status === status);
  }
  if (qualification) {
    jobs = jobs.filter(j => j.qualification && j.qualification.toLowerCase().includes(qualification.toLowerCase()));
  }
  if (experience) {
    jobs = jobs.filter(j => j.experience_required && j.experience_required.toLowerCase().includes(experience.toLowerCase()));
  }
  if (search) {
    const q = search.toLowerCase();
    jobs = jobs.filter(j =>
      (j.exam_name && j.exam_name.toLowerCase().includes(q)) ||
      (j.organization && j.organization.toLowerCase().includes(q)) ||
      (j.post_name && j.post_name.toLowerCase().includes(q)) ||
      (j.organization_full && j.organization_full.toLowerCase().includes(q))
    );
  }

  const total = jobs.length;
  const offset = (page - 1) * limit;
  const paginatedJobs = jobs.slice(offset, offset + limit);

  return {
    jobs: paginatedJobs,
    total,
    page: parseInt(page),
    totalPages: Math.ceil(total / limit)
  };
}

/**
 * Get a single job by ID
 */
async function getJobById(id) {
  return memoryStore.jobs.find(j => j.id === parseInt(id)) || null;
}

/**
 * Get cutoffs for a job
 */
async function getCutoffsByJobId(jobId) {
  return memoryStore.cutoffs.filter(c => c.job_id === parseInt(jobId));
}

/**
 * Get cutoffs with filtering
 */
async function getCutoffs(filters = {}) {
  const { exam, year, category } = filters;
  let cutoffs = [...memoryStore.cutoffs];

  if (year) cutoffs = cutoffs.filter(c => c.year === parseInt(year));
  if (category) cutoffs = cutoffs.filter(c => c.category.toLowerCase() === category.toLowerCase());

  // Enrich with job info
  return cutoffs.map(c => {
    const job = memoryStore.jobs.find(j => j.id === c.job_id);
    return { ...c, exam_name: job?.exam_name, organization: job?.organization };
  });
}

/**
 * Get all portals
 */
async function getPortals(category = null) {
  if (category) {
    return memoryStore.portals.filter(p => p.category === category);
  }
  return memoryStore.portals;
}

/**
 * Get portal by short name
 */
async function getPortalByShortName(shortName) {
  return memoryStore.portals.find(p => p.short_name.toLowerCase() === shortName.toLowerCase()) || null;
}

/**
 * Get dashboard stats
 */
async function getStats() {
  const jobs = memoryStore.jobs;
  const activeJobs = jobs.filter(j => j.status === 'active');
  const itJobs = jobs.filter(j => ['software_it', 'telecom', 'cybersecurity', 'data_analytics'].includes(j.job_domain));
  const totalVacancies = jobs.reduce((sum, j) => sum + (j.vacancies || 0), 0);

  // Count by domain
  const domainCounts = {};
  jobs.forEach(j => {
    domainCounts[j.job_domain] = (domainCounts[j.job_domain] || 0) + 1;
  });

  // Count by organization
  const orgCounts = {};
  jobs.forEach(j => {
    orgCounts[j.organization] = (orgCounts[j.organization] || 0) + 1;
  });

  return {
    totalJobs: jobs.length,
    activeJobs: activeJobs.length,
    itJobs: itJobs.length,
    totalVacancies,
    totalPortals: memoryStore.portals.length,
    domainCounts,
    orgCounts,
    lastUpdated: new Date().toISOString()
  };
}

module.exports = {
  initDatabase,
  getJobs,
  getJobById,
  getCutoffsByJobId,
  getCutoffs,
  getPortals,
  getPortalByShortName,
  getStats,
  saveJob
};
