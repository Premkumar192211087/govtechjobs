/**
 * Scraper Scheduler — orchestrates all scrapers using node-cron.
 * Runs Node.js scrapers + calls FastAPI AI service for ALL 59+ portals.
 */

const cron = require('node-cron');
const logger = require('../utils/logger');
const db = require('../database/db');

// Import all Node.js scrapers
const UpscScraper = require('./upscScraper');
const CdacScraper = require('./cdacScraper');
const SscScraper = require('./sscScraper');
const IbpsScraper = require('./ibpsScraper');
const IsroScraper = require('./isroScraper');

const scrapers = [UpscScraper, CdacScraper, SscScraper, IbpsScraper, IsroScraper];

/**
 * Call the FastAPI AI service to scrape ALL registered portals (covers 59+ portals)
 */
async function syncFromAIService() {
  try {
    const axios = require('axios');
    const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';
    
    logger.info('Scheduler', 'Calling FastAPI AI service for full portal scrape...');
    const response = await axios.post(`${AI_SERVICE_URL}/reload-notifications`, {}, {
      timeout: 600000 // 10 minutes — scraping 45+ portals takes time
    });
    
    if (response.data && response.data.success && response.data.jobs) {
      let savedCount = 0;
      for (const job of response.data.jobs) {
        try {
          await db.saveJob(job);
          savedCount++;
        } catch (err) {
          // Skip duplicates silently
        }
      }
      logger.info('Scheduler', `AI Service returned ${response.data.total_jobs_found} jobs, saved ${savedCount} new entries`);
      
      if (response.data.errors && response.data.errors.length > 0) {
        logger.warn('Scheduler', `AI Service had ${response.data.errors.length} portal errors`, {
          errors: response.data.errors.map(e => `${e.portal}: ${e.error}`).join(', ')
        });
      }
    }
  } catch (err) {
    logger.warn('Scheduler', `AI Service unavailable (will use Node scrapers only)`, { error: err.message });
  }
}

/**
 * Run all registered Node.js scrapers
 */
async function runAllScrapers() {
  logger.info('Scheduler', `Starting scrape cycle — ${scrapers.length} Node scrapers + AI service`);

  const results = [];
  for (const ScraperClass of scrapers) {
    try {
      const scraper = new ScraperClass();
      const result = await scraper.run();
      results.push(result);

      if (result.status === 'success' && result.jobs && result.jobs.length > 0) {
        for (const job of result.jobs) {
          await db.saveJob(job);
        }
      }
    } catch (err) {
      logger.error('Scheduler', `Scraper execution failed`, { error: err.message });
    }

    // Be polite: wait between portals
    await new Promise(resolve => setTimeout(resolve, 3000));
  }

  // Also call FastAPI AI service for the remaining portals
  await syncFromAIService();

  const successful = results.filter(r => r.status === 'success').length;
  const failed = results.filter(r => r.status === 'error').length;
  const totalJobs = results.reduce((sum, r) => sum + r.jobsFound, 0);

  logger.info('Scheduler', 'Scrape cycle complete', {
    nodeScrapersSuccessful: successful,
    nodeScrapersFailed: failed,
    nodeJobsFound: totalJobs
  });

  return results;
}

/**
 * Initialize the cron scheduler
 */
function initScheduler() {
  const interval = process.env.SCRAPE_INTERVAL_HOURS || 6;
  const cronExpression = `0 */${interval} * * *`;

  cron.schedule(cronExpression, async () => {
    logger.info('Scheduler', `Scheduled scrape triggered (every ${interval} hours)`);
    await runAllScrapers();
  });

  logger.info('Scheduler', `Initialized — scraping every ${interval} hours`);
  logger.info('Scheduler', `${scrapers.length} Node scrapers + FastAPI AI service registered`);
}

module.exports = { initScheduler, runAllScrapers, syncFromAIService };
