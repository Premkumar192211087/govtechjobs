"""
Model Monitoring — Performance tracking and alerting.

Tracks model health, scraping success rates, and per-portal accuracy.
"""

import os
import json
from datetime import datetime
from typing import Dict, List


class ModelMonitor:
    """Monitors ML model performance in production."""

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'monitoring_data'
        )
        os.makedirs(self.data_dir, exist_ok=True)
        self.metrics_path = os.path.join(self.data_dir, 'metrics.jsonl')
        self.alerts = []

    def log_scrape(self, portal: str, jobs_found: int, success: bool,
                   duration_ms: float, avg_confidence: float):
        """Log a portal scraping event."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'portal': portal,
            'jobs_found': jobs_found,
            'success': success,
            'duration_ms': duration_ms,
            'avg_confidence': avg_confidence,
        }
        with open(self.metrics_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        # Check for alerts
        if not success:
            self.alerts.append({
                'level': 'warning',
                'message': f'Portal {portal} scrape failed',
                'timestamp': datetime.now().isoformat(),
            })

        if avg_confidence < 0.5 and jobs_found > 0:
            self.alerts.append({
                'level': 'warning',
                'message': f'Low confidence ({avg_confidence:.2f}) for portal {portal}',
                'timestamp': datetime.now().isoformat(),
            })

    def get_dashboard(self) -> Dict:
        """Get monitoring dashboard data."""
        if not os.path.exists(self.metrics_path):
            return {'status': 'no_data'}

        entries = []
        with open(self.metrics_path, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        recent = entries[-100:]
        total_scrapes = len(recent)
        successful = sum(1 for e in recent if e['success'])
        total_jobs = sum(e['jobs_found'] for e in recent)
        avg_confidence = (
            sum(e['avg_confidence'] for e in recent if e['avg_confidence'] > 0) /
            max(sum(1 for e in recent if e['avg_confidence'] > 0), 1)
        )

        # Per-portal stats
        portal_stats = {}
        for e in recent:
            portal = e['portal']
            if portal not in portal_stats:
                portal_stats[portal] = {'scrapes': 0, 'success': 0, 'jobs': 0}
            portal_stats[portal]['scrapes'] += 1
            if e['success']:
                portal_stats[portal]['success'] += 1
            portal_stats[portal]['jobs'] += e['jobs_found']

        return {
            'total_scrapes': total_scrapes,
            'success_rate': successful / total_scrapes if total_scrapes > 0 else 0,
            'total_jobs_extracted': total_jobs,
            'avg_confidence': round(avg_confidence, 4),
            'portal_stats': portal_stats,
            'recent_alerts': self.alerts[-10:],
            'last_updated': datetime.now().isoformat(),
        }


monitor = ModelMonitor()
