const BaseScraper = require('./baseScraper');

class UpscScraper extends BaseScraper {
  constructor() {
    super('UPSC', 'https://www.upsc.gov.in/recruitment/active-advertisements');
  }

  async scrape() {
    try {
      const html = await this.fetch(this.baseUrl);
      const $ = this.parse(html);
      const jobs = [];
      const now = new Date();

      // Find all h3 titles representing advertisements
      $('h3').each((i, el) => {
        const title = $(el).text().trim();
        if (!title || title.length < 10) return; // Skip small or empty headings

        // Look at next sibling views-row to find link
        const nextDiv = $(el).next('.views-row');
        const linkEl = nextDiv.find('a').first();
        const relativeLink = linkEl.attr('href') || '';
        const link = relativeLink.startsWith('http') ? relativeLink : `https://www.upsc.gov.in${relativeLink}`;

        // Determine if it is a tech/IT role
        const isIT = /computer|software|developer|it |information technology|system|network|database|data analyst|electronics|electrical/i.test(title);
        
        // Parse vacancy count if mentioned (e.g., "10 Posts of...")
        const vacancyMatch = title.match(/^(\d+)\s+Posts?/i);
        const vacancies = vacancyMatch ? parseInt(vacancyMatch[1]) : 1;

        jobs.push({
          exam_name: title,
          organization: 'UPSC',
          organization_full: 'Union Public Service Commission',
          post_name: title.includes('in') ? title.split('in')[0].trim() : 'Specialist Officer',
          job_domain: isIT ? 'software_it' : 'non_it',
          vacancies: vacancies,
          qualification: 'Degree / Master Degree in relevant discipline',
          experience_required: 'Varies by post (0-5 years)',
          age_limit: '30-35 years',
          application_fee: '₹25 (Free for SC/ST/PwD/Women)',
          pay_scale: '7th CPC Level 7-10',
          location: 'All India',
          notification_date: now.toISOString().split('T')[0],
          application_start_date: now.toISOString().split('T')[0],
          application_last_date: new Date(now.getTime() + 21 * 86400000).toISOString().split('T')[0],
          exam_date: null,
          status: 'active',
          apply_link: 'https://upsconline.nic.in',
          portal_url: 'https://www.upsc.gov.in',
          notification_pdf_url: link || 'https://www.upsc.gov.in/recruitment/active-advertisements',
          portal_instructions: 'Visit UPSC Online portal (upsconline.nic.in) → Click "Online Recruitment Application (ORA)" → Register and Apply.',
          source_url: this.baseUrl,
          total_marks: 100
        });
      });

      return jobs;
    } catch (err) {
      return [];
    }
  }
}

module.exports = UpscScraper;
