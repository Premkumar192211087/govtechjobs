/**
 * Scraper Scheduler — orchestrates all scrapers using node-cron.
 * Runs scrapers periodically and logs results.
 */

const cron = require('node-cron');
const logger = require('../utils/logger');
const db = require('../database/db');

// Import scrapers
const SscScraper = null; // To be added when needed
const UpscScraper = require('./upscScraper');
const CdacScraper = require('./cdacScraper');

const scrapers = [UpscScraper, CdacScraper];

/**
 * Run all registered scrapers
 */
async function runAllScrapers() {
  logger.info('Scheduler', `Starting scrape cycle — ${scrapers.length} scrapers registered`);

  const results = [];
  for (const ScraperClass of scrapers) {
    try {
      const scraper = new ScraperClass();
      const result = await scraper.run();
      results.push(result);
      
      // Save scraped jobs to database
      if (result.status === 'success' && result.jobs && result.jobs.length > 0) {
        for (const job of result.jobs) {
          await db.saveJob(job);
        }
      }
    } catch (err) {
      logger.error('Scheduler', `Scraper execution failed`, { error: err.message });
    }

    // Be polite: wait between portals
    await new Promise(resolve => setTimeout(resolve, 5000));
  }

  const successful = results.filter(r => r.status === 'success').length;
  const failed = results.filter(r => r.status === 'error').length;
  const totalJobs = results.reduce((sum, r) => sum + r.jobsFound, 0);

  logger.info('Scheduler', 'Scrape cycle complete', {
    successful,
    failed,
    totalJobsFound: totalJobs
  });

  return results;
}

/**
 * Initialize the cron scheduler
 */
function initScheduler() {
  const interval = process.env.SCRAPE_INTERVAL_HOURS || 6;

  // Run every N hours
  const cronExpression = `0 */${interval} * * *`;

  cron.schedule(cronExpression, async () => {
    logger.info('Scheduler', `Scheduled scrape triggered (every ${interval} hours)`);
    await runAllScrapers();
  });

  logger.info('Scheduler', `Initialized — scraping every ${interval} hours`);
  logger.info('Scheduler', `${scrapers.length} scrapers registered`);
}

module.exports = { initScheduler, runAllScrapers };
