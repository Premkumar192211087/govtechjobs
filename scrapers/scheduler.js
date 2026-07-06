/**
 * Scraper Scheduler — orchestrates all scrapers using node-cron.
 * Runs scrapers periodically and logs results.
 */

const cron = require('node-cron');
const logger = require('../utils/logger');

// Import scrapers (stubbed for now — each will be implemented progressively)
// const SscScraper = require('./sscScraper');
// const UpscScraper = require('./upscScraper');
// ... add more as implemented

const scrapers = [];

/**
 * Run all registered scrapers
 */
async function runAllScrapers() {
  logger.info('Scheduler', `Starting scrape cycle — ${scrapers.length} scrapers registered`);

  const results = [];
  for (const ScraperClass of scrapers) {
    const scraper = new ScraperClass();
    const result = await scraper.run();
    results.push(result);

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
  logger.info('Scheduler', `${scrapers.length} scrapers registered (add more as implemented)`);
}

module.exports = { initScheduler, runAllScrapers };
