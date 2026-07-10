/**
 * GovTechJobs — Express Server Entry Point
 *
 * Serves the frontend, API routes, and schedules scrapers.
 */

require('dotenv').config();

const express = require('express');
const cors = require('cors');
const path = require('path');
const logger = require('./utils/logger');
const db = require('./database/db');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// API Routes
app.use('/api/jobs', require('./routes/jobRoutes'));
app.use('/api/portals', require('./routes/portalRoutes'));
app.use('/api', require('./routes/statsRoutes'));

// Health check (for cron-job.org keep-alive)
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development'
  });
});

// Manual scrape trigger
app.post('/api/scrape', async (req, res) => {
  try {
    const { runAllScrapers } = require('./scrapers/scheduler');
    // Run scrapers in background, respond immediately
    res.json({ message: 'Scrape triggered', status: 'running' });
    runAllScrapers().catch(err => {
      logger.error('Server', 'Manual scrape failed', { error: err.message });
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to trigger scrape', details: err.message });
  }
});

// SPA fallback — serve index.html for all other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start server
async function start() {
  try {
    await db.initDatabase();
    
    // Initialize scraper scheduler and run scrapers asynchronously
    const { initScheduler, runAllScrapers } = require('./scrapers/scheduler');
    initScheduler();
    
    app.listen(PORT, () => {
      logger.info('Server', `GovTechJobs running on http://localhost:${PORT}`);
      logger.info('Server', `Environment: ${process.env.NODE_ENV || 'development'}`);
      
      // Trigger live scrape in background on startup
      runAllScrapers().catch(err => {
        logger.error('Server', 'Initial live scrape failed', { error: err.message });
      });
    });
  } catch (err) {
    logger.error('Server', 'Failed to start', { error: err.message });
    process.exit(1);
  }
}

start();
