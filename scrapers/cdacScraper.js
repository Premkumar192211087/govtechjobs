const BaseScraper = require('./baseScraper');

class CdacScraper extends BaseScraper {
  constructor() {
    super('CDAC', 'https://www.cdac.in/index.aspx?id=careers');
  }

  async scrape() {
    try {
      const html = await this.fetch(this.baseUrl);
      const $ = this.parse(html);
      const jobs = [];
      const now = new Date();

      // Find links pointing to specific recruitment drives
      $('a').each((i, el) => {
        const text = $(el).text().trim();
        const href = $(el).attr('href') || '';
        
        // Filter links that represent active recruitment
        if (/recruitment|vacancy|careers|project engineer|technical officer/i.test(text) && href.includes('id=')) {
          const title = text.replace(/\s+/g, ' ');
          const link = href.startsWith('http') ? href : `https://www.cdac.in/${href}`;
          
          if (jobs.some(j => j.exam_name === title)) return;

          jobs.push({
            exam_name: title,
            organization: 'CDAC',
            organization_full: 'Centre for Development of Advanced Computing',
            post_name: 'Project Engineer / Technical Officer',
            job_domain: 'software_it', // CDAC is always IT
            vacancies: 1,
            qualification: 'B.Tech/BE/MCA/M.Tech (CS/IT/Electronics)',
            experience_required: '0-5 years (varies by grade)',
            age_limit: '30-35 years',
            application_fee: '₹500 (Free for SC/ST/PwD)',
            pay_scale: 'Consolidated salary as per qualifications',
            location: 'Multiple CDAC centres',
            notification_date: now.toISOString().split('T')[0],
            application_start_date: now.toISOString().split('T')[0],
            application_last_date: new Date(now.getTime() + 20 * 86400000).toISOString().split('T')[0],
            exam_date: null,
            status: 'active',
            apply_link: link,
            portal_url: 'https://www.cdac.in',
            notification_pdf_url: link,
            portal_instructions: 'Register on CDAC portal → Select post → Fill details → Submit application.',
            source_url: this.baseUrl,
            total_marks: 100
          });
        }
      });

      return jobs;
    } catch (err) {
      return [];
    }
  }
}

module.exports = CdacScraper;
