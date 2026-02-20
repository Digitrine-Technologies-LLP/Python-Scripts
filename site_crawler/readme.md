# 🔍 Site Link Crawler

A Python script that crawls all links on a website and reports their HTTP status codes, saving results to a CSV file.

---

## Features

- BFS (breadth-first) crawl starting from any URL
- Stays on the same domain by default
- Detects broken links (404, 410), server errors (5xx), and rate limits (429)
- Auto-retries on transient failures with exponential backoff
- Browser-like headers to reduce bot-blocking
- Random request jitter to avoid rate limits
- Clean CSV output with URL, status code, and label
- Broken URL summary printed at the end

---

## Requirements

- Python 3.10+
- [requests](https://pypi.org/project/requests/)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)

Install dependencies:

```bash
pip install requests beautifulsoup4
```

---

## Usage

**Basic:**
```bash
python site_crawler.py https://example.com
```

**With options:**
```bash
python site_crawler.py https://example.com --output results.csv --max-pages 500 --delay 2
```

**Include external links:**
```bash
python site_crawler.py https://example.com --external
```

---

## Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--output` | `-o` | `site_<domain>_<date>.csv` | Output CSV filename |
| `--max-pages` | `-m` | `200` | Maximum number of pages to crawl |
| `--delay` | `-d` | `1.0` | Seconds to wait between requests |
| `--timeout` | `-t` | `10` | Request timeout in seconds |
| `--external` | — | off | Also check (but not crawl) external links |

---

## Output

Results are saved to a CSV file with three columns:

| Column | Description |
|--------|-------------|
| `url` | The full URL that was checked |
| `status_code` | HTTP status code (e.g. 200, 404). `0` = connection error or timeout |
| `label` | Human-readable description of the status |

A summary is also printed to the terminal at the end of each run:

```
── Summary ──────────────────────────────────
  ✅ OK: 142
  ↪️  Redirect: 8
  ❌ Client Error: 3
  Total: 153
─────────────────────────────────────────────

🚨 Broken / Error URLs:
   [404] https://example.com/old-page
   [404] https://example.com/missing-resource
```

---

## Status Code Reference

| Code | Label | Meaning |
|------|-------|---------|
| 200 | ✅ OK | Page loaded successfully |
| 301 / 302 | ↪️ Redirect | Page has moved |
| 400 | ❌ Bad Request | Malformed URL |
| 401 | 🔒 Unauthorized | Login required |
| 403 | 🚫 Forbidden | Access denied — may be bot-blocked |
| 404 | ❌ Not Found | Broken link |
| 410 | ❌ Gone | Page permanently removed |
| 429 | ⏳ Rate Limited | Too many requests — increase `--delay` |
| 500 | ⚠️ Server Error | Site-side error |
| 0 | ⏱ Timeout/Error | Could not connect |

---

## Tips for Reducing Client Errors

- **403 Forbidden** — The site is blocking automated requests. The script already uses browser-like headers, but some sites (e.g. Cloudflare-protected) block all bots regardless. These 403s are intentional and cannot be bypassed with a simple HTTP client.
- **429 Rate Limited** — Increase the delay: `--delay 3` or higher.
- **Timeouts** — Increase the timeout: `--timeout 20`.
- **Large sites** — Use `--max-pages` to cap the crawl and run in batches.

---