/* Optional browser QA for the committed synthetic report. Requires Playwright. */
const { chromium } = require('playwright');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const report = path.resolve(process.argv[2] || 'docs/demo-report.html');
  const output = path.dirname(report);
  const launch = { headless: true };
  if (process.env.GTMKIT_BROWSER_CHANNEL) launch.channel = process.env.GTMKIT_BROWSER_CHANNEL;
  const browser = await chromium.launch(launch);
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1050 }, deviceScaleFactor: 1 });
    const errors = [], requests = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.route('**/*', async route => {
      if (route.request().url().startsWith('file:')) return route.continue();
      requests.push(route.request().url());
      await route.abort();
    });
    await page.goto(pathToFileURL(report).href);
    await page.screenshot({ path: path.join(output, 'demo-report.png') });
    const total = await page.locator('.record').count();
    await page.selectOption('#status', 'qualified');
    const qualified = await page.locator('.record:visible').count();
    await page.selectOption('#contact', 'suppressed');
    const suppressed = await page.locator('.record:visible').count();
    await page.fill('#search', 'no matching company');
    const empty = await page.locator('#empty').isVisible();
    await page.fill('#search', '');
    await page.selectOption('#status', '');
    await page.selectOption('#contact', '');
    await page.locator('.inspection summary').first().click();
    const expanded = await page.locator('.inspection[open]').count();
    await page.screenshot({ path: path.join(output, 'demo-evidence.png') });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.evaluate(() => scrollTo(0, 0));
    await page.waitForTimeout(250);
    await page.screenshot({ path: path.join(output, 'demo-mobile.png') });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    console.log(JSON.stringify({ total, qualified, suppressed, empty, expanded, mobileOverflow: overflow, errors, externalRequests: requests }, null, 2));
    if (total !== 90 || qualified !== 31 || suppressed !== 2 || !empty || expanded !== 1 || overflow || errors.length || requests.length) process.exitCode = 1;
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
