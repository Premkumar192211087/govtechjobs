const https = require('https');
const http = require('http');

const urls = [
  { org: 'DRDO', apply: 'https://rac.gov.in', portal: 'https://drdo.gov.in' },
  { org: 'ISRO', apply: 'https://apply.isro.gov.in', portal: 'https://isro.gov.in' },
  { org: 'NIC', apply: 'https://nic.in', portal: 'https://nic.in' },
  { org: 'SSC', apply: 'https://ssc.gov.in', portal: 'https://ssc.gov.in' },
  { org: 'IBPS', apply: 'https://ibps.in', portal: 'https://ibps.in' },
  { org: 'CDAC', apply: 'https://cdac.in', portal: 'https://cdac.in' },
  { org: 'BEL', apply: 'https://bel-india.in', portal: 'https://bel-india.in' },
  { org: 'UPSC', apply: 'https://upsconline.nic.in', portal: 'https://upsc.gov.in' },
  { org: 'SBI', apply: 'https://sbi.co.in', portal: 'https://sbi.co.in' },
  { org: 'RBI', apply: 'https://opportunities.rbi.org.in', portal: 'https://rbi.org.in' },
  { org: 'ECIL', apply: 'https://ecil.co.in', portal: 'https://ecil.co.in' },
  { org: 'NIELIT', apply: 'https://nielit.gov.in', portal: 'https://nielit.gov.in' },
  { org: 'RRB', apply: 'https://rrbcdg.gov.in', portal: 'https://rrbcdg.gov.in' },
  { org: 'NTPC', apply: 'https://ntpc.co.in', portal: 'https://ntpc.co.in' },
  { org: 'SEBI', apply: 'https://sebi.gov.in', portal: 'https://sebi.gov.in' },
  { org: 'KVS', apply: 'https://kvsangathan.nic.in', portal: 'https://kvsangathan.nic.in' },
  { org: 'PowerGrid', apply: 'https://powergrid.in', portal: 'https://powergrid.in' },
  { org: 'BSNL', apply: 'https://bsnl.co.in', portal: 'https://bsnl.co.in' },
  { org: 'HAL', apply: 'https://hal-india.co.in', portal: 'https://hal-india.co.in' },
  { org: 'RailTel', apply: 'https://railtelindia.com', portal: 'https://railtelindia.com' },
  { org: 'STPI', apply: 'https://stpi.in', portal: 'https://stpi.in' },
  { org: 'NTA', apply: 'https://ugcnet.nta.ac.in', portal: 'https://nta.ac.in' },
  { org: 'Navy', apply: 'https://joinindiannavy.gov.in', portal: 'https://joinindiannavy.gov.in' },
  { org: 'LIC', apply: 'https://licindia.in', portal: 'https://licindia.in' },
  { org: 'UIDAI', apply: 'https://uidai.gov.in', portal: 'https://uidai.gov.in' },
];

function checkUrl(url) {
  return new Promise((resolve) => {
    const mod = url.startsWith('https') ? https : http;
    const req = mod.get(url, { timeout: 8000, headers: { 'User-Agent': 'Mozilla/5.0' } }, (res) => {
      resolve({ status: res.statusCode, redirect: res.headers.location || null });
    });
    req.on('error', (err) => resolve({ status: 'ERROR', error: err.code || err.message }));
    req.on('timeout', () => { req.destroy(); resolve({ status: 'TIMEOUT' }); });
  });
}

async function main() {
  console.log('Checking all Apply/Portal URLs...\n');
  console.log('ORG'.padEnd(12) + 'STATUS'.padEnd(10) + 'URL');
  console.log('-'.repeat(80));

  for (const entry of urls) {
    const result = await checkUrl(entry.apply);
    const statusStr = result.status === 200 ? '✅ 200' 
      : (result.status >= 300 && result.status < 400) ? `🔄 ${result.status}` 
      : `❌ ${result.status}`;
    const extra = result.redirect ? ` → ${result.redirect}` : (result.error || '');
    console.log(entry.org.padEnd(12) + statusStr.padEnd(10) + entry.apply + extra);
  }
}

main();
