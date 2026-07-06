/**
 * Job API routes — /api/jobs
 */

const express = require('express');
const router = express.Router();
const db = require('../database/db');

// GET /api/jobs — List all jobs with filters & pagination
router.get('/', async (req, res) => {
  try {
    const filters = {
      domain: req.query.domain,
      organization: req.query.org || req.query.organization,
      status: req.query.status,
      qualification: req.query.qualification,
      experience: req.query.experience,
      search: req.query.q || req.query.search,
      page: req.query.page || 1,
      limit: req.query.limit || 20
    };

    const result = await db.getJobs(filters);
    res.json(result);
  } catch (err) {
    console.error('Error fetching jobs:', err);
    res.status(500).json({ error: 'Failed to fetch jobs' });
  }
});

// GET /api/jobs/search — Search jobs
router.get('/search', async (req, res) => {
  try {
    const result = await db.getJobs({
      search: req.query.q,
      domain: req.query.domain,
      page: req.query.page || 1,
      limit: req.query.limit || 20
    });
    res.json(result);
  } catch (err) {
    console.error('Error searching jobs:', err);
    res.status(500).json({ error: 'Search failed' });
  }
});

// GET /api/jobs/filter — Multi-filter endpoint
router.get('/filter', async (req, res) => {
  try {
    const result = await db.getJobs({
      domain: req.query.domain,
      organization: req.query.org,
      status: req.query.status,
      qualification: req.query.qualification,
      experience: req.query.experience,
      search: req.query.q,
      page: req.query.page || 1,
      limit: req.query.limit || 20
    });
    res.json(result);
  } catch (err) {
    console.error('Error filtering jobs:', err);
    res.status(500).json({ error: 'Filter failed' });
  }
});

// GET /api/jobs/:id — Single job details
router.get('/:id', async (req, res) => {
  try {
    const job = await db.getJobById(req.params.id);
    if (!job) {
      return res.status(404).json({ error: 'Job not found' });
    }
    const cutoffs = await db.getCutoffsByJobId(req.params.id);
    res.json({ ...job, cutoffs });
  } catch (err) {
    console.error('Error fetching job:', err);
    res.status(500).json({ error: 'Failed to fetch job' });
  }
});

module.exports = router;
