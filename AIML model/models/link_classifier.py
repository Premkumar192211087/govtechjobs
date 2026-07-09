"""
Link Classifier — XGBoost Gradient Boosted Trees

Classifies URLs from government job portals into 4 categories:
    0 = DIRECT_APPLY    (registration/login/apply pages)
    1 = CAREER_PAGE     (career listing/notification pages)
    2 = NOTIFICATION_PDF (PDF notification documents)
    3 = IGNORE          (home, about, social media, irrelevant)

Algorithm: XGBoost (Gradient Boosted Decision Trees)
    - Handles sparse text features efficiently
    - Excellent performance on tabular/feature data
    - Fast training and inference
    - Works well with small-to-medium datasets (100s-1000s of samples)
    
Target Accuracy: ≥ 95% F1-score
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional

from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.preprocessor import extract_url_features, extract_anchor_features


# ═══════════════════════════════════════════════════════════════
# MODEL CONSTANTS
# ═══════════════════════════════════════════════════════════════

LABEL_MAP = {
    0: 'DIRECT_APPLY',
    1: 'CAREER_PAGE',
    2: 'NOTIFICATION_PDF',
    3: 'IGNORE',
}

REVERSE_LABEL_MAP = {v: k for k, v in LABEL_MAP.items()}

MODEL_FILENAME = 'link_classifier_xgboost.pkl'
VECTORIZER_FILENAME = 'link_classifier_tfidf.pkl'


# ═══════════════════════════════════════════════════════════════
# FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════

class LinkFeatureExtractor:
    """Extracts features from URL + anchor text for classification."""

    def __init__(self):
        self.url_tfidf = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(3, 5),
            max_features=500,
            lowercase=True,
        )
        self.anchor_tfidf = TfidfVectorizer(
            analyzer='word',
            ngram_range=(1, 2),
            max_features=300,
            lowercase=True,
            token_pattern=r'(?u)\b\w+\b',
        )
        self.is_fitted = False

    def fit(self, urls: List[str], anchors: List[str]):
        """Fit TF-IDF vectorizers on training data."""
        self.url_tfidf.fit(urls)
        self.anchor_tfidf.fit(anchors)
        self.is_fitted = True

    def transform(self, urls: List[str], anchors: List[str]) -> np.ndarray:
        """Transform URLs and anchors into feature matrix."""
        if not self.is_fitted:
            raise ValueError("Feature extractor not fitted. Call fit() first.")

        # TF-IDF features
        url_tfidf_features = self.url_tfidf.transform(urls)
        anchor_tfidf_features = self.anchor_tfidf.transform(anchors)

        # Hand-crafted features
        url_features_list = []
        anchor_features_list = []

        for url, anchor in zip(urls, anchors):
            url_feats = extract_url_features(url)
            anchor_feats = extract_anchor_features(anchor)
            url_features_list.append(list(url_feats.values()))
            anchor_features_list.append(list(anchor_feats.values()))

        url_manual = np.array(url_features_list)
        anchor_manual = np.array(anchor_features_list)

        # Combine all features
        combined = hstack([
            url_tfidf_features,
            anchor_tfidf_features,
            url_manual,
            anchor_manual,
        ])

        return combined

    def fit_transform(self, urls: List[str], anchors: List[str]) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(urls, anchors)
        return self.transform(urls, anchors)


# ═══════════════════════════════════════════════════════════════
# LINK CLASSIFIER MODEL
# ═══════════════════════════════════════════════════════════════

class LinkClassifier:
    """
    XGBoost-based link classifier for government job portals.
    
    Classifies URLs into DIRECT_APPLY, CAREER_PAGE, NOTIFICATION_PDF, IGNORE.
    """

    def __init__(self, model_dir: str = None):
        self.model = None
        self.feature_extractor = LinkFeatureExtractor()
        self.model_dir = model_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'trained_models'
        )
        self.is_trained = False
        self.training_metrics = {}

    def train(self, dataset: List[Dict], test_size: float = 0.2) -> Dict:
        """
        Train the XGBoost classifier on the URL dataset.
        
        Args:
            dataset: List of dicts with 'url', 'anchor_text', 'label'
            test_size: Fraction for test split
            
        Returns:
            Dict with training metrics
        """
        from xgboost import XGBClassifier
        from sklearn.model_selection import train_test_split

        print("\n" + "=" * 60)
        print("TRAINING: XGBoost Link Classifier")
        print("=" * 60)

        # Prepare data
        urls = [d['url'] for d in dataset]
        anchors = [d['anchor_text'] for d in dataset]
        labels = np.array([d['label'] for d in dataset])

        print(f"  Total samples: {len(dataset)}")
        for label_id, label_name in LABEL_MAP.items():
            count = np.sum(labels == label_id)
            print(f"    {label_name}: {count} ({count/len(labels)*100:.1f}%)")

        # Split data
        X_train_urls, X_test_urls, X_train_anchors, X_test_anchors, y_train, y_test = \
            train_test_split(urls, anchors, labels, test_size=test_size, random_state=42, stratify=labels)

        # Extract features
        print("\n  Extracting features...")
        X_train = self.feature_extractor.fit_transform(X_train_urls, X_train_anchors)
        X_test = self.feature_extractor.transform(X_test_urls, X_test_anchors)

        print(f"  Feature matrix shape: {X_train.shape}")

        # Train XGBoost
        print("\n  Training XGBoost model...")
        self.model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            objective='multi:softprob',
            num_class=4,
            eval_metric='mlogloss',
            random_state=42,
            n_jobs=-1,
            use_label_encoder=False,
        )

        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )

        # Evaluate
        y_pred = self.model.predict(X_test)
        y_pred_train = self.model.predict(X_train)

        self.training_metrics = {
            'train_accuracy': float(accuracy_score(y_train, y_pred_train)),
            'test_accuracy': float(accuracy_score(y_test, y_pred)),
            'test_precision': float(precision_score(y_test, y_pred, average='weighted')),
            'test_recall': float(recall_score(y_test, y_pred, average='weighted')),
            'test_f1': float(f1_score(y_test, y_pred, average='weighted')),
            'classification_report': classification_report(
                y_test, y_pred, target_names=list(LABEL_MAP.values()), output_dict=True
            ),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'n_train': len(y_train),
            'n_test': len(y_test),
        }

        self.is_trained = True

        # Print results
        print(f"\n  {'─' * 50}")
        print(f"  RESULTS:")
        print(f"  Train Accuracy: {self.training_metrics['train_accuracy']:.4f}")
        print(f"  Test Accuracy:  {self.training_metrics['test_accuracy']:.4f}")
        print(f"  Test F1-Score:  {self.training_metrics['test_f1']:.4f}")
        print(f"  Test Precision: {self.training_metrics['test_precision']:.4f}")
        print(f"  Test Recall:    {self.training_metrics['test_recall']:.4f}")
        print(f"\n  Classification Report:")
        print(classification_report(y_test, y_pred, target_names=list(LABEL_MAP.values())))

        return self.training_metrics

    def cross_validate(self, dataset: List[Dict], k_folds: int = 5) -> Dict:
        """Run stratified k-fold cross-validation."""
        from xgboost import XGBClassifier

        print(f"\n  Running {k_folds}-fold cross-validation...")

        urls = [d['url'] for d in dataset]
        anchors = [d['anchor_text'] for d in dataset]
        labels = np.array([d['label'] for d in dataset])

        X = self.feature_extractor.fit_transform(urls, anchors)

        model = XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            objective='multi:softprob', num_class=4,
            random_state=42, n_jobs=-1, use_label_encoder=False,
        )

        cv = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=42)
        scores = cross_val_score(model, X, labels, cv=cv, scoring='f1_weighted')

        cv_results = {
            'mean_f1': float(np.mean(scores)),
            'std_f1': float(np.std(scores)),
            'fold_scores': scores.tolist(),
            'k_folds': k_folds,
        }

        print(f"  CV F1-Score: {cv_results['mean_f1']:.4f} ± {cv_results['std_f1']:.4f}")
        for i, score in enumerate(scores):
            print(f"    Fold {i+1}: {score:.4f}")

        return cv_results

    def predict(self, url: str, anchor_text: str) -> Tuple[str, float]:
        """
        Predict the category of a single URL.
        
        Returns:
            Tuple of (category_name, confidence_score)
        """
        if not self.is_trained:
            self._load_model()

        X = self.feature_extractor.transform([url], [anchor_text])
        proba = self.model.predict_proba(X)[0]
        pred_label = int(np.argmax(proba))
        confidence = float(proba[pred_label])

        return LABEL_MAP[pred_label], confidence

    def predict_batch(self, urls: List[str], anchors: List[str]) -> List[Dict]:
        """Predict categories for a batch of URLs."""
        if not self.is_trained:
            self._load_model()

        X = self.feature_extractor.transform(urls, anchors)
        probas = self.model.predict_proba(X)
        predictions = []

        for i, proba in enumerate(probas):
            pred_label = int(np.argmax(proba))
            predictions.append({
                'url': urls[i],
                'anchor_text': anchors[i],
                'category': LABEL_MAP[pred_label],
                'confidence': float(proba[pred_label]),
                'probabilities': {LABEL_MAP[j]: float(p) for j, p in enumerate(proba)},
            })

        return predictions

    def save_model(self):
        """Save trained model and feature extractor to disk."""
        os.makedirs(self.model_dir, exist_ok=True)

        model_path = os.path.join(self.model_dir, MODEL_FILENAME)
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)

        fe_path = os.path.join(self.model_dir, VECTORIZER_FILENAME)
        with open(fe_path, 'wb') as f:
            pickle.dump(self.feature_extractor, f)

        # Save metrics
        metrics_path = os.path.join(self.model_dir, 'link_classifier_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(self.training_metrics, f, indent=2)

        print(f"\n  ✅ Model saved to {self.model_dir}")

    def _load_model(self):
        """Load trained model from disk."""
        model_path = os.path.join(self.model_dir, MODEL_FILENAME)
        fe_path = os.path.join(self.model_dir, VECTORIZER_FILENAME)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"No trained model found at {model_path}. Run train() first.")

        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        with open(fe_path, 'rb') as f:
            self.feature_extractor = pickle.load(f)

        self.is_trained = True
        print(f"  ✅ Model loaded from {self.model_dir}")
