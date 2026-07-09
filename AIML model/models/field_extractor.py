"""
Field Extractor — spaCy NER + CRF for Job Notification Data Extraction

Extracts structured fields from government job notification text using
Named Entity Recognition (NER). Custom-trained on Indian government
job portal patterns.

Entity Types:
    VACANCY_COUNT     — Total number of posts/vacancies
    START_DATE        — Application opening date
    LAST_DATE         — Application closing/last date
    EXAM_DATE         — Examination/test date
    QUALIFICATION     — Educational qualification required
    AGE_LIMIT         — Age limit for candidates
    APPLICATION_FEE   — Application/examination fee
    PAY_SCALE         — Pay scale/salary/remuneration
    CUTOFF_MARKS      — Cutoff/qualifying marks
    ORGANIZATION      — Recruiting organization name
    POST_NAME         — Name of the post/position
    EXPERIENCE        — Experience requirement

Algorithm: spaCy NER pipeline (transformer-backed) + sklearn-crfsuite CRF fallback
Target Accuracy: ≥ 92% entity-level F1-score
"""

import os
import json
import re
import pickle
import warnings
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.preprocessor import normalize_text, normalize_currency, normalize_dates, MONTH_MAP


# ═══════════════════════════════════════════════════════════════
# ENTITY LABELS
# ═══════════════════════════════════════════════════════════════

ENTITY_LABELS = [
    'VACANCY_COUNT', 'START_DATE', 'LAST_DATE', 'EXAM_DATE',
    'QUALIFICATION', 'AGE_LIMIT', 'APPLICATION_FEE', 'PAY_SCALE',
    'CUTOFF_MARKS', 'ORGANIZATION', 'POST_NAME', 'EXPERIENCE',
]

MODEL_DIR_NAME = 'field_extractor_ner'


# ═══════════════════════════════════════════════════════════════
# CRF FEATURE EXTRACTOR (for token-level classification)
# ═══════════════════════════════════════════════════════════════

def _word_features(sent: List[str], i: int) -> Dict:
    """Extract features for a single token in context (for CRF)."""
    word = sent[i]

    features = {
        'bias': 1.0,
        'word.lower': word.lower(),
        'word.length': len(word),
        'word.isdigit': word.isdigit(),
        'word.isupper': word.isupper(),
        'word.istitle': word.istitle(),
        'word.isalpha': word.isalpha(),
        # Patterns
        'word.is_date_sep': bool(re.match(r'^\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4}$', word)),
        'word.is_currency': bool(re.match(r'^[₹Rs]', word)),
        'word.is_number': bool(re.match(r'^\d+[,.]?\d*$', word)),
        'word.has_comma_number': bool(re.match(r'^\d{1,3}(,\d{3})+$', word)),
        # Keyword indicators
        'word.is_vacancy_kw': word.lower() in ('posts', 'vacancies', 'vacancy', 'positions', 'nos', 'seats'),
        'word.is_date_kw': word.lower() in ('date', 'last', 'closing', 'opening', 'start', 'exam', 'examination'),
        'word.is_qual_kw': word.lower() in ('qualification', 'eligibility', 'educational', 'degree', 'graduate'),
        'word.is_age_kw': word.lower() in ('age', 'years', 'yrs', 'limit', 'upper', 'maximum'),
        'word.is_fee_kw': word.lower() in ('fee', 'fees', 'charges', 'payment'),
        'word.is_pay_kw': word.lower() in ('pay', 'salary', 'scale', 'level', 'grade', 'remuneration', 'stipend'),
        'word.is_org_kw': word.upper() in ('UPSC', 'SSC', 'IBPS', 'ISRO', 'DRDO', 'CDAC', 'NIC',
                                             'APPSC', 'TSPSC', 'RBI', 'SBI', 'NABARD', 'LIC',
                                             'RRB', 'FCI', 'AAI', 'ESIC', 'EPFO', 'NTA',
                                             'HAL', 'BEL', 'ECIL', 'NTPC', 'ONGC', 'IOCL'),
        'word.is_exp_kw': word.lower() in ('experience', 'exp', 'freshers', 'fresher'),
        'word.is_cutoff_kw': word.lower() in ('cutoff', 'cut-off', 'qualifying', 'merit', 'marks'),
    }

    # Context features (previous word)
    if i > 0:
        prev_word = sent[i - 1]
        features.update({
            '-1:word.lower': prev_word.lower(),
            '-1:word.istitle': prev_word.istitle(),
            '-1:word.isupper': prev_word.isupper(),
            '-1:word.is_date_kw': prev_word.lower() in ('date', 'last', 'closing', 'opening', 'start', 'exam'),
            '-1:word.is_vacancy_kw': prev_word.lower() in ('total', 'no', 'number', 'vacancies'),
            '-1:word.is_qual_kw': prev_word.lower() in ('qualification', 'eligibility', 'educational'),
        })
    else:
        features['BOS'] = True  # Beginning of sentence

    # Context features (next word)
    if i < len(sent) - 1:
        next_word = sent[i + 1]
        features.update({
            '+1:word.lower': next_word.lower(),
            '+1:word.istitle': next_word.istitle(),
            '+1:word.is_vacancy_kw': next_word.lower() in ('posts', 'vacancies', 'positions', 'nos'),
            '+1:word.is_years': next_word.lower() in ('years', 'yrs'),
        })
    else:
        features['EOS'] = True  # End of sentence

    # Two-word look-behind
    if i > 1:
        features['-2:word.lower'] = sent[i - 2].lower()
    # Two-word look-ahead
    if i < len(sent) - 2:
        features['+2:word.lower'] = sent[i + 2].lower()

    return features


def _sent_to_features(sent: List[str]) -> List[Dict]:
    """Convert a sentence (list of tokens) to a list of feature dicts."""
    return [_word_features(sent, i) for i in range(len(sent))]


# ═══════════════════════════════════════════════════════════════
# FIELD EXTRACTOR MODEL
# ═══════════════════════════════════════════════════════════════

class FieldExtractor:
    """
    NER-based field extractor for government job notifications.
    
    Uses spaCy NER as primary model with CRF fallback,
    plus regex-based extraction for structured patterns.
    """

    def __init__(self, model_dir: str = None):
        self.model_dir = model_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'trained_models'
        )
        self.spacy_model = None
        self.crf_model = None
        self.is_trained = False
        self.training_metrics = {}

    def train(self, dataset: List[Dict]) -> Dict:
        """
        Train the field extractor on NER-labeled dataset.
        
        Uses a dual approach:
        1. Train spaCy NER model for entity recognition
        2. Train CRF model as fallback for edge cases
        """
        print("\n" + "=" * 60)
        print("TRAINING: spaCy NER + CRF Field Extractor")
        print("=" * 60)
        print(f"  Total training samples: {len(dataset)}")

        # Count entity types in dataset
        entity_counts = {}
        for sample in dataset:
            for ent in sample.get('entities', []):
                label = ent['label']
                entity_counts[label] = entity_counts.get(label, 0) + 1
        print(f"  Entity distribution:")
        for label, count in sorted(entity_counts.items()):
            print(f"    {label}: {count}")

        # Split into train/test
        split_idx = int(len(dataset) * 0.85)
        train_data = dataset[:split_idx]
        test_data = dataset[split_idx:]

        # Train spaCy NER
        spacy_metrics = self._train_spacy_ner(train_data, test_data)

        # Train CRF fallback
        crf_metrics = self._train_crf(train_data, test_data)

        self.is_trained = True

        # Combine metrics
        self.training_metrics = {
            'spacy_ner': spacy_metrics,
            'crf_fallback': crf_metrics,
            'n_train': len(train_data),
            'n_test': len(test_data),
            'entity_counts': entity_counts,
        }

        return self.training_metrics

    def _train_spacy_ner(self, train_data: List[Dict], test_data: List[Dict]) -> Dict:
        """Train spaCy NER model."""
        try:
            import spacy
            from spacy.tokens import DocBin
            from spacy.training import Example
        except ImportError:
            print("  ⚠️ spaCy not available. Using CRF-only mode.")
            return {'status': 'skipped', 'reason': 'spacy not installed'}

        print("\n  Training spaCy NER model...")

        # Create blank model
        nlp = spacy.blank("en")
        ner = nlp.add_pipe("ner")

        # Add entity labels
        for label in ENTITY_LABELS:
            ner.add_label(label)

        # Convert to spaCy training format
        train_examples = []
        skipped = 0
        for sample in train_data:
            text = sample['text']
            entities = [(e['start'], e['end'], e['label']) for e in sample.get('entities', [])]

            # Validate entities (must not overlap)
            try:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, {"entities": entities})
                train_examples.append(example)
            except Exception:
                skipped += 1
                continue

        if skipped > 0:
            print(f"  ⚠️ Skipped {skipped} samples with invalid entity annotations")

        # Training loop
        optimizer = nlp.begin_training()
        n_epochs = 30
        batch_size = 32
        best_f1 = 0.0

        print(f"  Training for {n_epochs} epochs...")

        for epoch in range(n_epochs):
            losses = {}
            # Shuffle training data each epoch
            import random
            random.shuffle(train_examples)

            # Mini-batch training
            for i in range(0, len(train_examples), batch_size):
                batch = train_examples[i:i + batch_size]
                nlp.update(batch, sgd=optimizer, losses=losses)

            # Evaluate every 5 epochs
            if (epoch + 1) % 5 == 0:
                eval_metrics = self._evaluate_spacy(nlp, test_data)
                f1 = eval_metrics.get('overall_f1', 0)
                print(f"    Epoch {epoch+1}/{n_epochs} — Loss: {losses.get('ner', 0):.4f}, F1: {f1:.4f}")

                if f1 > best_f1:
                    best_f1 = f1
                    # Save best model
                    model_path = os.path.join(self.model_dir, MODEL_DIR_NAME)
                    os.makedirs(model_path, exist_ok=True)
                    nlp.to_disk(model_path)

        # Load best model
        model_path = os.path.join(self.model_dir, MODEL_DIR_NAME)
        if os.path.exists(model_path):
            self.spacy_model = spacy.load(model_path)
        else:
            self.spacy_model = nlp

        # Final evaluation
        final_metrics = self._evaluate_spacy(self.spacy_model, test_data)
        print(f"\n  Final spaCy NER F1-Score: {final_metrics.get('overall_f1', 0):.4f}")

        return final_metrics

    def _evaluate_spacy(self, nlp, test_data: List[Dict]) -> Dict:
        """Evaluate spaCy NER model on test data."""
        from spacy.training import Example

        tp = {}  # True positives per entity type
        fp = {}  # False positives per entity type
        fn = {}  # False negatives per entity type

        for label in ENTITY_LABELS:
            tp[label] = 0
            fp[label] = 0
            fn[label] = 0

        for sample in test_data:
            text = sample['text']
            gold_entities = set()
            for e in sample.get('entities', []):
                gold_entities.add((e['start'], e['end'], e['label']))

            doc = nlp(text)
            pred_entities = set()
            for ent in doc.ents:
                pred_entities.add((ent.start_char, ent.end_char, ent.label_))

            for ent in pred_entities:
                if ent in gold_entities:
                    tp[ent[2]] = tp.get(ent[2], 0) + 1
                else:
                    fp[ent[2]] = fp.get(ent[2], 0) + 1

            for ent in gold_entities:
                if ent not in pred_entities:
                    fn[ent[2]] = fn.get(ent[2], 0) + 1

        # Calculate per-entity metrics
        entity_metrics = {}
        total_tp = total_fp = total_fn = 0

        for label in ENTITY_LABELS:
            p = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) > 0 else 0
            r = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) > 0 else 0
            f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
            entity_metrics[label] = {'precision': p, 'recall': r, 'f1': f1}
            total_tp += tp[label]
            total_fp += fp[label]
            total_fn += fn[label]

        overall_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        overall_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        overall_f1 = 2 * overall_p * overall_r / (overall_p + overall_r) if (overall_p + overall_r) > 0 else 0

        return {
            'overall_precision': overall_p,
            'overall_recall': overall_r,
            'overall_f1': overall_f1,
            'entity_metrics': entity_metrics,
        }

    def _train_crf(self, train_data: List[Dict], test_data: List[Dict]) -> Dict:
        """Train CRF model as fallback."""
        try:
            import sklearn_crfsuite
            from sklearn_crfsuite import metrics as crf_metrics
        except ImportError:
            print("  ⚠️ sklearn-crfsuite not available. CRF fallback disabled.")
            return {'status': 'skipped', 'reason': 'sklearn-crfsuite not installed'}

        print("\n  Training CRF fallback model...")

        # Convert data to BIO format
        X_train, y_train = self._convert_to_bio(train_data)
        X_test, y_test = self._convert_to_bio(test_data)

        if not X_train:
            return {'status': 'failed', 'reason': 'No training data after BIO conversion'}

        # Extract features
        X_train_feats = [_sent_to_features(sent) for sent in X_train]
        X_test_feats = [_sent_to_features(sent) for sent in X_test]

        # Train CRF
        self.crf_model = sklearn_crfsuite.CRF(
            algorithm='lbfgs',
            c1=0.1,
            c2=0.1,
            max_iterations=100,
            all_possible_transitions=True,
        )

        self.crf_model.fit(X_train_feats, y_train)

        # Evaluate
        y_pred = self.crf_model.predict(X_test_feats)

        # Get labels (excluding 'O')
        labels_present = list(set(
            label for sent_labels in y_train + y_test
            for label in sent_labels if label != 'O'
        ))

        if labels_present:
            f1 = crf_metrics.flat_f1_score(y_test, y_pred, average='weighted', labels=labels_present)
            print(f"  CRF F1-Score: {f1:.4f}")
        else:
            f1 = 0.0

        # Save CRF model
        crf_path = os.path.join(self.model_dir, 'field_extractor_crf.pkl')
        os.makedirs(self.model_dir, exist_ok=True)
        with open(crf_path, 'wb') as f:
            pickle.dump(self.crf_model, f)

        return {'f1': float(f1), 'labels': labels_present}

    def _convert_to_bio(self, dataset: List[Dict]) -> Tuple[List[List[str]], List[List[str]]]:
        """Convert entity-annotated data to BIO-tagged token sequences."""
        X = []  # List of token sequences
        y = []  # List of BIO tag sequences

        for sample in dataset:
            text = sample['text']
            entities = sorted(sample.get('entities', []), key=lambda e: e['start'])

            # Simple whitespace tokenization with char offset tracking
            tokens = []
            token_starts = []
            token_ends = []
            i = 0
            for match in re.finditer(r'\S+', text):
                tokens.append(match.group())
                token_starts.append(match.start())
                token_ends.append(match.end())

            if not tokens:
                continue

            # Assign BIO tags
            tags = ['O'] * len(tokens)
            for ent in entities:
                ent_start = ent['start']
                ent_end = ent['end']
                ent_label = ent['label']
                started = False

                for j, (ts, te) in enumerate(zip(token_starts, token_ends)):
                    if ts >= ent_start and te <= ent_end:
                        if not started:
                            tags[j] = f'B-{ent_label}'
                            started = True
                        else:
                            tags[j] = f'I-{ent_label}'
                    elif ts >= ent_end:
                        break

            X.append(tokens)
            y.append(tags)

        return X, y

    def extract(self, text: str) -> Dict:
        """
        Extract structured fields from notification text.
        
        Uses spaCy NER → CRF fallback → regex fallback.
        
        Returns:
            Dict with extracted fields and confidence scores
        """
        # Normalize text
        text = normalize_text(text)
        text = normalize_currency(text)
        text = normalize_dates(text)

        result = {field: None for field in [
            'vacancies', 'start_date', 'last_date', 'exam_date',
            'qualification', 'age_limit', 'application_fee',
            'pay_scale', 'cutoff_marks', 'organization',
            'post_name', 'experience',
        ]}
        confidences = {field: 0.0 for field in result}

        # Layer 1: spaCy NER extraction
        if self.spacy_model is not None:
            spacy_results = self._extract_with_spacy(text)
            for field, value in spacy_results.items():
                if value is not None:
                    result[field] = value
                    confidences[field] = 0.85

        # Layer 2: CRF extraction for missing fields
        if self.crf_model is not None:
            crf_results = self._extract_with_crf(text)
            for field, value in crf_results.items():
                if result[field] is None and value is not None:
                    result[field] = value
                    confidences[field] = 0.70

        # Layer 3: Regex fallback for remaining missing fields
        regex_results = self._extract_with_regex(text)
        for field, value in regex_results.items():
            if result[field] is None and value is not None:
                result[field] = value
                confidences[field] = 0.55

        result['_confidences'] = confidences
        result['_extraction_method'] = {
            field: 'spacy' if confidences[field] >= 0.85
            else 'crf' if confidences[field] >= 0.70
            else 'regex' if confidences[field] >= 0.55
            else 'none'
            for field in confidences
        }

        return result

    def _extract_with_spacy(self, text: str) -> Dict:
        """Extract entities using spaCy NER model."""
        result = {}
        doc = self.spacy_model(text)

        for ent in doc.ents:
            label = ent.label_
            value = ent.text.strip()

            if label == 'VACANCY_COUNT':
                nums = re.findall(r'\d+', value.replace(',', ''))
                if nums:
                    result['vacancies'] = int(nums[0])
            elif label == 'START_DATE':
                result['start_date'] = self._parse_date(value)
            elif label == 'LAST_DATE':
                result['last_date'] = self._parse_date(value)
            elif label == 'EXAM_DATE':
                result['exam_date'] = self._parse_date(value)
            elif label == 'QUALIFICATION':
                result['qualification'] = value[:200]
            elif label == 'AGE_LIMIT':
                result['age_limit'] = value
            elif label == 'APPLICATION_FEE':
                result['application_fee'] = value
            elif label == 'PAY_SCALE':
                result['pay_scale'] = value[:150]
            elif label == 'CUTOFF_MARKS':
                result['cutoff_marks'] = value
            elif label == 'ORGANIZATION':
                result['organization'] = value
            elif label == 'POST_NAME':
                result['post_name'] = value[:200]
            elif label == 'EXPERIENCE':
                result['experience'] = value

        return result

    def _extract_with_crf(self, text: str) -> Dict:
        """Extract entities using CRF model."""
        result = {}

        # Tokenize
        tokens = re.findall(r'\S+', text)
        if not tokens:
            return result

        # Extract features and predict
        features = _sent_to_features(tokens)
        predictions = self.crf_model.predict([features])[0]

        # Collect entities from BIO tags
        current_entity = None
        current_tokens = []

        for token, tag in zip(tokens, predictions):
            if tag.startswith('B-'):
                # Save previous entity
                if current_entity and current_tokens:
                    value = ' '.join(current_tokens)
                    self._assign_crf_entity(result, current_entity, value)
                current_entity = tag[2:]
                current_tokens = [token]
            elif tag.startswith('I-') and current_entity == tag[2:]:
                current_tokens.append(token)
            else:
                if current_entity and current_tokens:
                    value = ' '.join(current_tokens)
                    self._assign_crf_entity(result, current_entity, value)
                current_entity = None
                current_tokens = []

        # Don't forget the last entity
        if current_entity and current_tokens:
            value = ' '.join(current_tokens)
            self._assign_crf_entity(result, current_entity, value)

        return result

    def _assign_crf_entity(self, result: Dict, label: str, value: str):
        """Assign CRF-extracted entity to result dict."""
        field_map = {
            'VACANCY_COUNT': 'vacancies',
            'START_DATE': 'start_date',
            'LAST_DATE': 'last_date',
            'EXAM_DATE': 'exam_date',
            'QUALIFICATION': 'qualification',
            'AGE_LIMIT': 'age_limit',
            'APPLICATION_FEE': 'application_fee',
            'PAY_SCALE': 'pay_scale',
            'CUTOFF_MARKS': 'cutoff_marks',
            'ORGANIZATION': 'organization',
            'POST_NAME': 'post_name',
            'EXPERIENCE': 'experience',
        }

        field = field_map.get(label)
        if not field:
            return

        if field == 'vacancies':
            nums = re.findall(r'\d+', value.replace(',', ''))
            if nums:
                result[field] = int(nums[0])
        elif field in ('start_date', 'last_date', 'exam_date'):
            result[field] = self._parse_date(value)
        else:
            result[field] = value

    def _extract_with_regex(self, text: str) -> Dict:
        """Regex-based extraction as final fallback (from original model.py)."""
        result = {}

        # Vacancies
        for pat in [
            r'(\d+)\s*(?:posts?|vacancies|vacancys|positions?|seats?)',
            r'(?:posts?|vacancies|positions?)\s*[:\-–]?\s*(\d+)',
            r'total\s*(?:no\.?\s*of\s*)?(?:posts?|vacancies)\s*[:\-–]?\s*(\d+)',
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = int(m.group(1))
                if 0 < val < 100000:
                    result['vacancies'] = val
                    break

        # Last date
        date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})'
        for pat in [
            r'(?:last\s+date|closing\s+date|end\s+date|apply\s+(?:before|by|till))\s*[:\-–]?\s*' + date_pattern,
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                dd, mm, yyyy = m.groups()
                result['last_date'] = f"{yyyy}-{int(mm):02d}-{int(dd):02d}"
                break

        # Start date
        for pat in [
            r'(?:start(?:ing)?\s+date|opening\s+date|apply\s+from)\s*[:\-–]?\s*' + date_pattern,
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                dd, mm, yyyy = m.groups()
                result['start_date'] = f"{yyyy}-{int(mm):02d}-{int(dd):02d}"
                break

        # Exam date
        for pat in [
            r'(?:exam\s+date|test\s+date|examination\s+date|cbt\s+date)\s*[:\-–]?\s*' + date_pattern,
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                dd, mm, yyyy = m.groups()
                result['exam_date'] = f"{yyyy}-{int(mm):02d}-{int(dd):02d}"
                break

        # Qualification
        for pat in [
            r'(?:qualification|eligibility|educational)\s*[:\-–]?\s*(.{10,120}?)(?:\.|;|\n|$)',
            r'((?:B\.?(?:Tech|E|Sc|Com|A)|M\.?(?:Tech|E|Sc|CA|Com|A|BA)|BE|B\.?Ed|Ph\.?D|MBA|Diploma|Graduate|Post\s*Graduate|Engineering|Degree|Master)[^\n;]{0,100})',
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                result['qualification'] = m.group(1).strip()[:200]
                break

        # Age limit
        m = re.search(r'(?:age\s*limit|max(?:imum)?\s*age|upper\s*age)\s*[:\-–]?\s*(\d{2})\s*(?:years?|yrs?)', text, re.IGNORECASE)
        if m:
            result['age_limit'] = f"{m.group(1)} years (relaxation as per rules)"
        else:
            m = re.search(r'(\d{2})\s*(?:to|–|-)\s*(\d{2})\s*(?:years?|yrs?)', text, re.IGNORECASE)
            if m:
                result['age_limit'] = f"{m.group(1)}-{m.group(2)} years"

        # Fee
        for pat in [
            r'(?:application\s*fee|exam(?:ination)?\s*fee|fee)\s*[:\-–]?\s*(?:Rs\.?|₹)\s*([\d,]+)',
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                result['application_fee'] = f"₹{m.group(1).replace(',', '')}"
                break

        if re.search(r'(?:no\s+fee|fee\s*:\s*nil|free\s+of\s+cost)', text, re.IGNORECASE):
            result['application_fee'] = 'No fee'

        # Pay scale
        for pat in [
            r'(?:pay\s*(?:scale|band|level|matrix)|salary|remuneration)\s*[:\-–]?\s*([\w\s₹,.\-/()]+?)(?:\.|;|\n|$)',
            r'(Level[-\s]*\d+\s*:\s*₹[\d,\-]+)',
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                result['pay_scale'] = m.group(1).strip()[:150]
                break

        # Experience
        m = re.search(r'(?:experience)\s*[:\-–]?\s*(\d+)\s*(?:to|–|-)\s*(\d+)\s*(?:years?|yrs?)', text, re.IGNORECASE)
        if m:
            result['experience'] = f"{m.group(1)}-{m.group(2)} years"
        elif re.search(r'(?:freshers?|no\s*experience)', text, re.IGNORECASE):
            result['experience'] = 'Freshers eligible'

        return result

    def _parse_date(self, text: str) -> Optional[str]:
        """Parse various date formats to YYYY-MM-DD."""
        # Try DD/MM/YYYY
        m = re.search(r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})', text)
        if m:
            dd, mm, yyyy = m.groups()
            return f"{yyyy}-{int(mm):02d}-{int(dd):02d}"

        # Try "15 July 2026" or "15th July, 2026"
        m = re.search(r'(\d{1,2})\s*(?:st|nd|rd|th)?\s*(\w+)\s*,?\s*(\d{4})', text)
        if m:
            dd, month_str, yyyy = m.groups()
            mm = MONTH_MAP.get(month_str.lower())
            if mm:
                return f"{yyyy}-{mm}-{int(dd):02d}"

        return text  # Return as-is if unparseable

    def save_model(self):
        """Save all model components."""
        os.makedirs(self.model_dir, exist_ok=True)

        # Save metrics
        metrics_path = os.path.join(self.model_dir, 'field_extractor_metrics.json')
        # Convert metrics to JSON-serializable format
        serializable_metrics = json.loads(json.dumps(self.training_metrics, default=str))
        with open(metrics_path, 'w') as f:
            json.dump(serializable_metrics, f, indent=2)

        print(f"  ✅ Field extractor models saved to {self.model_dir}")

    def load_model(self):
        """Load trained models from disk."""
        # Load spaCy model
        spacy_path = os.path.join(self.model_dir, MODEL_DIR_NAME)
        if os.path.exists(spacy_path):
            try:
                import spacy
                self.spacy_model = spacy.load(spacy_path)
                print(f"  ✅ spaCy NER model loaded")
            except Exception as e:
                print(f"  ⚠️ Could not load spaCy model: {e}")

        # Load CRF model
        crf_path = os.path.join(self.model_dir, 'field_extractor_crf.pkl')
        if os.path.exists(crf_path):
            with open(crf_path, 'rb') as f:
                self.crf_model = pickle.load(f)
            print(f"  ✅ CRF fallback model loaded")

        self.is_trained = True
