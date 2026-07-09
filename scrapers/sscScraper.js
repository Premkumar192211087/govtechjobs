const BaseScraper = require('./baseScraper');

class SscScraper extends BaseScraper {
  constructor() {
    super('SSC', 'https://ssc.gov.in/notice-board');
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
        // Only match recruitment/exam related announcements
        if (!/recruitment|examination|vacancies|selection|cgl|chsl|je |mts|steno|notification|apply/i.test(text)) return;
        if (seen.has(text)) return;
        seen.add(text);

        const link = href.startsWith('http') ? href : `https://ssc.gov.in${href}`;

        // Extract vacancy count
        let vacancies = 1;
        const vacMatch = text.match(/(\d+)\s*(?:posts?|vacancies|positions?)/i);
        if (vacMatch) vacancies = parseInt(vacMatch[1]);

        // Extract last date
        let lastDate = new Date(now.getTime() + 30 * 86400000).toISOString().split('T')[0];
        // Try from text first, then from page
        const textDateMatch = text.match(/(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})/);
        const pageDateMatch = pageText.match(/(?:last\s+date|closing\s+date)\s*[:\-–]?\s*(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})/i);
        const dateMatch = textDateMatch || pageDateMatch;
        if (dateMatch) {
          lastDate = `${dateMatch[3]}-${dateMatch[2].padStart(2, '0')}-${dateMatch[1].padStart(2, '0')}`;
        }

        // Detect domain
        const isIT = /computer|it |software|data|network|system|electronics|telecom|digital|cyber/i.test(text);
        const isBanking = /bank|clerk|po /i.test(text);

        // Extract qualification
        let qualification = 'As per official notification';
        const qualMatch = pageText.match(/(?:qualification|eligibility)\s*[:\-–]?\s*([^\n]{10,100})/i);
        if (qualMatch) qualification = qualMatch[1].trim();

        // Extract age limit
        let ageLimit = 'As per official notification';
        const ageMatch = pageText.match(/(?:age\s*limit|max\s*age)\s*[:\-–]?\s*(\d{2})\s*(?:years?|yrs?)/i);
        if (ageMatch) ageLimit = `${ageMatch[1]} years (relaxation as per rules)`;

        // Extract fee
        let fee = 'As per official notification';
        const feeMatch = pageText.match(/(?:application\s*fee|fee)\s*[:\-–]?\s*(?:Rs\.?|₹)\s*([\d,]+)/i);
        if (feeMatch) fee = `₹${feeMatch[1]} (concessions for reserved categories)`;

        jobs.push({
          exam_name: text,
          organization: 'SSC',
          organization_full: 'Staff Selection Commission',
          post_name: text,
          job_domain: isIT ? 'software_it' : (isBanking ? 'banking' : 'non_it'),
          vacancies,
          qualification,
          experience_required: 'As per official notification',
          age_limit: ageLimit,
          application_fee: fee,
          pay_scale: 'As per government norms',
          location: 'All India',
          notification_date: now.toISOString().split('T')[0],
          application_start_date: now.toISOString().split('T')[0],
          application_last_date: lastDate,
          exam_date: null,
          status: 'active',
          apply_link: 'https://ssc.gov.in/login',
          portal_url: 'https://ssc.gov.in',
          notification_pdf_url: link.endsWith('.pdf') ? link : 'https://ssc.gov.in/notice-board',
          portal_instructions: 'Visit ssc.gov.in → Login/Register → Find notification → Apply Online.',
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

module.exports = SscScraper;
