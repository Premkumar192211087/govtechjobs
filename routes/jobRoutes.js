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

// POST /api/jobs/sync-ai — Run Node scrapers + call FastAPI ML model for ALL 44+ portals
router.post('/sync-ai', async (req, res) => {
  try {
    const axios = require('axios');
    const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';
    
    // Step 1: Run Node scrapers first (fast, always works)
    const { runAllScrapers } = require('../scrapers/scheduler');
    const nodeResults = await runAllScrapers();
    const nodeJobCount = nodeResults.reduce((sum, r) => sum + r.jobsFound, 0);

    // Step 2: Call AI service for remaining 44+ portals
    let aiJobCount = 0;
    let aiErrors = [];
    try {
      const response = await axios.post(`${AI_SERVICE_URL}/reload-notifications`, {}, {
        timeout: 600000 // 10 minutes — concurrent scraping of 44+ portals
      });
      
      if (response.data && response.data.success && response.data.jobs) {
        for (const job of response.data.jobs) {
          try {
            await db.saveJob(job);
            aiJobCount++;
          } catch (err) {
            // Skip duplicates
          }
        }
        aiErrors = response.data.errors || [];
      }
    } catch (aiErr) {
      console.error('AI Service sync failed (Node scrapers still ran):', aiErr.message);
    }

    return res.json({
      success: true,
      count: nodeJobCount + aiJobCount,
      totalFound: nodeJobCount + aiJobCount,
      portalsScraped: 5 + 44, // Node + AI portals
      nodeJobsFound: nodeJobCount,
      aiJobsFound: aiJobCount,
      errors: aiErrors
    });
  } catch (err) {
    console.error('Error syncing:', err.message);
    res.status(500).json({ error: 'Sync failed', details: err.message });
  }
});

// DELETE /api/jobs/clear — Wipe all stale jobs before a full resync
router.delete('/clear', async (req, res) => {
  try {
    const count = await db.clearAllJobs();
    res.json({ success: true, cleared: count });
  } catch (err) {
    console.error('Error clearing jobs:', err);
    res.status(500).json({ error: 'Failed to clear jobs' });
  }
});

module.exports = router;

