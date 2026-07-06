/**
 * Portal API routes — /api/portals
 */

const express = require('express');
const router = express.Router();
const db = require('../database/db');

// GET /api/portals — All tracked portals
router.get('/', async (req, res) => {
  try {
    const category = req.query.category || null;
    const portals = await db.getPortals(category);
    res.json({ portals, total: portals.length });
  } catch (err) {
    console.error('Error fetching portals:', err);
    res.status(500).json({ error: 'Failed to fetch portals' });
  }
});

// GET /api/portals/:shortName — Single portal
router.get('/:shortName', async (req, res) => {
  try {
    const portal = await db.getPortalByShortName(req.params.shortName);
    if (!portal) {
      return res.status(404).json({ error: 'Portal not found' });
    }
    res.json(portal);
  } catch (err) {
    console.error('Error fetching portal:', err);
    res.status(500).json({ error: 'Failed to fetch portal' });
  }
});

module.exports = router;
