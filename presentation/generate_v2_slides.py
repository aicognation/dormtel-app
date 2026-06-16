"""Generate the v2 slides HTML with embedded screenshots."""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOTS_B64 = os.path.join(BASE_DIR, 'v2', 'screenshots_b64.json')
OUTPUT = os.path.join(BASE_DIR, 'v2-slides.html')

with open(SCREENSHOTS_B64) as f:
    screenshots = json.load(f)

# CSS styles
CSS = '''
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap");

:root {
  --navy: #1B2A6B;
  --navy-dark: #0F1B4A;
  --gold: #FFD600;
  --gold-light: #FFF3B0;
  --white: #FFFFFF;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: "Inter", -apple-system, sans-serif;
  background: var(--navy-dark);
  width: 1920px;
  height: 1080px;
  overflow: hidden;
}

.slide {
  width: 1920px;
  height: 1080px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

/* Title slide */
.slide-title {
  background: linear-gradient(135deg, var(--navy-dark) 0%, var(--navy) 50%, #2A3F8B 100%);
  justify-content: center;
  align-items: center;
  text-align: center;
  color: var(--white);
}
.slide-title .logo { font-size: 80px; font-weight: 900; letter-spacing: -2px; margin-bottom: 8px; }
.slide-title .logo span { color: var(--gold); }
.slide-title .tagline { font-size: 32px; font-weight: 300; color: rgba(255,255,255,0.7); margin-bottom: 60px; }
.slide-title .subtitle { font-size: 28px; font-weight: 500; color: var(--gold); border: 2px solid var(--gold); padding: 16px 40px; border-radius: 50px; }

/* Content slides */
.slide-content {
  background: linear-gradient(180deg, var(--navy-dark) 0%, var(--navy) 100%);
  padding: 80px 100px;
  color: var(--white);
}
.slide-content .accent-bar { width: 80px; height: 6px; background: var(--gold); border-radius: 3px; margin-bottom: 24px; }
.slide-content .slide-label { font-size: 16px; font-weight: 600; text-transform: uppercase; letter-spacing: 3px; color: var(--gold); margin-bottom: 12px; }
.slide-content .slide-heading { font-size: 52px; font-weight: 800; line-height: 1.1; margin-bottom: 50px; }

/* Problem list */
.problem-list { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; max-width: 1400px; }
.problem-item { display: flex; align-items: flex-start; gap: 20px; padding: 28px 32px; background: rgba(255,255,255,0.05); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); }
.problem-icon { width: 48px; height: 48px; background: rgba(255,65,54,0.15); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; }
.problem-text h4 { font-size: 20px; font-weight: 700; margin-bottom: 6px; }
.problem-text p { font-size: 16px; color: rgba(255,255,255,0.6); line-height: 1.4; }

/* Modules grid */
.modules-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 24px; }
.module-card { padding: 32px 24px; background: rgba(255,255,255,0.06); border-radius: 20px; border: 1px solid rgba(255,255,255,0.12); text-align: center; }
.module-card .module-num { font-size: 42px; font-weight: 900; color: var(--gold); margin-bottom: 12px; }
.module-card h4 { font-size: 18px; font-weight: 700; margin-bottom: 8px; }
.module-card p { font-size: 14px; color: rgba(255,255,255,0.6); line-height: 1.4; }

/* Tech grid */
.tech-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 28px; margin-top: 20px; }
.tech-card { padding: 36px 28px; background: rgba(255,255,255,0.06); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); text-align: center; }
.tech-card .tech-icon { font-size: 40px; margin-bottom: 16px; }
.tech-card h4 { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
.tech-card p { font-size: 15px; color: rgba(255,255,255,0.6); line-height: 1.4; }

/* Screenshot slides */
.slide-screenshot {
  background: linear-gradient(180deg, var(--navy-dark) 0%, var(--navy) 100%);
  padding: 60px 80px;
  color: var(--white);
  display: flex;
  flex-direction: column;
}
.slide-screenshot .accent-bar { width: 80px; height: 6px; background: var(--gold); border-radius: 3px; margin-bottom: 20px; }
.slide-screenshot .slide-label { font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 3px; color: var(--gold); margin-bottom: 8px; }
.slide-screenshot .slide-heading { font-size: 40px; font-weight: 800; line-height: 1.1; margin-bottom: 40px; }
.screenshot-layout { display: grid; grid-template-columns: 42% 55%; gap: 50px; flex: 1; align-items: center; }
.callout-panel { display: flex; flex-direction: column; gap: 20px; }
.callout-item { display: flex; align-items: flex-start; gap: 16px; padding: 18px 22px; background: rgba(255,255,255,0.05); border-radius: 14px; border-left: 4px solid var(--gold); }
.callout-bullet { width: 32px; height: 32px; background: var(--gold); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 14px; color: var(--navy-dark); flex-shrink: 0; }
.callout-text { font-size: 17px; line-height: 1.5; color: rgba(255,255,255,0.9); }
.callout-text strong { color: var(--white); }
.screenshot-panel { position: relative; }
.screenshot-panel img { width: 100%; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.1); }
.live-badge { position: absolute; top: 16px; right: 16px; background: #22C55E; color: white; font-size: 12px; font-weight: 700; padding: 6px 14px; border-radius: 20px; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 2px 8px rgba(34,197,94,0.4); }
.module-badge { position: absolute; bottom: 30px; left: 80px; background: rgba(255,214,0,0.15); border: 1px solid var(--gold); color: var(--gold); font-size: 13px; font-weight: 700; padding: 8px 20px; border-radius: 20px; text-transform: uppercase; letter-spacing: 2px; }

/* Data slide */
.data-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; max-width: 1200px; }
.data-card { padding: 40px; background: rgba(255,255,255,0.06); border-radius: 20px; border: 1px solid rgba(255,255,255,0.12); text-align: center; }
.data-card .data-value { font-size: 56px; font-weight: 900; color: var(--gold); margin-bottom: 8px; }
.data-card .data-label { font-size: 18px; color: rgba(255,255,255,0.7); }
.data-note { margin-top: 40px; font-size: 16px; color: rgba(255,255,255,0.5); font-style: italic; }

/* Summary/Benefits */
.benefits-list { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 50px; }
.benefit-item { display: flex; align-items: center; gap: 16px; font-size: 22px; font-weight: 500; }
.benefit-check { width: 36px; height: 36px; background: var(--gold); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; color: var(--navy-dark); flex-shrink: 0; }
.live-url { font-size: 28px; color: var(--gold); font-weight: 600; padding: 20px 40px; border: 2px solid var(--gold); border-radius: 16px; display: inline-block; }

/* Close slide */
.slide-close { background: linear-gradient(135deg, var(--navy-dark) 0%, var(--navy) 50%, #2A3F8B 100%); justify-content: center; align-items: center; text-align: center; color: var(--white); }
.close-heading { font-size: 56px; font-weight: 800; margin-bottom: 30px; }
.close-subtext { font-size: 24px; color: rgba(255,255,255,0.7); margin-bottom: 50px; max-width: 700px; }
.close-url { font-size: 32px; color: var(--gold); font-weight: 700; margin-bottom: 20px; }
.close-thanks { font-size: 20px; color: rgba(255,255,255,0.5); margin-top: 40px; }
'''

# Slide content definitions
SCREENSHOT_SLIDES = [
    {
        'id': '05', 'label': 'Module Overview', 'heading': 'Operations Dashboard',
        'img': 'dashboard',
        'callouts': [
            ("Today's Revenue", "Real-time total from all payment channels (&#8369;41,015 today)"),
            ('Inquiry Count', 'New inquiries awaiting response across all channels'),
            ('Occupancy Metrics', 'Total reservations and scheduled move-ins at a glance'),
            ('Quick Actions', 'One-click navigation to any task: billing, inquiries, DSR'),
        ],
        'badge': 'Dashboard'
    },
    {
        'id': '06', 'label': 'Module 1', 'heading': 'Smart Inquiry Hub',
        'img': 'inquiries-list',
        'callouts': [
            ('Multi-Channel Capture', 'Facebook, Instagram, TikTok, walk-ins, and phone'),
            ('AI Sentiment Score', 'Automatic tone analysis rates each message 0&ndash;1'),
            ('Lead Priority Score', 'Scoring from 0&ndash;100 prioritizes follow-up order'),
            ('Pipeline Status', 'Track: New, Responded, Escalated, Converted'),
        ],
        'badge': 'Module 1'
    },
    {
        'id': '07', 'label': 'Module 1', 'heading': 'Create New Inquiry',
        'img': 'inquiries-modal',
        'callouts': [
            ('Source Channel', 'Select the channel where the inquiry originated'),
            ('Message Content', 'Paste the actual inquiry message for AI analysis'),
            ('Auto-Scoring', 'System automatically calculates sentiment and lead score'),
            ('Instant Pipeline', 'New inquiries enter the pipeline immediately'),
        ],
        'badge': 'Module 1'
    },
    {
        'id': '08', 'label': 'Module 2', 'heading': 'Digital Onboarding &mdash; Rooms',
        'img': 'onboarding-rooms',
        'callouts': [
            ('25 Rooms, 3 Buildings', 'Tower A, Tower B, Tower C with capacity tracking'),
            ('Live Occupancy', 'See occupied beds vs capacity for every room'),
            ('Rate Per Bed', 'Monthly rates displayed for instant quoting'),
            ('Room Status', 'Available, occupied, and maintenance states'),
        ],
        'badge': 'Module 2'
    },
    {
        'id': '09', 'label': 'Module 2', 'heading': 'New Reservation Form',
        'img': 'onboarding-modal',
        'callouts': [
            ('Smart Room Search', 'Type to filter rooms by number or building name'),
            ('ID Verification', 'Government ID type and number captured digitally'),
            ('Auto Payment Link', 'GCash/Maya payment link generated on submission'),
            ('One-Click Activation', 'Convert reservation to active resident instantly'),
        ],
        'badge': 'Module 2'
    },
    {
        'id': '10', 'label': 'Module 3', 'heading': 'Auto-Billing Engine',
        'img': 'billing-list',
        'callouts': [
            ('Period-Based Billing', 'Monthly billing cycles with full charge breakdown'),
            ('Itemized Charges', 'Rent + Electric + Water + Other clearly separated'),
            ('Status Workflow', 'Draft, Pending Approval, Distributed, Paid'),
            ('Variance Detection', 'Flags unusual consumption for manager review'),
        ],
        'badge': 'Module 3'
    },
    {
        'id': '11', 'label': 'Module 3', 'heading': 'Generate Billing',
        'img': 'billing-modal',
        'callouts': [
            ('Building Filter', 'Generate for specific building or all buildings'),
            ('Meter Readings', 'Enter electric and water totals for auto-split'),
            ('Proportional Split', 'System divides utility costs across all residents'),
            ('Approval Required', 'Manager must approve before distribution'),
        ],
        'badge': 'Module 3'
    },
    {
        'id': '12', 'label': 'Module 4', 'heading': 'Payment Reconciliation &mdash; DSR',
        'img': 'payments-dsr',
        'callouts': [
            ('Daily Sales Report', 'Real-time revenue: &#8369;41,015 from 5 transactions today'),
            ('Multi-Gateway Support', 'GCash, Maya, bank transfers, and cash'),
            ('Unmatched Payments', 'Flagged payments awaiting resident matching'),
            ('Auto-Reconciliation', 'Webhook payments matched instantly to billings'),
        ],
        'badge': 'Module 4'
    },
    {
        'id': '13', 'label': 'Module 4', 'heading': 'Match Payment',
        'img': 'payments-modal',
        'callouts': [
            ('Resident Selection', 'Link payment to the correct resident account'),
            ('Billing Match', 'Associate with specific billing period'),
            ('Gateway Reference', 'Original transaction ID preserved for audit'),
            ('Instant DSR Update', 'Matched payments immediately reflect in reports'),
        ],
        'badge': 'Module 4'
    },
    {
        'id': '14', 'label': 'Module 5', 'heading': 'Move-Out Settlement',
        'img': 'moveouts-list',
        'callouts': [
            ('Structured Pipeline', 'Request, Clearance, Final Billing, Complete'),
            ('Resident Details', 'Name, room, dates, and reason tracked'),
            ('Action Buttons', 'Progress each move-out through workflow stages'),
            ('Full Audit Trail', 'Every step logged with timestamps'),
        ],
        'badge': 'Module 5'
    },
    {
        'id': '15', 'label': 'Module 5', 'heading': 'Create Move-Out Request',
        'img': 'moveouts-modal',
        'callouts': [
            ('Resident Selection', 'Choose from active residents with room details'),
            ('Move-Out Date', 'Scheduled date for vacancy planning'),
            ('Reason Tracking', 'Categories: graduation, relocation, personal, etc.'),
            ('Auto-Clearance', 'System generates room inspection checklist'),
        ],
        'badge': 'Module 5'
    },
]

def build_html():
    parts = []
    parts.append(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1920, height=1080">
<title>DormTel Stakeholder Demo</title>
<style>{CSS}</style>
</head>
<body>
''')

    # Slide 01: Title
    parts.append('''
<section class="slide slide-title" id="slide-01">
  <div class="logo">Dorm<span>Tel</span></div>
  <div class="tagline">My Dorm, My Home</div>
  <div style="font-size:24px; color:rgba(255,255,255,0.5); margin-bottom:40px;">Dormitory Operations Automation Platform</div>
  <div class="subtitle">Stakeholder Demo &mdash; May 2026</div>
</section>
''')

    # Slide 02: Problem
    parts.append('''
<section class="slide slide-content" id="slide-02">
  <div class="accent-bar"></div>
  <div class="slide-label">The Challenge</div>
  <div class="slide-heading">Why Dormitory Operators<br>Need Automation</div>
  <div class="problem-list">
    <div class="problem-item">
      <div class="problem-icon">&#x1F4F1;</div>
      <div class="problem-text"><h4>Scattered Inquiries</h4><p>Leads lost across Facebook, Instagram, TikTok, walk-ins, and phone calls</p></div>
    </div>
    <div class="problem-item">
      <div class="problem-icon">&#x1F4CA;</div>
      <div class="problem-text"><h4>Billing Errors</h4><p>Manual spreadsheet calculations with electric, water, and rent splits</p></div>
    </div>
    <div class="problem-item">
      <div class="problem-icon">&#x1F4B8;</div>
      <div class="problem-text"><h4>Payment Chaos</h4><p>Reconciling GCash, Maya, bank transfers takes hours daily</p></div>
    </div>
    <div class="problem-item">
      <div class="problem-icon">&#x1F441;</div>
      <div class="problem-text"><h4>Zero Visibility</h4><p>No real-time view of occupancy, revenue, or pending tasks</p></div>
    </div>
    <div class="problem-item" style="grid-column: span 2; max-width: 50%; margin: 0 auto;">
      <div class="problem-icon">&#x1F4DD;</div>
      <div class="problem-text"><h4>Manual Move-Outs</h4><p>Clearance, final billing, and refunds lost in chat threads and paperwork</p></div>
    </div>
  </div>
</section>
''')

    # Slide 03: Solution
    parts.append('''
<section class="slide slide-content" id="slide-03">
  <div class="accent-bar"></div>
  <div class="slide-label">The Solution</div>
  <div class="slide-heading">5 Integrated Modules</div>
  <div class="modules-grid">
    <div class="module-card"><div class="module-num">1</div><h4>Smart Inquiry Hub</h4><p>Multi-channel capture, AI scoring, pipeline tracking</p></div>
    <div class="module-card"><div class="module-num">2</div><h4>Digital Onboarding</h4><p>Room search, reservation, payment links, activation</p></div>
    <div class="module-card"><div class="module-num">3</div><h4>Auto-Billing Engine</h4><p>Meter readings, split calculations, approval workflow</p></div>
    <div class="module-card"><div class="module-num">4</div><h4>Payment Gateway</h4><p>GCash/Maya webhooks, auto-reconciliation, DSR</p></div>
    <div class="module-card"><div class="module-num">5</div><h4>Move-Out Settlement</h4><p>Clearance, final billing, refund tracking, audit trail</p></div>
  </div>
</section>
''')

    # Slide 04: Tech
    parts.append('''
<section class="slide slide-content" id="slide-04">
  <div class="accent-bar"></div>
  <div class="slide-label">Technology</div>
  <div class="slide-heading">Built for Philippine Dormitories</div>
  <div class="tech-grid">
    <div class="tech-card"><div class="tech-icon">&#x26A1;</div><h4>FastAPI Backend</h4><p>Python 3.12 async API with PostgreSQL 15 + Redis caching</p></div>
    <div class="tech-card"><div class="tech-icon">&#x1F3A8;</div><h4>React Frontend</h4><p>Modern responsive UI accessible from any device</p></div>
    <div class="tech-card"><div class="tech-icon">&#x1F4B3;</div><h4>Payment Webhooks</h4><p>Direct GCash &amp; Maya integration for instant reconciliation</p></div>
    <div class="tech-card"><div class="tech-icon">&#x2601;</div><h4>Cloud Deployed</h4><p>Docker containers on secure VPS with automated backups</p></div>
  </div>
</section>
''')

    # Slides 05-15: Screenshot slides
    for slide in SCREENSHOT_SLIDES:
        callout_html = ''
        for i, (title, desc) in enumerate(slide['callouts'], 1):
            callout_html += f'''
        <div class="callout-item">
          <div class="callout-bullet">{i}</div>
          <div class="callout-text"><strong>{title}</strong><br>{desc}</div>
        </div>'''

        img_data = screenshots[slide['img']]
        parts.append(f'''
<section class="slide slide-screenshot" id="slide-{slide['id']}">
  <div class="accent-bar"></div>
  <div class="slide-label">{slide['label']}</div>
  <div class="slide-heading">{slide['heading']}</div>
  <div class="screenshot-layout">
    <div class="callout-panel">{callout_html}
    </div>
    <div class="screenshot-panel">
      <img src="{img_data}" alt="{slide['heading']}">
      <div class="live-badge">&#x1F7E2; LIVE</div>
    </div>
  </div>
  <div class="module-badge">{slide['badge']}</div>
</section>
''')

    # Slide 16: Data
    parts.append('''
<section class="slide slide-content" id="slide-16">
  <div class="accent-bar"></div>
  <div class="slide-label">Live Production</div>
  <div class="slide-heading">Real Data, Real Results</div>
  <div class="data-grid">
    <div class="data-card"><div class="data-value">25</div><div class="data-label">Rooms Managed</div></div>
    <div class="data-card"><div class="data-value">18</div><div class="data-label">Active Residents</div></div>
    <div class="data-card"><div class="data-value">12</div><div class="data-label">Inquiries in Pipeline</div></div>
    <div class="data-card"><div class="data-value">&#8369;41K</div><div class="data-label">Today&#39;s Revenue</div></div>
    <div class="data-card"><div class="data-value">5</div><div class="data-label">Transactions Today</div></div>
    <div class="data-card"><div class="data-value">3</div><div class="data-label">Buildings</div></div>
  </div>
  <div class="data-note">Data captured from live production system &mdash; May 18, 2026</div>
</section>
''')

    # Slide 17: Summary
    parts.append('''
<section class="slide slide-content" id="slide-17">
  <div class="accent-bar"></div>
  <div class="slide-label">Summary</div>
  <div class="slide-heading">Ready to Deploy</div>
  <div class="benefits-list">
    <div class="benefit-item"><div class="benefit-check">&#x2713;</div>Eliminates manual spreadsheet billing</div>
    <div class="benefit-item"><div class="benefit-check">&#x2713;</div>Real-time payment reconciliation</div>
    <div class="benefit-item"><div class="benefit-check">&#x2713;</div>Multi-channel inquiry capture with AI</div>
    <div class="benefit-item"><div class="benefit-check">&#x2713;</div>Complete audit trail for compliance</div>
    <div class="benefit-item"><div class="benefit-check">&#x2713;</div>Accessible from any device, anywhere</div>
    <div class="benefit-item"><div class="benefit-check">&#x2713;</div>GCash &amp; Maya webhook integration</div>
  </div>
  <div class="live-url">dormtel.quriosity.cloud</div>
</section>
''')

    # Slide 18: Close
    parts.append('''
<section class="slide slide-close" id="slide-18">
  <div class="close-heading">Thank You</div>
  <div class="close-subtext">We welcome your questions, feedback, and next steps discussion.</div>
  <div class="close-url">dormtel.quriosity.cloud</div>
  <div style="font-size:18px; color:rgba(255,255,255,0.5); margin-top:16px;">Live demo available for hands-on exploration</div>
  <div class="close-thanks">DormTel &mdash; My Dorm, My Home</div>
</section>
''')

    parts.append('</body>\n</html>\n')
    return ''.join(parts)


if __name__ == '__main__':
    html = build_html()
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Created {OUTPUT}")
    print(f"Size: {len(html) // 1024}KB")
    print(f"Slides: 18 (4 text + 11 screenshot + 3 closing)")
