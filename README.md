# BAF Risk Monitor | Public Sentiment & Risk Intelligence Dashboard

A zero-budget, independent OSINT intelligence and risk monitoring system dedicated exclusively to monitoring publicly available information about **BlockAlgo Frontier Technologies (BAF)**.

---

## 1. System Overview & Core Objectives

**BAF Risk Monitor** is a personal OSINT surveillance and financial-intelligence application built to monitor BAF daily. It identifies warning signs, changes in public sentiment, user complaints, negative news, regulatory developments, and changes to the platform's published terms and policies.

### Primary Principles
* **Zero Commercial Budget:** Built 100% on free and open-source software. Requires zero paid APIs, zero subscriptions, zero commercial LLM tokens, and zero cloud databases.
* **Objective OSINT Evidence Categorization:** Never automatically declares BAF safe, legitimate, fraudulent, or profitable. Distinguishes verified facts, company claims, personal opinions, allegations, and unverified reports.
* **Transparent Source Health:** Never treats a failed collection as "zero complaints." Distinguishes between successful zero-match runs, matching runs, failed sources, and stale datasets.
* **Syndicate & Copy Deduplication:** Uses exact content hashing and 64-bit SimHash near-duplicate clustering to prevent syndicated press releases or copied forum complaints from artificially inflating risk metrics.
* **GitBook Snapshot & Policy Diff Tracking:** Snapshots official BAF documentation and computes unified text diffs whenever terms, fees, withdrawal minimums, or reward structures change.

---

## 2. Monitored Public Sources & Legal Compliance

| Source ID | Source Name | Target URL | Collection Method | Key Required? | Update Frequency | Documented Terms & Coverage Limitations |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `official_baf_docs` | **BAF Official GitBook** | [Introduction](https://baf-1.gitbook.io/baf/platform-overview/readme/introduction), [Root](https://baf-1.gitbook.io/baf/) | HTTP GET / BeautifulSoup text extraction | **No** | Daily | Public documentation pages. Computes SHA-256 hashes and unified text diffs. |
| `gdelt_news` | **GDELT News API** | `api.gdeltproject.org/api/v2/doc/doc` | GDELT 2.0 DOC JSON API | **No** | Daily | Global news database. Public non-commercial use. Handles HTTP 429 rate limits gracefully. |
| `google_news_rss` | **Google News RSS** | `news.google.com/rss/search` | Feedparser RSS XML | **No** | Daily | Public syndication RSS search for `"BlockAlgo"` and `"BlockAlgo Frontier"`. |
| `reddit_discussions`| **Reddit Public Search** | `reddit.com/search.json` | Reddit Public JSON Search | **No** | Daily | Searches public Reddit posts with compliant User-Agent. Captures uncorroborated allegations and user sentiment. |
| `manual_import` | **Regulatory & Manual Uploads**| SEC Philippines / DTI / Judicial Dockets | Web UI Form / Batch CSV Import | **No** | On Demand | Enables ingestion of official government advisories, court filings, and offline tips that lack open automated APIs. |

---

## 3. Technology Stack

* **Language:** Python 3.10+ (Tested on Python 3.13)
* **Web Dashboard:** Streamlit 1.65+
* **Data Visualization:** Plotly 7.1+
* **Data Persistence:** SQLite 3 (ACID compliant, zero cloud dependencies)
* **Local Sentiment Engine:** VADER (`vaderSentiment`) augmented with cryptocurrency risk lexicons
* **Network & Parsers:** `requests`, `beautifulsoup4`, `feedparser`, `python-dateutil`
* **Configuration:** `pyyaml`, `pydantic`
* **Test Suite:** `pytest` (24 automated tests passing)

---

## 4. Project Directory Structure

```
BAF Risk Monitoring & Public Sentiment Intelligence Dashboard/
├── app.py                      # Main Streamlit intelligence dashboard
├── requirements.txt            # Minimal, reproducible dependencies
├── README.md                   # Complete system documentation
├── .env.example                # Environment variables reference
├── .gitignore                  # Git privacy & database protection
├── run_dashboard.bat           # Double-click launcher for the Streamlit UI
├── run_collector.bat           # Launcher for the daily collector script
│
├── config/
│   ├── settings.yaml           # Source endpoints, timeouts, and alert thresholds
│   └── keywords.yaml           # Entity aliases, 10 issue categories & lexicons
│
├── collectors/
│   ├── base.py                 # BaseCollector abstract pipeline & health tracker
│   ├── official_baf.py         # GitBook scraper, content hasher & diff detector
│   ├── gdelt.py                # GDELT Global News 2.0 DOC API connector
│   ├── rss.py                  # Google News and media RSS parser
│   ├── reddit.py               # Compliant Reddit public discussion connector
│   └── manual_import.py        # SEC advisories, manual entry & CSV batch parser
│
├── analysis/
│   ├── sentiment.py            # Local offline VADER sentiment engine
│   ├── classification.py       # Rule-based entity & topic category classifier
│   ├── deduplication.py        # SimHash, content hash & URL normalizer
│   ├── risk_rules.py           # Multi-factor posture & traceable alert engine
│   └── daily_metrics.py        # Daily metrics aggregator (Asia/Manila timezone)
│
├── database/
│   ├── schema.sql              # Normalized SQLite schema with indexes
│   └── repository.py           # Idempotent CRUD, backups, and query repository
│
├── dashboard/
│   ├── overview.py             # Executive posture banner, KPI cards & active alerts
│   ├── charts.py               # Interactive Plotly time-series & category charts
│   ├── latest_findings.py      # Searchable intelligence feed with verification badges
│   ├── sources_status.py       # Connector health monitor & "Run Now" trigger
│   └── evidence_detail.py      # GitBook diff viewer, manual form & CSV exports
│
├── scripts/
│   ├── collect_daily.py        # Standalone scheduler script (idempotent, locked)
│   ├── backup_database.py      # SQLite consistent backup command
│   └── restore_database.py     # SQLite database restoration command
│
├── tests/                      # 24 unit & integration tests
│   ├── test_collectors.py      # Resiliency & error handling tests
│   ├── test_database.py        # DB initialization, idempotency, snapshots
│   ├── test_deduplication.py   # SimHash distance & duplicate group clustering
│   ├── test_risk_rules.py      # Alert triggers & threshold tests
│   └── test_sentiment.py       # Positive, negative, mixed sentiment tests
│
├── data/
│   ├── baf_risk_monitor.db     # Local SQLite database (ignored by git)
│   └── backups/                # Database backup snapshots
│
└── logs/
    └── collector.log           # Daily collection execution logs
```

---

## 5. Windows Installation & Launch Guide

### Step 1: Clone or Navigate to Directory
Open PowerShell or Command Prompt:
```powershell
cd "c:\BAF Risk Monitoring & Public Sentiment Intelligence Dashboard"
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run Initial Collection
Fetch baseline snapshots from BAF GitBook and public news feeds:
```powershell
python scripts\collect_daily.py
```

### Step 5: Start the Dashboard
Launch via the Windows batch script:
```powershell
.\run_dashboard.bat
```
Or directly via Streamlit:
```powershell
streamlit run app.py
```
Open your browser to: **`http://localhost:8501`**

---

## 6. Daily Automation via Windows Task Scheduler

The collector runs completely decoupled from the Streamlit UI. It can run in the background daily at a set time (e.g. 8:00 AM Manila time) while your computer is on.

### Method A: One-Line PowerShell Command (Recommended)
Open PowerShell as Administrator and run:
```powershell
$action = New-ScheduledTaskAction -Execute "C:\BAF Risk Monitoring & Public Sentiment Intelligence Dashboard\run_collector.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "BAFRiskMonitor_DailyCollection" -Description "Daily BAF Public Intelligence & Sentiment Collector"
```

### Method B: Windows Task Scheduler GUI
1. Press `Win + R`, type `taskschd.msc`, and press **Enter**.
2. Click **Create Basic Task...** in the right-hand panel.
3. Name: `BAF Risk Monitor Daily Collection`.
4. Trigger: Select **Daily**, recur every **1 day** at **8:00 AM**.
5. Action: Select **Start a program**.
6. Program/script: Browse to `C:\BAF Risk Monitoring & Public Sentiment Intelligence Dashboard\run_collector.bat`.
7. Start in: `C:\BAF Risk Monitoring & Public Sentiment Intelligence Dashboard`.
8. Click **Finish**.

*Note: The script features process-locking (`data/collector.lock`) to prevent overlapping executions.*

---

## 7. Database Backups, Restores & Data Export

### Automated & Manual Backups
Backups use the native SQLite online backup API to ensure 100% transactional consistency without locking out readers:

```powershell
# Create a timestamped backup in data/backups/
python scripts\backup_database.py
```

### Restore Database
```powershell
# Restore from a previous backup file:
python scripts\restore_database.py data\backups\baf_risk_monitor_backup_YYYYMMDD_HHMMSS.db
```

### CSV / JSON Export
* Through the web dashboard under **📥 Ingestion & Data Export**:
  * Click **Download Raw Observations CSV** for full records with sentiment scores and evidence tags.
  * Click **Download Daily Metrics CSV** for aggregated longitudinal trend data.

---

## 8. Risk Alert Postures & Evidence Classification

### Monitoring States
1. **🛡️ Normal Monitoring:** No acute withdrawal clusters or regulatory enforcement actions identified.
2. **⚠️ Increased Concern:** Elevated complaints (>= 3 payment/deposit issues), official GitBook policy modifications, or prolonged collector failure (> 48h).
3. **🚨 Serious Warning Requiring Investigation:** Critical threshold breach (>= 3 unique withdrawal failure complaints) or official regulatory warning/advisory detected.

### Evidence Status Definitions
* **Official Statement:** Published directly by BAF team on official documentation/domains.
* **Independently Corroborated:** Verified across multiple independent publishers or regulatory registries.
* **Reported Allegation:** Individual complaint, user claim, or forum post alleging non-payment or withholding of funds.
* **Personal Opinion / Testimonial:** Subjective post, referral link promotion, or earnings claim.
* **Unverified:** Public mention without sufficient independent cross-validation.
* **Unable to Verify:** Dead link, missing context, or deleted forum post.

---

## 9. Running Automated Tests

Run the complete test suite:
```powershell
.\venv\Scripts\pytest.exe -v
```
All 24 tests cover database initialization, idempotency, doc diffs, backups/restores, URL normalization, SimHash clustering, sentiment classification, risk rules, collector resilience, manual uploads, and timezone normalization.

---

## 10. Known Limitations & Access Documentation

1. **Reddit Access (HTTP 403 / Rate Limits):** Modern Reddit endpoints require an OAuth User-Agent or Reddit Developer Client ID/Secret for high-volume automated querying. If unauthenticated requests are blocked, use the dashboard's **📥 Manual Intelligence & Regulatory Ingestion** tab to paste relevant threads.
2. **GDELT Rate Limits (HTTP 429):** GDELT DOC API imposes IP-based rate limiting during heavy traffic. The connector logs this transparently and retains existing records.
3. **SEC Philippines & Corporate Registries:** The Philippine SEC public advisory portal requires CAPTCHA verification; direct automated web scraping is disallowed. The **Manual Intelligence Ingestion** interface is specifically built to record verified SEC notices with full audit trails.
