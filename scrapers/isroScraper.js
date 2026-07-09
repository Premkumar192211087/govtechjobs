const BaseScraper = require('./baseScraper');

class IsroScraper extends BaseScraper {
  constructor() {
    super('ISRO', 'https://www.isro.gov.in/Careers.html');
  }

  async scrape() {
    try {
      const html = await this.fetch(this.baseUrl);
      const $ = this.parse(html);
      const jobs = [];
      const now = new Date();
      const pageText = $('body').text();
      const seen = new Set();

      $('a').each((i, el) => {
        const text = $(el).text().trim().replace(/\s+/g, ' ');
        const href = $(el).attr('href') || '';

        if (text.length < 15) return;
        if (!/recruitment|scientist|engineer|technician|icrb|vacancy|openings|apply|walk-in|trainee/i.test(text)) return;
        if (seen.has(text)) return;
        seen.add(text);

        const link = href.startsWith('http') ? href : `https://www.isro.gov.in/${href}`;

        let vacancies = 1;
        const vacMatch = text.match(/(\d+)\s*(?:posts?|vacancies|positions?)/i);
        if (vacMatch) vacancies = parseInt(vacMatch[1]);

        let lastDate = new Date(now.getTime() + 30 * 86400000).toISOString().split('T')[0];
        const dateMatch = pageText.match(/(?:last\s+date|closing\s+date)\s*[:\-–]?\s*(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})/i);
        if (dateMatch) lastDate = `${dateMatch[3]}-${dateMatch[2].padStart(2, '0')}-${dateMatch[1].padStart(2, '0')}`;

        let qualification = 'As per official notification';
        const qualMatch = pageText.match(/(?:qualification|eligibility)\s*[:\-–]?\s*([^\n]{10,100})/i);
        if (qualMatch) qualification = qualMatch[1].trim();

        let ageLimit = 'As per official notification';
        const ageMatch = pageText.match(/(?:age\s*limit|max\s*age)\s*[:\-–]?\s*(\d{2})\s*(?:years?|yrs?)/i);
        if (ageMatch) ageLimit = `${ageMatch[1]} years (relaxation as per rules)`;

        let fee = 'As per official notification';
        const feeMatch = pageText.match(/(?:application\s*fee|fee)\s*[:\-–]?\s*(?:Rs\.?|₹)\s*([\d,]+)/i);
        if (feeMatch) fee = `₹${feeMatch[1]} (concessions for reserved categories)`;

        jobs.push({
          exam_name: text,
          organization: 'ISRO',
          organization_full: 'Indian Space Research Organisation',
          post_name: text,
          job_domain: 'software_it',
          vacancies,
          qualification,
          experience_required: 'As per official notification',
          age_limit: ageLimit,
          application_fee: fee,
          pay_scale: 'As per government norms',
          location: 'All India (ISRO Centres)',
          notification_date: now.toISOString().split('T')[0],
          application_start_date: now.toISOString().split('T')[0],
          application_last_date: lastDate,
          exam_date: null,
          status: 'active',
          apply_link: link,
          portal_url: 'https://www.isro.gov.in',
          notification_pdf_url: link.endsWith('.pdf') ? link : 'https://www.isro.gov.in/Careers.html',
          portal_instructions: 'Visit isro.gov.in/Careers → Find notification → Apply via ISRO recruitment portal.',
          source_url: this.baseUrl,
          total_marks: null
        });
      });

      return jobs.slice(0, 10);
    } catch (err) {
      return [];
    }
  }
}

module.exports = IsroScraper;
