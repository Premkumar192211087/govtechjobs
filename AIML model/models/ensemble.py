"""
Ensemble Orchestrator — Chains all 3 ML models into a unified pipeline.

Pipeline:
    1. Link Classifier (XGBoost) → Classify URL type
    2. Field Extractor (spaCy NER + CRF) → Extract structured fields
    3. Confidence Scorer (Random Forest) → Validate and score results

Handles model loading, fallbacks, and end-to-end inference.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from models.link_classifier import LinkClassifier
from models.field_extractor import FieldExtractor
from models.confidence_scorer import ConfidenceScorer


# ═══════════════════════════════════════════════════════════════
# ENSEMBLE MODEL
# ═══════════════════════════════════════════════════════════════

class GovJobsEnsemble:
    """
    3-layer ensemble for government job notification extraction.
    
    Orchestrates:
        Layer 1: XGBoost Link Classifier
        Layer 2: spaCy NER + CRF Field Extractor
        Layer 3: Random Forest Confidence Scorer
    """

    def __init__(self, model_dir: str = None):
        self.model_dir = model_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'trained_models'
        )
        self.link_classifier = LinkClassifier(self.model_dir)
        self.field_extractor = FieldExtractor(self.model_dir)
        self.confidence_scorer = ConfidenceScorer(self.model_dir)
        self.is_loaded = False
        self.version = '2.0.0'
        self.prediction_log = []

    def load(self):
        """Load all model components."""
        print("\n" + "=" * 60)
        print(f"Loading GovTechJobs AI Ensemble v{self.version}")
        print("=" * 60)

        try:
            self.link_classifier._load_model()
        except (FileNotFoundError, Exception) as e:
            print(f"  ⚠️ Link classifier not loaded: {e}")

        try:
            self.field_extractor.load_model()
        except (FileNotFoundError, Exception) as e:
            print(f"  ⚠️ Field extractor not loaded: {e}")

        try:
            self.confidence_scorer._load_model()
        except (FileNotFoundError, Exception) as e:
            print(f"  ⚠️ Confidence scorer not loaded: {e}")

        self.is_loaded = True
        print(f"\n  ✅ Ensemble loaded successfully")

    def classify_link(self, url: str, anchor_text: str) -> Dict:
        """
        Classify a single URL using the XGBoost link classifier.
        
        Returns:
            Dict with category, confidence, and probabilities
        """
        try:
            category, confidence = self.link_classifier.predict(url, anchor_text)
            return {
                'url': url,
                'anchor_text': anchor_text,
                'category': category,
                'confidence': confidence,
            }
        except Exception as e:
            # Fallback to rule-based classification
            return self._fallback_classify_link(url, anchor_text)

    def classify_links_batch(self, urls: List[str], anchors: List[str]) -> List[Dict]:
        """Classify a batch of URLs."""
        try:
            return self.link_classifier.predict_batch(urls, anchors)
        except Exception:
            return [self._fallback_classify_link(u, a) for u, a in zip(urls, anchors)]

    def extract_job_details(self, title: str, page_text: str, org: str,
                            org_full: str, portal_url: str, apply_link: str,
                            pdf_url: str = None) -> Dict:
        """
        Full pipeline extraction: Extract structured job details from text.
        
        Steps:
            1. Field Extractor (NER) extracts entities
            2. Confidence Scorer validates results
            3. Fallback enrichment for missing fields
        """
        start_time = time.time()

        combined_text = f"{title} {page_text}"
        today = datetime.now().strftime('%Y-%m-%d')

        # ── Step 1: ML Field Extraction ──
        try:
            extracted = self.field_extractor.extract(combined_text)
        except Exception:
            extracted = {}

        # ── Step 2: Build job record ──
        vacancies = extracted.get('vacancies', 0)
        if not vacancies or vacancies <= 0:
            vacancies = self._extract_vacancy_fallback(combined_text)

        start_date = extracted.get('start_date')
        last_date = extracted.get('last_date')
        exam_date = extracted.get('exam_date')

        if not last_date:
            last_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

        qualification = extracted.get('qualification', 'As per official notification')
        age_limit = extracted.get('age_limit', 'As per official notification')
        fee = extracted.get('application_fee', 'As per official notification')
        pay_scale = extracted.get('pay_scale', 'As per government norms')
        experience = extracted.get('experience', 'As per official notification')

        # Detect domain
        domain = self._detect_domain(combined_text, org)

        # Determine status
        status = 'active'
        if last_date:
            try:
                ld = datetime.strptime(str(last_date)[:10], '%Y-%m-%d')
                status = 'active' if ld >= datetime.now() else 'closed'
            except ValueError:
                pass

        job = {
            'exam_name': title.strip(),
            'organization': org,
            'organization_full': org_full,
            'post_name': extracted.get('post_name') or title.strip(),
            'job_domain': domain,
            'vacancies': vacancies if vacancies > 0 else 1,
            'qualification': qualification,
            'experience_required': experience,
            'age_limit': age_limit,
            'application_fee': fee,
            'pay_scale': pay_scale,
            'location': 'All India',
            'notification_date': start_date or today,
            'application_start_date': start_date or today,
            'application_last_date': last_date,
            'exam_date': exam_date,
            'status': status,
            'apply_link': apply_link,
            'portal_url': portal_url,
            'notification_pdf_url': pdf_url or portal_url,
            'portal_instructions': f"Visit {org} official portal → Find this notification → Register/Login → Fill application → Submit.",
            'source_url': portal_url,
            'total_marks': None,
        }

        # ── Step 3: Confidence Scoring ──
        try:
            confidence_result = self.confidence_scorer.score(job)
            job['_ml_confidence'] = confidence_result['confidence_score']
            job['_ml_is_reliable'] = confidence_result['is_reliable']
            job['_ml_flagged_fields'] = confidence_result['flagged_fields']
        except Exception:
            job['_ml_confidence'] = 0.5
            job['_ml_is_reliable'] = True
            job['_ml_flagged_fields'] = []

        # ── Step 4: Extraction metadata ──
        extraction_time = time.time() - start_time
        job['_extraction_method'] = extracted.get('_extraction_method', {})
        job['_extraction_time_ms'] = round(extraction_time * 1000, 2)
        job['_model_version'] = self.version

        # Log prediction
        self.prediction_log.append({
            'timestamp': datetime.now().isoformat(),
            'org': org,
            'title': title[:100],
            'confidence': job['_ml_confidence'],
            'is_reliable': job['_ml_is_reliable'],
            'extraction_time_ms': job['_extraction_time_ms'],
        })

        return job

    def extract_cutoffs(self, text: str) -> List[Dict]:
        """Extract cutoff marks data from text."""
        import re

        cutoffs = []

        # Pattern: Category: marks
        categories = {
            'General': ['general', 'gen', 'ur', 'unreserved'],
            'OBC': ['obc', 'other backward'],
            'SC': ['sc', 'scheduled caste'],
            'ST': ['st', 'scheduled tribe'],
            'EWS': ['ews', 'economically weaker'],
            'PH/PwBD': ['ph', 'pwd', 'pwbd', 'physically'],
        }

        for std_cat, keywords in categories.items():
            for kw in keywords:
                patterns = [
                    rf'{kw}\s*[:\-–]?\s*([\d.]+)\s*(?:/\s*\d+)?',
                    rf'{kw}\s+(?:cutoff|cut-off|marks?)\s*[:\-–]?\s*([\d.]+)',
                ]
                for pat in patterns:
                    m = re.search(pat, text, re.IGNORECASE)
                    if m:
                        try:
                            marks = float(m.group(1))
                            if 0 < marks < 2100:  # Reasonable range
                                cutoffs.append({
                                    'category': std_cat,
                                    'marks': marks,
                                })
                        except ValueError:
                            pass
                        break

        return cutoffs

    def get_model_status(self) -> Dict:
        """Get status of all model components."""
        return {
            'version': self.version,
            'is_loaded': self.is_loaded,
            'link_classifier': {
                'is_trained': self.link_classifier.is_trained,
                'metrics': self.link_classifier.training_metrics,
            },
            'field_extractor': {
                'is_trained': self.field_extractor.is_trained,
                'metrics': self.field_extractor.training_metrics,
            },
            'confidence_scorer': {
                'is_trained': self.confidence_scorer.is_trained,
                'metrics': self.confidence_scorer.training_metrics,
            },
            'total_predictions': len(self.prediction_log),
            'avg_confidence': (
                sum(p['confidence'] for p in self.prediction_log) / len(self.prediction_log)
                if self.prediction_log else 0
            ),
        }

    # ─────────────────────────────────────────────────────────
    # FALLBACK METHODS
    # ─────────────────────────────────────────────────────────

    def _fallback_classify_link(self, url: str, anchor_text: str) -> Dict:
        """Rule-based fallback for link classification."""
        import re
        url_lower = url.lower()
        text_lower = anchor_text.lower()

        # Direct apply indicators
        apply_keywords = ['apply', 'register', 'registration', 'login', 'signup', 'sign-up', 'ora', 'newreg']
        if any(kw in url_lower for kw in apply_keywords) or any(kw in text_lower for kw in apply_keywords):
            return {'url': url, 'anchor_text': anchor_text, 'category': 'DIRECT_APPLY', 'confidence': 0.6}

        # PDF
        if '.pdf' in url_lower:
            return {'url': url, 'anchor_text': anchor_text, 'category': 'NOTIFICATION_PDF', 'confidence': 0.7}

        # Career page
        career_kw = ['career', 'recruitment', 'vacancy', 'vacancies', 'notification', 'jobs', 'openings']
        if any(kw in url_lower for kw in career_kw) or any(kw in text_lower for kw in career_kw):
            return {'url': url, 'anchor_text': anchor_text, 'category': 'CAREER_PAGE', 'confidence': 0.5}

        # Ignore
        ignore_kw = ['facebook', 'twitter', 'linkedin', 'youtube', 'about', 'contact', 'privacy', 'disclaimer']
        if any(kw in url_lower for kw in ignore_kw):
            return {'url': url, 'anchor_text': anchor_text, 'category': 'IGNORE', 'confidence': 0.7}

        from urllib.parse import urlparse
        parsed = urlparse(url_lower)
        if parsed.path in ('/', '', '/index.html', '/index.aspx'):
            return {'url': url, 'anchor_text': anchor_text, 'category': 'IGNORE', 'confidence': 0.5}

        return {'url': url, 'anchor_text': anchor_text, 'category': 'CAREER_PAGE', 'confidence': 0.3}

    def _extract_vacancy_fallback(self, text: str) -> int:
        """Regex fallback for vacancy extraction."""
        import re
        patterns = [
            r'(\d+)\s*(?:posts?|vacancies|vacancys|positions?|seats?)',
            r'(?:posts?|vacancies|positions?)\s*[:\-–]?\s*(\d+)',
            r'total\s*(?:no\.?\s*of\s*)?(?:posts?|vacancies)\s*[:\-–]?\s*(\d+)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = int(m.group(1))
                if 0 < val < 100000:
                    return val
        return 0

    def _detect_domain(self, text: str, org: str) -> str:
        """Classify the job domain using keyword analysis."""
        text_lower = text.lower()

        it_keywords = ['software', 'computer', 'it ', 'information technology', 'programmer',
                       'developer', 'data', 'cyber', 'network', 'system admin', 'electronics',
                       'telecom', 'digital', 'web', 'cloud', 'database', 'scientist', 'engineer']
        banking_keywords = ['bank', 'clerk', 'probationary officer', 'po ', 'financial', 'insurance']
        teaching_keywords = ['teacher', 'professor', 'faculty', 'lecturer', 'tgt', 'pgt', 'instructor']
        defence_keywords = ['army', 'navy', 'air force', 'agniveer', 'nda', 'cds', 'afcat', 'defence']

        it_orgs = ['CDAC', 'NIC', 'NIELIT', 'STPI', 'ISRO', 'DRDO', 'ECIL', 'BEL', 'CRIS', 'RailTel', 'HAL']
        banking_orgs = ['SBI', 'RBI', 'IBPS', 'NABARD', 'LIC', 'SEBI', 'SIDBI', 'IRDAI']
        teaching_orgs = ['KVS', 'NVS', 'UGC', 'NTA']
        defence_orgs = ['Indian Army', 'Indian Navy', 'Indian Air Force']

        if org.upper() in it_orgs or any(k in text_lower for k in it_keywords):
            return 'software_it'
        if org.upper() in banking_orgs or any(k in text_lower for k in banking_keywords):
            return 'banking'
        if org.upper() in teaching_orgs or any(k in text_lower for k in teaching_keywords):
            return 'teaching'
        if org in defence_orgs or any(k in text_lower for k in defence_keywords):
            return 'defence'
        return 'non_it'
