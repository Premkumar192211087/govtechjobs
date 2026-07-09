const { syncFromAIService } = require('./scrapers/scheduler');
const db = require('./database/db');

async function testSync() {
  console.log("Initializing database...");
  await db.initDatabase();
  
  const axios = require('axios');
  const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';
  
  console.log("Testing single portal scrape integration via FastAPI...");
  try {
    const response = await axios.post(`${AI_SERVICE_URL}/scrape-portal`, {
      portal_url: "https://www.upsc.gov.in/recruitment/active-advertisements",
      org: "UPSC",
      org_full: "Union Public Service Commission"
    });
    
    if (response.data && response.data.success && response.data.jobs) {
      console.log(`FastAPI scraped UPSC successfully. Found ${response.data.jobs.length} jobs.`);
      for (const job of response.data.jobs) {
        await db.saveJob(job);
      }
    } else {
      console.log("FastAPI scrape call failed:", response.data);
    }
  } catch (err) {
    console.error("FastAPI call error:", err.message);
  }
  
  console.log("Checking total jobs in database...");
  const result = await db.getJobs();
  const jobs = result.jobs;
  console.log(`Total jobs in database: ${result.total}`);
  if (jobs.length > 0) {
    console.log("Sample jobs:");
    jobs.slice(0, 5).forEach(j => {
      console.log(`- [${j.organization}] ${j.exam_name} (Vacancies: ${j.vacancies}, Last Date: ${j.application_last_date})`);
    });
  }
  process.exit(0);
}

testSync().catch(err => {
  console.error("Test sync failed:", err);
  process.exit(1);
});
