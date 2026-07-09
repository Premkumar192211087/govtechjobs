/**
 * Base Scraper — shared functionality for all portal scrapers.
 * Handles fetching, parsing, rate-limiting, and error handling.
 */

const axios = require('axios');
const cheerio = require('cheerio');
const logger = require('../utils/logger');

class BaseScraper {
  constructor(portalName, baseUrl) {
    this.portalName = portalName;
    this.baseUrl = baseUrl;
    this.requestDelay = 2000; // 2s between requests to be polite
    this.maxRetries = 3;
    this.timeout = 15000; // 15s timeout
  }

  /**
   * Fetch a URL with retry logic and polite delays
   */
  async fetch(url) {
    let lastError;
    const https = require('https');
    const agent = new https.Agent({ rejectUnauthorized: false });

    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        logger.debug(this.portalName, `Fetching (attempt ${attempt}): ${url}`);
        const response = await axios.get(url, {
          timeout: this.timeout,
          httpsAgent: agent,
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-IN,en;q=0.9,hi;q=0.8'
          }
        });
        return response.data;
      } catch (err) {
        lastError = err;
        logger.warn(this.portalName, `Fetch failed (attempt ${attempt}/${this.maxRetries})`, {
          url,
          status: err.response?.status,
          message: err.message
        });

        if (attempt < this.maxRetries) {
          await this.delay(this.requestDelay * attempt);
        }
      }
    }

    throw lastError;
  }

  /**
   * Parse HTML into a Cheerio instance
   */
  parse(html) {
    return cheerio.load(html);
  }

  /**
   * Delay execution (rate limiting)
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Main scrape method — override in subclasses
   * @returns {Array} Array of job objects
   */
  async scrape() {
    throw new Error(`${this.portalName}: scrape() not implemented`);
  }

  /**
   * Run the scraper with timing and error tracking
   */
  async run() {
    const startTime = Date.now();
    try {
      logger.info(this.portalName, 'Starting scrape...');
      const jobs = await this.scrape();
      const duration = Date.now() - startTime;
      logger.info(this.portalName, `Scrape complete`, {
        jobsFound: jobs.length,
        durationMs: duration
      });
      return {
        portal: this.portalName,
        status: 'success',
        jobs,
        jobsFound: jobs.length,
        durationMs: duration
      };
    } catch (err) {
      const duration = Date.now() - startTime;
      logger.error(this.portalName, 'Scrape failed', {
        error: err.message,
        durationMs: duration
      });
      return {
        portal: this.portalName,
        status: 'error',
        jobs: [],
        jobsFound: 0,
        error: err.message,
        durationMs: duration
      };
    }
  }
}

module.exports = BaseScraper;
