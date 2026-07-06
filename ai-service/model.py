import re
import json

# Pre-calculated features and likelihood weights for direct application URL classification
# Higher weights represent terms that strongly correlate with direct application pages (forms, registration, login)
MODEL_WEIGHTS = {
    "direct_apply": {
        "apply": 4.5,
        "register": 4.5,
        "login": 4.0,
        "registration": 4.0,
        "applyonline": 5.0,
        "candidate": 3.0,
        "signup": 4.0,
        "sign-up": 4.0,
        "ora": 4.5,  # Online Recruitment Application (UPSC)
        "newreg": 4.5,
        "new-reg": 4.5,
        "form": 3.0,
        "register.php": 5.0,
        "login.php": 4.5,
        "ops": 3.5,
        "app": 2.5
    },
    "generic_careers": {
        "career": 3.0,
        "recruitment": 3.0,
        "vacancy": 2.5,
        "jobs": 2.5,
        "current-opening": 2.5,
        "advertisement": 2.0,
        "notice": 1.5,
        "pdf": 1.0,
        "notification": 1.5
    },
    "ignore": {
        "home": -3.0,
        "contact": -3.0,
        "about": -3.0,
        "policy": -4.0,
        "help": -2.0,
        "disclaimer": -3.0,
        "sitemap": -4.0,
        "facebook": -5.0,
        "twitter": -5.0,
        "linkedin": -5.0,
        "youtube": -5.0
    }
}

def tokenize(text: str):
    """Tokenize input text or URL into lowercase alphanumeric words."""
    return re.findall(r'[a-z0-9]+', text.lower())

def predict_link_category(url: str, anchor_text: str):
    """
    ML Classifier predicting if a URL points to a DIRECT_APPLY portal, a GENERIC_CAREER page, or IGNORE.
    Returns: (category, confidence_score)
    """
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

    # Boost scores based on specific URL structures (e.g. subdomains)
    url_lower = url.lower()
    if any(prefix in url_lower for prefix in ["apply.", "register.", "online.", "ops.", "upsconline.", "ibpsonline."]):
        direct_score += 5.0
    
    # Penalize root domains or homepages
    if url_lower.endswith('.gov.in') or url_lower.endswith('.nic.in') or url_lower.endswith('/') or url_lower.endswith('/index.aspx') or url_lower.endswith('/index.php'):
        ignore_score += 4.0

    # Decision boundary
    if ignore_score > (direct_score + generic_score):
        return "IGNORE", max(ignore_score, 1.0)
    
    if direct_score > generic_score and direct_score > 0.0:
        return "DIRECT_APPLY", direct_score
    
    if generic_score > 0.0:
        return "GENERIC_CAREER", generic_score
        
    return "IGNORE", 0.0
