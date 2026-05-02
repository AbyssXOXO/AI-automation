# Big Tech Opportunity Bot

FastAPI service that monitors big-company developer opportunities and sends the good ones to Telegram.

1. Fetch items from RSS feeds with `feedparser`.
2. Scrape configured pages with `BeautifulSoup4`.
3. Ask Gemini to decide whether an item is a real opportunity worth your time.
4. Send high-scoring items to your Telegram chat/account ID.
5. Expose HTTP endpoints that Render and Cron-job.org can ping.

By default, the bot is tuned for:

- Google developer events, codelabs, and Skills Boost learning paths
- Microsoft Learn student opportunities, hackathons, and AI challenges
- IBM SkillsBuild and IBM free digital learning pages

## Project Structure

```text
.
+-- app/
|   +-- ai_gatekeeper.py  # Gemini prompt, JSON parsing, relevance scoring
|   +-- config.py         # Environment variable settings
|   +-- defaults.py       # Built-in Google/Microsoft/IBM source targets
|   +-- fetchers.py       # RSS fetching and BeautifulSoup scraping
|   +-- models.py         # Shared dataclasses
|   +-- notifier.py       # Telegram message formatting and sending
|   +-- scanner.py        # Scan loop, dedupe, orchestration
|   +-- server.py         # FastAPI routes and app factory
|   +-- state.py          # Local seen-item state
|   +-- utils.py          # Small shared helpers
+-- main.py               # Render/uvicorn entrypoint
+-- requirements.txt
+-- render.yaml
+-- runtime.txt
```

## Run Locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:

- `http://127.0.0.1:8000/` for health
- `http://127.0.0.1:8000/scan` to run a scan now
- `http://127.0.0.1:8000/ping?scan=true` to scan only when the interval is due
- `http://127.0.0.1:8000/state` to inspect the last scan

## Environment Variables

Copy `.env.example` into your Render dashboard values or your local environment.

Required for AI filtering:

- `GEMINI_API_KEY` or `API_KEY`
- `GEMINI_MODEL`, default `gemini-1.5-flash`

Required for Telegram notifications:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_ACCOUNT_ID` also works as an alias

Source configuration:

- `SCRAPE_TARGETS`: optional JSON override. If you leave it unset, the bot uses the built-in Google/Microsoft/IBM sources.
- `RSS_FEEDS`: optional comma-separated RSS list. Leave it empty unless you want extra sources.

```text
Google Blog=https://blog.google/rss
```

- Example `SCRAPE_TARGETS` override:

```json
[
  {
    "name": "Custom Google Source",
    "url": "https://example.com/news",
    "company": "Google",
    "category": "hackathons",
    "limit": 6
  }
]
```

Filtering:

- `TARGET_COMPANIES`: default `Google, Microsoft, IBM`
- `USER_PROFILE`: personal context for Gemini, for example your interest in Python and AI
- `TOPIC_PROMPT`: what Gemini should consider relevant
- `RELEVANCE_THRESHOLD`: minimum score to notify, default `0.7`
- `MAX_ITEMS_PER_SCAN`: caps Gemini calls per scan
- `MAX_ITEMS_PER_SOURCE`: keeps one source from flooding the scan
- `MAX_TEXT_CHARS`: caps scraped text sent to Gemini

Scheduling:

- `SCAN_INTERVAL_MINUTES`: default `180`
- `RUN_BACKGROUND_LOOP`: default `true`
- `RUN_SCAN_ON_STARTUP`: default `false`

## Render Deployment

Use this start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

The included `render.yaml` contains the same command and required environment variable placeholders.

## Cron-job.org Setup

Render free services can sleep after inactivity. Create a Cron-job.org job that runs every 10 to 14 minutes and pings:

```text
https://your-render-service.onrender.com/ping
```

If you also want the ping to trigger scans when your configured interval has elapsed, use:

```text
https://your-render-service.onrender.com/ping?scan=true&background=true
```

Use `/scan?background=true` when you want every cron hit to start a scan regardless of the interval.

## Telegram Alert Shape

Relevant opportunities are sent in a compact format like:

```text
New Google opportunity
Type: hackathon
Title: Build with Gemini Challenge
Deadline: June 30, 2026
Cost: Free
Prize/Certificate: Free certificate + prizes
Why it matters: Strong match for Python and AI learning.
```
