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
      const pageText = $('body').text();

      // UPSC lists each advertisement under h3 headings with companion PDF links
      $('h3').each((i, el) => {
        const title = $(el).text().trim();
        if (!title || title.length < 15) return;
        if (/menu|navigation|footer|header|search/i.test(title)) return;

        // Find nearest PDF link
        let pdfUrl = this.baseUrl;
        const nextLink = $(el).next().find('a[href]').first();
        if (nextLink.length) {
          const href = nextLink.attr('href') || '';
          pdfUrl = href.startsWith('http') ? href : `https://www.upsc.gov.in${href}`;
        }

        // Extract vacancy count from title (e.g. "20 Posts of Senior Scientific...")
        const vacancyMatch = title.match(/^(\d+)\s+Posts?/i);
        const vacancies = vacancyMatch ? parseInt(vacancyMatch[1]) : 1;

        // Detect IT/Software domain from title keywords
        const isIT = /computer|software|developer|it |information technology|system|network|database|data|electronics|electrical|telecom|digital|cyber/i.test(title);

        // Extract post name from title — text after "Posts of" or "Post of"
        let postName = title;
        const postMatch = title.match(/\d+\s+Posts?\s+of\s+(.+)/i);
        if (postMatch) postName = postMatch[1].trim();

        // Extract qualification hints from surrounding text
        let qualification = 'As per official notification';
        const qualSection = pageText.match(/qualification[s]?\s*[:\-–]?\s*([^\n]{10,120})/i);
        if (qualSection) qualification = qualSection[1].trim();

        // Extract age limit from page
        let ageLimit = 'As per official notification';
        const ageMatch = pageText.match(/(?:age\s*limit|max(?:imum)?\s*age)\s*[:\-–]?\s*(\d{2})\s*(?:years?|yrs?)/i);
        if (ageMatch) ageLimit = `${ageMatch[1]} years (relaxation as per rules)`;

        // Extract application fee from page
        let fee = 'As per official notification';
        const feeMatch = pageText.match(/(?:application\s*fee|exam\s*fee)\s*[:\-–]?\s*(?:Rs\.?|₹)\s*([\d,]+)/i);
        if (feeMatch) fee = `₹${feeMatch[1]} (concessions for reserved categories)`;

        // Try to extract last date
        let lastDate = new Date(now.getTime() + 30 * 86400000).toISOString().split('T')[0];
        const dateMatch = pageText.match(/(?:last\s+date|closing\s+date)\s*[:\-–]?\s*(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})/i);
        if (dateMatch) {
          lastDate = `${dateMatch[3]}-${dateMatch[2].padStart(2, '0')}-${dateMatch[1].padStart(2, '0')}`;
        }

        // Extract pay scale
        let payScale = 'As per government norms';
        const payMatch = pageText.match(/(?:pay\s*(?:scale|level|matrix)|salary)\s*[:\-–]?\s*([^\n]{5,80})/i);
        if (payMatch) payScale = payMatch[1].trim();

        jobs.push({
          exam_name: title,
          organization: 'UPSC',
          organization_full: 'Union Public Service Commission',
          post_name: postName,
          job_domain: isIT ? 'software_it' : 'non_it',
          vacancies,
          qualification,
          experience_required: 'As per official notification',
          age_limit: ageLimit,
          application_fee: fee,
          pay_scale: payScale,
          location: 'All India',
          notification_date: now.toISOString().split('T')[0],
          application_start_date: now.toISOString().split('T')[0],
          application_last_date: lastDate,
          exam_date: null,
          status: 'active',
          apply_link: 'https://upsconline.nic.in/ora/',
          portal_url: 'https://www.upsc.gov.in',
          notification_pdf_url: pdfUrl,
          portal_instructions: 'Visit UPSC Online (upsconline.nic.in) → Online Recruitment Application (ORA) → Register → Apply.',
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

module.exports = UpscScraper;
