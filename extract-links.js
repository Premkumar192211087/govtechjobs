const { discoverDirectApplyLinks } = require('./utils/aiExtractorService');

const targetUrl = process.argv[2] || 'https://www.cdac.in/index.aspx?id=careers';

async function run() {
  console.log(`================================================================`);
  console.log(`🤖 AI/ML Government Job Direct Application Link Extractor`);
  console.log(`================================================================`);
  console.log(`Target URL: ${targetUrl}\n`);

  console.log(`Crawling and analyzing page using AI feature-classification...`);
  const results = await discoverDirectApplyLinks(targetUrl);

  if (!results.success) {
    console.error(`❌ Error: ${results.error}`);
    return;
  }

  console.log(`\n🎉 Analysis Complete!\n`);

  if (results.bestDirectApply) {
    console.log(`🔥 [BEST DIRECT APPLY LINK FOUND]`);
    console.log(`   URL:      \x1b[32m${results.bestDirectApply.url}\x1b[0m`);
    console.log(`   Anchor:   "${results.bestDirectApply.anchorText}"`);
    console.log(`   AI Score: ${results.bestDirectApply.confidenceScore}\n`);
  } else {
    console.log(`⚠️ No direct apply links found (falling back to generic listings).\n`);
  }

  console.log(`📋 Classified Direct Application Links:`);
  console.log(`----------------------------------------------------------------`);
  if (results.allDirectApplyLinks.length === 0) {
    console.log(`   (None found)`);
  } else {
    results.allDirectApplyLinks.forEach((item, index) => {
      console.log(`   [${index + 1}] Score: ${item.confidenceScore} | Anchor: "${item.anchorText}"`);
      console.log(`       Link: ${item.url}`);
    });
  }

  console.log(`\n📂 Classified Generic Career/Listing Pages:`);
  console.log(`----------------------------------------------------------------`);
  if (results.genericCareerLinks.length === 0) {
    console.log(`   (None found)`);
  } else {
    results.genericCareerLinks.slice(0, 5).forEach((item, index) => {
      console.log(`   [${index + 1}] Score: ${item.confidenceScore} | Anchor: "${item.anchorText}"`);
      console.log(`       Link: ${item.url}`);
    });
  }
  console.log(`================================================================`);
}

run();
