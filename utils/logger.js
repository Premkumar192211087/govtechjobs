/**
 * Logger utility — structured console logging with levels and timestamps
 */

const LOG_LEVELS = {
  ERROR: 0,
  WARN: 1,
  INFO: 2,
  DEBUG: 3
};

const currentLevel = process.env.NODE_ENV === 'production' ? LOG_LEVELS.INFO : LOG_LEVELS.DEBUG;

function timestamp() {
  return new Date().toISOString();
}

function formatMessage(level, context, message, data) {
  const base = `[${timestamp()}] [${level}] [${context}] ${message}`;
  if (data) {
    return `${base} ${JSON.stringify(data)}`;
  }
  return base;
}

const logger = {
  error(context, message, data) {
    if (currentLevel >= LOG_LEVELS.ERROR) {
      console.error(formatMessage('ERROR', context, message, data));
    }
  },
  warn(context, message, data) {
    if (currentLevel >= LOG_LEVELS.WARN) {
      console.warn(formatMessage('WARN', context, message, data));
    }
  },
  info(context, message, data) {
    if (currentLevel >= LOG_LEVELS.INFO) {
      console.info(formatMessage('INFO', context, message, data));
    }
  },
  debug(context, message, data) {
    if (currentLevel >= LOG_LEVELS.DEBUG) {
      console.log(formatMessage('DEBUG', context, message, data));
    }
  }
};

module.exports = logger;
