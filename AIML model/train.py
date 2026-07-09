"""
Training Pipeline — End-to-end training for all 3 ML models.

Workflow:
    1. Generate/load training datasets
    2. Train XGBoost Link Classifier
    3. Train spaCy NER + CRF Field Extractor
    4. Train Random Forest Confidence Scorer
    5. Run cross-validation
    6. Save all models and metrics
    7. Generate evaluation report

Usage:
    python train.py                    # Full training pipeline
    python train.py --model link       # Train only link classifier
    python train.py --model ner        # Train only field extractor
    python train.py --model confidence # Train only confidence scorer
    python train.py --generate-data    # Only generate datasets
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from data.dataset_generator import save_datasets, generate_url_classification_dataset, \
    generate_ner_dataset, generate_confidence_dataset, generate_cutoff_dataset
from models.link_classifier import LinkClassifier
from models.field_extractor import FieldExtractor
from models.confidence_scorer import ConfidenceScorer


# ═══════════════════════════════════════════════════════════════
# TRAINING CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DATASETS_DIR = os.path.join(PROJECT_ROOT, 'datasets')
MODELS_DIR = os.path.join(PROJECT_ROOT, 'trained_models')


# ═══════════════════════════════════════════════════════════════
# MAIN TRAINING PIPELINE
# ═══════════════════════════════════════════════════════════════

def generate_datasets():
    """Generate all training datasets."""
    print("\n" + "█" * 60)
    print("  PHASE 1: DATASET GENERATION")
    print("█" * 60)

    paths = save_datasets(output_dir=DATASETS_DIR)
    return paths


def load_dataset(filename: str):
    """Load a dataset from the datasets directory."""
    path = os.path.join(DATASETS_DIR, filename)
    if not os.path.exists(path):
        print(f"  ⚠️ Dataset not found: {path}")
        print(f"  → Generating datasets first...")
        generate_datasets()

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def train_link_classifier():
    """Train the XGBoost Link Classifier."""
    print("\n" + "█" * 60)
    print("  PHASE 2A: LINK CLASSIFIER (XGBoost)")
    print("█" * 60)

    dataset = load_dataset('url_classification.json')
    classifier = LinkClassifier(model_dir=MODELS_DIR)

    # Train
    metrics = classifier.train(dataset, test_size=0.2)

    # Cross-validate
    cv_results = classifier.cross_validate(dataset, k_folds=5)
    metrics['cross_validation'] = cv_results

    # Save
    classifier.save_model()

    return metrics


def train_field_extractor():
    """Train the spaCy NER + CRF Field Extractor."""
    print("\n" + "█" * 60)
    print("  PHASE 2B: FIELD EXTRACTOR (spaCy NER + CRF)")
    print("█" * 60)

    dataset = load_dataset('ner_field_extraction.json')
    extractor = FieldExtractor(model_dir=MODELS_DIR)

    # Train
    metrics = extractor.train(dataset)

    # Save
    extractor.save_model()

    return metrics


def train_confidence_scorer():
    """Train the Random Forest Confidence Scorer."""
    print("\n" + "█" * 60)
    print("  PHASE 2C: CONFIDENCE SCORER (Random Forest)")
    print("█" * 60)

    dataset = load_dataset('confidence_scoring.json')
    scorer = ConfidenceScorer(model_dir=MODELS_DIR)

    # Train
    metrics = scorer.train(dataset)

    # Save
    scorer.save_model()

    return metrics


def run_full_pipeline():
    """Run the complete training pipeline for all 3 models."""
    start_time = time.time()

    print("\n" + "═" * 60)
    print("  GovTechJobs AI/ML — Full Training Pipeline")
    print("  Started: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("═" * 60)

    all_metrics = {}

    # Phase 1: Generate datasets
    generate_datasets()

    # Phase 2: Train all models
    try:
        all_metrics['link_classifier'] = train_link_classifier()
    except Exception as e:
        print(f"\n  ❌ Link classifier training failed: {e}")
        all_metrics['link_classifier'] = {'error': str(e)}

    try:
        all_metrics['field_extractor'] = train_field_extractor()
    except Exception as e:
        print(f"\n  ❌ Field extractor training failed: {e}")
        all_metrics['field_extractor'] = {'error': str(e)}

    try:
        all_metrics['confidence_scorer'] = train_confidence_scorer()
    except Exception as e:
        print(f"\n  ❌ Confidence scorer training failed: {e}")
        all_metrics['confidence_scorer'] = {'error': str(e)}

    # Phase 3: Save combined report
    total_time = time.time() - start_time

    report = {
        'training_timestamp': datetime.now().isoformat(),
        'total_training_time_seconds': round(total_time, 2),
        'models': all_metrics,
        'target_metrics': {
            'link_classifier_accuracy': '≥ 95%',
            'field_extractor_f1': '≥ 92%',
            'overall_accuracy': '≥ 90%',
            'error_rate': '< 0.5%',
        },
    }

    report_path = os.path.join(MODELS_DIR, 'training_report.json')
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    # Print summary
    print("\n" + "═" * 60)
    print("  TRAINING COMPLETE — SUMMARY")
    print("═" * 60)

    lc = all_metrics.get('link_classifier', {})
    fe = all_metrics.get('field_extractor', {})
    cs = all_metrics.get('confidence_scorer', {})

    print(f"\n  Link Classifier (XGBoost):")
    if 'error' not in lc:
        print(f"    Test Accuracy: {lc.get('test_accuracy', 'N/A')}")
        print(f"    Test F1-Score: {lc.get('test_f1', 'N/A')}")
        cv = lc.get('cross_validation', {})
        if cv:
            print(f"    CV F1 (5-fold): {cv.get('mean_f1', 'N/A'):.4f} ± {cv.get('std_f1', 'N/A'):.4f}")
    else:
        print(f"    ❌ Error: {lc['error']}")

    print(f"\n  Field Extractor (spaCy NER + CRF):")
    if 'error' not in fe:
        spacy_m = fe.get('spacy_ner', {})
        crf_m = fe.get('crf_fallback', {})
        if isinstance(spacy_m, dict):
            print(f"    spaCy NER F1: {spacy_m.get('overall_f1', 'N/A')}")
        if isinstance(crf_m, dict):
            print(f"    CRF F1:       {crf_m.get('f1', 'N/A')}")
    else:
        print(f"    ❌ Error: {fe['error']}")

    print(f"\n  Confidence Scorer (Random Forest):")
    if 'error' not in cs:
        print(f"    Accuracy:   {cs.get('test_accuracy', 'N/A')}")
        print(f"    F1-Score:   {cs.get('test_f1', 'N/A')}")
        print(f"    Error Rate: {cs.get('error_rate', 'N/A')}")
    else:
        print(f"    ❌ Error: {cs['error']}")

    print(f"\n  Total Training Time: {total_time:.1f} seconds")
    print(f"  Report saved: {report_path}")
    print(f"  Models saved: {MODELS_DIR}")
    print("═" * 60)

    return report


# ═══════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GovTechJobs AI/ML Training Pipeline')
    parser.add_argument('--model', choices=['link', 'ner', 'confidence', 'all'],
                        default='all', help='Which model to train')
    parser.add_argument('--generate-data', action='store_true',
                        help='Only generate datasets without training')

    args = parser.parse_args()

    if args.generate_data:
        generate_datasets()
    elif args.model == 'link':
        generate_datasets()
        train_link_classifier()
    elif args.model == 'ner':
        generate_datasets()
        train_field_extractor()
    elif args.model == 'confidence':
        generate_datasets()
        train_confidence_scorer()
    else:
        run_full_pipeline()
