/**
 * Stats & Cutoffs API routes — /api/stats, /api/cutoffs
 */

const express = require('express');
const router = express.Router();
const db = require('../database/db');

// GET /api/stats — Dashboard statistics
router.get('/stats', async (req, res) => {
  try {
    const stats = await db.getStats();
    res.json(stats);
  } catch (err) {
    console.error('Error fetching stats:', err);
    res.status(500).json({ error: 'Failed to fetch stats' });
  }
});

// GET /api/cutoffs — Cutoff marks data
router.get('/cutoffs', async (req, res) => {
  try {
    const filters = {
      exam: req.query.exam,
      year: req.query.year,
      category: req.query.category
    };
    const cutoffs = await db.getCutoffs(filters);
    res.json({ cutoffs, total: cutoffs.length });
  } catch (err) {
    console.error('Error fetching cutoffs:', err);
    res.status(500).json({ error: 'Failed to fetch cutoffs' });
  }
});

module.exports = router;
