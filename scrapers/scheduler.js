/**
 * Scraper Scheduler — orchestrates all scrapers using node-cron.
 * Runs Node.js scrapers + calls FastAPI AI service for ALL 44+ portals.
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
 * Call the FastAPI AI service to scrape ALL registered portals (covers 44+ portals)
 * Retries up to 3 times with 30s delay between attempts (handles cold starts)
 */
async function syncFromAIService(retries = 3) {
  const axios = require('axios');
  const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      logger.info('Scheduler', `Calling AI service for full portal scrape (attempt ${attempt}/${retries})...`);
      const response = await axios.post(`${AI_SERVICE_URL}/reload-notifications`, {}, {
        timeout: 600000 // 10 minutes — concurrent scraping of 44+ portals
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
            errors: response.data.errors.slice(0, 5).map(e => `${e.portal}: ${e.error}`).join(', ')
          });
        }
        return; // Success — exit retry loop
      }
    } catch (err) {
      logger.warn('Scheduler', `AI Service attempt ${attempt}/${retries} failed`, { error: err.message });
      if (attempt < retries) {
        logger.info('Scheduler', `Waiting 30s before retry...`);
        await new Promise(resolve => setTimeout(resolve, 30000));
      }
    }
  }
  logger.warn('Scheduler', 'AI Service sync failed after all retries (Node scrapers still active)');
}

/**
 * Run all registered Node.js scrapers
 */
async function runAllScrapers() {
  logger.info('Scheduler', `Starting scrape cycle — ${scrapers.length} Node scrapers`);

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

  const successful = results.filter(r => r.status === 'success').length;
  const failed = results.filter(r => r.status === 'error').length;
  const totalJobs = results.reduce((sum, r) => sum + r.jobsFound, 0);

  logger.info('Scheduler', 'Node scrape cycle complete', {
    nodeScrapersSuccessful: successful,
    nodeScrapersFailed: failed,
    nodeJobsFound: totalJobs
  });

  return results;
}

/**
 * Full scrape cycle: Node scrapers + AI service
 */
async function runFullScrape() {
  await runAllScrapers();
  await syncFromAIService();
}

/**
 * Initialize the cron scheduler
 */
function initScheduler() {
  const interval = process.env.SCRAPE_INTERVAL_HOURS || 6;
  const cronExpression = `0 */${interval} * * *`;

  cron.schedule(cronExpression, async () => {
    logger.info('Scheduler', `Scheduled scrape triggered (every ${interval} hours)`);
    await runFullScrape();
  });

  logger.info('Scheduler', `Initialized — scraping every ${interval} hours`);
  logger.info('Scheduler', `${scrapers.length} Node scrapers + FastAPI AI service (44+ portals) registered`);

  // Delayed AI sync on startup — give AI service 90s to boot on Render free tier
  setTimeout(async () => {
    logger.info('Scheduler', 'Running delayed AI service sync (startup)...');
    await syncFromAIService(3);
  }, 90000);
}

module.exports = { initScheduler, runAllScrapers, runFullScrape, syncFromAIService };

