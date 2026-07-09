"""
Dataset Generator — Creates training datasets for all 3 ML models.

Since no public labeled dataset exists for Indian government job portal scraping,
this module generates comprehensive synthetic + pattern-based datasets:

1. URL Classification Dataset (1500+ samples) — for XGBoost link classifier
2. NER/Field Extraction Dataset (2000+ samples) — for spaCy NER + CRF extractor  
3. Confidence Scoring Dataset — for Random Forest validator

All data is based on real patterns observed across UPSC, SSC, IBPS, ISRO, DRDO,
State PSCs (AP, TS), RRB, Banking, PSU, and other Indian government portals.
"""

import json
import os
import random
import re
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


# ═══════════════════════════════════════════════════════════════
# SEED DATA — Real patterns from Indian government portals
# ═══════════════════════════════════════════════════════════════

# Real government portal domains
GOV_DOMAINS = [
    'upsc.gov.in', 'ssc.gov.in', 'ibps.in', 'isro.gov.in', 'drdo.gov.in',
    'rac.gov.in', 'cdac.in', 'nic.in', 'nielit.gov.in', 'bel-india.in',
    'ecil.co.in', 'hal-india.co.in', 'nta.ac.in', 'uidai.gov.in', 'stpi.in',
    'meity.gov.in', 'cert-in.org.in', 'railtelindia.com', 'bsnl.co.in',
    'rrbcdg.gov.in', 'joinindianarmy.nic.in', 'joinindiannavy.gov.in',
    'indiapost.gov.in', 'csir.res.in', 'dae.gov.in', 'barc.gov.in',
    'bank.sbi', 'rbi.org.in', 'nabard.org', 'licindia.in', 'sebi.gov.in',
    'ntpc.co.in', 'ongcindia.com', 'iocl.com', 'gailonline.com',
    'bhel.com', 'sail.co.in', 'powergrid.in', 'coalindia.in',
    'kvsangathan.nic.in', 'navodaya.gov.in', 'ugc.gov.in', 'aiimsexams.ac.in',
    'psc.ap.gov.in', 'tspsc.gov.in', 'esic.gov.in', 'epfindia.gov.in',
    'fci.gov.in', 'aai.aero', 'delhimetrorail.com', 'ctet.nic.in',
    'cbseresults.nic.in', 'nhmmp.gov.in',
]

SOCIAL_DOMAINS = [
    'facebook.com', 'twitter.com', 'linkedin.com', 'youtube.com',
    'instagram.com', 't.me', 'wa.me', 'pinterest.com',
]

# Real exam names used in Indian government recruitment
EXAM_NAMES = [
    'Combined Graduate Level Examination (CGL) 2026',
    'Combined Higher Secondary Level Examination (CHSL) 2026',
    'Junior Engineer (JE) Recruitment 2026',
    'Multi Tasking Staff (MTS) Examination 2026',
    'Stenographer Grade C & D Recruitment 2026',
    'Civil Services Examination (CSE) 2026',
    'Engineering Services Examination (ESE) 2026',
    'Combined Defence Services Examination (CDS) 2026',
    'National Defence Academy (NDA) Examination 2026',
    'Indian Forest Service Examination 2026',
    'IBPS PO/MT Recruitment CRP-XIV',
    'IBPS Clerk Recruitment CRP Clerks-XIV',
    'IBPS SO Specialist Officer Recruitment 2026',
    'IBPS RRB Officer Scale-I Recruitment 2026',
    'SBI PO Recruitment 2026',
    'SBI Clerk Recruitment 2026',
    'SBI Specialist Officer (IT) Recruitment 2026',
    'RBI Grade B Officer Recruitment 2026',
    'RBI Assistant Recruitment 2026',
    'RBI Security Guard Recruitment 2026',
    'NABARD Grade A & B Officer Recruitment 2026',
    'LIC AAO Recruitment 2026',
    'LIC ADO Recruitment 2026',
    'LIC Assistant Recruitment 2026',
    'SEBI Grade A Officer Recruitment 2026',
    'ISRO Scientist/Engineer SC Recruitment 2026',
    'ISRO Technician B Recruitment 2026',
    'ISRO ICRB Centralised Recruitment 2026',
    'DRDO Scientist B Recruitment through RAC 2026',
    'DRDO CEPTAM Recruitment 2026',
    'CDAC Project Engineer Recruitment 2026',
    'CDAC Research Engineer Walk-in 2026',
    'NIC Scientist B Recruitment 2026',
    'NIELIT Scientist B Recruitment 2026',
    'BEL Project Engineer Recruitment 2026',
    'BEL Trainee Engineer Recruitment 2026',
    'ECIL Graduate Engineer Trainee (GET) Recruitment 2026',
    'HAL Management Trainee Recruitment 2026',
    'RRB NTPC Recruitment 2026',
    'RRB Group D Recruitment 2026',
    'RRB JE Recruitment 2026',
    'RRB ALP Technician Recruitment 2026',
    'FCI Manager & Assistant Grade III Recruitment 2026',
    'AAI Junior Executive Recruitment 2026',
    'DMRC Junior Engineer Recruitment 2026',
    'ESIC UDC/Stenographer/MTS Recruitment 2026',
    'EPFO Assistant Recruitment 2026',
    'India Post GDS Recruitment 2026',
    'India Post Postal Assistant/SA Recruitment 2026',
    'KVS PGT/TGT/PRT Recruitment 2026',
    'NVS TGT/PGT Recruitment 2026',
    'UGC NET June 2026',
    'CTET July 2026',
    'AIIMS Nursing Officer Recruitment 2026',
    'NTPC Executive Trainee through GATE 2026',
    'ONGC Graduate Trainee through GATE 2026',
    'IOCL Engineers/Officers through GATE 2026',
    'GAIL Executive Trainee through GATE 2026',
    'BHEL Engineer Trainee through GATE 2026',
    'Power Grid Executive Trainee through GATE 2026',
    'Coal India Management Trainee through GATE 2026',
    'SAIL Management Trainee through GATE 2026',
    'APPSC Group-I Services Recruitment 2026',
    'APPSC Group-II Services Recruitment 2026',
    'APPSC Panchayat Secretary Recruitment 2026',
    'APPSC Degree College Lecturer Recruitment 2026',
    'TSPSC Group-I Services Recruitment 2026',
    'TSPSC Group-II Services Recruitment 2026',
    'TSPSC Group-III Services Recruitment 2026',
    'TSPSC Gurukula Teacher Recruitment 2026',
    'TSPSC Forest Range Officer Recruitment 2026',
    'Indian Army Agniveer Rally 2026',
    'Indian Navy Agniveer SSR/MR 2026',
    'Indian Air Force AFCAT 2026',
    'CSIR NET June 2026',
    'BARC OCES/DGFS 2026',
]

# Real post names
POST_NAMES = [
    'Junior Engineer (Civil/Mechanical/Electrical/IT)',
    'Scientist/Engineer SC', 'Scientist B', 'Scientist C',
    'Probationary Officer', 'Clerk', 'Specialist Officer (IT)',
    'Grade B Officer', 'Assistant', 'Stenographer Grade C',
    'Multi Tasking Staff (MTS)', 'Sub Inspector',
    'Project Engineer', 'Research Engineer', 'Software Developer',
    'Graduate Engineer Trainee (GET)', 'Management Trainee',
    'Executive Trainee', 'Technical Officer',
    'Panchayat Secretary', 'Group-I Officer', 'Group-II Officer',
    'Degree College Lecturer', 'PGT Computer Science',
    'TGT Mathematics', 'Primary Teacher (PRT)',
    'Upper Division Clerk (UDC)', 'Lower Division Clerk (LDC)',
    'Postal Assistant', 'Sorting Assistant', 'Gramin Dak Sevak',
    'Nursing Officer', 'Staff Nurse', 'Junior Resident',
    'Constable', 'Head Constable', 'ASI',
    'Section Officer', 'Accounts Officer',
    'Junior Analyst', 'Data Entry Operator',
    'Technician B', 'Draughtsman', 'Fitter',
    'Forest Range Officer', 'Forest Beat Officer',
    'Inspector of Posts', 'Junior Accountant',
    'Agniveer (General Duty)', 'Agniveer (Technical)',
]

# Qualification patterns
QUALIFICATIONS = [
    'B.Tech/B.E. in Computer Science/IT/Electronics from recognized university',
    'B.Sc. in Computer Science/IT with minimum 60% marks',
    'MCA from recognized university with minimum 55% marks',
    'M.Tech in Computer Science/Information Technology',
    'Bachelor Degree in any discipline from recognized university',
    'Graduate with minimum 60% marks from recognized university',
    '10+2 pass with Science stream from recognized board',
    'Matriculation (10th pass) from recognized board',
    'MBA/PGDM from recognized institute',
    'Ph.D. in relevant discipline',
    'B.E./B.Tech in any engineering discipline with valid GATE score',
    'Diploma in Engineering (Computer/IT/Electronics/Electrical)',
    'B.Ed. with B.Sc. in relevant subject',
    'M.Sc. in relevant subject with NET/SLET qualification',
    'MBBS from recognized medical college',
    'B.Sc. Nursing from recognized institute',
    'Post Graduate Degree in relevant subject with UGC NET',
    'B.Com/M.Com with CA/ICWA qualification',
    'Any Degree with knowledge of Computer Applications',
    'ITI in relevant trade with NCVT certificate',
    'Intermediate (10+2) with typing speed 35 WPM',
    'Degree in Engineering with 2 years experience',
]

# Age limit patterns
AGE_LIMITS = [
    '18-27 years', '18-25 years', '20-30 years', '21-30 years',
    '18-32 years', '21-32 years', '18-35 years', '21-35 years',
    '20-28 years', '25-40 years', '18-30 years', '23-35 years',
    '17.5-21 years', '19.5-25 years',
]

# Application fee patterns
FEES = [
    '₹100', '₹200', '₹250', '₹300', '₹500', '₹600', '₹750',
    '₹1000', '₹1500', '₹2000', 'No fee', 'Nil',
]

# Pay scale patterns
PAY_SCALES = [
    'Level-1: ₹18,000-56,900', 'Level-2: ₹19,900-63,200',
    'Level-3: ₹21,700-69,100', 'Level-4: ₹25,500-81,100',
    'Level-5: ₹29,200-92,300', 'Level-6: ₹35,400-1,12,400',
    'Level-7: ₹44,900-1,42,400', 'Level-8: ₹47,600-1,51,100',
    'Level-10: ₹56,100-1,77,500', 'Level-11: ₹67,700-2,08,700',
    'Level-12: ₹78,800-2,09,200', 'Level-13: ₹1,23,100-2,15,900',
    'Level-14: ₹1,44,200-2,18,200',
    '₹25,000 consolidated per month', '₹30,000 consolidated per month',
    '₹35,000-₹40,000 per month', '₹50,000-₹60,000 per month',
    'Pay Band-2: ₹9,300-34,800 + Grade Pay ₹4,200',
    'Pay Band-3: ₹15,600-39,100 + Grade Pay ₹5,400',
    '₹21,700-₹69,100 (7th CPC)', '₹44,900-₹1,42,400 (7th CPC)',
]

# Organizations with full names
ORGANIZATIONS = {
    'UPSC': 'Union Public Service Commission',
    'SSC': 'Staff Selection Commission',
    'IBPS': 'Institute of Banking Personnel Selection',
    'ISRO': 'Indian Space Research Organisation',
    'DRDO': 'Defence Research & Development Organisation',
    'CDAC': 'Centre for Development of Advanced Computing',
    'NIC': 'National Informatics Centre',
    'NIELIT': 'National Institute of Electronics & IT',
    'BEL': 'Bharat Electronics Limited',
    'ECIL': 'Electronics Corporation of India Limited',
    'HAL': 'Hindustan Aeronautics Limited',
    'NTA': 'National Testing Agency',
    'BARC': 'Bhabha Atomic Research Centre',
    'SBI': 'State Bank of India',
    'RBI': 'Reserve Bank of India',
    'NABARD': 'National Bank for Agriculture & Rural Development',
    'LIC': 'Life Insurance Corporation of India',
    'SEBI': 'Securities & Exchange Board of India',
    'RRB': 'Railway Recruitment Boards',
    'FCI': 'Food Corporation of India',
    'AAI': 'Airports Authority of India',
    'DMRC': 'Delhi Metro Rail Corporation',
    'ESIC': 'Employees State Insurance Corporation',
    'EPFO': 'Employees Provident Fund Organisation',
    'NTPC': 'National Thermal Power Corporation',
    'ONGC': 'Oil & Natural Gas Corporation',
    'IOCL': 'Indian Oil Corporation Limited',
    'GAIL': 'Gas Authority of India Limited',
    'BHEL': 'Bharat Heavy Electricals Limited',
    'SAIL': 'Steel Authority of India Limited',
    'KVS': 'Kendriya Vidyalaya Sangathan',
    'NVS': 'Navodaya Vidyalaya Samiti',
    'APPSC': 'Andhra Pradesh Public Service Commission',
    'TSPSC': 'Telangana State Public Service Commission',
    'AIIMS': 'All India Institute of Medical Sciences',
    'CSIR': 'Council of Scientific & Industrial Research',
    'STPI': 'Software Technology Parks of India',
}

# Category-wise cutoff patterns (realistic marks)
CUTOFF_CATEGORIES = ['General/UR', 'OBC', 'SC', 'ST', 'EWS', 'PH/PwBD']


# ═══════════════════════════════════════════════════════════════
# 1. URL CLASSIFICATION DATASET GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_url_classification_dataset(n_samples: int = 1500) -> List[Dict]:
    """
    Generate labeled URL classification dataset.
    
    Labels:
        0 = DIRECT_APPLY (registration/login/apply pages)
        1 = CAREER_PAGE (career listing/notification pages)
        2 = NOTIFICATION_PDF (PDF notification documents)
        3 = IGNORE (home, about, social media, irrelevant)
    """
    dataset = []

    # ── Class 0: DIRECT_APPLY URLs ──
    apply_patterns = [
        ('https://upsconline.nic.in/ora/candidate/registration.php', 'New Registration ORA UPSC'),
        ('https://upsconline.nic.in/ora/candidate/login.php', 'UPSC ORA Login Apply Online'),
        ('https://ssc.gov.in/login', 'SSC Login and Apply Portal'),
        ('https://ibpsonline.ibps.in/crp-po-nov26/registration.php', 'IBPS PO Apply Online Registration'),
        ('https://ibpsonline.ibps.in/crp-clerk-nov26/registration.php', 'IBPS Clerk Apply Online Registration'),
        ('https://ibpsonline.ibps.in/crp-so-nov26/registration.php', 'IBPS SO Apply Online Registration'),
        ('https://apply.rrbcdg.gov.in/', 'RRB Online Application Registration'),
        ('https://recruitment.cdac.in/register', 'CDAC Project Engineer Apply Online'),
        ('https://apply.hal-india.co.in/careers', 'HAL Online Application Portal'),
        ('https://careers.ecil.co.in/login.php', 'ECIL GET Registration Login'),
        ('https://www.joinindiannavy.gov.in/en/account/login', 'Indian Navy Candidate Login Apply'),
        ('https://register-delhi.nielit.gov.in/', 'NIELIT Online Registration Portal'),
        ('https://exams.nta.ac.in/UGC-NET/register', 'NTA UGC NET Apply Registration'),
        ('https://exams.nta.ac.in/CTET/register', 'CTET Apply Online Registration'),
        ('https://exams.nta.ac.in/JEE-MAIN/register', 'JEE Main Online Registration'),
        ('https://online.drdo.gov.in/drdoentry/register.aspx', 'DRDO Scientist Apply Register'),
        ('https://recruitment.stpi.in/register', 'STPI Online Registration Form'),
        ('https://bank.sbi/web/careers/apply-online', 'SBI PO Apply Online Portal'),
        ('https://opportunities.rbi.org.in/Scripts/ApplyOnline.aspx', 'RBI Grade B Apply Online'),
        ('https://rac.gov.in/apply', 'RAC DRDO Scientist B Application'),
        ('https://apply.bel-india.in/', 'BEL Project Engineer Apply'),
        ('https://rectt.isro.gov.in/registration', 'ISRO Scientist Registration Apply'),
        ('https://psc.ap.gov.in/ApplyOnline', 'APPSC Group I Apply Online'),
        ('https://tspsc.gov.in/TSPSCWEB/ApplyOnline.jsp', 'TSPSC Group I Apply Online'),
        ('https://onlineapplication.esic.gov.in/', 'ESIC UDC Apply Online Registration'),
        ('https://recruit.aai.aero/apply', 'AAI JE Online Application'),
        ('https://dfrccil.indianrailways.gov.in/register', 'Railway JE Apply Online'),
        ('https://application.fci.gov.in/register', 'FCI Manager Apply Registration'),
        ('https://career.ntpc.co.in/register', 'NTPC ET Apply Registration Portal'),
        ('https://login.nabard.org/apply', 'NABARD Grade A Apply Online'),
        ('https://applyonline.licindia.in/register', 'LIC AAO Apply Online Registration'),
        ('https://examinationservices.nic.in/registration', 'UPSC ESE Apply Registration'),
        ('https://onlineexam.sebi.gov.in/register', 'SEBI Grade A Apply Online'),
        ('https://coalindia.in/career/apply', 'Coal India MT Apply Online'),
        ('https://sailcareers.com/apply', 'SAIL MT Apply Registration'),
        ('https://powergridjobs.co.in/register', 'PowerGrid ET Apply Online'),
        ('https://onlineapply.iocl.com/register', 'IOCL Engineer Apply Registration'),
        ('https://ongcjobs.co.in/register', 'ONGC GT Apply Online Portal'),
        ('https://gailonline.com/careers/apply', 'GAIL ET Apply Online Registration'),
        ('https://hpclcareers.in/register', 'HPCL Officer Apply Registration'),
        ('https://bpclcareers.co.in/register', 'BPCL MT Apply Online Portal'),
        ('https://kvsangathan.nic.in/apply', 'KVS PGT TGT Apply Online'),
        ('https://navodaya.gov.in/apply', 'NVS Teacher Apply Online Registration'),
        ('https://cris.org.in/apply/register', 'CRIS Developer Apply Online'),
        ('https://appost.in/apply', 'India Post GDS Apply Registration'),
    ]

    for url, anchor in apply_patterns:
        dataset.append({'url': url, 'anchor_text': anchor, 'label': 0, 'label_name': 'DIRECT_APPLY'})

    # Generate more DIRECT_APPLY variations
    apply_url_parts = ['apply', 'register', 'registration', 'login', 'signup', 'sign-up',
                       'newreg', 'new-reg', 'applyonline', 'online-apply', 'candidate/registration',
                       'account/login', 'ora/candidate']
    for _ in range(int(n_samples * 0.20)):
        domain = random.choice(GOV_DOMAINS)
        path_part = random.choice(apply_url_parts)
        ext = random.choice(['.php', '.aspx', '.jsp', '', '/'])
        url = f'https://{domain}/{path_part}{ext}'
        anchor_words = random.choice([
            'Apply Online', 'Register Now', 'New Registration', 'Login to Apply',
            'Online Application Form', 'Click Here to Apply', 'Submit Application',
            f'{random.choice(list(ORGANIZATIONS.keys()))} Apply Online Registration',
            f'Apply for {random.choice(POST_NAMES)}',
            f'{random.choice(EXAM_NAMES[:20])} - Apply Online',
        ])
        dataset.append({'url': url, 'anchor_text': anchor_words, 'label': 0, 'label_name': 'DIRECT_APPLY'})

    # ── Class 1: CAREER_PAGE URLs ──
    career_patterns = [
        ('https://upsc.gov.in/recruitment/active-advertisements', 'Active Advertisements UPSC Recruitment'),
        ('https://ssc.gov.in/notice-board', 'SSC Notice Board Latest Notifications'),
        ('https://www.isro.gov.in/Careers.html', 'ISRO Careers Current Openings'),
        ('https://www.cdac.in/index.aspx?id=careers', 'CDAC Careers Current Vacancies'),
        ('https://nic.in/careers/', 'NIC Careers Government IT Jobs'),
        ('https://www.nielit.gov.in/content/recruitment', 'NIELIT Recruitment Notifications'),
        ('https://bel-india.in/ContentPage.aspx?MId=17&CId=37', 'BEL Recruitment Careers Page'),
        ('https://ecil.co.in/jobs/', 'ECIL Jobs Current Openings'),
        ('https://hal-india.co.in/Career%20with%20HAL/M__57', 'Career with HAL Recruitment'),
        ('https://www.ibps.in/', 'IBPS Recruitment CRP Notifications'),
        ('https://rac.gov.in/', 'RAC DRDO Scientist Recruitment'),
        ('https://nta.ac.in/', 'NTA Examination Notifications'),
        ('https://bank.sbi/web/careers/current-openings', 'SBI Current Openings Careers'),
        ('https://opportunities.rbi.org.in/Scripts/Vacancies.aspx', 'RBI Vacancies Current'),
        ('https://nabard.org/career-notices.aspx', 'NABARD Career Notices'),
        ('https://licindia.in/careers', 'LIC Careers Recruitment'),
        ('https://ntpc.co.in/en/career', 'NTPC Career Opportunities'),
        ('https://ongcindia.com/web/ongcrecruit/careers', 'ONGC Recruitment Careers'),
        ('https://iocl.com/working-with-iocl', 'IOCL Working with IOCL Careers'),
        ('https://psc.ap.gov.in/Recruitment', 'APPSC Recruitment Notifications'),
        ('https://tspsc.gov.in/TSPSCWEB/Recruitment.jsp', 'TSPSC Recruitment Notifications'),
        ('https://rrbcdg.gov.in/', 'RRB Recruitment Notifications'),
        ('https://joinindianarmy.nic.in/', 'Join Indian Army Recruitment'),
        ('https://kvsangathan.nic.in/careers', 'KVS Recruitment Teacher Vacancies'),
        ('https://navodaya.gov.in/nvs/en/Recruitment/', 'NVS Recruitment Notifications'),
        ('https://esic.gov.in/recruitment', 'ESIC Recruitment Notifications'),
        ('https://fci.gov.in/recruitment.php', 'FCI Recruitment Notifications'),
        ('https://aai.aero/en/careers', 'AAI Careers Recruitment'),
    ]

    for url, anchor in career_patterns:
        dataset.append({'url': url, 'anchor_text': anchor, 'label': 1, 'label_name': 'CAREER_PAGE'})

    # Generate more CAREER_PAGE variations
    career_url_parts = ['careers', 'recruitment', 'vacancies', 'current-openings',
                        'career', 'jobs', 'openings', 'notice-board', 'notifications',
                        'advertisements', 'positions', 'opportunities']
    for _ in range(int(n_samples * 0.20)):
        domain = random.choice(GOV_DOMAINS)
        path_part = random.choice(career_url_parts)
        url = f'https://{domain}/{path_part}'
        org = random.choice(list(ORGANIZATIONS.keys()))
        anchor_words = random.choice([
            f'{org} Recruitment', f'{org} Careers', f'{org} Current Vacancies',
            f'{org} Notification {random.randint(2024, 2026)}',
            f'Latest {org} Jobs', f'{org} Recruitment Drive {random.randint(2024, 2026)}',
            f'Walk-in Interview at {org}', f'{org} Vacancy Circular',
            f'{org} Advertisement No. {random.randint(1, 20)}/{random.randint(2024, 2026)}',
        ])
        dataset.append({'url': url, 'anchor_text': anchor_words, 'label': 1, 'label_name': 'CAREER_PAGE'})

    # ── Class 2: NOTIFICATION_PDF URLs ──
    pdf_patterns = [
        ('https://upsc.gov.in/sites/default/files/Advt-06-2026-engl.pdf', 'UPSC Advertisement No. 06/2026 PDF Download'),
        ('https://ssc.gov.in/assets/notice/SSC-CGL-2026-Notification.pdf', 'SSC CGL 2026 Notification PDF'),
        ('https://ssc.gov.in/assets/notice/SSC-CHSL-2026-Notice.pdf', 'SSC CHSL 2026 Notice PDF Download'),
        ('https://ibps.in/wp-content/uploads/CRP-PO-XIV-Notification.pdf', 'IBPS PO XIV Detailed Notification PDF'),
        ('https://www.isro.gov.in/media_isro/pdf/Recruitment/ISRO-SAC-Advt-2026.pdf', 'ISRO SAC Scientist Recruitment Notification PDF'),
        ('https://psc.ap.gov.in/Documents/notifications/GroupI-2026.pdf', 'APPSC Group I Notification 2026 PDF'),
        ('https://tspsc.gov.in/notifications/GroupI-2026.pdf', 'TSPSC Group I 2026 Notification PDF'),
        ('https://rbi.org.in/Scripts/Recruitment/Grade-B-2026.pdf', 'RBI Grade B 2026 Notification PDF'),
        ('https://bank.sbi/documents/PO-2026-notification.pdf', 'SBI PO 2026 Detailed Notification PDF'),
        ('https://ntpc.co.in/sites/default/files/ET-GATE-2026.pdf', 'NTPC ET through GATE 2026 PDF'),
        ('https://fci.gov.in/uploads/FCI-Manager-Grade-III-2026.pdf', 'FCI Manager Recruitment 2026 PDF'),
    ]

    for url, anchor in pdf_patterns:
        dataset.append({'url': url, 'anchor_text': anchor, 'label': 2, 'label_name': 'NOTIFICATION_PDF'})

    # Generate more PDF variations
    for _ in range(int(n_samples * 0.15)):
        domain = random.choice(GOV_DOMAINS)
        org = random.choice(list(ORGANIZATIONS.keys()))
        year = random.randint(2024, 2026)
        exam = random.choice(EXAM_NAMES[:30])
        filename = f'{org}-{random.choice(["Notification", "Advertisement", "Notice", "Circular", "Recruitment"])}-{year}.pdf'
        url = f'https://{domain}/documents/{filename}'
        anchor = random.choice([
            f'{exam} - Download Notification PDF',
            f'Click here to download {org} recruitment notification',
            f'{org} Official Notification PDF {year}',
            f'Detailed Advertisement for {random.choice(POST_NAMES)}',
            f'Download Notice: {exam}',
        ])
        dataset.append({'url': url, 'anchor_text': anchor, 'label': 2, 'label_name': 'NOTIFICATION_PDF'})

    # ── Class 3: IGNORE URLs ──
    ignore_patterns = [
        ('https://upsc.gov.in/', 'UPSC Home Page'),
        ('https://ssc.gov.in/', 'Staff Selection Commission Home'),
        ('https://www.isro.gov.in/', 'ISRO Indian Space Research Organisation'),
        ('https://facebook.com/upsc.gov.in', 'Follow UPSC on Facebook'),
        ('https://twitter.com/isaboratory', 'ISRO Twitter Handle'),
        ('https://youtube.com/sscofficial', 'SSC Official YouTube Channel'),
        ('https://linkedin.com/company/drdo', 'DRDO LinkedIn Page'),
        ('https://instagram.com/indianarmy', 'Indian Army Instagram'),
        ('https://upsc.gov.in/about-us', 'About UPSC Commission'),
        ('https://ssc.gov.in/contact-us', 'Contact SSC Regional Offices'),
        ('https://www.isro.gov.in/disclaimer', 'ISRO Website Disclaimer'),
        ('https://cdac.in/index.aspx?id=about', 'About CDAC Organisation'),
        ('https://nic.in/privacy-policy', 'NIC Privacy Policy'),
        ('https://bel-india.in/sitemap', 'BEL Site Map'),
        ('https://hal-india.co.in/help.aspx', 'HAL Help FAQ Section'),
        ('https://ssc.gov.in/index.html', 'SSC Main Page'),
        ('https://upsc.gov.in/tender', 'UPSC Tender Notices'),
        ('https://drdo.gov.in/rti', 'DRDO RTI Information'),
        ('https://ssc.gov.in/feedback', 'SSC Feedback Form'),
        ('https://www.isro.gov.in/gallery', 'ISRO Photo Gallery'),
        ('https://t.me/govtjobs', 'Join Telegram Channel'),
        ('https://wa.me/919876543210', 'WhatsApp Group Join Link'),
        ('https://psc.ap.gov.in/aboutUs', 'About APPSC History'),
        ('https://tspsc.gov.in/about.jsp', 'About TSPSC Commission'),
    ]

    for url, anchor in ignore_patterns:
        dataset.append({'url': url, 'anchor_text': anchor, 'label': 3, 'label_name': 'IGNORE'})

    # Generate more IGNORE variations
    ignore_paths = ['/', '/index.html', '/index.aspx', '/about', '/contact',
                    '/privacy-policy', '/disclaimer', '/sitemap', '/help', '/faq',
                    '/tender', '/rti', '/feedback', '/gallery', '/media',
                    '/annual-report', '/acts-rules', '/citizen-charter']
    for _ in range(int(n_samples * 0.20)):
        if random.random() < 0.3:
            domain = random.choice(SOCIAL_DOMAINS)
            path = f'/{random.choice(list(ORGANIZATIONS.keys())).lower()}'
        else:
            domain = random.choice(GOV_DOMAINS)
            path = random.choice(ignore_paths)
        url = f'https://{domain}{path}'
        anchor = random.choice([
            'Home Page', 'About Us', 'Contact Us', 'Privacy Policy',
            'Disclaimer', 'Site Map', 'Help & FAQ', 'Feedback',
            'Follow us on Facebook', 'Share on Twitter', 'RTI Information',
            'Tender Notices', 'Annual Report', 'Photo Gallery',
            'Acts & Rules', 'Citizen Charter', 'Important Links',
            'Subscribe to Newsletter', 'Accessibility Statement',
        ])
        dataset.append({'url': url, 'anchor_text': anchor, 'label': 3, 'label_name': 'IGNORE'})

    random.shuffle(dataset)
    return dataset


# ═══════════════════════════════════════════════════════════════
# 2. NER / FIELD EXTRACTION DATASET GENERATOR
# ═══════════════════════════════════════════════════════════════

def _random_date(start_year=2024, end_year=2027) -> Tuple[str, str]:
    """Generate a random date and its formatted string."""
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    dt = datetime(year, month, day)

    formats = [
        dt.strftime('%d/%m/%Y'),
        dt.strftime('%d-%m-%Y'),
        dt.strftime('%d.%m.%Y'),
        f"{day}{random.choice(['st', 'nd', 'rd', 'th'])} {dt.strftime('%B')} {year}",
        f"{day} {dt.strftime('%B')}, {year}",
        f"{day}-{dt.strftime('%b')}-{year}",
        dt.strftime('%d %B %Y'),
    ]

    return dt.strftime('%Y-%m-%d'), random.choice(formats)


def generate_ner_dataset(n_samples: int = 2000) -> List[Dict]:
    """
    Generate NER-labeled dataset for field extraction.
    
    Each sample is a realistic government job notification text with
    annotated entity spans for training spaCy NER.
    
    Entity types:
        VACANCY_COUNT, START_DATE, LAST_DATE, EXAM_DATE,
        QUALIFICATION, AGE_LIMIT, APPLICATION_FEE, PAY_SCALE,
        CUTOFF_MARKS, ORGANIZATION, POST_NAME, EXPERIENCE
    """
    dataset = []

    for i in range(n_samples):
        org_key = random.choice(list(ORGANIZATIONS.keys()))
        org_full = ORGANIZATIONS[org_key]
        exam = random.choice(EXAM_NAMES)
        post = random.choice(POST_NAMES)
        qualification = random.choice(QUALIFICATIONS)
        age = random.choice(AGE_LIMITS)
        fee = random.choice(FEES)
        pay = random.choice(PAY_SCALES)
        vacancies = random.choice([1, 2, 3, 5, 10, 15, 20, 25, 30, 50, 75,
                                   100, 150, 200, 250, 300, 500, 750,
                                   1000, 1500, 2000, 3000, 5000, 10000, 14000, 27000])

        _, start_date_fmt = _random_date(2026, 2026)
        _, last_date_fmt = _random_date(2026, 2027)
        _, exam_date_fmt = _random_date(2026, 2027)

        experience_years = random.choice([0, 1, 2, 3, 5])
        if experience_years == 0:
            experience = random.choice(['Freshers eligible', 'No experience required', 'Freshers can apply'])
        else:
            experience = f'{experience_years} years of experience in relevant field'

        # Generate diverse notification text patterns
        template_id = random.randint(0, 9)
        entities = []

        if template_id == 0:
            text = (
                f"{org_full} ({org_key}) has released notification for {exam}. "
                f"Total number of vacancies: {vacancies} posts for the post of {post}. "
                f"Educational Qualification: {qualification}. "
                f"Age Limit: {age} as on last date of application (relaxation for reserved categories as per govt rules). "
                f"Application Fee: {fee} for General/OBC candidates (SC/ST/PH candidates are exempted). "
                f"Pay Scale: {pay}. "
                f"Application Start Date: {start_date_fmt}. "
                f"Last Date to Apply: {last_date_fmt}. "
                f"Date of Examination: {exam_date_fmt}. "
                f"Experience: {experience}."
            )
        elif template_id == 1:
            text = (
                f"RECRUITMENT NOTIFICATION\n"
                f"Advertisement No. {random.randint(1,20)}/{random.randint(2024,2026)}\n"
                f"Organization: {org_full}\n"
                f"Name of Post: {post}\n"
                f"No. of Vacancies: {vacancies}\n"
                f"Qualification Required: {qualification}\n"
                f"Maximum Age: {age}\n"
                f"Fee: {fee}\n"
                f"Salary/Pay: {pay}\n"
                f"Opening Date: {start_date_fmt}\n"
                f"Closing Date: {last_date_fmt}\n"
                f"Exam Date: {exam_date_fmt}\n"
                f"Work Experience: {experience}"
            )
        elif template_id == 2:
            text = (
                f"The {org_key} invites online applications from eligible candidates for direct recruitment "
                f"to {vacancies} posts of {post} in {org_full}. "
                f"Candidates should possess {qualification}. "
                f"The age of the candidate should be between {age}. "
                f"Application fee is {fee}. The pay scale for the post is {pay}. "
                f"Interested candidates may apply online from {start_date_fmt} to {last_date_fmt}. "
                f"The computer based test is tentatively scheduled on {exam_date_fmt}. "
                f"Required experience: {experience}."
            )
        elif template_id == 3:
            text = (
                f"GOVERNMENT OF INDIA\n{org_full}\n"
                f"EMPLOYMENT NOTIFICATION NO. {random.randint(1,50)}/{random.randint(2024,2026)}\n\n"
                f"{org_key} proposes to fill up {vacancies} vacancies of {post} "
                f"on direct recruitment basis.\n\n"
                f"1. ELIGIBILITY CRITERIA:\n"
                f"   (a) Educational Qualification: {qualification}\n"
                f"   (b) Age Limit: {age} (Relaxation applicable as per Central Government Rules)\n"
                f"   (c) Experience: {experience}\n\n"
                f"2. PAY AND ALLOWANCES:\n"
                f"   {pay} plus DA, HRA, and other allowances as per Central Government Rules.\n\n"
                f"3. APPLICATION FEE:\n"
                f"   {fee} (SC/ST/Women/PwBD candidates exempted)\n\n"
                f"4. IMPORTANT DATES:\n"
                f"   Start Date of Online Application: {start_date_fmt}\n"
                f"   Last Date of Online Application: {last_date_fmt}\n"
                f"   Tentative Date of CBT/Examination: {exam_date_fmt}"
            )
        elif template_id == 4:
            text = (
                f"{org_key} Recruitment {random.randint(2024,2026)} - {post}\n\n"
                f"The {org_full} has announced {vacancies} vacancies.\n"
                f"Eligible candidates having {qualification} can apply.\n"
                f"Candidates age should not exceed {age}.\n"
                f"Pay: {pay}\n"
                f"Fee: {fee}\n"
                f"Apply from: {start_date_fmt}\n"
                f"Apply before: {last_date_fmt}\n"
                f"Exam: {exam_date_fmt}\n"
                f"Experience required: {experience}"
            )
        elif template_id == 5:
            vacancy_str = f"{vacancies:,}" if vacancies >= 1000 else str(vacancies)
            text = (
                f"Applications are invited for {vacancy_str} positions of {post} in "
                f"{org_full} ({org_key}). "
                f"Essential qualification is {qualification}. "
                f"Upper age limit is {age} as on closing date. "
                f"Selection will be through written examination. "
                f"Examination fee: {fee}. "
                f"Remuneration: {pay}. "
                f"Online registration opens: {start_date_fmt}. "
                f"Last date for submission: {last_date_fmt}. "
                f"Written test date: {exam_date_fmt}. "
                f"Desired experience: {experience}."
            )
        elif template_id == 6:
            text = (
                f"WALK-IN INTERVIEW / RECRUITMENT DRIVE\n"
                f"{org_full} ({org_key})\n\n"
                f"Post: {post}\n"
                f"Number of Posts: {vacancies} nos.\n"
                f"Qualification: {qualification}\n"
                f"Age: Not exceeding {age}\n"
                f"Consolidated Pay: {pay}\n"
                f"No application fee required.\n"
                f"Registration Date: {start_date_fmt}\n"
                f"Walk-in Date: {last_date_fmt}\n"
                f"Experience: {experience}"
            )
        elif template_id == 7:
            # AP/TS PSC style notification
            state = random.choice(['Andhra Pradesh', 'Telangana'])
            state_psc = 'APPSC' if state == 'Andhra Pradesh' else 'TSPSC'
            text = (
                f"{state} PUBLIC SERVICE COMMISSION\n"
                f"NOTIFICATION NO. {random.randint(1,30)}/{random.randint(2024,2026)}\n\n"
                f"The {state} Public Service Commission ({state_psc}) invites applications "
                f"for recruitment to the post of {post}.\n\n"
                f"Total Vacancies: {vacancies} posts\n"
                f"Educational Qualification: {qualification}\n"
                f"Age: {age} as on 01/07/{random.randint(2024,2026)}\n"
                f"Fee: {fee}\n"
                f"Pay Scale: {pay}\n"
                f"Registration Start: {start_date_fmt}\n"
                f"Last Date to Apply: {last_date_fmt}\n"
                f"Preliminary Exam Date: {exam_date_fmt}\n"
                f"Experience: {experience}\n"
                f"Selection: Prelims + Mains + Interview"
            )
            org_key = state_psc
            org_full = f'{state} Public Service Commission'
        elif template_id == 8:
            text = (
                f"Notification: {exam}\n"
                f"Issued by: {org_full}\n"
                f"Total posts to be filled: {vacancies}\n"
                f"Post name: {post}\n"
                f"Required qualification: {qualification}\n"
                f"Age criteria: {age}\n"
                f"Exam fee: {fee}\n"
                f"Pay after selection: {pay}\n"
                f"Important dates - \n"
                f"  Apply from: {start_date_fmt}\n"
                f"  Apply till: {last_date_fmt}\n"
                f"  Exam on: {exam_date_fmt}\n"
                f"Experience criteria: {experience}"
            )
        else:  # template_id == 9
            # Banking style
            text = (
                f"{org_full}\n"
                f"RECRUITMENT OF {post.upper()} - {random.randint(2024,2026)}\n\n"
                f"{org_key} invites applications from eligible Indian Citizens for appointment of "
                f"{post} in various branches/offices across India.\n\n"
                f"Vacancies: {vacancies} (including backlog)\n"
                f"Category-wise: UR-{int(vacancies*0.4)}, OBC-{int(vacancies*0.27)}, "
                f"SC-{int(vacancies*0.15)}, ST-{int(vacancies*0.08)}, EWS-{int(vacancies*0.1)}\n\n"
                f"Eligibility: {qualification}\n"
                f"Age on cutoff date: {age}\n"
                f"Fee: {fee} + GST for General/OBC, Nil for SC/ST/PwBD\n"
                f"CTC: {pay} approximately\n"
                f"Online application: {start_date_fmt} to {last_date_fmt}\n"
                f"Online exam: {exam_date_fmt}\n"
                f"Experience: {experience}"
            )

        # Create entity annotations (character offsets)
        entities = []

        # Find entity spans in the generated text
        _add_entity_if_found(text, str(vacancies), 'VACANCY_COUNT', entities)
        if vacancies >= 1000:
            _add_entity_if_found(text, f"{vacancies:,}", 'VACANCY_COUNT', entities)
        _add_entity_if_found(text, start_date_fmt, 'START_DATE', entities)
        _add_entity_if_found(text, last_date_fmt, 'LAST_DATE', entities)
        _add_entity_if_found(text, exam_date_fmt, 'EXAM_DATE', entities)
        _add_entity_if_found(text, qualification, 'QUALIFICATION', entities)
        _add_entity_if_found(text, age, 'AGE_LIMIT', entities)
        _add_entity_if_found(text, fee, 'APPLICATION_FEE', entities)
        _add_entity_if_found(text, pay, 'PAY_SCALE', entities)
        _add_entity_if_found(text, org_key, 'ORGANIZATION', entities)
        _add_entity_if_found(text, post, 'POST_NAME', entities)
        _add_entity_if_found(text, experience, 'EXPERIENCE', entities)

        # Remove overlapping entities (keep the one with the longer span)
        entities = _remove_overlapping_entities(entities)

        dataset.append({
            'text': text,
            'entities': entities,
            'metadata': {
                'org': org_key,
                'org_full': org_full,
                'exam': exam,
                'vacancies': vacancies,
                'template_id': template_id,
            }
        })

    return dataset


def _add_entity_if_found(text: str, value: str, label: str, entities: list):
    """Find entity value in text and add to entities list with char offsets."""
    if not value:
        return
    value_str = str(value)
    # Escape regex special chars for literal search
    escaped = re.escape(value_str)
    match = re.search(escaped, text)
    if match:
        entities.append({
            'start': match.start(),
            'end': match.end(),
            'label': label,
            'text': value_str,
        })


def _remove_overlapping_entities(entities: List[Dict]) -> List[Dict]:
    """Remove overlapping entities, keeping the longer one."""
    if not entities:
        return []
    # Sort by start position, then by length (descending)
    sorted_ents = sorted(entities, key=lambda e: (e['start'], -(e['end'] - e['start'])))
    result = [sorted_ents[0]]
    for ent in sorted_ents[1:]:
        last = result[-1]
        if ent['start'] >= last['end']:
            result.append(ent)
        elif (ent['end'] - ent['start']) > (last['end'] - last['start']):
            result[-1] = ent
    return result


# ═══════════════════════════════════════════════════════════════
# 3. CUTOFF DATASET GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_cutoff_dataset(n_samples: int = 500) -> List[Dict]:
    """
    Generate cutoff marks dataset for training and reference.
    Based on real cutoff patterns from SSC, UPSC, IBPS, RRB, State PSCs.
    """
    dataset = []

    cutoff_configs = [
        # SSC CGL
        {'exam': 'SSC CGL', 'org': 'SSC', 'tiers': ['Tier-I', 'Tier-II', 'Final'],
         'total_marks': [200, 400, 700],
         'gen_range': [(130, 170), (280, 360), (500, 620)],
         'obc_range': [(120, 155), (260, 330), (470, 580)],
         'sc_range': [(100, 135), (220, 290), (400, 510)],
         'st_range': [(85, 125), (190, 260), (360, 470)]},
        # SSC CHSL
        {'exam': 'SSC CHSL', 'org': 'SSC', 'tiers': ['Tier-I', 'Final'],
         'total_marks': [200, 300],
         'gen_range': [(140, 180), (200, 260)],
         'obc_range': [(130, 165), (180, 240)],
         'sc_range': [(110, 145), (150, 210)],
         'st_range': [(95, 130), (130, 190)]},
        # UPSC CSE
        {'exam': 'UPSC CSE', 'org': 'UPSC', 'tiers': ['Prelims', 'Mains', 'Final'],
         'total_marks': [200, 1750, 2025],
         'gen_range': [(90, 110), (750, 850), (900, 1050)],
         'obc_range': [(85, 105), (720, 820), (870, 1020)],
         'sc_range': [(75, 95), (680, 770), (820, 960)],
         'st_range': [(70, 90), (650, 740), (780, 920)]},
        # IBPS PO
        {'exam': 'IBPS PO', 'org': 'IBPS', 'tiers': ['Prelims', 'Mains'],
         'total_marks': [100, 225],
         'gen_range': [(55, 75), (100, 140)],
         'obc_range': [(50, 70), (90, 130)],
         'sc_range': [(40, 60), (75, 115)],
         'st_range': [(35, 55), (65, 105)]},
        # SBI PO
        {'exam': 'SBI PO', 'org': 'SBI', 'tiers': ['Prelims', 'Mains'],
         'total_marks': [100, 225],
         'gen_range': [(60, 82), (105, 145)],
         'obc_range': [(55, 77), (95, 135)],
         'sc_range': [(45, 65), (80, 120)],
         'st_range': [(40, 60), (70, 110)]},
        # RBI Grade B
        {'exam': 'RBI Grade B', 'org': 'RBI', 'tiers': ['Phase-I', 'Phase-II'],
         'total_marks': [200, 300],
         'gen_range': [(100, 140), (150, 210)],
         'obc_range': [(90, 130), (140, 195)],
         'sc_range': [(80, 115), (120, 175)],
         'st_range': [(70, 105), (110, 160)]},
        # RRB NTPC
        {'exam': 'RRB NTPC', 'org': 'RRB', 'tiers': ['CBT-1', 'CBT-2'],
         'total_marks': [100, 120],
         'gen_range': [(60, 80), (75, 100)],
         'obc_range': [(55, 75), (68, 92)],
         'sc_range': [(45, 65), (55, 80)],
         'st_range': [(38, 58), (48, 72)]},
        # APPSC Group I
        {'exam': 'APPSC Group I', 'org': 'APPSC', 'tiers': ['Prelims', 'Mains', 'Final'],
         'total_marks': [150, 900, 1050],
         'gen_range': [(75, 100), (450, 580), (580, 720)],
         'obc_range': [(70, 95), (430, 560), (550, 690)],
         'sc_range': [(60, 85), (380, 510), (490, 630)],
         'st_range': [(55, 80), (350, 480), (450, 590)]},
        # TSPSC Group I
        {'exam': 'TSPSC Group I', 'org': 'TSPSC', 'tiers': ['Prelims', 'Mains', 'Final'],
         'total_marks': [150, 900, 1050],
         'gen_range': [(72, 98), (440, 570), (570, 710)],
         'obc_range': [(68, 93), (420, 550), (540, 680)],
         'sc_range': [(58, 83), (370, 500), (480, 620)],
         'st_range': [(53, 78), (340, 470), (440, 580)]},
    ]

    for _ in range(n_samples):
        config = random.choice(cutoff_configs)
        year = random.randint(2020, 2026)
        tier_idx = random.randint(0, len(config['tiers']) - 1)
        tier = config['tiers'][tier_idx]
        total = config['total_marks'][tier_idx]

        gen_marks = round(random.uniform(*config['gen_range'][tier_idx]), 2)
        obc_marks = round(random.uniform(*config['obc_range'][tier_idx]), 2)
        sc_marks = round(random.uniform(*config['sc_range'][tier_idx]), 2)
        st_marks = round(random.uniform(*config['st_range'][tier_idx]), 2)
        ews_marks = round(gen_marks - random.uniform(2, 8), 2)

        dataset.append({
            'exam_name': config['exam'],
            'organization': config['org'],
            'year': year,
            'tier': tier,
            'total_marks': total,
            'cutoffs': {
                'General/UR': gen_marks,
                'OBC': obc_marks,
                'SC': sc_marks,
                'ST': st_marks,
                'EWS': ews_marks,
            },
            # Generate cutoff text for NER training
            'text': _generate_cutoff_text(config['exam'], year, tier, total,
                                          gen_marks, obc_marks, sc_marks, st_marks, ews_marks),
        })

    return dataset


def _generate_cutoff_text(exam, year, tier, total, gen, obc, sc, st, ews):
    """Generate natural language cutoff text for NER training."""
    templates = [
        f"{exam} {year} {tier} Cutoff Marks (Out of {total}):\n"
        f"General: {gen}\nOBC: {obc}\nSC: {sc}\nST: {st}\nEWS: {ews}",

        f"The cutoff for {exam} {tier} ({year}) has been declared. "
        f"General category cutoff is {gen}/{total}, OBC cutoff is {obc}/{total}, "
        f"SC cutoff is {sc}/{total}, ST cutoff is {st}/{total}.",

        f"{exam} {year}\n{tier} Qualifying Marks:\n"
        f"UR: {gen} | OBC: {obc} | SC: {sc} | ST: {st} | EWS: {ews}\n"
        f"Total Marks: {total}",

        f"Category-wise {tier} cut-off marks for {exam} {year}:\n"
        f"Unreserved: {gen}, Other Backward Classes: {obc}, "
        f"Scheduled Caste: {sc}, Scheduled Tribe: {st}. "
        f"Maximum marks: {total}.",
    ]
    return random.choice(templates)


# ═══════════════════════════════════════════════════════════════
# 4. CONFIDENCE SCORING TRAINING DATA
# ═══════════════════════════════════════════════════════════════

def generate_confidence_dataset(n_samples: int = 1000) -> List[Dict]:
    """
    Generate training data for the confidence scoring model.
    
    Features are extraction quality indicators; labels are 1 (reliable) or 0 (unreliable).
    """
    dataset = []

    for _ in range(n_samples):
        is_good = random.random() < 0.7  # 70% good extractions

        if is_good:
            # Good extraction
            vacancies = random.randint(1, 50000)
            start_year = random.randint(2024, 2026)
            start_month = random.randint(1, 12)
            start_day = random.randint(1, 28)
            last_day = start_day + random.randint(15, 90)

            features = {
                'has_vacancy': 1,
                'vacancy_value': vacancies,
                'vacancy_in_range': 1,  # 0 < v < 100000
                'has_start_date': random.choice([0, 1]),
                'has_last_date': 1,
                'has_exam_date': random.choice([0, 1]),
                'dates_chronological': 1,  # start < last < exam
                'has_qualification': 1,
                'qualification_length': random.randint(20, 150),
                'has_age_limit': random.choice([0, 1]),
                'has_fee': random.choice([0, 1]),
                'has_pay_scale': random.choice([0, 1]),
                'has_org': 1,
                'org_is_known': 1,
                'has_post_name': 1,
                'post_name_length': random.randint(10, 100),
                'fields_extracted': random.randint(7, 12),
                'total_fields': 12,
                'extraction_completeness': random.uniform(0.6, 1.0),
                'text_length': random.randint(200, 5000),
                'confidence_score': random.uniform(0.7, 1.0),
            }
            label = 1
        else:
            # Bad extraction — various failure modes
            failure_mode = random.choice(['no_vacancy', 'bad_dates', 'missing_fields',
                                          'garbage_text', 'wrong_values'])

            features = {
                'has_vacancy': 1 if failure_mode != 'no_vacancy' else 0,
                'vacancy_value': random.choice([0, -1, 999999]) if failure_mode == 'wrong_values' else random.randint(1, 100),
                'vacancy_in_range': 0 if failure_mode == 'wrong_values' else 1,
                'has_start_date': random.choice([0, 1]),
                'has_last_date': 0 if failure_mode in ['bad_dates', 'missing_fields'] else 1,
                'has_exam_date': 0,
                'dates_chronological': 0 if failure_mode == 'bad_dates' else random.choice([0, 1]),
                'has_qualification': 0 if failure_mode == 'missing_fields' else 1,
                'qualification_length': random.randint(0, 10) if failure_mode == 'garbage_text' else random.randint(20, 150),
                'has_age_limit': 0,
                'has_fee': 0,
                'has_pay_scale': 0,
                'has_org': random.choice([0, 1]),
                'org_is_known': 0 if failure_mode == 'garbage_text' else random.choice([0, 1]),
                'has_post_name': 0 if failure_mode == 'missing_fields' else 1,
                'post_name_length': random.randint(0, 5) if failure_mode == 'garbage_text' else random.randint(10, 100),
                'fields_extracted': random.randint(1, 5),
                'total_fields': 12,
                'extraction_completeness': random.uniform(0.05, 0.45),
                'text_length': random.randint(10, 100) if failure_mode == 'garbage_text' else random.randint(200, 5000),
                'confidence_score': random.uniform(0.0, 0.5),
            }
            label = 0

        dataset.append({
            'features': features,
            'label': label,
            'label_name': 'reliable' if label == 1 else 'unreliable',
        })

    return dataset


# ═══════════════════════════════════════════════════════════════
# DATASET EXPORT FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def save_datasets(output_dir: str = None):
    """Generate and save all datasets to disk."""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datasets')

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("GovTechJobs AI — Training Dataset Generator")
    print("=" * 60)

    # 1. URL Classification Dataset
    print("\n[1/4] Generating URL Classification Dataset...")
    url_data = generate_url_classification_dataset(n_samples=1500)
    url_path = os.path.join(output_dir, 'url_classification.json')
    with open(url_path, 'w', encoding='utf-8') as f:
        json.dump(url_data, f, indent=2, ensure_ascii=False)
    print(f"  ✅ {len(url_data)} samples saved to {url_path}")
    
    # Export URL Classification as CSV
    url_csv_path = os.path.join(output_dir, 'url_classification.csv')
    with open(url_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'anchor_text', 'label', 'label_name'])
        for row in url_data:
            writer.writerow([row['url'], row['anchor_text'], row['label'], row['label_name']])
    print(f"  ✅ CSV format saved to {url_csv_path}")
    _print_class_distribution(url_data, 'label_name')

    # 2. NER / Field Extraction Dataset
    print("\n[2/4] Generating NER Field Extraction Dataset...")
    ner_data = generate_ner_dataset(n_samples=2000)
    ner_path = os.path.join(output_dir, 'ner_field_extraction.json')
    with open(ner_path, 'w', encoding='utf-8') as f:
        json.dump(ner_data, f, indent=2, ensure_ascii=False)
    print(f"  ✅ {len(ner_data)} samples saved to {ner_path}")

    # Export flattened NER as CSV (for Excel viewing)
    ner_csv_path = os.path.join(output_dir, 'ner_field_extraction.csv')
    with open(ner_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['text', 'entities_extracted', 'organization', 'exam_name', 'vacancies'])
        for row in ner_data:
            meta = row.get('metadata', {})
            # Format entities to a friendly string
            ent_list = [f"{e['label']}:{e['text']}" for e in row.get('entities', [])]
            writer.writerow([
                row['text'],
                "; ".join(ent_list),
                meta.get('org', ''),
                meta.get('exam', ''),
                meta.get('vacancies', '')
            ])
    print(f"  ✅ CSV format saved to {ner_csv_path}")

    # Also export in spaCy format
    spacy_path = os.path.join(output_dir, 'ner_spacy_format.json')
    spacy_data = _convert_to_spacy_format(ner_data)
    with open(spacy_path, 'w', encoding='utf-8') as f:
        json.dump(spacy_data, f, indent=2, ensure_ascii=False)
    print(f"  ✅ spaCy format saved to {spacy_path}")

    # 3. Cutoff Dataset
    print("\n[3/4] Generating Cutoff Marks Dataset...")
    cutoff_data = generate_cutoff_dataset(n_samples=500)
    cutoff_path = os.path.join(output_dir, 'cutoff_marks.json')
    with open(cutoff_path, 'w', encoding='utf-8') as f:
        json.dump(cutoff_data, f, indent=2, ensure_ascii=False)
    print(f"  ✅ {len(cutoff_data)} samples saved to {cutoff_path}")

    # Export Cutoff marks as CSV
    cutoff_csv_path = os.path.join(output_dir, 'cutoff_marks.csv')
    with open(cutoff_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['exam_name', 'organization', 'year', 'tier', 'total_marks', 'General/UR', 'OBC', 'SC', 'ST', 'EWS', 'text'])
        for row in cutoff_data:
            cuts = row.get('cutoffs', {})
            writer.writerow([
                row['exam_name'],
                row['organization'],
                row['year'],
                row['tier'],
                row['total_marks'],
                cuts.get('General/UR', ''),
                cuts.get('OBC', ''),
                cuts.get('SC', ''),
                cuts.get('ST', ''),
                cuts.get('EWS', ''),
                row['text']
            ])
    print(f"  ✅ CSV format saved to {cutoff_csv_path}")

    # 4. Confidence Scoring Dataset
    print("\n[4/4] Generating Confidence Scoring Dataset...")
    conf_data = generate_confidence_dataset(n_samples=1000)
    conf_path = os.path.join(output_dir, 'confidence_scoring.json')
    with open(conf_path, 'w', encoding='utf-8') as f:
        json.dump(conf_data, f, indent=2, ensure_ascii=False)
    print(f"  ✅ {len(conf_data)} samples saved to {conf_path}")

    # Export Confidence Scoring as CSV
    conf_csv_path = os.path.join(output_dir, 'confidence_scoring.csv')
    with open(conf_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # Headers from features keys
        headers = list(conf_data[0]['features'].keys()) + ['label', 'label_name']
        writer.writerow(headers)
        for row in conf_data:
            vals = list(row['features'].values()) + [row['label'], row['label_name']]
            writer.writerow(vals)
    print(f"  ✅ CSV format saved to {conf_csv_path}")
    _print_class_distribution(conf_data, 'label_name')

    # Summary
    total = len(url_data) + len(ner_data) + len(cutoff_data) + len(conf_data)
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {total} training samples generated across 4 datasets")
    print(f"Output directory: {output_dir}")
    print(f"{'=' * 60}")

    return {
        'url_classification': url_path,
        'ner_field_extraction': ner_path,
        'ner_spacy_format': spacy_path,
        'cutoff_marks': cutoff_path,
        'confidence_scoring': conf_path,
    }


def _convert_to_spacy_format(ner_data: List[Dict]) -> List:
    """Convert NER dataset to spaCy training format: (text, {"entities": [(start, end, label)]})"""
    spacy_data = []
    for sample in ner_data:
        entities = [(e['start'], e['end'], e['label']) for e in sample['entities']]
        spacy_data.append({
            'text': sample['text'],
            'entities': entities,
        })
    return spacy_data


def _print_class_distribution(data: List[Dict], label_key: str):
    """Print class distribution of a dataset."""
    counts = {}
    for d in data:
        label = d.get(label_key, 'unknown')
        counts[label] = counts.get(label, 0) + 1
    for label, count in sorted(counts.items()):
        pct = count / len(data) * 100
        print(f"    {label}: {count} ({pct:.1f}%)")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    save_datasets()
