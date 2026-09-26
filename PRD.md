# 🚀 Autonomous Hostinger Client Acquisition & Cold Outreach Engine
## Product Requirements Document (PRD) & Technical Architecture Specification

**Version:** 1.0.0  
**Target:** 100% Autonomous, Zero-Cost ($0/mo), Client First 2-Step Soft Pitch Funnel  
**Orchestration:** Antigravity AI Agent Engine (Full n8n / Zapier Replacement)

---

## 1. Executive Summary & Core Objective

The system automates the entire client acquisition funnel to earn passive affiliate commissions via the Hostinger referral program (`https://www.hostinger.com/in?REFERRALCODE=YYUADRASHKGH`):
1. **Targeting:** Automatically select categories from the 100 high-intent niches doc (or custom search keywords) and target high-ticket geographic regions (e.g. US, UK, Canada, Australia).
2. **Lead Harvesting & Filtering:** Scrape Google Maps & business websites; automatically discard businesses without emails; prevent contacting duplicates forever.
3. **Auditing:** Analyze live target website response time (TTFB) and site latency to create authentic proof.
4. **Step 1 ("Concerned Customer Hook"):** AI crafts hyper-personalized, non-salesy emails pointing out real loading issues from a customer perspective.
5. **Smart Sending:** Rotate across 5+ Gmail accounts with human-like delays (3-8 mins) to guarantee 0% account bans.
6. **Step 2 (Autonomous Reply Engine):** A background daemon detects incoming client replies, reads their context using Gemini AI, and sends a natural recommendation featuring the Hostinger discount link.
7. **Frontend Experience:** Modern Dark-Mode Canvas (n8n-style animated nodes), Live Progress Stream, Metric Dashboard (Today / 7-Day / 30-Day metrics), Lead Manager, and Settings.

---

## 2. System Architecture & Module Breakdown

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MODERN WEB UI (CANVAS & DASHBOARD)                 │
│  [Visual n8n Canvas]  [Analytics (7d/30d)]  [Leads Table]  [Settings / Gmails] │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ WebSocket / REST API
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    PYTHON AUTONOMOUS BACKEND ORCHESTRATOR                   │
│                                (server.py)                                  │
├───────────────────┬───────────────────┬───────────────────┬─────────────────┤
│ 1. MAPS & WEB     │ 2. SPEED AUDITOR  │ 3. GEMINI AI      │ 4. MULTI-GMAIL  │
│    SCRAPER        │    ENGINE         │    AGENT          │    ROTATOR      │
│  (scraper.py)     │   (auditor.py)    │  (ai_engine.py)   │(email_engine.py)│
└─────────┬─────────┴─────────┬─────────┴─────────┬─────────┴────────┬────────┘
          │                   │                   │                  │
          ▼                   ▼                   ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    5. 24/7 INBOX REPLY LISTENER & AUTO-PITCH                │
│                               (reply_listener.py)                           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│               HYBRID DATABASE (SQLite Local + Supabase Cloud Sync)          │
│                                (database.py)                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Component Specifications

### 3.1 Lead Harvester & Strict Filter (`scraper.py`)
* **Inputs:** Niche Category (pre-loaded with 100 doc categories), Target Location (City/State/Country), Lead Count Target (e.g., 50, 100, 200), Review filter (< 200 reviews).
* **Extraction:**
  - Business Name, Full Address, Phone, Website URL, Rating, Review count.
  - Deep Crawler: Fetches homepage, `/contact`, `/about`, footer links to extract valid business emails (`info@`, `contact@`, `sales@`, `support@`, owner email).
* **Strict Quality Filter:** 
  - If no email is discovered, the lead is **automatically dropped** (never stored in DB as junk).
  - Normalizes email (`lower()`, strip whitespace).
  - Checks Master Database: If email or domain already exists, skips with `DUPLICATE` flag.

### 3.2 Live Website Auditor (`auditor.py`)
* **Function:** Measures Time to First Byte (TTFB), total page load duration, server headers, and SSL status.
* **Outputs:** 
  - Real load time (e.g. `4.2s`).
  - Flagged bottlenecks (e.g., slow TTFB, image bloat, server response lag).
  - Provides authentic ammunition for AI personalization.

### 3.3 Gemini AI Prompt Orchestrator (`ai_engine.py`)
* **Model:** Gemini 2.0 Flash / 1.5 Flash (Free Tier via Google AI Studio).
* **Email 1 ("Concerned Customer Hook"):**
  - High open-rate subjects (e.g., *"Quick question about loading speed on [Business Name]"*).
  - Genuine customer tone: *"Hey [Name/Team], was looking into your services today on [Website], but the page took nearly 4.5 seconds to open and timed out once on mobile. Just wanted to ask if you guys are having server trouble today or if it's on my end?"*
* **Email 2 ("The Casual Recommendation" upon reply):**
  - Reads client's exact reply message.
  - Empathetic follow-up: *"Glad to hear back! Actually it loaded fine after a couple of tries. We had the exact same server bottleneck on our own sites until we moved over to Hostinger (LiteSpeed infrastructure). If your web developer wants to check it out, here is a discount link: [REFERRAL_LINK]. Hope it helps save you some headaches!"*

### 3.4 Multi-Account Gmail Pool (`email_engine.py`)
* **Account Storage:** Supports unlimited accounts (1 to 5+ accounts).
* **Security:** Google App Passwords (16-char code) over SSL/TLS.
* **Sending Strategy:**
  - Strict round-robin dispatching: Email 1 via Account #1, Email 2 via Account #2, etc.
  - Drip pacing: 180 to 420 seconds random delay between dispatches.
  - Daily safety limit: 15-20 emails per account per day.
  - Tracks `Message-ID`, `Thread-ID`, and `Subject` for conversation continuity.

### 3.5 24/7 Autonomous Inbox Listener (`reply_listener.py`)
* **Polling:** Background daemon checks IMAP SSL for each configured Gmail account every 5-10 minutes.
* **Thread Matcher:** Matches incoming `In-Reply-To` and `References` headers against sent threads in `leads.db`.
* **Zero-Human Action:** When reply is confirmed:
  1. AI analyzes sentiment (e.g. apologetic, curious, checking with IT).
  2. Generates tailored Email #2 with referral link.
  3. Sends reply inside the **exact same email thread**.
  4. Updates database status to `REPLIED` and `EMAIL_2_SENT`.

### 3.6 Hybrid Database Layer (`database.py`)
* **Primary:** Local SQLite (`leads.db`) — zero configuration, works instantly.
* **Cloud Sync:** Supabase PostgreSQL adapter — if credentials (`SUPABASE_URL`, `SUPABASE_KEY`) are provided in settings, leads and logs sync to cloud in real time.
* **Schema:**
  - `leads`: id, business_name, email (UNIQUE), website, phone, location, category, ttfb_seconds, status, created_at.
  - `email_logs`: id, lead_id, account_used, step (1 or 2), message_id, thread_id, subject, body, sent_at, open_status.
  - `replies`: id, lead_id, raw_reply_text, ai_reply_text, replied_at.
  - `accounts`: id, email, app_password, daily_sent_count, is_active, last_used_at.
  - `settings`: key, value (Hostinger link, Gemini API key, delay settings, etc.).

---

## 4. Frontend User Experience Specification

### 4.1 Tab 1: n8n-Style Interactive Workflow Canvas
* **Visual Graph:** 7 interactive SVG/Canvas nodes with flowing animated pulses:
  1. `[Niche Category Selector]`
  2. `[Google Maps Harvester]`
  3. `[Domain Tech Auditor]`
  4. `[Gemini Hook Drafter]`
  5. `[Multi-Gmail Rotator]`
  6. `[24/7 Inbox Listener]`
  7. `[Hostinger Pitch Engine]`
* **Real-time Node Badges:** Shows active state (`IDLE`, `RUNNING`, `SUCCESS`) with live metrics per node.
* **Live Progress Bar:** Overall campaign completion percentage (0 - 100%).
* **Live Console Output:** Real-time log stream showing scraper and sender actions line by line.

### 4.2 Tab 2: Analytics & Performance Dashboard
* **KPI Metric Cards:**
  - Total Businesses Scraped
  - Valid Emails Extracted (with Filter Drop-off %)
  - Emails Sent Today
  - Open Rate (%)
  - Reply Rate (%)
  - Hostinger Link Sent Count
* **Timeframe Filters:** Today | Last 7 Days | Last 30 Days | All Time.
* **Funnel Chart:** Visual conversion funnel showing `Scraped` ➔ `Filtered` ➔ `Email 1 Sent` ➔ `Replied` ➔ `Email 2 Sent`.

### 4.3 Tab 3: Leads & Sent History Explorer
* Searchable, paginated table of all leads.
* Columns: Business Name, Category, Website, Email, Status (`New`, `Sent 1`, `Replied`, `Sent 2`), TTFB, Timestamp.
* **"View Conversation" Modal:** Click any lead to see the full email chain (Email 1 sent, Client Reply received, Email 2 sent).
* **Export:** "Export Clean Leads to CSV" button.

### 4.4 Tab 4: Settings & Account Management
* **Gmail Pool Manager:** Add/Remove unlimited Gmail accounts with 1-click "Test Connection" button.
* **Gemini API Key:** Input field with status validator.
* **Hostinger Referral Link:** Pre-populated with `https://www.hostinger.com/in?REFERRALCODE=YYUADRASHKGH`, fully editable.
* **Supabase Cloud Sync:** Optional URL & Anon Key inputs.
* **Sending Delays:** Configurable minimum and maximum delay in seconds.

---

## 5. Verification & Testing Plan

1. **Database & Schema Verification:** Verify SQLite tables creation, unique email constraint, and duplicate rejection.
2. **Scraper & Filter Verification:** Test query (e.g., "Web Agency Miami") to ensure website contact extraction and auto-dropping leads without emails.
3. **Speed Auditor Verification:** Verify TTFB calculation returns true numeric latency within 3 seconds.
4. **Gemini Engine Verification:** Verify Email 1 and Email 2 generation with authentic dynamic insertion of the Hostinger referral link.
5. **Multi-Gmail Rotator Verification:** Test mock/real SMTP dispatch with rotating account selection.
6. **Reply Listener Verification:** Test IMAP polling and matching of reply threads.
7. **Frontend Canvas & Analytics Verification:** Verify responsive layout, animated canvas nodes, live metrics (Today / 7d / 30d), and WebSocket logs.
