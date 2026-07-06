/**
 * Database layer with in-memory fallback for local development.
 * When DATABASE_URL is configured, uses PostgreSQL via node-postgres.
 * Otherwise, uses an in-memory store seeded with demo data.
 */

const logger = require('../utils/logger');

let pool = null;
let useInMemory = true;

// In-memory data store
let memoryStore = {
  jobs: [],
  cutoffs: [],
  portals: [],
  scrapeLogs: []
};

/**
 * Initialize database connection
 */
async function initDatabase() {
  if (process.env.DATABASE_URL) {
    try {
      const { Pool } = require('pg');
      pool = new Pool({ connectionString: process.env.DATABASE_URL, ssl: { rejectUnauthorized: false } });
      await pool.query('SELECT 1');
      useInMemory = false;
      logger.info('Database', 'Connected to PostgreSQL');
      return;
    } catch (err) {
      logger.warn('Database', 'PostgreSQL unavailable, falling back to in-memory', { error: err.message });
    }
  }

  logger.info('Database', 'Using in-memory database with seed data');
  useInMemory = true;
  seedData();
}

/**
 * Seed the in-memory store with realistic demo data
 */
function seedData() {
  const now = new Date();
  const futureDate = (days) => {
    const d = new Date(now);
    d.setDate(d.getDate() + days);
    return d.toISOString().split('T')[0];
  };
  const pastDate = (days) => {
    const d = new Date(now);
    d.setDate(d.getDate() - days);
    return d.toISOString().split('T')[0];
  };

  memoryStore.jobs = [
    {
      id: 1,
      exam_name: 'DRDO SET 2026',
      organization: 'DRDO',
      organization_full: 'Defence Research & Development Organisation',
      post_name: 'Scientist \'B\' (Computer Science)',
      job_domain: 'software_it',
      vacancies: 47,
      qualification: 'B.Tech/BE (CS/IT)',
      experience_required: 'Fresher',
      age_limit: '28 years (relaxation as per rules)',
      application_fee: '₹100 (Free for SC/ST/PwD/Women)',
      pay_scale: '7th CPC Level 10 (₹56,100 - ₹1,77,500)',
      location: 'All India',
      notification_date: pastDate(10),
      application_start_date: pastDate(7),
      application_last_date: futureDate(23),
      exam_date: futureDate(60),
      status: 'active',
      apply_link: 'https://rac.gov.in/apply',
      portal_url: 'https://drdo.gov.in',
      notification_pdf_url: 'https://rac.gov.in/notifications/set2026.pdf',
      portal_instructions: 'Apply through RAC website. Create account → Fill application → Upload documents → Pay fee → Submit.',
      source_url: 'https://rac.gov.in',
      total_marks: 300,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 2,
      exam_name: 'ISRO ICRB 2026',
      organization: 'ISRO',
      organization_full: 'Indian Space Research Organisation',
      post_name: 'Scientist/Engineer \'SC\' (CS)',
      job_domain: 'software_it',
      vacancies: 31,
      qualification: 'B.Tech/BE (CS/IT) with 65%+',
      experience_required: 'Fresher',
      age_limit: '30 years',
      application_fee: '₹100 (Free for Women/SC/ST/PwD)',
      pay_scale: '7th CPC Level 10 (₹56,100 - ₹1,77,500)',
      location: 'Various ISRO centres across India',
      notification_date: pastDate(15),
      application_start_date: pastDate(12),
      application_last_date: futureDate(18),
      exam_date: futureDate(75),
      status: 'active',
      apply_link: 'https://www.isro.gov.in/Careers.html',
      portal_url: 'https://www.isro.gov.in',
      notification_pdf_url: 'https://www.isro.gov.in/Careers.html',
      portal_instructions: 'Register on ISRO recruitment portal → Fill details → Upload photo & signature → Pay fee → Download admit card later.',
      source_url: 'https://isro.gov.in/careers',
      total_marks: 200,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 3,
      exam_name: 'NIC Scientist B 2026',
      organization: 'NIC',
      organization_full: 'National Informatics Centre',
      post_name: 'Scientist \'B\' (Computer Science)',
      job_domain: 'software_it',
      vacancies: 108,
      qualification: 'B.Tech/BE/MCA (CS/IT)',
      experience_required: 'Fresher',
      age_limit: '30 years',
      application_fee: '₹500 (Free for SC/ST/PwD/Women)',
      pay_scale: '7th CPC Level 10 (₹56,100 - ₹1,77,500)',
      location: 'Delhi + All India posting',
      notification_date: pastDate(5),
      application_start_date: pastDate(3),
      application_last_date: futureDate(27),
      exam_date: futureDate(90),
      status: 'active',
      apply_link: 'https://www.nic.in/careers/',
      portal_url: 'https://www.nic.in',
      notification_pdf_url: 'https://www.nic.in/careers/',
      portal_instructions: 'Visit NIC careers page → Online application → Document upload → Fee payment → Print confirmation.',
      source_url: 'https://nic.in/careers',
      total_marks: 200,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 4,
      exam_name: 'SSC CGL 2026',
      organization: 'SSC',
      organization_full: 'Staff Selection Commission',
      post_name: 'Assistant Section Officer / Inspector / Tax Asst',
      job_domain: 'non_it',
      vacancies: 14582,
      qualification: 'Any Graduate',
      experience_required: 'Fresher',
      age_limit: '20-30 years (varies by post)',
      application_fee: '₹100 (Free for Women/SC/ST/PwD)',
      pay_scale: '7th CPC Level 7-8 (₹44,900 - ₹1,42,400)',
      location: 'All India',
      notification_date: pastDate(20),
      application_start_date: pastDate(15),
      application_last_date: futureDate(10),
      exam_date: futureDate(45),
      status: 'active',
      apply_link: 'https://ssc.gov.in/portal/apply',
      portal_url: 'https://ssc.gov.in',
      notification_pdf_url: 'https://ssc.gov.in/noticeboardportlet/view-notices',
      portal_instructions: 'SSC one-time registration → Login → Fill application → Upload photo/signature → Pay fee.',
      source_url: 'https://ssc.gov.in',
      total_marks: 200,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 5,
      exam_name: 'IBPS SO IT Officer 2026',
      organization: 'IBPS',
      organization_full: 'Institute of Banking Personnel Selection',
      post_name: 'IT Officer (Scale I)',
      job_domain: 'software_it',
      vacancies: 250,
      qualification: 'B.Tech/BE (CS/IT/ECE) or MCA',
      experience_required: 'Fresher',
      age_limit: '20-30 years',
      application_fee: '₹175 (₹850 for General/OBC)',
      pay_scale: 'Bank Scale I (₹36,000 - ₹63,840 + DA)',
      location: 'All India (Public Sector Banks)',
      notification_date: pastDate(8),
      application_start_date: pastDate(5),
      application_last_date: futureDate(22),
      exam_date: futureDate(55),
      status: 'active',
      apply_link: 'https://www.ibps.in/',
      portal_url: 'https://www.ibps.in',
      notification_pdf_url: 'https://www.ibps.in/',
      portal_instructions: 'Register on IBPS → Fill application form → Upload documents → Pay fee → Take printout.',
      source_url: 'https://ibps.in',
      total_marks: 200,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 6,
      exam_name: 'C-DAC Project Engineer 2026',
      organization: 'CDAC',
      organization_full: 'Centre for Development of Advanced Computing',
      post_name: 'Project Engineer (Software Development)',
      job_domain: 'software_it',
      vacancies: 85,
      qualification: 'B.Tech/BE/MCA (CS/IT)',
      experience_required: '0-2 years',
      age_limit: '30 years',
      application_fee: '₹500',
      pay_scale: '₹40,000 - ₹60,000 per month (consolidated)',
      location: 'Pune, Noida, Hyderabad, Bengaluru',
      notification_date: pastDate(3),
      application_start_date: pastDate(1),
      application_last_date: futureDate(29),
      exam_date: null,
      status: 'active',
      apply_link: 'https://cdac.in/careers/apply',
      portal_url: 'https://cdac.in',
      notification_pdf_url: 'https://cdac.in/careers/pe2026.pdf',
      portal_instructions: 'Apply on C-DAC recruitment portal → Online test → Interview.',
      source_url: 'https://cdac.in/careers',
      total_marks: null,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 7,
      exam_name: 'BEL Probationary Engineer 2026',
      organization: 'BEL',
      organization_full: 'Bharat Electronics Limited',
      post_name: 'Probationary Engineer (Electronics/CS)',
      job_domain: 'software_it',
      vacancies: 150,
      qualification: 'B.Tech/BE (CS/IT/ECE) with valid GATE score',
      experience_required: 'Fresher',
      age_limit: '25 years',
      application_fee: '₹500 (Free for SC/ST/PwD)',
      pay_scale: '₹40,000 - ₹1,40,000 (IDA Pattern)',
      location: 'Bengaluru, Ghaziabad, Pune, Hyderabad, Chennai',
      notification_date: pastDate(12),
      application_start_date: pastDate(10),
      application_last_date: futureDate(5),
      exam_date: null,
      status: 'active',
      apply_link: 'https://bel-india.in/careers',
      portal_url: 'https://bel-india.in',
      notification_pdf_url: 'https://bel-india.in/pe2026.pdf',
      portal_instructions: 'GATE score based shortlisting → Apply online → Interview.',
      source_url: 'https://bel-india.in',
      total_marks: null,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 8,
      exam_name: 'UPSC CSE 2026',
      organization: 'UPSC',
      organization_full: 'Union Public Service Commission',
      post_name: 'IAS / IPS / IFS / IRS and allied services',
      job_domain: 'non_it',
      vacancies: 1056,
      qualification: 'Any Graduate',
      experience_required: 'Fresher',
      age_limit: '21-32 years (relaxation for reserved)',
      application_fee: '₹100 (Free for Women/SC/ST/PwD)',
      pay_scale: '7th CPC Level 10+ (₹56,100+)',
      location: 'All India',
      notification_date: pastDate(30),
      application_start_date: pastDate(25),
      application_last_date: futureDate(3),
      exam_date: futureDate(40),
      status: 'active',
      apply_link: 'https://upsconline.nic.in',
      portal_url: 'https://upsc.gov.in',
      notification_pdf_url: 'https://upsc.gov.in/sites/default/files/CSE2026.pdf',
      portal_instructions: 'Register on UPSC ORA portal → Fill DAF → Upload documents → Pay fee.',
      source_url: 'https://upsc.gov.in',
      total_marks: 2025,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 9,
      exam_name: 'SBI IT Specialist Officer 2026',
      organization: 'SBI',
      organization_full: 'State Bank of India',
      post_name: 'IT Specialist Officer (Systems)',
      job_domain: 'software_it',
      vacancies: 72,
      qualification: 'B.Tech/BE (CS/IT) or MCA',
      experience_required: '2-5 years in IT',
      age_limit: '25-35 years',
      application_fee: '₹750 (₹125 for SC/ST/PwD)',
      pay_scale: 'MMGS-II (₹48,170 - ₹69,810 + DA)',
      location: 'Mumbai, Delhi, Bengaluru, Kolkata, Chennai',
      notification_date: pastDate(6),
      application_start_date: pastDate(4),
      application_last_date: futureDate(20),
      exam_date: futureDate(50),
      status: 'active',
      apply_link: 'https://sbi.co.in/careers/apply',
      portal_url: 'https://sbi.co.in',
      notification_pdf_url: 'https://sbi.co.in/web/careers/so2026.pdf',
      portal_instructions: 'Apply on SBI Careers portal → Online exam → Group Exercise → Interview.',
      source_url: 'https://sbi.co.in/web/careers',
      total_marks: 200,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 10,
      exam_name: 'RBI Grade B (IT) 2026',
      organization: 'RBI',
      organization_full: 'Reserve Bank of India',
      post_name: 'Officer Grade B (DSIM — IT Stream)',
      job_domain: 'software_it',
      vacancies: 38,
      qualification: 'B.Tech/BE/MCA (CS/IT) with 60%+',
      experience_required: '2-5 years',
      age_limit: '21-30 years',
      application_fee: '₹850 (₹100 for SC/ST/PwD)',
      pay_scale: '₹55,200 - ₹2,19,400 (RBI Grade B)',
      location: 'Mumbai (HQ) + All India',
      notification_date: pastDate(18),
      application_start_date: pastDate(14),
      application_last_date: futureDate(7),
      exam_date: futureDate(35),
      status: 'active',
      apply_link: 'https://opportunities.rbi.org.in',
      portal_url: 'https://rbi.org.in',
      notification_pdf_url: 'https://rbi.org.in/scripts/gradeb2026.pdf',
      portal_instructions: 'Register on RBI opportunities portal → Fill form → Upload documents → Pay fee → Phase I & II exam → Interview.',
      source_url: 'https://opportunities.rbi.org.in',
      total_marks: 300,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 11,
      exam_name: 'ECIL Graduate Engineer 2026',
      organization: 'ECIL',
      organization_full: 'Electronics Corporation of India Limited',
      post_name: 'Graduate Engineer Trainee (CS/IT/ECE)',
      job_domain: 'software_it',
      vacancies: 200,
      qualification: 'B.Tech/BE (CS/IT/ECE) with valid GATE score',
      experience_required: 'Fresher',
      age_limit: '25 years',
      application_fee: '₹500 (Free for SC/ST/PwD)',
      pay_scale: '₹30,000 - ₹1,20,000 (IDA Pattern)',
      location: 'Hyderabad + Project sites',
      notification_date: pastDate(4),
      application_start_date: pastDate(2),
      application_last_date: futureDate(26),
      exam_date: null,
      status: 'active',
      apply_link: 'https://www.ecil.co.in/careers.html',
      portal_url: 'https://www.ecil.co.in',
      notification_pdf_url: 'https://www.ecil.co.in/careers.html',
      portal_instructions: 'Apply online with GATE scorecard → Shortlisting → Interview.',
      source_url: 'https://ecil.co.in',
      total_marks: null,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 12,
      exam_name: 'NIELIT Scientist B 2026',
      organization: 'NIELIT',
      organization_full: 'National Institute of Electronics & IT',
      post_name: 'Scientist \'B\' (CS/Electronics)',
      job_domain: 'software_it',
      vacancies: 45,
      qualification: 'B.Tech/BE/MCA (CS/IT/Electronics)',
      experience_required: 'Fresher',
      age_limit: '30 years',
      application_fee: '₹500 (Free for SC/ST/PwD/Women)',
      pay_scale: '7th CPC Level 10 (₹56,100 - ₹1,77,500)',
      location: 'Delhi, Calicut, Chennai, Gorakhpur, Chandigarh',
      notification_date: pastDate(2),
      application_start_date: pastDate(1),
      application_last_date: futureDate(30),
      exam_date: futureDate(80),
      status: 'active',
      apply_link: 'https://www.nielit.gov.in/content/recruitment',
      portal_url: 'https://www.nielit.gov.in',
      notification_pdf_url: 'https://www.nielit.gov.in/content/recruitment',
      portal_instructions: 'Register → Apply online → Written exam → Interview.',
      source_url: 'https://nielit.gov.in',
      total_marks: 200,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 13,
      exam_name: 'RRB NTPC 2026',
      organization: 'RRB',
      organization_full: 'Railway Recruitment Board',
      post_name: 'Non-Technical Popular Categories (Clerk, TA, CA)',
      job_domain: 'non_it',
      vacancies: 11558,
      qualification: 'Any Graduate / 12th Pass (by post)',
      experience_required: 'Fresher',
      age_limit: '18-33 years',
      application_fee: '₹500 (₹250 for SC/ST/PwD/Women)',
      pay_scale: '7th CPC Level 5-6 (₹29,200 - ₹92,300)',
      location: 'All India (Indian Railways)',
      notification_date: pastDate(25),
      application_start_date: pastDate(20),
      application_last_date: futureDate(8),
      exam_date: futureDate(60),
      status: 'active',
      apply_link: 'https://www.rrbcdg.gov.in/',
      portal_url: 'https://www.rrbcdg.gov.in',
      notification_pdf_url: 'https://www.rrbcdg.gov.in/',
      portal_instructions: 'Register on RRB website → Fill form → Upload photo/signature → Pay fee → CBT-1 → CBT-2 → Typing test (for some posts).',
      source_url: 'https://rrbcdg.gov.in',
      total_marks: 100,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 14,
      exam_name: 'NTPC Executive Trainee (IT) 2026',
      organization: 'NTPC',
      organization_full: 'National Thermal Power Corporation',
      post_name: 'Executive Trainee (IT)',
      job_domain: 'psu',
      vacancies: 35,
      qualification: 'B.Tech/BE (CS/IT) with valid GATE score',
      experience_required: 'Fresher',
      age_limit: '27 years',
      application_fee: '₹300 (Free for SC/ST/PwD)',
      pay_scale: '₹40,000 - ₹1,40,000 (IDA, E2 Grade)',
      location: 'NTPC Plants across India',
      notification_date: pastDate(14),
      application_start_date: pastDate(10),
      application_last_date: futureDate(15),
      exam_date: null,
      status: 'active',
      apply_link: 'https://ntpc.co.in/careers/apply',
      portal_url: 'https://ntpc.co.in',
      notification_pdf_url: 'https://ntpc.co.in/et2026.pdf',
      portal_instructions: 'GATE score based → Apply online → Group Discussion → Interview.',
      source_url: 'https://ntpc.co.in/careers',
      total_marks: null,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 15,
      exam_name: 'SEBI Officer Grade A (IT) 2026',
      organization: 'SEBI',
      organization_full: 'Securities & Exchange Board of India',
      post_name: 'Officer Grade A (IT Stream)',
      job_domain: 'software_it',
      vacancies: 24,
      qualification: 'B.Tech/BE/MCA (CS/IT) with 60%+',
      experience_required: '0-2 years',
      age_limit: '30 years',
      application_fee: '₹1,000 (₹100 for SC/ST/PwD)',
      pay_scale: '₹44,500 - ₹2,17,100 (SEBI Grade A)',
      location: 'Mumbai (HQ) + Regional Offices',
      notification_date: pastDate(7),
      application_start_date: pastDate(5),
      application_last_date: futureDate(25),
      exam_date: futureDate(55),
      status: 'active',
      apply_link: 'https://sebi.gov.in/careers/apply',
      portal_url: 'https://sebi.gov.in',
      notification_pdf_url: 'https://sebi.gov.in/gradea2026.pdf',
      portal_instructions: 'Apply on SEBI website → Phase I (Online) → Phase II (Online) → Interview.',
      source_url: 'https://sebi.gov.in',
      total_marks: 250,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 16,
      exam_name: 'KVS PGT Computer Science 2026',
      organization: 'KVS',
      organization_full: 'Kendriya Vidyalaya Sangathan',
      post_name: 'Post Graduate Teacher — Computer Science',
      job_domain: 'teaching',
      vacancies: 120,
      qualification: 'M.Tech/MCA/M.Sc (CS) + B.Ed',
      experience_required: 'Fresher',
      age_limit: '40 years',
      application_fee: '₹1,000 (₹500 for SC/ST/PwD)',
      pay_scale: '7th CPC Level 8 (₹47,600 - ₹1,51,100)',
      location: 'All India (1,200+ Kendriya Vidyalayas)',
      notification_date: pastDate(9),
      application_start_date: pastDate(6),
      application_last_date: futureDate(24),
      exam_date: futureDate(65),
      status: 'active',
      apply_link: 'https://kvsangathan.nic.in/apply',
      portal_url: 'https://kvsangathan.nic.in',
      notification_pdf_url: 'https://kvsangathan.nic.in/pgt2026.pdf',
      portal_instructions: 'Register on KVS portal → Apply for PGT CS → Written test → Demo teaching → Interview.',
      source_url: 'https://kvsangathan.nic.in',
      total_marks: 200,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 17,
      exam_name: 'Power Grid ET (IT) 2026',
      organization: 'PowerGrid',
      organization_full: 'Power Grid Corporation of India',
      post_name: 'Executive Trainee (IT/CS)',
      job_domain: 'psu',
      vacancies: 28,
      qualification: 'B.Tech/BE (CS/IT) with valid GATE score',
      experience_required: 'Fresher',
      age_limit: '28 years',
      application_fee: '₹500 (Free for SC/ST/PwD)',
      pay_scale: '₹40,000 - ₹1,40,000 (IDA, E2 Grade)',
      location: 'Power Grid offices across India',
      notification_date: pastDate(11),
      application_start_date: pastDate(8),
      application_last_date: futureDate(12),
      exam_date: null,
      status: 'active',
      apply_link: 'https://www.powergrid.in/careers',
      portal_url: 'https://www.powergrid.in',
      notification_pdf_url: 'https://www.powergrid.in/careers',
      portal_instructions: 'GATE based → Apply online → Interview.',
      source_url: 'https://powergrid.in/careers',
      total_marks: null,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 18,
      exam_name: 'BSNL JTO 2026',
      organization: 'BSNL',
      organization_full: 'Bharat Sanchar Nigam Limited',
      post_name: 'Junior Telecom Officer (IT/Telecom)',
      job_domain: 'telecom',
      vacancies: 300,
      qualification: 'B.Tech/BE (CS/IT/ECE/EEE)',
      experience_required: 'Fresher',
      age_limit: '30 years',
      application_fee: '₹1,000 (₹500 for SC/ST/PwD)',
      pay_scale: '₹16,400 - ₹40,500 (IDA)',
      location: 'All India (BSNL Telecom Circles)',
      notification_date: pastDate(16),
      application_start_date: pastDate(12),
      application_last_date: futureDate(6),
      exam_date: futureDate(40),
      status: 'active',
      apply_link: 'https://bsnl.co.in/jto-apply',
      portal_url: 'https://bsnl.co.in',
      notification_pdf_url: 'https://bsnl.co.in/jto2026.pdf',
      portal_instructions: 'Apply on BSNL External JTO portal → Written Exam → Document Verification.',
      source_url: 'https://bsnl.co.in',
      total_marks: 300,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 19,
      exam_name: 'HAL Management Trainee 2026',
      organization: 'HAL',
      organization_full: 'Hindustan Aeronautics Limited',
      post_name: 'Management Trainee (CS/IT)',
      job_domain: 'software_it',
      vacancies: 42,
      qualification: 'B.Tech/BE (CS/IT) with valid GATE score + 60%',
      experience_required: 'Fresher',
      age_limit: '28 years',
      application_fee: '₹500 (Free for SC/ST/PwD)',
      pay_scale: '₹40,000 - ₹1,40,000 (IDA, E-II)',
      location: 'Bengaluru, Nasik, Lucknow, Koraput, Kanpur',
      notification_date: pastDate(13),
      application_start_date: pastDate(10),
      application_last_date: futureDate(14),
      exam_date: null,
      status: 'active',
      apply_link: 'https://hal-india.co.in/careers/apply',
      portal_url: 'https://hal-india.co.in',
      notification_pdf_url: 'https://hal-india.co.in/mt2026.pdf',
      portal_instructions: 'GATE based shortlisting → Apply online → Interview at HAL division.',
      source_url: 'https://hal-india.co.in/careers',
      total_marks: null,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 20,
      exam_name: 'RailTel Manager (IT) 2026',
      organization: 'RailTel',
      organization_full: 'RailTel Corporation of India',
      post_name: 'Manager / Deputy Manager (IT/Network)',
      job_domain: 'software_it',
      vacancies: 18,
      qualification: 'B.Tech/BE (CS/IT/ECE)',
      experience_required: '2-5 years',
      age_limit: '35 years',
      application_fee: '₹600 (Free for SC/ST/PwD)',
      pay_scale: '₹50,000 - ₹1,60,000 (IDA, E3 Grade)',
      location: 'New Delhi (HQ) + Regional offices',
      notification_date: pastDate(1),
      application_start_date: pastDate(0),
      application_last_date: futureDate(30),
      exam_date: futureDate(60),
      status: 'active',
      apply_link: 'https://www.railtel.in/careers/',
      portal_url: 'https://www.railtel.in',
      notification_pdf_url: 'https://www.railtel.in/careers/',
      portal_instructions: 'Apply online → Written test → Interview.',
      source_url: 'https://railtelindia.com/careers',
      total_marks: 200,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 21,
      exam_name: 'STPI MTS Recruitment 2026',
      organization: 'STPI',
      organization_full: 'Software Technology Parks of India',
      post_name: 'Member Technical Staff (Software)',
      job_domain: 'software_it',
      vacancies: 30,
      qualification: 'B.Tech/BE/MCA (CS/IT)',
      experience_required: '0-2 years',
      age_limit: '30 years',
      application_fee: '₹500',
      pay_scale: '7th CPC Level 7 (₹44,900 - ₹1,42,400)',
      location: 'Delhi, Bengaluru, Pune, Chennai, Mohali',
      notification_date: pastDate(3),
      application_start_date: pastDate(1),
      application_last_date: futureDate(28),
      exam_date: futureDate(70),
      status: 'active',
      apply_link: 'https://www.stpi.in/careers',
      portal_url: 'https://www.stpi.in',
      notification_pdf_url: 'https://www.stpi.in/careers',
      portal_instructions: 'Apply on STPI recruitment portal → Written exam → Interview.',
      source_url: 'https://stpi.in/careers',
      total_marks: 200,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 22,
      exam_name: 'NTA UGC NET (CS) Dec 2026',
      organization: 'NTA',
      organization_full: 'National Testing Agency',
      post_name: 'UGC NET — Computer Science & Applications',
      job_domain: 'teaching',
      vacancies: null,
      qualification: 'M.Tech/MCA/M.Sc (CS/IT)',
      experience_required: 'Fresher',
      age_limit: 'No upper limit for JRF eligibility',
      application_fee: '₹1,150 (₹600 for OBC, ₹325 for SC/ST/PwD)',
      pay_scale: 'Assistant Professor (Level 10) / JRF ₹31,000+',
      location: 'All India (Exam centres)',
      notification_date: pastDate(22),
      application_start_date: pastDate(18),
      application_last_date: futureDate(4),
      exam_date: futureDate(30),
      status: 'active',
      apply_link: 'https://exams.nta.ac.in/UGC-NET/',
      portal_url: 'https://nta.ac.in',
      notification_pdf_url: 'https://exams.nta.ac.in/UGC-NET/',
      portal_instructions: 'Register on NTA portal → Fill form → Upload documents → Pay fee → Download admit card → Appear for exam.',
      source_url: 'https://ugcnet.nta.ac.in',
      total_marks: 300,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 23,
      exam_name: 'Indian Navy SSC IT 2026',
      organization: 'Navy',
      organization_full: 'Indian Navy',
      post_name: 'Short Service Commission (IT Branch)',
      job_domain: 'software_it',
      vacancies: 15,
      qualification: 'B.Tech/BE (CS/IT) with 60%+',
      experience_required: 'Fresher',
      age_limit: '19.5-25 years',
      application_fee: 'Free',
      pay_scale: 'Level 10 (₹56,100) + Military Service Pay + Allowances',
      location: 'Naval bases across India',
      notification_date: pastDate(15),
      application_start_date: pastDate(12),
      application_last_date: futureDate(9),
      exam_date: null,
      status: 'active',
      apply_link: 'https://www.joinindiannavy.gov.in',
      portal_url: 'https://www.joinindiannavy.gov.in',
      notification_pdf_url: 'https://www.joinindiannavy.gov.in',
      portal_instructions: 'Register → Apply online → SSB Interview → Medical → Merit list.',
      source_url: 'https://joinindiannavy.gov.in',
      total_marks: null,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 24,
      exam_name: 'LIC AAO 2026',
      organization: 'LIC',
      organization_full: 'Life Insurance Corporation of India',
      post_name: 'Assistant Administrative Officer (Generalist + IT)',
      job_domain: 'banking',
      vacancies: 300,
      qualification: 'Any Graduate (CS/IT eligible)',
      experience_required: 'Fresher',
      age_limit: '21-30 years',
      application_fee: '₹700 (₹85 for SC/ST/PwD)',
      pay_scale: '₹53,600 - ₹1,47,000',
      location: 'All India',
      notification_date: pastDate(17),
      application_start_date: pastDate(14),
      application_last_date: futureDate(11),
      exam_date: futureDate(45),
      status: 'active',
      apply_link: 'https://licindia.in/careers',
      portal_url: 'https://licindia.in',
      notification_pdf_url: 'https://licindia.in/aao2026.pdf',
      portal_instructions: 'Register on LIC careers → Apply online → Preliminary exam → Main exam → Interview.',
      source_url: 'https://licindia.in',
      total_marks: 300,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    },
    {
      id: 25,
      exam_name: 'UIDAI Technology Officer 2026',
      organization: 'UIDAI',
      organization_full: 'Unique Identification Authority of India',
      post_name: 'Deputy Director / Assistant Director (Technology)',
      job_domain: 'software_it',
      vacancies: 12,
      qualification: 'B.Tech/BE (CS/IT)',
      experience_required: '5+ years',
      age_limit: '40 years',
      application_fee: 'Free (Deputation)',
      pay_scale: '7th CPC Level 11-12',
      location: 'New Delhi, Bengaluru',
      notification_date: pastDate(5),
      application_start_date: pastDate(3),
      application_last_date: futureDate(20),
      exam_date: null,
      status: 'active',
      apply_link: 'https://uidai.gov.in/careers',
      portal_url: 'https://uidai.gov.in',
      notification_pdf_url: 'https://uidai.gov.in/tech2026.pdf',
      portal_instructions: 'Apply via deputation/direct recruitment through UIDAI website.',
      source_url: 'https://uidai.gov.in',
      total_marks: null,
      created_at: now.toISOString(),
      updated_at: now.toISOString()
    }
  ];

  // Cutoff data for some exams
  memoryStore.cutoffs = [
    { id: 1, job_id: 1, tier: 'SET Exam', year: 2025, category: 'General', qualifying_marks: 120.00, merit_marks: 145.50, total_marks: 300 },
    { id: 2, job_id: 1, tier: 'SET Exam', year: 2025, category: 'OBC', qualifying_marks: 108.00, merit_marks: 132.25, total_marks: 300 },
    { id: 3, job_id: 1, tier: 'SET Exam', year: 2025, category: 'SC', qualifying_marks: 90.00, merit_marks: 110.00, total_marks: 300 },
    { id: 4, job_id: 1, tier: 'SET Exam', year: 2025, category: 'ST', qualifying_marks: 85.00, merit_marks: 105.50, total_marks: 300 },
    { id: 5, job_id: 1, tier: 'SET Exam', year: 2024, category: 'General', qualifying_marks: 115.00, merit_marks: 140.00, total_marks: 300 },
    { id: 6, job_id: 4, tier: 'Tier 1', year: 2025, category: 'General', qualifying_marks: 142.50, merit_marks: 165.00, total_marks: 200 },
    { id: 7, job_id: 4, tier: 'Tier 1', year: 2025, category: 'OBC', qualifying_marks: 130.00, merit_marks: 152.00, total_marks: 200 },
    { id: 8, job_id: 4, tier: 'Tier 1', year: 2025, category: 'SC', qualifying_marks: 110.00, merit_marks: 135.00, total_marks: 200 },
    { id: 9, job_id: 4, tier: 'Tier 2', year: 2025, category: 'General', qualifying_marks: 280.00, merit_marks: 350.00, total_marks: 500 },
    { id: 10, job_id: 10, tier: 'Phase I', year: 2025, category: 'General', qualifying_marks: 95.00, merit_marks: 115.00, total_marks: 200 },
    { id: 11, job_id: 10, tier: 'Phase II', year: 2025, category: 'General', qualifying_marks: 145.00, merit_marks: 170.00, total_marks: 300 },
  ];

  // Load portals from config
  const { portals: portalConfig } = require('../config/portals');
  memoryStore.portals = portalConfig.map((p, i) => ({
    id: i + 1,
    name: p.name,
    short_name: p.shortName,
    url: p.url,
    description: p.description,
    category: p.category,
    exams_covered: p.exams,
    it_roles_available: p.itRoles,
    last_scraped: null,
    scrape_status: 'pending',
    is_active: true
  }));

  logger.info('Database', `Seeded ${memoryStore.jobs.length} jobs, ${memoryStore.cutoffs.length} cutoffs, ${memoryStore.portals.length} portals`);
}

// ============================================================
// Query interface (works for both PG and in-memory)
// ============================================================

/**
 * Get jobs with filtering, searching, and pagination
 */
async function getJobs(filters = {}) {
  const { domain, organization, status, qualification, experience, search, page = 1, limit = 20 } = filters;

  let jobs = [...memoryStore.jobs];

  // Apply filters
  if (domain) {
    jobs = jobs.filter(j => j.job_domain === domain);
  }
  if (organization) {
    jobs = jobs.filter(j => j.organization.toLowerCase() === organization.toLowerCase());
  }
  if (status) {
    jobs = jobs.filter(j => j.status === status);
  }
  if (qualification) {
    jobs = jobs.filter(j => j.qualification && j.qualification.toLowerCase().includes(qualification.toLowerCase()));
  }
  if (experience) {
    jobs = jobs.filter(j => j.experience_required && j.experience_required.toLowerCase().includes(experience.toLowerCase()));
  }
  if (search) {
    const q = search.toLowerCase();
    jobs = jobs.filter(j =>
      (j.exam_name && j.exam_name.toLowerCase().includes(q)) ||
      (j.organization && j.organization.toLowerCase().includes(q)) ||
      (j.post_name && j.post_name.toLowerCase().includes(q)) ||
      (j.organization_full && j.organization_full.toLowerCase().includes(q))
    );
  }

  const total = jobs.length;
  const offset = (page - 1) * limit;
  const paginatedJobs = jobs.slice(offset, offset + limit);

  return {
    jobs: paginatedJobs,
    total,
    page: parseInt(page),
    totalPages: Math.ceil(total / limit)
  };
}

/**
 * Get a single job by ID
 */
async function getJobById(id) {
  return memoryStore.jobs.find(j => j.id === parseInt(id)) || null;
}

/**
 * Get cutoffs for a job
 */
async function getCutoffsByJobId(jobId) {
  return memoryStore.cutoffs.filter(c => c.job_id === parseInt(jobId));
}

/**
 * Get cutoffs with filtering
 */
async function getCutoffs(filters = {}) {
  const { exam, year, category } = filters;
  let cutoffs = [...memoryStore.cutoffs];

  if (year) cutoffs = cutoffs.filter(c => c.year === parseInt(year));
  if (category) cutoffs = cutoffs.filter(c => c.category.toLowerCase() === category.toLowerCase());

  // Enrich with job info
  return cutoffs.map(c => {
    const job = memoryStore.jobs.find(j => j.id === c.job_id);
    return { ...c, exam_name: job?.exam_name, organization: job?.organization };
  });
}

/**
 * Get all portals
 */
async function getPortals(category = null) {
  if (category) {
    return memoryStore.portals.filter(p => p.category === category);
  }
  return memoryStore.portals;
}

/**
 * Get portal by short name
 */
async function getPortalByShortName(shortName) {
  return memoryStore.portals.find(p => p.short_name.toLowerCase() === shortName.toLowerCase()) || null;
}

/**
 * Get dashboard stats
 */
async function getStats() {
  const jobs = memoryStore.jobs;
  const activeJobs = jobs.filter(j => j.status === 'active');
  const itJobs = jobs.filter(j => ['software_it', 'telecom', 'cybersecurity', 'data_analytics'].includes(j.job_domain));
  const totalVacancies = jobs.reduce((sum, j) => sum + (j.vacancies || 0), 0);

  // Count by domain
  const domainCounts = {};
  jobs.forEach(j => {
    domainCounts[j.job_domain] = (domainCounts[j.job_domain] || 0) + 1;
  });

  // Count by organization
  const orgCounts = {};
  jobs.forEach(j => {
    orgCounts[j.organization] = (orgCounts[j.organization] || 0) + 1;
  });

  return {
    totalJobs: jobs.length,
    activeJobs: activeJobs.length,
    itJobs: itJobs.length,
    totalVacancies,
    totalPortals: memoryStore.portals.length,
    domainCounts,
    orgCounts,
    lastUpdated: new Date().toISOString()
  };
}

module.exports = {
  initDatabase,
  getJobs,
  getJobById,
  getCutoffsByJobId,
  getCutoffs,
  getPortals,
  getPortalByShortName,
  getStats
};
