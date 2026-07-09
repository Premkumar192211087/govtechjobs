"""
Confidence Scorer — Random Forest Anomaly Detection & Validation

Validates extracted job data and assigns a reliability confidence score.
Catches extraction errors, flags low-quality results, and ensures
data integrity before it reaches the database.

Algorithm: Random Forest Classifier
    - Robust to noisy features
    - Provides feature importance for interpretability
    - Fast inference for real-time validation
    
Target: Flag ≥ 98% of incorrect extractions, error rate < 0.5%
"""

import os
import json
import pickle
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)


# ═══════════════════════════════════════════════════════════════
# FEATURE NAMES (for interpretability)
# ═══════════════════════════════════════════════════════════════

FEATURE_NAMES = [
    'has_vacancy', 'vacancy_value', 'vacancy_in_range',
    'has_start_date', 'has_last_date', 'has_exam_date',
    'dates_chronological',
    'has_qualification', 'qualification_length',
    'has_age_limit', 'has_fee', 'has_pay_scale',
    'has_org', 'org_is_known', 'has_post_name', 'post_name_length',
    'fields_extracted', 'total_fields', 'extraction_completeness',
    'text_length', 'confidence_score',
]

KNOWN_ORGANIZATIONS = {
    'UPSC', 'SSC', 'IBPS', 'ISRO', 'DRDO', 'CDAC', 'NIC', 'NIELIT',
    'BEL', 'ECIL', 'HAL', 'NTA', 'BARC', 'SBI', 'RBI', 'NABARD',
    'LIC', 'SEBI', 'RRB', 'FCI', 'AAI', 'DMRC', 'ESIC', 'EPFO',
    'NTPC', 'ONGC', 'IOCL', 'GAIL', 'BHEL', 'SAIL', 'KVS', 'NVS',
    'APPSC', 'TSPSC', 'AIIMS', 'CSIR', 'STPI', 'BSNL', 'MTNL',
    'UIDAI', 'MeitY', 'CERT-In', 'RailTel', 'HPCL', 'BPCL',
    'CONCOR', 'NPCIL', 'NHPC', 'THDC', 'CRIS', 'CSC', 'DAE',
    'SIDBI', 'IRDAI', 'PowerGrid', 'Coal India',
}

MODEL_FILENAME = 'confidence_scorer_rf.pkl'


# ═══════════════════════════════════════════════════════════════
# CONFIDENCE SCORER MODEL
# ═══════════════════════════════════════════════════════════════

class ConfidenceScorer:
    """
    Random Forest-based confidence scorer for extracted job data.
    
    Validates extraction quality and assigns a reliability score (0-1).
    """

    def __init__(self, model_dir: str = None):
        self.model = None
        self.model_dir = model_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'trained_models'
        )
        self.is_trained = False
        self.training_metrics = {}
        self.feature_importance = {}

    def train(self, dataset: List[Dict]) -> Dict:
        """
        Train the confidence scorer on labeled extraction quality data.
        
        Args:
            dataset: List of dicts with 'features' and 'label' (1=reliable, 0=unreliable)
        """
        print("\n" + "=" * 60)
        print("TRAINING: Random Forest Confidence Scorer")
        print("=" * 60)

        # Prepare features matrix
        X = np.array([list(d['features'].values()) for d in dataset])
        y = np.array([d['label'] for d in dataset])

        print(f"  Total samples: {len(dataset)}")
        print(f"  Reliable: {np.sum(y == 1)} ({np.sum(y == 1)/len(y)*100:.1f}%)")
        print(f"  Unreliable: {np.sum(y == 0)} ({np.sum(y == 0)/len(y)*100:.1f}%)")
        print(f"  Feature count: {X.shape[1]}")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train Random Forest
        print("\n  Training Random Forest model...")
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            class_weight='balanced',
            random_state=42,
            n_jobs=-1,
        )

        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)

        self.training_metrics = {
            'test_accuracy': float(accuracy_score(y_test, y_pred)),
            'test_precision': float(precision_score(y_test, y_pred)),
            'test_recall': float(recall_score(y_test, y_pred)),
            'test_f1': float(f1_score(y_test, y_pred)),
            'classification_report': classification_report(
                y_test, y_pred, target_names=['Unreliable', 'Reliable'], output_dict=True
            ),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'n_train': len(y_train),
            'n_test': len(y_test),
        }

        # Feature importance
        importances = self.model.feature_importances_
        feature_names = list(dataset[0]['features'].keys()) if dataset else FEATURE_NAMES
        self.feature_importance = {
            name: float(imp) for name, imp in
            sorted(zip(feature_names, importances), key=lambda x: -x[1])
        }

        self.is_trained = True

        # Print results
        print(f"\n  {'─' * 50}")
        print(f"  RESULTS:")
        print(f"  Accuracy:  {self.training_metrics['test_accuracy']:.4f}")
        print(f"  Precision: {self.training_metrics['test_precision']:.4f}")
        print(f"  Recall:    {self.training_metrics['test_recall']:.4f}")
        print(f"  F1-Score:  {self.training_metrics['test_f1']:.4f}")

        print(f"\n  Top Feature Importances:")
        for name, imp in list(self.feature_importance.items())[:10]:
            bar = '█' * int(imp * 50)
            print(f"    {name:30s} {imp:.4f} {bar}")

        # Calculate error rates
        fp = np.sum((y_pred == 1) & (y_test == 0))
        fn = np.sum((y_pred == 0) & (y_test == 1))
        total = len(y_test)
        error_rate = (fp + fn) / total

        print(f"\n  Error Rate: {error_rate:.4f} ({error_rate*100:.2f}%)")
        print(f"  False Positives (bad data marked reliable): {fp}")
        print(f"  False Negatives (good data marked unreliable): {fn}")

        self.training_metrics['error_rate'] = float(error_rate)

        return self.training_metrics

    def score(self, extraction: Dict) -> Dict:
        """
        Score the quality/reliability of an extracted job record.
        
        Args:
            extraction: Dict with extracted job fields
            
        Returns:
            Dict with confidence_score, is_reliable, flagged_fields, details
        """
        if not self.is_trained:
            self._load_model()

        features = self._extract_quality_features(extraction)
        feature_vector = np.array([list(features.values())])

        # ML prediction
        if self.model is not None:
            proba = self.model.predict_proba(feature_vector)[0]
            ml_confidence = float(proba[1])  # Probability of being reliable
        else:
            ml_confidence = 0.5

        # Rule-based validation checks
        rule_checks = self._run_validation_rules(extraction)
        rule_score = sum(1 for check in rule_checks.values() if check['passed']) / len(rule_checks)

        # Combined confidence: weighted average of ML and rules
        final_confidence = 0.6 * ml_confidence + 0.4 * rule_score

        # Determine if reliable
        is_reliable = final_confidence >= 0.6

        # Identify flagged fields
        flagged_fields = [
            field for field, check in rule_checks.items()
            if not check['passed']
        ]

        return {
            'confidence_score': round(final_confidence, 4),
            'is_reliable': is_reliable,
            'ml_confidence': round(ml_confidence, 4),
            'rule_score': round(rule_score, 4),
            'flagged_fields': flagged_fields,
            'validation_details': rule_checks,
            'quality_features': features,
        }

    def _extract_quality_features(self, extraction: Dict) -> Dict:
        """Extract quality indicator features from an extraction result."""
        fields_present = 0
        total_fields = 12

        has_vacancy = extraction.get('vacancies') is not None and extraction.get('vacancies', 0) > 0
        vacancy_val = extraction.get('vacancies', 0) or 0

        has_start = extraction.get('start_date') is not None
        has_last = extraction.get('last_date') is not None or extraction.get('application_last_date') is not None
        has_exam = extraction.get('exam_date') is not None

        has_qual = bool(extraction.get('qualification'))
        qual_len = len(str(extraction.get('qualification', '')))

        has_age = bool(extraction.get('age_limit'))
        has_fee = bool(extraction.get('application_fee'))
        has_pay = bool(extraction.get('pay_scale'))

        has_org = bool(extraction.get('organization'))
        org_str = str(extraction.get('organization', '')).upper()
        org_known = any(org in org_str for org in KNOWN_ORGANIZATIONS)

        has_post = bool(extraction.get('post_name') or extraction.get('exam_name'))
        post_len = len(str(extraction.get('post_name', '') or extraction.get('exam_name', '')))

        has_exp = bool(extraction.get('experience') or extraction.get('experience_required'))

        # Count present fields
        for val in [has_vacancy, has_start, has_last, has_exam, has_qual,
                     has_age, has_fee, has_pay, has_org, has_post, has_exp]:
            if val:
                fields_present += 1

        # Check date chronology
        dates_ok = True
        if has_start and has_last:
            try:
                start = extraction.get('start_date', '') or extraction.get('application_start_date', '')
                last = extraction.get('last_date', '') or extraction.get('application_last_date', '')
                if start and last and start > last:
                    dates_ok = False
            except (TypeError, ValueError):
                dates_ok = False

        features = {
            'has_vacancy': float(has_vacancy),
            'vacancy_value': float(vacancy_val),
            'vacancy_in_range': float(0 < vacancy_val < 100000) if has_vacancy else 0.0,
            'has_start_date': float(has_start),
            'has_last_date': float(has_last),
            'has_exam_date': float(has_exam),
            'dates_chronological': float(dates_ok),
            'has_qualification': float(has_qual),
            'qualification_length': float(qual_len),
            'has_age_limit': float(has_age),
            'has_fee': float(has_fee),
            'has_pay_scale': float(has_pay),
            'has_org': float(has_org),
            'org_is_known': float(org_known),
            'has_post_name': float(has_post),
            'post_name_length': float(post_len),
            'fields_extracted': float(fields_present),
            'total_fields': float(total_fields),
            'extraction_completeness': float(fields_present / total_fields),
            'text_length': float(len(str(extraction))),
            'confidence_score': float(extraction.get('_confidences', {}).get('vacancies', 0.5)),
        }

        return features

    def _run_validation_rules(self, extraction: Dict) -> Dict:
        """Run rule-based validation checks."""
        checks = {}

        # 1. Vacancy check
        vac = extraction.get('vacancies', 0) or 0
        checks['vacancy_valid'] = {
            'passed': 0 < vac < 100000,
            'reason': f'Vacancy count ({vac}) should be between 1 and 100,000',
        }

        # 2. Date checks
        last_date = extraction.get('last_date') or extraction.get('application_last_date')
        checks['has_deadline'] = {
            'passed': last_date is not None,
            'reason': 'Job notification should have a last date / deadline',
        }

        # 3. Date chronology
        start = extraction.get('start_date') or extraction.get('application_start_date')
        if start and last_date:
            try:
                checks['date_order'] = {
                    'passed': str(start) <= str(last_date),
                    'reason': f'Start date ({start}) should be before last date ({last_date})',
                }
            except (TypeError, ValueError):
                checks['date_order'] = {'passed': True, 'reason': 'Could not compare dates'}
        else:
            checks['date_order'] = {'passed': True, 'reason': 'Dates not available for comparison'}

        # 4. Organization check
        org = extraction.get('organization', '')
        checks['has_organization'] = {
            'passed': bool(org) and len(str(org)) > 1,
            'reason': 'Should have a recognizable organization name',
        }

        # 5. Post name check
        post = extraction.get('post_name') or extraction.get('exam_name', '')
        checks['has_post_name'] = {
            'passed': bool(post) and len(str(post)) > 5,
            'reason': 'Should have a meaningful post/exam name',
        }

        # 6. Qualification check
        qual = extraction.get('qualification', '')
        checks['has_qualification'] = {
            'passed': bool(qual) and len(str(qual)) > 10,
            'reason': 'Should have qualification details',
        }

        # 7. Field completeness
        present_count = sum(1 for v in [
            extraction.get('vacancies'),
            extraction.get('qualification'),
            extraction.get('organization'),
            extraction.get('post_name') or extraction.get('exam_name'),
            last_date,
        ] if v)
        checks['minimum_fields'] = {
            'passed': present_count >= 3,
            'reason': f'At least 3 core fields needed, found {present_count}',
        }

        return checks

    def save_model(self):
        """Save trained model to disk."""
        os.makedirs(self.model_dir, exist_ok=True)

        model_path = os.path.join(self.model_dir, MODEL_FILENAME)
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)

        metrics_path = os.path.join(self.model_dir, 'confidence_scorer_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump({
                'metrics': self.training_metrics,
                'feature_importance': self.feature_importance,
            }, f, indent=2)

        print(f"  ✅ Confidence scorer saved to {self.model_dir}")

    def _load_model(self):
        """Load trained model from disk."""
        model_path = os.path.join(self.model_dir, MODEL_FILENAME)
        if not os.path.exists(model_path):
            print(f"  ⚠️ No trained confidence scorer found. Using rule-based validation only.")
            return

        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        self.is_trained = True
        print(f"  ✅ Confidence scorer loaded")
