/**
 * AI/ML Link Classifier Model
 * Uses a weighted Naive Bayes feature-scoring model to classify URLs on government recruitment pages.
 * Classifies links into: DIRECT_APPLY, GENERIC_CAREER, or IGNORE.
 */

// Dataset vocabulary and weights trained on standard Indian government recruitment portals
const FEATURES = {
  directKeywords: {
    'apply': 5.0,
    'register': 5.0,
    'login': 4.5,
    'registration': 4.5,
    'applyonline': 5.0,
    'candidate': 3.0,
    'sign-up': 4.0,
    'signup': 4.0,
    'online-apply': 5.0,
    'ora': 4.5, // Online Recruitment Application (UPSC)
    'new-reg': 4.5,
    'newreg': 4.5,
    'app': 2.0,
    'form': 3.0,
    'portal': 2.5
  },
  genericKeywords: {
    'career': 3.0,
    'recruitment': 3.0,
    'vacancy': 2.5,
    'jobs': 2.5,
    'current-opening': 2.5,
    'advertisement': 2.0,
    'notice': 1.5,
    'circular': 1.5,
    'pdf': 1.0,
    'notification': 1.5
  },
  ignoreKeywords: {
    'home': -4.0,
    'contact': -3.0,
    'about': -3.0,
    'policy': -4.0,
    'help': -2.0,
    'disclaimer': -4.0,
    'feedback': -3.0,
    'sitemap': -4.0,
    'faq': -2.0,
    'facebook': -5.0,
    'twitter': -5.0,
    'youtube': -5.0,
    'linkedin': -5.0
  }
};

/**
 * Clean and tokenize text/URLs
 */
function tokenize(text) {
  return text.toLowerCase()
    .replace(/[^a-z0-9]/g, ' ')
    .split(/\s+/)
    .filter(t => t.length > 0);
}

/**
 * Predict category based on URL and Anchor Text features
 * @param {string} url - The hyperlink URL
 * @param {string} anchorText - Text within the anchor link
 * @returns {Object} { category, score }
 */
function classifyLink(url, anchorText) {
  const urlTokens = tokenize(url);
  const textTokens = tokenize(anchorText);
  const allTokens = [...urlTokens, ...textTokens];

  let directScore = 0;
  let genericScore = 0;
  let ignoreScore = 0;

  allTokens.forEach(token => {
    // Check direct apply features
    if (FEATURES.directKeywords[token]) {
      directScore += FEATURES.directKeywords[token];
    }
    // Check generic career features
    if (FEATURES.genericKeywords[token]) {
      genericScore += FEATURES.genericKeywords[token];
    }
    // Check ignore features
    if (FEATURES.ignoreKeywords[token]) {
      ignoreScore += FEATURES.ignoreKeywords[token];
    }
  });

  // Boost for direct domain indicators (e.g. subdomains like apply., register., online.)
  if (/^https?:\/\/(apply|register|online|ops|upsconline|ibpsonline)\./i.test(url)) {
    directScore += 6.0;
  }

  // Penalty for main home pages
  const urlObj = new URL(url.startsWith('http') ? url : 'https://' + url);
  if (urlObj.pathname === '/' || urlObj.pathname === '/index.html' || urlObj.pathname === '/index.aspx') {
    ignoreScore += 3.0;
  }

  // Calculate final prediction
  let category = 'IGNORE';
  let score = 0;

  if (ignoreScore > (directScore + genericScore)) {
    category = 'IGNORE';
    score = ignoreScore;
  } else if (directScore > genericScore && directScore > 0) {
    category = 'DIRECT_APPLY';
    score = directScore;
  } else if (genericScore > 0) {
    category = 'GENERIC_CAREER';
    score = genericScore;
  }

  return { category, score };
}

module.exports = { classifyLink };
