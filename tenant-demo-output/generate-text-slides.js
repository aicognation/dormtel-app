// Generates PNG slides for text-only bullet slides using puppeteer
const puppeteer = require(require.resolve('puppeteer', { paths: [require('path').join(process.env.HOME || process.env.USERPROFILE, '.qoder/skills/app-demo-presenter/scripts/node_modules')] }));
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, 'screenshots');
fs.mkdirSync(OUT, { recursive: true });

const slides = [
  {
    file: '01-the-problem.png',
    category: 'CONTEXT',
    title: 'The Problem',
    bullets: [
      'Residents call or text admins just to check their balance',
      'Bill payments require physical visits or manual bank transfers',
      'Maintenance requests are lost in group chats',
      'No visibility into move-out status or contract dates',
      'Admins overwhelmed with repetitive resident inquiries'
    ]
  },
  {
    file: '02-the-solution.png',
    category: 'OVERVIEW',
    title: 'The Solution',
    bullets: [
      'Mobile-first web portal — no app install needed',
      'Instant access to billing history and outstanding balance',
      'Online payments via GCash, Maya, or bank transfer',
      'Maintenance request tracking with real-time status',
      'Self-service move-out scheduling and announcements'
    ]
  },
  {
    file: '14-architecture.png',
    category: 'TECHNICAL',
    title: 'Architecture',
    bullets: [
      'React 18 SPA — standalone from admin portal, mobile-first design',
      'FastAPI backend — async SQLAlchemy, PostgreSQL database',
      'Bottom-tab navigation — 5 tabs: Home, Bills, Pay, Requests, More',
      'Deployed via Docker Compose on VPS — nginx reverse proxy',
      'Live at dormtel.bayanaihan.net/tenant — zero downtime for admin'
    ]
  }
];

function buildHtml(slide) {
  const bulletHtml = slide.bullets.map(b => `
    <li style="display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.07);">
      <span style="color:#3b82f6;font-size:20px;margin-top:2px;flex-shrink:0;">▸</span>
      <span style="font-size:17px;line-height:1.5;color:#e2e8f0;">${b}</span>
    </li>`).join('');

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    width: 390px; height: 844px;
    background: #0f172a;
    font-family: 'Segoe UI', Arial, sans-serif;
    display: flex; flex-direction: column;
    justify-content: center;
    padding: 40px 32px;
    overflow: hidden;
  }
  .category {
    font-size: 11px; font-weight: 700; letter-spacing: 3px;
    color: #3b82f6; text-transform: uppercase; margin-bottom: 14px;
  }
  .title {
    font-size: 28px; font-weight: 700; color: #f1f5f9;
    margin-bottom: 28px; line-height: 1.2;
  }
  .title span { color: #3b82f6; }
  ul { list-style: none; }
  .dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #3b82f6; flex-shrink: 0; margin-top: 8px;
  }
</style>
</head>
<body>
  <div class="category">${slide.category}</div>
  <div class="title">${slide.title === 'Architecture' ? '<span>Tech</span> Architecture' : slide.title}</div>
  <ul>${bulletHtml}</ul>
</body>
</html>`;
}

(async () => {
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });

  for (const slide of slides) {
    const html = buildHtml(slide);
    await page.setContent(html, { waitUntil: 'networkidle0' });
    const outPath = path.join(OUT, slide.file);
    await page.screenshot({ path: outPath, fullPage: false });
    console.log(`Saved: ${slide.file}`);
  }

  await browser.close();
  console.log('Done.');
})();
