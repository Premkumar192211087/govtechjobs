"""
GovTechJobs AI/ML FastAPI Service

Endpoints:
  GET  /                  — Health check
  GET  /extract           — Classify all links on a page
  POST /scrape-portal     — Scrape a single portal and extract real job details
  POST /reload-notifications — Scrape ALL registered portals and return live jobs
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import traceback

from model import predict_link_category, extract_job_details

app = FastAPI(
    title="GovTechJobs AI/ML Service",
    description="Real-time government job scraper powered by NLP extraction and link classification models.",
    version="2.0"
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

# ═══════════════════════════════════════════════════════════════
# PORTAL REGISTRY — No hardcoded job data. Only scraping configs.
# ═══════════════════════════════════════════════════════════════

PORTAL_REGISTRY = [
    # ═══════ IT/SOFTWARE FOCUSED PORTALS ═══════
    {"org": "BARC", "org_full": "Bhabha Atomic Research Centre", "career_url": "https://barc.gov.in/careers/", "apply_url": "https://barc.gov.in/careers/", "scraper": "generic"},
    {"org": "BEL", "org_full": "Bharat Electronics Limited", "career_url": "https://bel-india.in/Ede/ContentPage.aspx?MId=17&CId=37&LId=1&link=37", "apply_url": "https://bel-india.in/", "scraper": "generic"},
    {"org": "BSNL", "org_full": "Bharat Sanchar Nigam Limited", "career_url": "https://bsnl.co.in/", "apply_url": "https://bsnl.co.in/", "scraper": "generic"},
    {"org": "CDAC", "org_full": "Centre for Development of Advanced Computing", "career_url": "https://www.cdac.in/index.aspx?id=careers", "apply_url": "https://www.cdac.in/index.aspx?id=careers", "scraper": "cdac"},
    {"org": "CRIS", "org_full": "Centre for Railway Information Systems", "career_url": "https://cris.org.in/crisweb/design1/innerContent.jsp?linkID=71", "apply_url": "https://cris.org.in/", "scraper": "generic"},
    {"org": "CSC", "org_full": "Common Services Centres", "career_url": "https://csc.gov.in/", "apply_url": "https://csc.gov.in/", "scraper": "generic"},
    {"org": "DRDO", "org_full": "Defence Research & Development Organisation", "career_url": "https://rac.gov.in/", "apply_url": "https://rac.gov.in/", "scraper": "generic"},
    {"org": "ECIL", "org_full": "Electronics Corporation of India Limited", "career_url": "https://ecil.co.in/jobs/", "apply_url": "https://ecil.co.in/jobs/", "scraper": "generic"},
    {"org": "HAL", "org_full": "Hindustan Aeronautics Limited", "career_url": "https://hal-india.co.in/Career%20with%20HAL/M__57", "apply_url": "https://hal-india.co.in/", "scraper": "generic"},
    {"org": "IBPS", "org_full": "Institute of Banking Personnel Selection", "career_url": "https://www.ibps.in/", "apply_url": "https://www.ibps.in/", "scraper": "generic"},
    {"org": "ISRO", "org_full": "Indian Space Research Organisation", "career_url": "https://www.isro.gov.in/Careers.html", "apply_url": "https://www.isro.gov.in/Careers.html", "scraper": "isro"},
    {"org": "MTNL", "org_full": "Mahanagar Telephone Nigam Limited", "career_url": "https://mtnl.in/", "apply_url": "https://mtnl.in/", "scraper": "generic"},
    {"org": "NIC", "org_full": "National Informatics Centre", "career_url": "https://www.nic.in/careers/", "apply_url": "https://www.nic.in/careers/", "scraper": "generic"},
    {"org": "NIELIT", "org_full": "National Institute of Electronics & Information Technology", "career_url": "https://www.nielit.gov.in/content/recruitment", "apply_url": "https://www.nielit.gov.in/content/recruitment", "scraper": "generic"},
    {"org": "NTA", "org_full": "National Testing Agency", "career_url": "https://nta.ac.in/", "apply_url": "https://nta.ac.in/", "scraper": "generic"},
    {"org": "UIDAI", "org_full": "Unique Identification Authority of India", "career_url": "https://uidai.gov.in/en/about-uidai/work-with-uidai.html", "apply_url": "https://uidai.gov.in/", "scraper": "generic"},
    {"org": "STPI", "org_full": "Software Technology Parks of India", "career_url": "https://stpi.in/en/careers", "apply_url": "https://stpi.in/en/careers", "scraper": "generic"},
    {"org": "MeitY", "org_full": "Ministry of Electronics & IT", "career_url": "https://meity.gov.in/", "apply_url": "https://meity.gov.in/", "scraper": "generic"},
    {"org": "CERT-In", "org_full": "Indian Computer Emergency Response Team", "career_url": "https://cert-in.org.in/", "apply_url": "https://cert-in.org.in/", "scraper": "generic"},
    {"org": "RailTel", "org_full": "RailTel Corporation of India", "career_url": "https://railtelindia.com/career", "apply_url": "https://railtelindia.com/career", "scraper": "generic"},

    # ═══════ CENTRAL GOVERNMENT ═══════
    {"org": "SSC", "org_full": "Staff Selection Commission", "career_url": "https://ssc.gov.in/notice-board", "apply_url": "https://ssc.gov.in/login", "scraper": "ssc"},
    {"org": "UPSC", "org_full": "Union Public Service Commission", "career_url": "https://www.upsc.gov.in/recruitment/active-advertisements", "apply_url": "https://upsconline.nic.in/ora/", "scraper": "upsc"},
    {"org": "RRB", "org_full": "Railway Recruitment Boards", "career_url": "https://rrbcdg.gov.in/", "apply_url": "https://rrbcdg.gov.in/", "scraper": "generic"},
    {"org": "Indian Army", "org_full": "Indian Army", "career_url": "https://joinindianarmy.nic.in/", "apply_url": "https://joinindianarmy.nic.in/", "scraper": "generic"},
    {"org": "Indian Navy", "org_full": "Indian Navy", "career_url": "https://www.joinindiannavy.gov.in/en/", "apply_url": "https://www.joinindiannavy.gov.in/en/account/login", "scraper": "generic"},
    {"org": "Indian Air Force", "org_full": "Indian Air Force", "career_url": "https://careerindianairforce.cdac.in/", "apply_url": "https://careerindianairforce.cdac.in/", "scraper": "generic"},
    {"org": "India Post", "org_full": "India Post", "career_url": "https://indiapost.gov.in/VAS/Pages/IndiaPostHome.aspx", "apply_url": "https://indiapost.gov.in/", "scraper": "generic"},
    {"org": "CSIR", "org_full": "Council of Scientific & Industrial Research", "career_url": "https://csir.res.in/", "apply_url": "https://csir.res.in/", "scraper": "generic"},
    {"org": "DAE", "org_full": "Department of Atomic Energy", "career_url": "https://dae.gov.in/", "apply_url": "https://dae.gov.in/", "scraper": "generic"},

    # ═══════ BANKING & FINANCE ═══════
    {"org": "SBI", "org_full": "State Bank of India", "career_url": "https://bank.sbi/web/careers/current-openings", "apply_url": "https://bank.sbi/web/careers/apply-online", "scraper": "generic"},
    {"org": "RBI", "org_full": "Reserve Bank of India", "career_url": "https://opportunities.rbi.org.in/Scripts/Vacancies.aspx", "apply_url": "https://opportunities.rbi.org.in/Scripts/Vacancies.aspx", "scraper": "generic"},
    {"org": "NABARD", "org_full": "National Bank for Agriculture & Rural Development", "career_url": "https://nabard.org/career-notices.aspx", "apply_url": "https://nabard.org/", "scraper": "generic"},
    {"org": "LIC", "org_full": "Life Insurance Corporation of India", "career_url": "https://licindia.in/careers", "apply_url": "https://licindia.in/careers", "scraper": "generic"},
    {"org": "SEBI", "org_full": "Securities & Exchange Board of India", "career_url": "https://sebi.gov.in/sebiweb/other/OtherAction.do?doRecruit=yes", "apply_url": "https://sebi.gov.in/", "scraper": "generic"},
    {"org": "SIDBI", "org_full": "Small Industries Development Bank of India", "career_url": "https://sidbi.in/en/careers", "apply_url": "https://sidbi.in/", "scraper": "generic"},
    {"org": "IRDAI", "org_full": "Insurance Regulatory & Development Authority", "career_url": "https://irdai.gov.in/vacancies", "apply_url": "https://irdai.gov.in/", "scraper": "generic"},

    # ═══════ PSU / PUBLIC SECTOR ═══════
    {"org": "NTPC", "org_full": "National Thermal Power Corporation", "career_url": "https://ntpc.co.in/en/career", "apply_url": "https://ntpc.co.in/", "scraper": "generic"},
    {"org": "ONGC", "org_full": "Oil & Natural Gas Corporation", "career_url": "https://ongcindia.com/web/ongcrecruit/careers", "apply_url": "https://ongcindia.com/", "scraper": "generic"},
    {"org": "IOCL", "org_full": "Indian Oil Corporation Limited", "career_url": "https://iocl.com/working-with-iocl", "apply_url": "https://iocl.com/", "scraper": "generic"},
    {"org": "GAIL", "org_full": "Gas Authority of India Limited", "career_url": "https://gailonline.com/careers.html", "apply_url": "https://gailonline.com/", "scraper": "generic"},
    {"org": "BHEL", "org_full": "Bharat Heavy Electricals Limited", "career_url": "https://bhel.com/careers", "apply_url": "https://bhel.com/", "scraper": "generic"},
    {"org": "PowerGrid", "org_full": "Power Grid Corporation of India", "career_url": "https://powergrid.in/career", "apply_url": "https://powergrid.in/", "scraper": "generic"},
    {"org": "Coal India", "org_full": "Coal India Limited", "career_url": "https://coalindia.in/career.aspx", "apply_url": "https://coalindia.in/", "scraper": "generic"},
    {"org": "SAIL", "org_full": "Steel Authority of India Limited", "career_url": "https://sail.co.in/en/careers", "apply_url": "https://sail.co.in/", "scraper": "generic"},
    {"org": "HPCL", "org_full": "Hindustan Petroleum Corporation Limited", "career_url": "https://hindustanpetroleum.com/pages/recruitment", "apply_url": "https://hindustanpetroleum.com/", "scraper": "generic"},
    {"org": "BPCL", "org_full": "Bharat Petroleum Corporation Limited", "career_url": "https://bharatpetroleum.in/Careers/Career-Home.aspx", "apply_url": "https://bharatpetroleum.in/", "scraper": "generic"},
    {"org": "CONCOR", "org_full": "Container Corporation of India", "career_url": "https://concorindia.co.in/concor/english/career/career.aspx", "apply_url": "https://concorindia.co.in/", "scraper": "generic"},
    {"org": "NPCIL", "org_full": "Nuclear Power Corporation of India", "career_url": "https://npcil.nic.in/content/300_1_CareeratNPCIL.aspx", "apply_url": "https://npcil.nic.in/", "scraper": "generic"},
    {"org": "NHPC", "org_full": "National Hydroelectric Power Corporation", "career_url": "https://nhpcindia.com/career.htm", "apply_url": "https://nhpcindia.com/", "scraper": "generic"},
    {"org": "THDC", "org_full": "THDC India Limited", "career_url": "https://thdc.co.in/en/career/", "apply_url": "https://thdc.co.in/", "scraper": "generic"},

    # ═══════ EDUCATION & RESEARCH ═══════
    {"org": "IITs", "org_full": "Indian Institutes of Technology", "career_url": "https://iit.ac.in/", "apply_url": "https://iit.ac.in/", "scraper": "generic"},
    {"org": "NITs", "org_full": "National Institutes of Technology", "career_url": "https://nitcouncil.org.in/", "apply_url": "https://nitcouncil.org.in/", "scraper": "generic"},
    {"org": "AIIMS", "org_full": "All India Institute of Medical Sciences", "career_url": "https://aiimsexams.ac.in/", "apply_url": "https://aiimsexams.ac.in/", "scraper": "generic"},
    {"org": "KVS", "org_full": "Kendriya Vidyalaya Sangathan", "career_url": "https://kvsangathan.nic.in/", "apply_url": "https://kvsangathan.nic.in/", "scraper": "generic"},
    {"org": "NVS", "org_full": "Navodaya Vidyalaya Samiti", "career_url": "https://navodaya.gov.in/nvs/en/Recruitment/", "apply_url": "https://navodaya.gov.in/", "scraper": "generic"},
    {"org": "UGC", "org_full": "University Grants Commission", "career_url": "https://ugc.gov.in/", "apply_url": "https://ugc.gov.in/", "scraper": "generic"},

    # ═══════ STATE GOVERNMENT ═══════
    {"org": "State PSC", "org_full": "State Public Service Commissions", "career_url": "https://upsc.gov.in/state-pscs", "apply_url": "https://upsc.gov.in/", "scraper": "generic"},
    {"org": "Smart Cities", "org_full": "Smart Cities Mission", "career_url": "https://smartcities.gov.in/", "apply_url": "https://smartcities.gov.in/", "scraper": "generic"},
]

# ═══════════════════════════════════════════════════════════════
# HELPER: Fetch a page
# ═══════════════════════════════════════════════════════════════

def fetch_page(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=12, verify=False)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or 'utf-8'
    return resp.text


# ═══════════════════════════════════════════════════════════════
# PORTAL-SPECIFIC SCRAPERS
# ═══════════════════════════════════════════════════════════════

def scrape_upsc(portal: dict) -> list:
    """Scrape UPSC active advertisements — extract real titles, PDF links, vacancy counts."""
    html = fetch_page(portal["career_url"])
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    page_text = soup.get_text(" ", strip=True)

    # UPSC lists advertisements with h3 titles and PDF download links
    for heading in soup.find_all(['h3', 'h4']):
        title = heading.get_text(strip=True)
        if not title or len(title) < 15:
            continue
        # Skip navigation/menu headings
        if any(skip in title.lower() for skip in ['menu', 'navigation', 'footer', 'header', 'search']):
            continue

        # Find nearest PDF link
        pdf_url = None
        sibling = heading.find_next('a', href=True)
        if sibling:
            href = sibling.get('href', '')
            resolved = urljoin(portal["career_url"], href)
            if '.pdf' in resolved.lower():
                pdf_url = resolved

        job = extract_job_details(
            title=title,
            page_text=page_text,
            org=portal["org"],
            org_full=portal["org_full"],
            portal_url=portal["career_url"],
            apply_link=portal["apply_url"],
            pdf_url=pdf_url
        )
        jobs.append(job)
    
    return jobs


def scrape_ssc(portal: dict) -> list:
    """Scrape SSC notice board for recruitment notifications."""
    html = fetch_page(portal["career_url"])
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    page_text = soup.get_text(" ", strip=True)

    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        href = link.get('href', '')
        # Focus on recruitment-related notices
        if len(text) > 20 and any(kw in text.lower() for kw in ['recruitment', 'examination', 'vacancies', 'selection', 'cgl', 'chsl', 'je ', 'mts', 'steno']):
            resolved = urljoin(portal["career_url"], href)
            pdf_url = resolved if '.pdf' in resolved.lower() else None
            
            job = extract_job_details(
                title=text,
                page_text=page_text,
                org=portal["org"],
                org_full=portal["org_full"],
                portal_url=portal["career_url"],
                apply_link=portal["apply_url"],
                pdf_url=pdf_url
            )
            jobs.append(job)
    
    return jobs[:10]  # Limit to avoid duplicates


def scrape_cdac(portal: dict) -> list:
    """Scrape CDAC careers page for active recruitment drives."""
    html = fetch_page(portal["career_url"])
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    page_text = soup.get_text(" ", strip=True)
    seen = set()

    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        href = link.get('href', '')
        if len(text) > 10 and any(kw in text.lower() for kw in ['recruitment', 'project engineer', 'technical', 'vacancy', 'career', 'walk-in', 'contractual']):
            if text in seen:
                continue
            seen.add(text)
            resolved = urljoin(portal["career_url"], href)

            job = extract_job_details(
                title=text,
                page_text=page_text,
                org=portal["org"],
                org_full=portal["org_full"],
                portal_url=portal["career_url"],
                apply_link=resolved,
                pdf_url=resolved
            )
            jobs.append(job)
    
    return jobs


def scrape_isro(portal: dict) -> list:
    """Scrape ISRO careers page."""
    html = fetch_page(portal["career_url"])
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    page_text = soup.get_text(" ", strip=True)
    seen = set()

    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        href = link.get('href', '')
        if len(text) > 15 and any(kw in text.lower() for kw in ['recruitment', 'scientist', 'engineer', 'technician', 'icrb', 'vacancy', 'openings']):
            if text in seen:
                continue
            seen.add(text)
            resolved = urljoin(portal["career_url"], href)

            # Try to find direct apply link
            _, score = predict_link_category(resolved, text)
            apply_link = resolved if score > 3 else portal["apply_url"]

            job = extract_job_details(
                title=text,
                page_text=page_text,
                org=portal["org"],
                org_full=portal["org_full"],
                portal_url=portal["career_url"],
                apply_link=apply_link,
                pdf_url=resolved if '.pdf' in resolved.lower() else None
            )
            jobs.append(job)
    
    return jobs


def scrape_generic(portal: dict) -> list:
    """Generic scraper for portals without custom logic — uses AI model to find job links."""
    try:
        html = fetch_page(portal["career_url"])
    except Exception:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    page_text = soup.get_text(" ", strip=True)
    seen = set()

    # Use ML link classifier to find the best apply link on this page
    best_apply = portal["apply_url"]
    best_score = 0
    
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        anchor = link.get_text(strip=True)
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue
        try:
            resolved = urljoin(portal["career_url"], href)
            cat, score = predict_link_category(resolved, anchor)
            if cat == "DIRECT_APPLY" and score > best_score:
                best_apply = resolved
                best_score = score
        except Exception:
            pass

    # Extract notification titles
    recruitment_keywords = ['recruitment', 'vacancy', 'vacancies', 'notification',
                            'advertisement', 'opening', 'walk-in', 'engagement',
                            'appointment', 'selection', 'apply', 'posts']

    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        href = link.get('href', '')
        if len(text) > 15 and any(kw in text.lower() for kw in recruitment_keywords):
            if text in seen:
                continue
            seen.add(text)
            resolved = urljoin(portal["career_url"], href)
            pdf_url = resolved if '.pdf' in resolved.lower() else None

            job = extract_job_details(
                title=text,
                page_text=page_text,
                org=portal["org"],
                org_full=portal["org_full"],
                portal_url=portal["career_url"],
                apply_link=best_apply,
                pdf_url=pdf_url
            )
            jobs.append(job)
    
    return jobs[:8]


SCRAPER_MAP = {
    "upsc": scrape_upsc,
    "ssc": scrape_ssc,
    "cdac": scrape_cdac,
    "isro": scrape_isro,
    "generic": scrape_generic,
}


# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/")
def read_root():
    return {
        "status": "running",
        "model": "NLP Job Extractor + Naive-Bayes Link Classifier v2.0",
        "portals_registered": len(PORTAL_REGISTRY),
    }


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
            category, score = predict_link_category(resolved, text)
            if category != "IGNORE":
                classified.append({"url": resolved, "anchor_text": text, "category": category, "score": score})
        except Exception:
            pass

    classified.sort(key=lambda x: x["score"], reverse=True)
    direct = [c for c in classified if c["category"] == "DIRECT_APPLY"]
    generic = [c for c in classified if c["category"] == "GENERIC_CAREER"]

    return {
        "success": True,
        "best_direct_apply": direct[0] if direct else None,
        "direct_apply_links": direct,
        "generic_career_links": generic,
    }


class PortalRequest(BaseModel):
    portal_url: str
    org: str = "Unknown"
    org_full: str = "Unknown Organization"

@app.post("/scrape-portal")
def scrape_single_portal(req: PortalRequest):
    """Scrape a single portal URL using the generic AI extractor."""
    portal = {
        "org": req.org,
        "org_full": req.org_full,
        "career_url": req.portal_url,
        "apply_url": req.portal_url,
        "scraper": "generic",
    }
    try:
        jobs = scrape_generic(portal)
        return {"success": True, "count": len(jobs), "jobs": jobs}
    except Exception as e:
        return {"success": False, "error": str(e), "jobs": []}


@app.post("/reload-notifications")
def reload_notifications():
    """
    Scrape ALL registered government portals using portal-specific or generic AI scrapers.
    Returns real-time extracted job notifications with zero hardcoded data.
    """
    all_jobs = []
    errors = []

    for portal in PORTAL_REGISTRY:
        scraper_fn = SCRAPER_MAP.get(portal["scraper"], scrape_generic)
        try:
            jobs = scraper_fn(portal)
            all_jobs.extend(jobs)
        except Exception as e:
            errors.append({"portal": portal["org"], "error": str(e)})
    
    # Deduplicate by title
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job["exam_name"], job["organization"])
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
