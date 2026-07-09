"""
Feedback Loop — Continuous learning and model improvement.

Tracks prediction accuracy over time, identifies degradation,
and auto-generates new training samples from high-confidence predictions.
"""

import os
import json
from datetime import datetime
from typing import Dict, List


class FeedbackLoop:
    """Continuous learning system for the AI ensemble."""

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'feedback_data'
        )
        os.makedirs(self.data_dir, exist_ok=True)
        self.prediction_log_path = os.path.join(self.data_dir, 'prediction_log.jsonl')
        self.high_confidence_path = os.path.join(self.data_dir, 'high_confidence_samples.json')
        self.accuracy_history_path = os.path.join(self.data_dir, 'accuracy_history.json')

    def log_prediction(self, prediction: Dict, ground_truth: Dict = None):
        """Log a prediction for future analysis."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'prediction': prediction,
            'ground_truth': ground_truth,
            'verified': ground_truth is not None,
        }
        with open(self.prediction_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, default=str) + '\n')

    def collect_high_confidence_samples(self, predictions: List[Dict], threshold: float = 0.85):
        """
        Collect high-confidence predictions as candidate training data.
        These can be reviewed and added to the training set.
        """
        high_conf = [p for p in predictions if p.get('_ml_confidence', 0) >= threshold]

        if not high_conf:
            return

        existing = []
        if os.path.exists(self.high_confidence_path):
            with open(self.high_confidence_path, 'r') as f:
                existing = json.load(f)

        existing.extend(high_conf)

        # Keep only last 5000 samples
        existing = existing[-5000:]

        with open(self.high_confidence_path, 'w') as f:
            json.dump(existing, f, indent=2, default=str)

    def get_accuracy_trend(self) -> Dict:
        """Analyze prediction accuracy trends over time."""
        if not os.path.exists(self.prediction_log_path):
            return {'status': 'no_data'}

        verified = []
        with open(self.prediction_log_path, 'r') as f:
            for line in f:
                entry = json.loads(line.strip())
                if entry.get('verified'):
                    verified.append(entry)

        if not verified:
            return {'status': 'no_verified_predictions'}

        # Calculate accuracy over recent predictions
        recent = verified[-100:]
        correct = sum(1 for v in recent if self._is_correct(v))
        accuracy = correct / len(recent)

        return {
            'total_predictions': len(verified),
            'recent_accuracy': accuracy,
            'recent_count': len(recent),
            'needs_retraining': accuracy < 0.85,
        }

    def _is_correct(self, entry: Dict) -> bool:
        """Check if a prediction matches ground truth."""
        pred = entry.get('prediction', {})
        truth = entry.get('ground_truth', {})

        # Check key fields
        checks = []
        if truth.get('vacancies') and pred.get('vacancies'):
            checks.append(pred['vacancies'] == truth['vacancies'])
        if truth.get('organization') and pred.get('organization'):
            checks.append(truth['organization'].lower() in str(pred['organization']).lower())

        return all(checks) if checks else True

    def should_retrain(self) -> bool:
        """Determine if model should be retrained based on accuracy trends."""
        trend = self.get_accuracy_trend()
        return trend.get('needs_retraining', False)


feedback_loop = FeedbackLoop()
