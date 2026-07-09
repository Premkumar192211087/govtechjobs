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
      const pageText = $('body').text();
      const seen = new Set();

      $('a').each((i, el) => {
        const text = $(el).text().trim().replace(/\s+/g, ' ');
        const href = $(el).attr('href') || '';

        // Match recruitment/career related anchor text
        if (text.length < 10) return;
        if (!/recruitment|project engineer|technical|vacancy|career|walk-in|contractual|openings/i.test(text)) return;
        if (seen.has(text)) return;
        seen.add(text);

        const link = href.startsWith('http') ? href : `https://www.cdac.in/${href}`;

        // Extract vacancy count from text
        let vacancies = 1;
        const vacMatch = text.match(/(\d+)\s*(?:posts?|vacancies|positions?)/i);
        if (vacMatch) vacancies = parseInt(vacMatch[1]);

        // Extract qualification from surrounding text
        let qualification = 'As per official notification';
        const qualMatch = pageText.match(/(?:qualification|eligibility)\s*[:\-–]?\s*([^\n]{10,100})/i);
        if (qualMatch) qualification = qualMatch[1].trim();

        // Extract last date from page
        let lastDate = new Date(now.getTime() + 30 * 86400000).toISOString().split('T')[0];
        const dateMatch = pageText.match(/(?:last\s+date|closing\s+date)\s*[:\-–]?\s*(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})/i);
        if (dateMatch) {
          lastDate = `${dateMatch[3]}-${dateMatch[2].padStart(2, '0')}-${dateMatch[1].padStart(2, '0')}`;
        }

        // Extract age limit
        let ageLimit = 'As per official notification';
        const ageMatch = pageText.match(/(?:age\s*limit|max\s*age)\s*[:\-–]?\s*(\d{2})\s*(?:years?|yrs?)/i);
        if (ageMatch) ageLimit = `${ageMatch[1]} years (relaxation as per rules)`;

        // Extract fee
        let fee = 'As per official notification';
        const feeMatch = pageText.match(/(?:application\s*fee|fee)\s*[:\-–]?\s*(?:Rs\.?|₹)\s*([\d,]+)/i);
        if (feeMatch) fee = `₹${feeMatch[1]} (concessions for reserved categories)`;

        // Extract pay/salary
        let payScale = 'As per government norms';
        const payMatch = pageText.match(/(?:salary|pay|remuneration|consolidated)\s*[:\-–]?\s*([^\n]{5,80})/i);
        if (payMatch) payScale = payMatch[1].trim();

        jobs.push({
          exam_name: text,
          organization: 'CDAC',
          organization_full: 'Centre for Development of Advanced Computing',
          post_name: text,
          job_domain: 'software_it',
          vacancies,
          qualification,
          experience_required: 'As per official notification',
          age_limit: ageLimit,
          application_fee: fee,
          pay_scale: payScale,
          location: 'Multiple CDAC centres across India',
          notification_date: now.toISOString().split('T')[0],
          application_start_date: now.toISOString().split('T')[0],
          application_last_date: lastDate,
          exam_date: null,
          status: 'active',
          apply_link: link,
          portal_url: 'https://www.cdac.in',
          notification_pdf_url: link,
          portal_instructions: 'Visit CDAC portal → Select the notification → Register/Login → Fill application → Submit.',
          source_url: this.baseUrl,
          total_marks: null
        });
      });

      return jobs;
    } catch (err) {
      return [];
    }
  }
}

module.exports = CdacScraper;
