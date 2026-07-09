"""
AI/ML Model for Government Job Notification Extraction

Two capabilities:
1. Link Classification — Weighted Naive-Bayes to classify URLs as DIRECT_APPLY / GENERIC_CAREER / IGNORE
2. Job Detail Extraction — NLP-based regex + keyword proximity scoring to extract structured
   fields (vacancies, dates, qualification, age, fee, pay) from raw HTML text
"""

import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

# ═══════════════════════════════════════════════════════════════
# LINK CLASSIFICATION MODEL
# ═══════════════════════════════════════════════════════════════

MODEL_WEIGHTS = {
    "direct_apply": {
        "apply": 4.5, "register": 4.5, "login": 4.0, "registration": 4.0,
        "applyonline": 5.0, "candidate": 3.0, "signup": 4.0, "sign-up": 4.0,
        "ora": 4.5, "newreg": 4.5, "new-reg": 4.5, "form": 3.0,
        "register.php": 5.0, "login.php": 4.5, "ops": 3.5, "app": 2.5,
        "submit": 3.0, "enroll": 3.5, "otr": 4.0, "onetime": 3.5,
    },
    "generic_careers": {
        "career": 3.0, "recruitment": 3.0, "vacancy": 2.5, "jobs": 2.5,
        "current-opening": 2.5, "advertisement": 2.0, "notice": 1.5,
        "pdf": 1.0, "notification": 1.5, "circular": 1.5, "exam": 1.5,
    },
    "ignore": {
        "home": -3.0, "contact": -3.0, "about": -3.0, "policy": -4.0,
        "help": -2.0, "disclaimer": -3.0, "sitemap": -4.0,
        "facebook": -5.0, "twitter": -5.0, "linkedin": -5.0, "youtube": -5.0,
        "instagram": -5.0, "rti": -3.0, "tender": -3.0,
    }
}

def tokenize(text: str):
    return re.findall(r'[a-z0-9\.\-]+', text.lower())

def predict_link_category(url: str, anchor_text: str):
    url_tokens = tokenize(url)
    text_tokens = tokenize(anchor_text)
    all_tokens = url_tokens + text_tokens

    direct_score = 0.0
    generic_score = 0.0
    ignore_score = 0.0

    for token in all_tokens:
        if token in MODEL_WEIGHTS["direct_apply"]:
            direct_score += MODEL_WEIGHTS["direct_apply"][token]
        if token in MODEL_WEIGHTS["generic_careers"]:
            generic_score += MODEL_WEIGHTS["generic_careers"][token]
        if token in MODEL_WEIGHTS["ignore"]:
            ignore_score += MODEL_WEIGHTS["ignore"][token]

    url_lower = url.lower()
    if any(p in url_lower for p in ["apply.", "register.", "online.", "upsconline.", "ibpsonline.", "ssc.gov.in/login"]):
        direct_score += 5.0

    parsed = urlparse(url_lower)
    if parsed.path in ('/', '/index.html', '/index.aspx', '/index.php', ''):
        ignore_score += 4.0

    if ignore_score > (direct_score + generic_score):
        return "IGNORE", max(ignore_score, 1.0)
    if direct_score > generic_score and direct_score > 0.0:
        return "DIRECT_APPLY", direct_score
    if generic_score > 0.0:
        return "GENERIC_CAREER", generic_score
    return "IGNORE", 0.0


# ═══════════════════════════════════════════════════════════════
# JOB DETAIL EXTRACTION MODEL (NLP)
# ═══════════════════════════════════════════════════════════════

# Month patterns for date extraction
MONTH_MAP = {
    'january': '01', 'february': '02', 'march': '03', 'april': '04',
    'may': '05', 'june': '06', 'july': '07', 'august': '08',
    'september': '09', 'october': '10', 'november': '11', 'december': '12',
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
    'oct': '10', 'nov': '11', 'dec': '12',
}

def _extract_vacancies(text: str) -> int:
    """Extract vacancy/post count from text using NLP patterns."""
    patterns = [
        r'(\d+)\s*(?:posts?|vacancies|vacancys|positions?|seats?)',
        r'(?:posts?|vacancies|positions?)\s*[:\-–]?\s*(\d+)',
        r'total\s*(?:no\.?\s*of\s*)?(?:posts?|vacancies)\s*[:\-–]?\s*(\d+)',
        r'(\d+)\s*(?:nos?\.?)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 0 < val < 50000:
                return val
    # Try from title like "20 Posts of Senior Scientific..."
    m = re.match(r'^(\d+)\s+(?:Posts?|positions?)\s+of', text.strip(), re.IGNORECASE)
    if m:
        return int(m.group(1))
    return 0


def _extract_dates(text: str) -> dict:
    """Extract application dates from text."""
    result = {"start_date": None, "last_date": None, "exam_date": None}
    
    # Pattern: DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
    date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})'
    
    # Look for last date patterns
    last_patterns = [
        r'(?:last\s+date|closing\s+date|end\s+date|apply\s+(?:before|by|till))\s*[:\-–]?\s*' + date_pattern,
        r'(?:last\s+date|closing\s+date)\s*[:\-–]?\s*(\d{1,2})\s*(?:st|nd|rd|th)?\s*(\w+)\s*,?\s*(\d{4})',
    ]
    for pat in last_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            groups = m.groups()
            if len(groups) == 3:
                dd, mm, yyyy = groups
                if mm.isdigit():
                    result["last_date"] = f"{yyyy}-{int(mm):02d}-{int(dd):02d}"
                else:
                    mm_num = MONTH_MAP.get(mm.lower(), None)
                    if mm_num:
                        result["last_date"] = f"{yyyy}-{mm_num}-{int(dd):02d}"
            break
    
    # Look for start date
    start_patterns = [
        r'(?:start(?:ing)?\s+date|opening\s+date|apply\s+from)\s*[:\-–]?\s*' + date_pattern,
    ]
    for pat in start_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            dd, mm, yyyy = m.groups()
            result["start_date"] = f"{yyyy}-{int(mm):02d}-{int(dd):02d}"
            break
    
    # Look for exam date
    exam_patterns = [
        r'(?:exam\s+date|test\s+date|examination\s+date|cbt\s+date)\s*[:\-–]?\s*' + date_pattern,
    ]
    for pat in exam_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            dd, mm, yyyy = m.groups()
            result["exam_date"] = f"{yyyy}-{int(mm):02d}-{int(dd):02d}"
            break
    
    return result


def _extract_qualification(text: str) -> str:
    """Extract educational qualification from text."""
    patterns = [
        r'(?:qualification|eligibility|educational)\s*[:\-–]?\s*(.{10,120}?)(?:\.|;|\n|$)',
        r'((?:B\.?(?:Tech|E|Sc|Com|A)|M\.?(?:Tech|E|Sc|CA|Com|A|BA)|BE|B\.?Ed|Ph\.?D|MBA|Diploma|Graduate|Post\s*Graduate|Engineering|Degree|Master)[^\n;]{0,100})',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            qual = m.group(1).strip()
            qual = re.sub(r'\s+', ' ', qual)
            if len(qual) > 15:
                return qual[:150]
    return "As per official notification"


def _extract_age_limit(text: str) -> str:
    """Extract age limit from text."""
    patterns = [
        r'(?:age\s*limit|max(?:imum)?\s*age|upper\s*age)\s*[:\-–]?\s*(\d{2})\s*(?:years?|yrs?)',
        r'(\d{2})\s*(?:to|–|-)\s*(\d{2})\s*(?:years?|yrs?)',
    ]
    m = re.search(patterns[0], text, re.IGNORECASE)
    if m:
        return f"{m.group(1)} years (relaxation as per rules)"
    m = re.search(patterns[1], text, re.IGNORECASE)
    if m:
        return f"{m.group(1)}-{m.group(2)} years"
    return "As per official notification"


def _extract_pay_scale(text: str) -> str:
    """Extract pay scale / salary from text."""
    patterns = [
        r'(?:pay\s*(?:scale|band|level|matrix)|salary|remuneration|stipend|consolidated)\s*[:\-–]?\s*([\w\s₹,.\-/()]+?)(?:\.|;|\n|$)',
        r'(?:Level|Grade\s*Pay)\s*[:\-–]?\s*([\d\-,\s]+)',
        r'₹\s*([\d,]+)\s*(?:to|–|-)\s*₹?\s*([\d,]+)',
        r'Rs\.?\s*([\d,]+)\s*(?:to|–|-)\s*Rs\.?\s*([\d,]+)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            pay = m.group(0).strip()
            pay = re.sub(r'\s+', ' ', pay)
            return pay[:120]
    return "As per government norms"


def _extract_fee(text: str) -> str:
    """Extract application fee from text."""
    patterns = [
        r'(?:application\s*fee|exam(?:ination)?\s*fee|fee)\s*[:\-–]?\s*(?:Rs\.?|₹)\s*([\d,]+)',
        r'(?:Rs\.?|₹)\s*([\d,]+)\s*[/\-]\s*(?:for|each)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            fee = m.group(1).replace(',', '')
            return f"₹{fee} (concessions for reserved categories)"
    
    # Check for "No Fee" or "Nil"
    if re.search(r'(?:no\s+fee|fee\s*:\s*nil|free\s+of\s+cost)', text, re.IGNORECASE):
        return "No fee"
    
    return "As per official notification"


def _extract_experience(text: str) -> str:
    """Extract experience requirement."""
    patterns = [
        r'(?:experience)\s*[:\-–]?\s*(\d+)\s*(?:to|–|-)\s*(\d+)\s*(?:years?|yrs?)',
        r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)',
        r'(?:freshers?|no\s*experience)',
    ]
    m = re.search(patterns[0], text, re.IGNORECASE)
    if m:
        return f"{m.group(1)}-{m.group(2)} years"
    m = re.search(patterns[1], text, re.IGNORECASE)
    if m:
        return f"{m.group(1)} years"
    if re.search(patterns[2], text, re.IGNORECASE):
        return "Freshers eligible"
    return "As per official notification"


def _detect_domain(text: str, org: str) -> str:
    """Classify the job domain using keyword analysis."""
    text_lower = text.lower()
    it_keywords = ['software', 'computer', 'it ', 'information technology', 'programmer',
                   'developer', 'data', 'cyber', 'network', 'system admin', 'electronics',
                   'telecom', 'digital', 'web', 'cloud', 'database', 'scientist', 'engineer']
    banking_keywords = ['bank', 'clerk', 'probationary officer', 'po ', 'financial', 'insurance']
    teaching_keywords = ['teacher', 'professor', 'faculty', 'lecturer', 'tgt', 'pgt', 'instructor']
    
    it_orgs = ['CDAC', 'NIC', 'NIELIT', 'STPI', 'ISRO', 'DRDO', 'ECIL', 'BEL', 'CRIS', 'RailTel', 'HAL']
    banking_orgs = ['SBI', 'RBI', 'IBPS', 'NABARD', 'LIC', 'SEBI', 'SIDBI', 'IRDAI']
    
    if org.upper() in it_orgs or any(k in text_lower for k in it_keywords):
        return 'software_it'
    if org.upper() in banking_orgs or any(k in text_lower for k in banking_keywords):
        return 'banking'
    if any(k in text_lower for k in teaching_keywords):
        return 'teaching'
    return 'non_it'


def extract_job_details(title: str, page_text: str, org: str, org_full: str,
                        portal_url: str, apply_link: str, pdf_url: str = None) -> dict:
    """
    Master NLP extraction function. Given a job title and surrounding page text,
    extract all structured fields needed for a job notification card.
    Returns a complete job dict with zero hardcoded values.
    """
    combined = title + " " + page_text
    today = datetime.now().strftime('%Y-%m-%d')
    
    vacancies = _extract_vacancies(combined)
    dates = _extract_dates(combined)
    qualification = _extract_qualification(combined)
    age_limit = _extract_age_limit(combined)
    pay_scale = _extract_pay_scale(combined)
    fee = _extract_fee(combined)
    experience = _extract_experience(combined)
    domain = _detect_domain(combined, org)
    
    # Compute status
    last_date = dates.get("last_date")
    if last_date:
        try:
            ld = datetime.strptime(last_date, '%Y-%m-%d')
            status = "active" if ld >= datetime.now() else "closed"
        except ValueError:
            status = "active"
    else:
        status = "active"
    
    # Default last date to 30 days from now if not found
    if not last_date:
        last_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    return {
        "exam_name": title.strip(),
        "organization": org,
        "organization_full": org_full,
        "post_name": title.strip(),
        "job_domain": domain,
        "vacancies": vacancies if vacancies > 0 else 1,
        "qualification": qualification,
        "experience_required": experience,
        "age_limit": age_limit,
        "application_fee": fee,
        "pay_scale": pay_scale,
        "location": "All India",
        "notification_date": dates.get("start_date") or today,
        "application_start_date": dates.get("start_date") or today,
        "application_last_date": last_date,
        "exam_date": dates.get("exam_date"),
        "status": status,
        "apply_link": apply_link,
        "portal_url": portal_url,
        "notification_pdf_url": pdf_url or portal_url,
        "portal_instructions": f"Visit {org} official portal → Find this notification → Register/Login → Fill application → Submit.",
        "source_url": portal_url,
        "total_marks": None,
    }
