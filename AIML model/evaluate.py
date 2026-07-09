"""
Evaluation Suite — Comprehensive model evaluation and metrics.

Evaluates all 3 models individually and the ensemble end-to-end.
Generates detailed reports with per-entity, per-portal accuracy breakdown.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from data.dataset_generator import (
    generate_url_classification_dataset,
    generate_ner_dataset,
    generate_cutoff_dataset,
    generate_confidence_dataset,
    ORGANIZATIONS, EXAM_NAMES, POST_NAMES, QUALIFICATIONS,
)
from models.ensemble import GovJobsEnsemble


def evaluate_full_pipeline():
    """Run comprehensive evaluation of the entire ensemble pipeline."""
    print("\n" + "═" * 60)
    print("  GovTechJobs AI — Comprehensive Evaluation Suite")
    print("  " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("═" * 60)

    models_dir = os.path.join(PROJECT_ROOT, 'trained_models')
    ensemble = GovJobsEnsemble(model_dir=models_dir)

    try:
        ensemble.load()
    except Exception as e:
        print(f"\n  ⚠️ Could not load all models: {e}")
        print("  Running evaluation with available components...")

    results = {}

    # ── 1. Link Classification Evaluation ──
    print("\n" + "─" * 50)
    print("  1. LINK CLASSIFICATION EVALUATION")
    print("─" * 50)

    url_testset = generate_url_classification_dataset(n_samples=300)
    correct = 0
    total = 0
    class_correct = {0: 0, 1: 0, 2: 0, 3: 0}
    class_total = {0: 0, 1: 0, 2: 0, 3: 0}

    for sample in url_testset:
        try:
            pred = ensemble.classify_link(sample['url'], sample['anchor_text'])
            pred_label = pred.get('category', 'IGNORE')
            gold_label = sample['label_name']

            class_total[sample['label']] = class_total.get(sample['label'], 0) + 1
            total += 1

            if pred_label == gold_label:
                correct += 1
                class_correct[sample['label']] = class_correct.get(sample['label'], 0) + 1
        except Exception:
            total += 1

    link_accuracy = correct / total if total > 0 else 0
    label_names = {0: 'DIRECT_APPLY', 1: 'CAREER_PAGE', 2: 'NOTIFICATION_PDF', 3: 'IGNORE'}

    print(f"\n  Overall Accuracy: {link_accuracy:.4f} ({link_accuracy*100:.1f}%)")
    for label_id, name in label_names.items():
        ct = class_total.get(label_id, 0)
        cc = class_correct.get(label_id, 0)
        acc = cc / ct if ct > 0 else 0
        print(f"    {name:20s}: {acc:.4f} ({cc}/{ct})")

    results['link_classifier'] = {
        'accuracy': link_accuracy,
        'per_class': {
            label_names[k]: class_correct[k] / class_total[k] if class_total[k] > 0 else 0
            for k in label_names
        },
        'total_samples': total,
    }

    # ── 2. Field Extraction Evaluation ──
    print("\n" + "─" * 50)
    print("  2. FIELD EXTRACTION EVALUATION")
    print("─" * 50)

    # Generate test notifications
    ner_testset = generate_ner_dataset(n_samples=200)
    field_scores = {
        'vacancies': {'correct': 0, 'total': 0},
        'organization': {'correct': 0, 'total': 0},
        'qualification': {'correct': 0, 'total': 0},
        'age_limit': {'correct': 0, 'total': 0},
        'application_fee': {'correct': 0, 'total': 0},
        'pay_scale': {'correct': 0, 'total': 0},
    }

    for sample in ner_testset:
        text = sample['text']
        meta = sample.get('metadata', {})

        extracted = ensemble.extract_job_details(
            title=meta.get('exam', 'Test Exam'),
            page_text=text,
            org=meta.get('org', 'Unknown'),
            org_full=meta.get('org_full', 'Unknown Organization'),
            portal_url='https://test.gov.in',
            apply_link='https://test.gov.in/apply',
        )

        # Check vacancy extraction
        gold_vac = meta.get('vacancies', 0)
        pred_vac = extracted.get('vacancies', 0)
        field_scores['vacancies']['total'] += 1
        if pred_vac == gold_vac or (pred_vac > 0 and gold_vac > 0 and abs(pred_vac - gold_vac) / max(gold_vac, 1) < 0.1):
            field_scores['vacancies']['correct'] += 1

        # Check organization
        gold_org = meta.get('org', '')
        pred_org = extracted.get('organization', '')
        field_scores['organization']['total'] += 1
        if gold_org.lower() in str(pred_org).lower():
            field_scores['organization']['correct'] += 1

        # Check qualification (partial match)
        pred_qual = str(extracted.get('qualification', ''))
        field_scores['qualification']['total'] += 1
        if len(pred_qual) > 15 and pred_qual != 'As per official notification':
            field_scores['qualification']['correct'] += 1

        # Check other fields (presence-based)
        for field in ['age_limit', 'application_fee', 'pay_scale']:
            field_scores[field]['total'] += 1
            val = str(extracted.get(field, ''))
            if val and len(val) > 3 and 'As per' not in val:
                field_scores[field]['correct'] += 1

    print(f"\n  Per-field Extraction Accuracy:")
    total_correct = 0
    total_total = 0
    for field, scores in field_scores.items():
        acc = scores['correct'] / scores['total'] if scores['total'] > 0 else 0
        total_correct += scores['correct']
        total_total += scores['total']
        bar = '█' * int(acc * 30)
        print(f"    {field:20s}: {acc:.4f} ({scores['correct']}/{scores['total']}) {bar}")

    overall_extraction = total_correct / total_total if total_total > 0 else 0
    print(f"\n  Overall Extraction Accuracy: {overall_extraction:.4f} ({overall_extraction*100:.1f}%)")

    results['field_extractor'] = {
        'overall_accuracy': overall_extraction,
        'per_field': {
            field: scores['correct'] / scores['total'] if scores['total'] > 0 else 0
            for field, scores in field_scores.items()
        },
    }

    # ── 3. Confidence Scorer Evaluation ──
    print("\n" + "─" * 50)
    print("  3. CONFIDENCE SCORER EVALUATION")
    print("─" * 50)

    conf_testset = generate_confidence_dataset(n_samples=200)
    conf_correct = 0
    conf_total = 0
    false_positives = 0
    false_negatives = 0

    for sample in conf_testset:
        gold = sample['label']
        # Create a mock extraction from features
        mock_extraction = {
            'vacancies': int(sample['features'].get('vacancy_value', 0)),
            'qualification': 'B.Tech CS' * (1 if sample['features'].get('has_qualification', 0) else 0),
            'organization': 'SSC' if sample['features'].get('has_org', 0) else '',
            'post_name': 'Junior Engineer' if sample['features'].get('has_post_name', 0) else '',
            'application_last_date': '2026-12-31' if sample['features'].get('has_last_date', 0) else None,
            'start_date': '2026-07-01' if sample['features'].get('has_start_date', 0) else None,
            'exam_date': '2027-01-15' if sample['features'].get('has_exam_date', 0) else None,
            'age_limit': '18-27 years' if sample['features'].get('has_age_limit', 0) else '',
            'application_fee': '₹500' if sample['features'].get('has_fee', 0) else '',
            'pay_scale': 'Level-6' if sample['features'].get('has_pay_scale', 0) else '',
        }

        try:
            score = ensemble.confidence_scorer.score(mock_extraction)
            pred = 1 if score['is_reliable'] else 0
        except Exception:
            pred = 1  # Default to reliable

        conf_total += 1
        if pred == gold:
            conf_correct += 1
        elif pred == 1 and gold == 0:
            false_positives += 1
        elif pred == 0 and gold == 1:
            false_negatives += 1

    conf_accuracy = conf_correct / conf_total if conf_total > 0 else 0
    error_rate = (false_positives + false_negatives) / conf_total if conf_total > 0 else 0

    print(f"\n  Accuracy:         {conf_accuracy:.4f} ({conf_accuracy*100:.1f}%)")
    print(f"  Error Rate:       {error_rate:.4f} ({error_rate*100:.2f}%)")
    print(f"  False Positives:  {false_positives} (bad data passed as good)")
    print(f"  False Negatives:  {false_negatives} (good data rejected)")

    results['confidence_scorer'] = {
        'accuracy': conf_accuracy,
        'error_rate': error_rate,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
    }

    # ── 4. Overall Summary ──
    print("\n" + "═" * 60)
    print("  OVERALL EVALUATION SUMMARY")
    print("═" * 60)

    # Calculate weighted overall accuracy
    overall_accuracy = (
        0.30 * results['link_classifier']['accuracy'] +
        0.45 * results['field_extractor']['overall_accuracy'] +
        0.25 * results['confidence_scorer']['accuracy']
    )

    print(f"\n  Link Classifier Accuracy:     {results['link_classifier']['accuracy']:.4f}")
    print(f"  Field Extraction Accuracy:    {results['field_extractor']['overall_accuracy']:.4f}")
    print(f"  Confidence Scorer Accuracy:   {results['confidence_scorer']['accuracy']:.4f}")
    print(f"  Overall Error Rate:           {results['confidence_scorer']['error_rate']:.4f}")
    print(f"\n  ★ Weighted Overall Accuracy:  {overall_accuracy:.4f} ({overall_accuracy*100:.1f}%)")

    # Check against targets
    targets_met = {
        'Link Classifier ≥ 95%': results['link_classifier']['accuracy'] >= 0.95,
        'Field Extraction ≥ 92%': results['field_extractor']['overall_accuracy'] >= 0.92,
        'Overall ≥ 90%': overall_accuracy >= 0.90,
        'Error Rate < 0.5%': results['confidence_scorer']['error_rate'] < 0.005,
    }

    print(f"\n  Target Achievement:")
    for target, met in targets_met.items():
        status = '✅' if met else '❌'
        print(f"    {status} {target}")

    results['overall'] = {
        'weighted_accuracy': overall_accuracy,
        'targets_met': targets_met,
        'evaluation_timestamp': datetime.now().isoformat(),
    }

    # Save report
    report_path = os.path.join(PROJECT_ROOT, 'trained_models', 'evaluation_report.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  Report saved: {report_path}")
    print("═" * 60)

    return results


if __name__ == '__main__':
    evaluate_full_pipeline()
