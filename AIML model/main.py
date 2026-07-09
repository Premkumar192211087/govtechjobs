"""
GovTechJobs AI/ML FastAPI Service — Production Inference API

Endpoints:
    GET  /                        — Health check + model status
    GET  /extract                 — Classify all links on a page (ML)
    POST /scrape-portal           — Scrape a single portal with ML extraction
    POST /reload-notifications    — Scrape ALL portals with ML ensemble
    GET  /model-status            — Detailed model performance metrics
    POST /predict                 — ML prediction on raw text
    POST /extract-pdf             — Extract data from notification PDF
"""

import os
import sys
import traceback
from typing import Optional, List

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from models.ensemble import GovJobsEnsemble
from data.pdf_extractor import extract_pdf_from_url


# ═══════════════════════════════════════════════════════════════
# APP INITIALIZATION
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="GovTechJobs AI/ML Service",
    description="Real-time government job notification extraction powered by 3-layer ML ensemble "
                "(XGBoost + spaCy NER + Random Forest)",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}

# Load ML ensemble
ensemble = GovJobsEnsemble(model_dir=os.path.join(PROJECT_ROOT, 'trained_models'))
try:
    ensemble.load()
except Exception as e:
    print(f"⚠️ ML models not loaded: {e}. Run train.py first. Using fallbacks.")


# ═══════════════════════════════════════════════════════════════
# PORTAL REGISTRY
# ═══════════════════════════════════════════════════════════════

PORTAL_REGISTRY = [
    # ═══════ IT/SOFTWARE FOCUSED ═══════
    {"org": "BARC", "org_full": "Bhabha Atomic Research Centre", "career_url": "https://barc.gov.in/careers/", "apply_url": "https://barc.gov.in/careers/"},
    {"org": "BEL", "org_full": "Bharat Electronics Limited", "career_url": "https://bel-india.in/Ede/ContentPage.aspx?MId=17&CId=37&LId=1&link=37", "apply_url": "https://bel-india.in/"},
    {"org": "BSNL", "org_full": "Bharat Sanchar Nigam Limited", "career_url": "https://bsnl.co.in/", "apply_url": "https://bsnl.co.in/"},
    {"org": "CDAC", "org_full": "Centre for Development of Advanced Computing", "career_url": "https://www.cdac.in/index.aspx?id=careers", "apply_url": "https://www.cdac.in/index.aspx?id=careers"},
    {"org": "CRIS", "org_full": "Centre for Railway Information Systems", "career_url": "https://cris.org.in/crisweb/design1/innerContent.jsp?linkID=71", "apply_url": "https://cris.org.in/"},
    {"org": "DRDO", "org_full": "Defence Research & Development Organisation", "career_url": "https://rac.gov.in/", "apply_url": "https://rac.gov.in/"},
    {"org": "ECIL", "org_full": "Electronics Corporation of India Limited", "career_url": "https://ecil.co.in/jobs/", "apply_url": "https://ecil.co.in/jobs/"},
    {"org": "HAL", "org_full": "Hindustan Aeronautics Limited", "career_url": "https://hal-india.co.in/Career%20with%20HAL/M__57", "apply_url": "https://hal-india.co.in/"},
    {"org": "IBPS", "org_full": "Institute of Banking Personnel Selection", "career_url": "https://www.ibps.in/", "apply_url": "https://www.ibps.in/"},
    {"org": "ISRO", "org_full": "Indian Space Research Organisation", "career_url": "https://www.isro.gov.in/Careers.html", "apply_url": "https://www.isro.gov.in/Careers.html"},
    {"org": "NIC", "org_full": "National Informatics Centre", "career_url": "https://www.nic.in/careers/", "apply_url": "https://www.nic.in/careers/"},
    {"org": "NIELIT", "org_full": "National Institute of Electronics & IT", "career_url": "https://www.nielit.gov.in/content/recruitment", "apply_url": "https://www.nielit.gov.in/content/recruitment"},
    {"org": "NTA", "org_full": "National Testing Agency", "career_url": "https://nta.ac.in/", "apply_url": "https://nta.ac.in/"},
    {"org": "UIDAI", "org_full": "Unique Identification Authority of India", "career_url": "https://uidai.gov.in/en/about-uidai/work-with-uidai.html", "apply_url": "https://uidai.gov.in/"},
    {"org": "STPI", "org_full": "Software Technology Parks of India", "career_url": "https://stpi.in/en/careers", "apply_url": "https://stpi.in/en/careers"},
    {"org": "RailTel", "org_full": "RailTel Corporation of India", "career_url": "https://railtelindia.com/career", "apply_url": "https://railtelindia.com/career"},

    # ═══════ CENTRAL GOVERNMENT ═══════
    {"org": "SSC", "org_full": "Staff Selection Commission", "career_url": "https://ssc.gov.in/notice-board", "apply_url": "https://ssc.gov.in/login"},
    {"org": "UPSC", "org_full": "Union Public Service Commission", "career_url": "https://www.upsc.gov.in/recruitment/active-advertisements", "apply_url": "https://upsconline.nic.in/ora/"},
    {"org": "RRB", "org_full": "Railway Recruitment Boards", "career_url": "https://rrbcdg.gov.in/", "apply_url": "https://rrbcdg.gov.in/"},
    {"org": "Indian Army", "org_full": "Indian Army", "career_url": "https://joinindianarmy.nic.in/", "apply_url": "https://joinindianarmy.nic.in/"},
    {"org": "Indian Navy", "org_full": "Indian Navy", "career_url": "https://www.joinindiannavy.gov.in/en/", "apply_url": "https://www.joinindiannavy.gov.in/en/account/login"},
    {"org": "Indian Air Force", "org_full": "Indian Air Force", "career_url": "https://careerindianairforce.cdac.in/", "apply_url": "https://careerindianairforce.cdac.in/"},
    {"org": "India Post", "org_full": "India Post", "career_url": "https://indiapost.gov.in/VAS/Pages/IndiaPostHome.aspx", "apply_url": "https://indiapost.gov.in/"},
    {"org": "CSIR", "org_full": "Council of Scientific & Industrial Research", "career_url": "https://csir.res.in/", "apply_url": "https://csir.res.in/"},
    {"org": "ESIC", "org_full": "Employees State Insurance Corporation", "career_url": "https://esic.gov.in/recruitment", "apply_url": "https://esic.gov.in/"},
    {"org": "EPFO", "org_full": "Employees Provident Fund Organisation", "career_url": "https://epfindia.gov.in/", "apply_url": "https://epfindia.gov.in/"},
    {"org": "FCI", "org_full": "Food Corporation of India", "career_url": "https://fci.gov.in/recruitment.php", "apply_url": "https://fci.gov.in/"},
    {"org": "AAI", "org_full": "Airports Authority of India", "career_url": "https://aai.aero/en/careers", "apply_url": "https://aai.aero/"},
    {"org": "DMRC", "org_full": "Delhi Metro Rail Corporation", "career_url": "https://delhimetrorail.com/careers", "apply_url": "https://delhimetrorail.com/"},

    # ═══════ BANKING & FINANCE ═══════
    {"org": "SBI", "org_full": "State Bank of India", "career_url": "https://bank.sbi/web/careers/current-openings", "apply_url": "https://bank.sbi/web/careers/apply-online"},
    {"org": "RBI", "org_full": "Reserve Bank of India", "career_url": "https://opportunities.rbi.org.in/Scripts/Vacancies.aspx", "apply_url": "https://opportunities.rbi.org.in/"},
    {"org": "NABARD", "org_full": "National Bank for Agriculture & Rural Development", "career_url": "https://nabard.org/career-notices.aspx", "apply_url": "https://nabard.org/"},
    {"org": "LIC", "org_full": "Life Insurance Corporation of India", "career_url": "https://licindia.in/careers", "apply_url": "https://licindia.in/careers"},
    {"org": "SEBI", "org_full": "Securities & Exchange Board of India", "career_url": "https://sebi.gov.in/sebiweb/other/OtherAction.do?doRecruit=yes", "apply_url": "https://sebi.gov.in/"},

    # ═══════ PSUs ═══════
    {"org": "NTPC", "org_full": "National Thermal Power Corporation", "career_url": "https://ntpc.co.in/en/career", "apply_url": "https://ntpc.co.in/"},
    {"org": "ONGC", "org_full": "Oil & Natural Gas Corporation", "career_url": "https://ongcindia.com/web/ongcrecruit/careers", "apply_url": "https://ongcindia.com/"},
    {"org": "IOCL", "org_full": "Indian Oil Corporation Limited", "career_url": "https://iocl.com/working-with-iocl", "apply_url": "https://iocl.com/"},
    {"org": "BHEL", "org_full": "Bharat Heavy Electricals Limited", "career_url": "https://bhel.com/careers", "apply_url": "https://bhel.com/"},
    {"org": "SAIL", "org_full": "Steel Authority of India Limited", "career_url": "https://sail.co.in/en/careers", "apply_url": "https://sail.co.in/"},

    # ═══════ EDUCATION ═══════
    {"org": "KVS", "org_full": "Kendriya Vidyalaya Sangathan", "career_url": "https://kvsangathan.nic.in/", "apply_url": "https://kvsangathan.nic.in/"},
    {"org": "NVS", "org_full": "Navodaya Vidyalaya Samiti", "career_url": "https://navodaya.gov.in/nvs/en/Recruitment/", "apply_url": "https://navodaya.gov.in/"},
    {"org": "AIIMS", "org_full": "All India Institute of Medical Sciences", "career_url": "https://aiimsexams.ac.in/", "apply_url": "https://aiimsexams.ac.in/"},

    # ═══════ STATE PSCs (AP & TS) ═══════
    {"org": "APPSC", "org_full": "Andhra Pradesh Public Service Commission", "career_url": "https://psc.ap.gov.in/", "apply_url": "https://psc.ap.gov.in/"},
    {"org": "TSPSC", "org_full": "Telangana State Public Service Commission", "career_url": "https://tspsc.gov.in/", "apply_url": "https://tspsc.gov.in/"},
]


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def fetch_page(url: str) -> str:
    """Fetch a webpage with error handling."""
    resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or 'utf-8'
    return resp.text


def scrape_portal_with_ml(portal: dict) -> list:
    """Scrape a portal using ML ensemble for link classification and data extraction."""
    try:
        html = fetch_page(portal["career_url"])
    except Exception:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    page_text = soup.get_text(" ", strip=True)
    jobs = []
    seen = set()

    # Step 1: Classify all links using ML
    best_apply = portal["apply_url"]
    best_score = 0

    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        anchor = link.get_text(strip=True)
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue
        try:
            resolved = urljoin(portal["career_url"], href)
            result = ensemble.classify_link(resolved, anchor)
            if result['category'] == 'DIRECT_APPLY' and result['confidence'] > best_score:
                best_apply = resolved
                best_score = result['confidence']
        except Exception:
            pass

    # Step 2: Extract job notifications using ML
    recruitment_keywords = [
        'recruitment', 'vacancy', 'vacancies', 'notification',
        'advertisement', 'opening', 'walk-in', 'engagement',
        'appointment', 'selection', 'apply', 'posts', 'examination',
    ]

    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        href = link.get('href', '')
        if len(text) > 15 and any(kw in text.lower() for kw in recruitment_keywords):
            if text in seen:
                continue
            seen.add(text)
            resolved = urljoin(portal["career_url"], href)
            pdf_url = resolved if '.pdf' in resolved.lower() else None

            # Use ML ensemble for extraction
            job = ensemble.extract_job_details(
                title=text,
                page_text=page_text,
                org=portal["org"],
                org_full=portal["org_full"],
                portal_url=portal["career_url"],
                apply_link=best_apply,
                pdf_url=pdf_url,
            )

            # Only include if confidence is above threshold
            if job.get('_ml_confidence', 0) >= 0.3:
                # Remove internal ML metadata before returning
                clean_job = {k: v for k, v in job.items() if not k.startswith('_')}
                clean_job['ml_confidence'] = job.get('_ml_confidence', 0)
                jobs.append(clean_job)

    return jobs[:10]  # Limit per portal


# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/")
def read_root():
    """Health check with model status."""
    status = ensemble.get_model_status()
    return {
        "status": "running",
        "model": f"GovTechJobs AI Ensemble v{ensemble.version}",
        "models_loaded": ensemble.is_loaded,
        "portals_registered": len(PORTAL_REGISTRY),
        "link_classifier_trained": status['link_classifier']['is_trained'],
        "field_extractor_trained": status['field_extractor']['is_trained'],
        "confidence_scorer_trained": status['confidence_scorer']['is_trained'],
    }


@app.get("/model-status")
def model_status():
    """Detailed model performance metrics."""
    return ensemble.get_model_status()


@app.get("/extract")
def extract_links(target_url: str = Query(..., description="Webpage URL to crawl")):
    """Crawl a page, classify all links via ML model."""
    try:
        html = fetch_page(target_url)
    except Exception as e:
        return {"success": False, "error": str(e)}

    soup = BeautifulSoup(html, 'html.parser')
    classified = []
    seen = set()

    urls_batch = []
    anchors_batch = []
    resolved_urls = []

    for anchor in soup.find_all('a', href=True):
        text = anchor.get_text(strip=True)
        href = anchor.get('href', '')
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue
        try:
            resolved = urljoin(target_url, href)
            if resolved in seen:
                continue
            seen.add(resolved)
            urls_batch.append(resolved)
            anchors_batch.append(text)
            resolved_urls.append(resolved)
        except Exception:
            pass

    # Batch classification
    if urls_batch:
        predictions = ensemble.classify_links_batch(urls_batch, anchors_batch)
        for pred in predictions:
            if pred['category'] != 'IGNORE':
                classified.append(pred)

    classified.sort(key=lambda x: x['confidence'], reverse=True)
    direct = [c for c in classified if c['category'] == 'DIRECT_APPLY']
    career = [c for c in classified if c['category'] == 'CAREER_PAGE']
    pdfs = [c for c in classified if c['category'] == 'NOTIFICATION_PDF']

    return {
        "success": True,
        "best_direct_apply": direct[0] if direct else None,
        "direct_apply_links": direct,
        "career_page_links": career,
        "notification_pdfs": pdfs,
        "total_classified": len(classified),
    }


class PortalRequest(BaseModel):
    portal_url: str
    org: str = "Unknown"
    org_full: str = "Unknown Organization"


@app.post("/scrape-portal")
def scrape_single_portal(req: PortalRequest):
    """Scrape a single portal using ML ensemble."""
    portal = {
        "org": req.org,
        "org_full": req.org_full,
        "career_url": req.portal_url,
        "apply_url": req.portal_url,
    }
    try:
        jobs = scrape_portal_with_ml(portal)
        return {"success": True, "count": len(jobs), "jobs": jobs}
    except Exception as e:
        return {"success": False, "error": str(e), "jobs": []}


class PredictRequest(BaseModel):
    text: str
    org: str = "Unknown"
    org_full: str = "Unknown Organization"
    title: str = ""


@app.post("/predict")
def predict_from_text(req: PredictRequest):
    """Run ML extraction on raw text."""
    try:
        job = ensemble.extract_job_details(
            title=req.title or "Unknown Notification",
            page_text=req.text,
            org=req.org,
            org_full=req.org_full,
            portal_url="",
            apply_link="",
        )
        return {
            "success": True,
            "extraction": {k: v for k, v in job.items() if not k.startswith('_')},
            "ml_confidence": job.get('_ml_confidence', 0),
            "is_reliable": job.get('_ml_is_reliable', False),
            "flagged_fields": job.get('_ml_flagged_fields', []),
            "extraction_time_ms": job.get('_extraction_time_ms', 0),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class PdfRequest(BaseModel):
    pdf_url: str
    org: str = "Unknown"


@app.post("/extract-pdf")
def extract_from_pdf(req: PdfRequest):
    """Download and extract data from a notification PDF."""
    try:
        pdf_data = extract_pdf_from_url(req.pdf_url)
        if not pdf_data or 'error' in pdf_data:
            return {"success": False, "error": pdf_data.get('error', 'Failed to extract PDF')}

        # Run ML extraction on PDF text
        job = ensemble.extract_job_details(
            title=f"{req.org} Notification",
            page_text=pdf_data['text'][:5000],  # Limit text length
            org=req.org,
            org_full=req.org,
            portal_url=req.pdf_url,
            apply_link="",
            pdf_url=req.pdf_url,
        )

        # Extract cutoffs from PDF
        cutoffs = ensemble.extract_cutoffs(pdf_data['text'])

        return {
            "success": True,
            "extraction": {k: v for k, v in job.items() if not k.startswith('_')},
            "cutoffs": cutoffs,
            "pdf_pages": pdf_data.get('page_count', 0),
            "ml_confidence": job.get('_ml_confidence', 0),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/reload-notifications")
def reload_notifications():
    """Scrape ALL registered portals using ML ensemble."""
    all_jobs = []
    errors = []

    for portal in PORTAL_REGISTRY:
        try:
            jobs = scrape_portal_with_ml(portal)
            all_jobs.extend(jobs)
        except Exception as e:
            errors.append({"portal": portal["org"], "error": str(e)})

    # Deduplicate
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job.get("exam_name", ""), job.get("organization", ""))
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return {
        "success": True,
        "total_portals_scraped": len(PORTAL_REGISTRY),
        "total_jobs_found": len(unique_jobs),
        "errors": errors,
        "jobs": unique_jobs,
    }
