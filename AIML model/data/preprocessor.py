"""
Data Preprocessor — Text Cleaning & Normalization Pipeline

Converts raw HTML and scraped text from Indian government job portals into
clean, normalized text suitable for ML model training and inference.

Handles:
- HTML → clean text conversion with structure preservation
- Indian date format normalization (DD/MM/YYYY, DD-Mon-YYYY, etc.)
- Currency normalization (₹, Rs., Lakhs, Crores)
- Vacancy count normalization
- Text segmentation into relevant sections
"""

import re
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

MONTH_MAP = {
    'january': '01', 'february': '02', 'march': '03', 'april': '04',
    'may': '05', 'june': '06', 'july': '07', 'august': '08',
    'september': '09', 'october': '10', 'november': '11', 'december': '12',
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
    'oct': '10', 'nov': '11', 'dec': '12',
}

# Sections commonly found in Indian government job notifications
SECTION_HEADERS = [
    'eligibility', 'qualification', 'educational qualification',
    'age limit', 'upper age', 'age relaxation',
    'application fee', 'fee details', 'examination fee',
    'pay scale', 'pay band', 'salary', 'remuneration', 'pay matrix',
    'important dates', 'last date', 'closing date',
    'vacancies', 'vacancy details', 'number of posts', 'total posts',
    'how to apply', 'application process',
    'selection process', 'selection procedure',
    'exam pattern', 'scheme of examination',
    'cutoff', 'cut-off', 'qualifying marks', 'merit list',
    'experience', 'work experience',
]

# Indian government organization abbreviations
KNOWN_ORGS = {
    'UPSC', 'SSC', 'IBPS', 'RRB', 'ISRO', 'DRDO', 'BARC', 'CDAC',
    'NIC', 'NIELIT', 'BEL', 'ECIL', 'HAL', 'BSNL', 'MTNL', 'NTA',
    'UIDAI', 'STPI', 'CRIS', 'CSC', 'RBI', 'SBI', 'NABARD', 'LIC',
    'SEBI', 'SIDBI', 'IRDAI', 'NTPC', 'ONGC', 'IOCL', 'GAIL',
    'BHEL', 'SAIL', 'HPCL', 'BPCL', 'CONCOR', 'NPCIL', 'NHPC',
    'APPSC', 'TSPSC', 'FCI', 'AAI', 'DMRC', 'ESIC', 'EPFO',
    'CBSE', 'KVS', 'NVS', 'UGC', 'AIIMS', 'CSIR', 'DAE',
    'MeitY', 'CERT-In', 'RailTel',
}


# ═══════════════════════════════════════════════════════════════
# HTML CLEANING
# ═══════════════════════════════════════════════════════════════

def strip_html_tags(html: str) -> str:
    """Remove HTML tags while preserving meaningful whitespace."""
    # Replace block-level elements with newlines
    block_tags = r'<\s*/?\s*(?:div|p|br|tr|li|h[1-6]|table|section|article|header|footer|nav|ul|ol|dl|dt|dd|blockquote|pre|hr)\b[^>]*>'
    text = re.sub(block_tags, '\n', html, flags=re.IGNORECASE)
    # Replace table cells with tabs
    text = re.sub(r'<\s*/?\s*(?:td|th)\b[^>]*>', '\t', text, flags=re.IGNORECASE)
    # Remove all remaining tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode HTML entities
    text = _decode_html_entities(text)
    return text


def _decode_html_entities(text: str) -> str:
    """Decode common HTML entities."""
    entities = {
        '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',
        '&quot;': '"', '&#39;': "'", '&ndash;': '–', '&mdash;': '—',
        '&rsquo;': "'", '&lsquo;': "'", '&rdquo;': '"', '&ldquo;': '"',
        '&bull;': '•', '&hellip;': '…', '&#8377;': '₹', '&rupee;': '₹',
    }
    for entity, char in entities.items():
        text = text.replace(entity, char)
    # Handle numeric entities
    text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    return text


# ═══════════════════════════════════════════════════════════════
# TEXT NORMALIZATION
# ═══════════════════════════════════════════════════════════════

def normalize_text(text: str) -> str:
    """Full text normalization pipeline."""
    # Unicode normalization
    text = unicodedata.normalize('NFKD', text)
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    # Normalize dashes
    text = re.sub(r'[–—−‒]', '-', text)
    # Normalize quotes
    text = re.sub(r'[""''`]', "'", text)
    # Remove zero-width characters
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    return text.strip()


def normalize_currency(text: str) -> str:
    """Normalize Indian currency formats to a standard form."""
    # Rs./Rs to ₹
    text = re.sub(r'Rs\.?\s*', '₹', text, flags=re.IGNORECASE)
    text = re.sub(r'INR\s*', '₹', text, flags=re.IGNORECASE)
    # Normalize lakh/crore
    text = re.sub(r'(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?)', r'\1 lakh', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+(?:\.\d+)?)\s*crores?', r'\1 crore', text, flags=re.IGNORECASE)
    # Remove /- suffix
    text = re.sub(r'(\d)\s*/\s*-', r'\1', text)
    return text


def normalize_dates(text: str) -> str:
    """Normalize various Indian date formats to DD/MM/YYYY."""
    # DD-Mon-YYYY → DD/MM/YYYY (e.g., 15-Jul-2026)
    def _replace_month_name(m):
        day, month_str, year = m.groups()
        mm = MONTH_MAP.get(month_str.lower(), None)
        if mm:
            return f"{int(day):02d}/{mm}/{year}"
        return m.group(0)

    text = re.sub(
        r'(\d{1,2})\s*[-/.]\s*([A-Za-z]{3,9})\s*[-/.]\s*(\d{4})',
        _replace_month_name, text
    )

    # DD Month YYYY → DD/MM/YYYY (e.g., 15 July 2026)
    text = re.sub(
        r'(\d{1,2})\s*(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\s*,?\s*(\d{4})',
        _replace_month_name, text
    )

    # Normalize separators to /
    text = re.sub(r'(\d{2})\s*[-\.]\s*(\d{2})\s*[-\.]\s*(\d{4})', r'\1/\2/\3', text)

    return text


def normalize_vacancies(text: str) -> str:
    """Normalize vacancy/post count expressions."""
    # "1,000 posts" → "1000 posts"
    text = re.sub(r'(\d+),(\d{3})\s*(posts?|vacancies|positions?)', r'\1\2 \3', text, flags=re.IGNORECASE)
    # Standardize to "N posts"
    text = re.sub(r'(\d+)\s*nos\.?\s*(?:of\s+)?(?:posts?|vacancies|positions?)', r'\1 posts', text, flags=re.IGNORECASE)
    return text


# ═══════════════════════════════════════════════════════════════
# TEXT SEGMENTATION
# ═══════════════════════════════════════════════════════════════

def segment_into_sections(text: str) -> Dict[str, str]:
    """Segment notification text into logical sections for targeted extraction."""
    sections = {}
    lines = text.split('\n')
    current_section = 'general'
    current_content = []

    for line in lines:
        line_clean = line.strip().lower()
        matched_section = None

        for header in SECTION_HEADERS:
            if header in line_clean and len(line_clean) < 80:
                matched_section = header.replace(' ', '_')
                break

        if matched_section:
            # Save previous section
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = matched_section
            current_content = []
        else:
            current_content.append(line)

    # Save last section
    if current_content:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections


# ═══════════════════════════════════════════════════════════════
# URL FEATURE EXTRACTION
# ═══════════════════════════════════════════════════════════════

def extract_url_features(url: str) -> Dict[str, float]:
    """Extract numerical features from a URL for ML classification."""
    from urllib.parse import urlparse

    parsed = urlparse(url.lower())
    path = parsed.path
    domain = parsed.netloc

    features = {
        # Structural features
        'path_depth': path.count('/') - 1 if path != '/' else 0,
        'path_length': len(path),
        'has_query_params': 1.0 if parsed.query else 0.0,
        'url_length': len(url),
        'is_gov_in': 1.0 if '.gov.in' in domain else 0.0,
        'is_nic_in': 1.0 if '.nic.in' in domain else 0.0,
        'is_ac_in': 1.0 if '.ac.in' in domain else 0.0,
        'is_co_in': 1.0 if '.co.in' in domain else 0.0,
        'is_org_in': 1.0 if '.org.in' in domain else 0.0,
        'is_pdf': 1.0 if '.pdf' in path else 0.0,
        'is_php': 1.0 if '.php' in path else 0.0,
        'is_aspx': 1.0 if '.aspx' in path else 0.0,
        'is_root_page': 1.0 if path in ('/', '', '/index.html', '/index.aspx', '/index.php') else 0.0,

        # Keyword presence in URL
        'has_apply': 1.0 if 'apply' in url.lower() else 0.0,
        'has_register': 1.0 if 'register' in url.lower() else 0.0,
        'has_login': 1.0 if 'login' in url.lower() else 0.0,
        'has_career': 1.0 if 'career' in url.lower() else 0.0,
        'has_recruit': 1.0 if 'recruit' in url.lower() else 0.0,
        'has_vacancy': 1.0 if 'vacanc' in url.lower() else 0.0,
        'has_notification': 1.0 if 'notif' in url.lower() else 0.0,
        'has_exam': 1.0 if 'exam' in url.lower() else 0.0,
        'has_result': 1.0 if 'result' in url.lower() else 0.0,
        'has_admit': 1.0 if 'admit' in url.lower() else 0.0,
        'has_download': 1.0 if 'download' in url.lower() else 0.0,
        'has_contact': 1.0 if 'contact' in url.lower() else 0.0,
        'has_about': 1.0 if 'about' in url.lower() else 0.0,
        'has_social_media': 1.0 if any(sm in domain for sm in ['facebook', 'twitter', 'linkedin', 'youtube', 'instagram']) else 0.0,
        'has_online_subdomain': 1.0 if any(sd in domain for sd in ['apply.', 'register.', 'online.', 'upsconline.', 'ibpsonline.', 'recruitment.']) else 0.0,

        # Known organization detection
        'has_known_org': 0.0,
    }

    # Check for known org abbreviations in domain
    for org in KNOWN_ORGS:
        if org.lower() in domain:
            features['has_known_org'] = 1.0
            break

    return features


def extract_anchor_features(anchor_text: str) -> Dict[str, float]:
    """Extract features from link anchor text."""
    text_lower = anchor_text.lower()
    words = re.findall(r'[a-z0-9]+', text_lower)

    features = {
        'anchor_length': len(anchor_text),
        'anchor_word_count': len(words),
        'anchor_has_apply': 1.0 if any(w in words for w in ['apply', 'register', 'registration', 'signup']) else 0.0,
        'anchor_has_career': 1.0 if any(w in words for w in ['career', 'careers', 'jobs', 'openings']) else 0.0,
        'anchor_has_recruit': 1.0 if any(w in words for w in ['recruitment', 'vacancy', 'vacancies', 'notification']) else 0.0,
        'anchor_has_exam': 1.0 if any(w in words for w in ['exam', 'examination', 'test', 'cbt']) else 0.0,
        'anchor_has_year': 1.0 if re.search(r'202[4-9]', text_lower) else 0.0,
        'anchor_has_ignore': 1.0 if any(w in words for w in ['home', 'contact', 'about', 'help', 'faq', 'disclaimer', 'sitemap']) else 0.0,
        'anchor_has_social': 1.0 if any(w in words for w in ['facebook', 'twitter', 'linkedin', 'youtube', 'instagram', 'share']) else 0.0,
        'anchor_has_pdf': 1.0 if 'pdf' in text_lower else 0.0,
        'anchor_has_login': 1.0 if any(w in words for w in ['login', 'signin', 'sign']) else 0.0,
        'anchor_has_download': 1.0 if any(w in words for w in ['download', 'admit', 'result', 'answer', 'key']) else 0.0,
    }

    return features


# ═══════════════════════════════════════════════════════════════
# FULL PREPROCESSING PIPELINE
# ═══════════════════════════════════════════════════════════════

def preprocess_page(html: str) -> Dict:
    """Full preprocessing pipeline for a scraped page."""
    # Step 1: Strip HTML
    text = strip_html_tags(html)

    # Step 2: Normalize text
    text = normalize_text(text)
    text = normalize_currency(text)
    text = normalize_dates(text)
    text = normalize_vacancies(text)

    # Step 3: Segment into sections
    sections = segment_into_sections(text)

    return {
        'full_text': text,
        'sections': sections,
        'text_length': len(text),
        'section_count': len(sections),
    }


def preprocess_for_ner(text: str) -> List[Tuple[str, str]]:
    """Tokenize text for NER training in BIO format."""
    # Split into sentences
    sentences = re.split(r'[.!?\n]+', text)
    tokens_list = []

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 5:
            continue
        # Tokenize preserving numbers, dates, currency
        tokens = re.findall(r'₹[\d,]+|\d{1,2}/\d{1,2}/\d{4}|\d+(?:,\d{3})*|\w+|[^\s\w]', sentence)
        if tokens:
            tokens_list.append(tokens)

    return tokens_list
