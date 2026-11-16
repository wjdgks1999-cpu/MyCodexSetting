// Independent browser checks for the fixed existing-page fixture.
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

async function main() {
  const [runtime, html, output] = process.argv.slice(2);
  const puppeteer = require(path.join(runtime, 'node_modules/puppeteer-core'));
  fs.mkdirSync(output, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true,
  });
  const report = { viewports: [], behavior: {}, browser: await browser.version() };
  try {
    const page = await browser.newPage();
    await page.setRequestInterception(true);
    page.on('request', r => /^(file:|data:|about:)/.test(r.url()) ? r.continue() : r.abort());
    for (const width of [360, 768, 1280, 1920]) {
      await page.setViewport({ width, height: 800 });
      await page.goto(pathToFileURL(path.resolve(html)).href, { waitUntil: 'load' });
      const metrics = await page.evaluate(() => ({
        clientWidth: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        title: document.title,
        searchMargin: document.querySelector('#search') && getComputedStyle(document.querySelector('#search')).marginLeft,
        hasRequiredText: document.body.innerText.includes('자료 · 검색'),
      }));
      report.viewports.push({ width, ...metrics, noOverflow: metrics.scrollWidth <= metrics.clientWidth + 1 });
      await page.screenshot({ path: path.join(output, `${width}.png`), fullPage: true });
    }
    if (await page.$('#q')) {
      await page.type('#q', '하천'); await page.click('#search');
      report.behavior.search = await page.$$eval('#results li', rows => rows.filter(x => !x.hidden).map(x => x.textContent));
      await page.$eval('#q', el => { el.value = ''; });
      await page.select('#category', 'transport'); await page.click('#search');
      report.behavior.filter = await page.$$eval('#results li', rows => rows.filter(x => !x.hidden).map(x => x.textContent));
      await page.type('#email', 'fixture@example.test'); await page.click('#contact button');
      report.behavior.contact = await page.$eval('#status', el => el.textContent);
      await page.focus('#q'); await page.keyboard.press('Tab');
      report.behavior.keyboardNext = await page.evaluate(() => document.activeElement.id);
      await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
      report.behavior.reducedMotion = await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
    }
  } finally { await browser.close(); }
  fs.writeFileSync(path.join(output, 'browser.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
}
main().catch(e => { console.error(e.message); process.exitCode = 1; });
