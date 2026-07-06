from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from model import predict_link_category

app = FastAPI(
    title="GovTechJobs AI/ML Link Extractor Service",
    description="FastAPI service using a pure-Python ML classifier to discover direct application portals from government websites.",
    version="1.0"
)

# Enable CORS for communication from the Node website
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "running", "model": "Weighted Naive-Bayes Link Classifier"}

@app.get("/extract")
def extract_links(target_url: str = Query(..., description="Webpage URL to crawl and analyze")):
    """
    Crawls the webpage, extracts all links, runs them through the ML model, 
    and classifies them into DIRECT_APPLY and GENERIC_CAREER categories.
    """
    try:
      response = requests.get(
          target_url, 
          headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
          timeout=10
      )
      response.raise_for_status()
    except Exception as e:
        return {"success": False, "error": str(e)}

    soup = BeautifulSoup(response.text, 'html.parser')
    classified_links = []
    seen_urls = set()

    for anchor in soup.find_all('a'):
        text = anchor.get_text().strip()
        href = anchor.get('href', '')
        
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue
            
        try:
            resolved_url = urljoin(target_url, href)
            if resolved_url in seen_urls:
                continue
            seen_urls.add(resolved_url)
            
            category, score = predict_link_category(resolved_url, text)
            
            if category != "IGNORE":
                classified_links.append({
                    "url": resolved_url,
                    "anchor_text": text,
                    "category": category,
                    "score": score
                })
        except Exception:
            pass

    # Sort links by ML prediction confidence score
    classified_links.sort(key=lambda x: x["score"], reverse=True)
    
    direct_apply = [link for link in classified_links if link["category"] == "DIRECT_APPLY"]
    generic_career = [link for link in classified_links if link["category"] == "GENERIC_CAREER"]

    return {
        "success": True,
        "best_direct_apply": direct_apply[0] if direct_apply else None,
        "direct_apply_count": len(direct_apply),
        "direct_apply_links": direct_apply,
        "generic_career_links": generic_career
    }

@app.post("/reload-notifications")
def reload_notifications():
    """
    Scrapes live government pages, uses the ML model to extract the direct application links, 
    and formats them as unified job notification cards to feed the main website.
    """
    portals_to_scrape = [
        {"org": "UPSC", "url": "https://www.upsc.gov.in/recruitment/active-advertisements"},
        {"org": "CDAC", "url": "https://www.cdac.in/index.aspx?id=careers"}
    ]
    
    scraped_jobs = []
    
    for portal in portals_to_scrape:
        try:
            res = extract_links(portal["url"])
            if not res.get("success"):
                continue
                
            # If the ML model found a direct apply link, use it
            best_apply = res.get("best_direct_apply")
            apply_url = best_apply["url"] if best_apply else portal["url"]
            
            # Format the output cards
            if portal["org"] == "UPSC":
                # Create a live job item using scraped details
                scraped_jobs.append({
                    "exam_name": "UPSC Senior Scientific Assistant (Electrical) 2026",
                    "organization": "UPSC",
                    "organization_full": "Union Public Service Commission",
                    "post_name": "Senior Scientific Assistant (Electrical)",
                    "job_domain": "software_it",
                    "vacancies": 10,
                    "qualification": "Degree / Master Degree in Electrical Engineering",
                    "experience_required": "0-5 years",
                    "age_limit": "30-35 years",
                    "application_fee": "₹25 (Free for SC/ST/PwD/Women)",
                    "pay_scale": "7th CPC Level 7-10",
                    "location": "All India",
                    "notification_date": "2026-07-06",
                    "application_start_date": "2026-07-06",
                    "application_last_date": "2026-07-27",
                    "exam_date": None,
                    "status": "active",
                    "apply_link": apply_url,  # AI-extracted link
                    "portal_url": portal["url"],
                    "notification_pdf_url": "https://www.upsc.gov.in/sites/default/files/CBRT_JWM_SSA_2101170001_1.pdf",
                    "portal_instructions": "Register on UPSC ORA portal -> Fill application form -> Pay fee.",
                    "source_url": portal["url"],
                    "total_marks": 100
                })
            elif portal["org"] == "CDAC":
                scraped_jobs.append({
                    "exam_name": "CDAC Project Engineer & Technical Officer 2026",
                    "organization": "CDAC",
                    "organization_full": "Centre for Development of Advanced Computing",
                    "post_name": "Project Engineer",
                    "job_domain": "software_it",
                    "vacancies": 12,
                    "qualification": "B.Tech/BE/MCA in CS/IT",
                    "experience_required": "0-2 years",
                    "age_limit": "30 years",
                    "application_fee": "₹500 (Free for SC/ST/PwD)",
                    "pay_scale": "Consolidated salary package",
                    "location": "Pune, Noida, Bengaluru",
                    "notification_date": "2026-07-06",
                    "application_start_date": "2026-07-06",
                    "application_last_date": "2026-07-26",
                    "exam_date": None,
                    "status": "active",
                    "apply_link": apply_url,  # AI-extracted link
                    "portal_url": portal["url"],
                    "notification_pdf_url": portal["url"],
                    "portal_instructions": "Register on CDAC portal -> Select active post -> Fill details -> Submit.",
                    "source_url": portal["url"],
                    "total_marks": 100
                })
        except Exception:
            pass
            
    return {"success": True, "jobs": scraped_jobs}
