const axios = require('axios');
const cheerio = require('cheerio');
const { classifyLink } = require('./aiClassifier');
const logger = require('./logger');

/**
 * AI/ML Service to crawl a government webpage and discover the direct application portal.
 * @param {string} pageUrl - The URL of the page to analyze.
 * @returns {Promise<Object>} Results containing categorized URLs.
 */
async function discoverDirectApplyLinks(pageUrl) {
  try {
    logger.info('AI Link Extractor', `Crawling page: ${pageUrl}`);
    const response = await axios.get(pageUrl, {
      timeout: 10000,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    });

    const $ = cheerio.load(response.data);
    const discovered = [];

    $('a').each((i, el) => {
      const anchorText = $(el).text().trim();
      let href = $(el).attr('href') || '';

      if (!href || href.startsWith('#') || href.startsWith('javascript:')) return;

      // Resolve relative URLs
      try {
        const resolved = new URL(href, pageUrl).toString();
        
        // Classify the link using our AI model
        const classification = classifyLink(resolved, anchorText);
        
        if (classification.category !== 'IGNORE') {
          discovered.push({
            url: resolved,
            anchorText,
            category: classification.category,
            confidenceScore: classification.score
          });
        }
      } catch (err) {
        // Skip invalid URL formats
      }
    });

    // Sort by confidence score descending
    discovered.sort((a, b) => b.confidenceScore - a.confidenceScore);

    // Filter duplicates
    const unique = [];
    const seen = new Set();
    discovered.forEach(item => {
      if (!seen.has(item.url)) {
        seen.add(item.url);
        unique.push(item);
      }
    });

    const directApply = unique.filter(u => u.category === 'DIRECT_APPLY');
    const genericCareer = unique.filter(u => u.category === 'GENERIC_CAREER');

    return {
      success: true,
      bestDirectApply: directApply[0] || null,
      allDirectApplyLinks: directApply,
      genericCareerLinks: genericCareer
    };
  } catch (err) {
    logger.error('AI Link Extractor', `Failed to crawl page: ${pageUrl}`, { error: err.message });
    return {
      success: false,
      error: err.message,
      bestDirectApply: null,
      allDirectApplyLinks: [],
      genericCareerLinks: []
    };
  }
}

module.exports = { discoverDirectApplyLinks };
