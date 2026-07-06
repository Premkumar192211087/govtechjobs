-- GovTechJobs Database Schema (PostgreSQL)
-- Run this on your Supabase instance to set up tables

-- Jobs/Notifications
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    exam_name VARCHAR(255) NOT NULL,
    organization VARCHAR(100) NOT NULL,
    organization_full VARCHAR(255),
    post_name VARCHAR(255),
    job_domain VARCHAR(50),
    vacancies INTEGER,
    qualification VARCHAR(255),
    experience_required VARCHAR(100),
    age_limit VARCHAR(100),
    application_fee TEXT,
    pay_scale VARCHAR(100),
    location VARCHAR(255),

    notification_date DATE,
    application_start_date DATE,
    application_last_date DATE,
    exam_date DATE,
    status VARCHAR(50) DEFAULT 'active',

    apply_link TEXT,
    portal_url TEXT,
    notification_pdf_url TEXT,
    portal_instructions TEXT,
    source_url TEXT,

    total_marks INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(exam_name, organization, notification_date)
);

-- Cutoff Marks
CREATE TABLE IF NOT EXISTS cutoffs (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    tier VARCHAR(50),
    year INTEGER,
    category VARCHAR(20),
    qualifying_marks DECIMAL(6,2),
    merit_marks DECIMAL(6,2),
    total_marks INTEGER
);

-- Portal Directory
CREATE TABLE IF NOT EXISTS portals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(50),
    url VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    exams_covered TEXT,
    it_roles_available TEXT,
    last_scraped TIMESTAMP,
    scrape_status VARCHAR(20) DEFAULT 'pending',
    is_active BOOLEAN DEFAULT true
);

-- Scrape Logs
CREATE TABLE IF NOT EXISTS scrape_logs (
    id SERIAL PRIMARY KEY,
    portal VARCHAR(100),
    status VARCHAR(20),
    jobs_found INTEGER DEFAULT 0,
    new_jobs INTEGER DEFAULT 0,
    error_message TEXT,
    duration_ms INTEGER,
    scraped_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_domain ON jobs(job_domain);
CREATE INDEX IF NOT EXISTS idx_jobs_org ON jobs(organization);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_dates ON jobs(application_last_date);
CREATE INDEX IF NOT EXISTS idx_cutoffs_job ON cutoffs(job_id);
