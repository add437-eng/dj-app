# AGENTS.md — Coding Agent Operating Manual

> Give this file to your coding agent and check that it is using these instructions. Keep the stack, commands, and ground rules current.

## 1. Project Overview
- **What this repo builds:** Springboard, a DJ set builder. Pick a starting song and it builds a set that flows by Camelot key, tempo and style, explains every transition, and can ask an AI model for real songs to fill gaps.
- **Primary user & core workflow:** Beginner/intermediate DJs. See the living PRD in `docs/index.html`.
- **Tech stack:** Plain HTML/CSS/JS (no build step) + Python 3 standard-library server + OpenRouter API + PostHog analytics.

## 2. Project Structure
```
docs/index.html      Product Page (PRD, build log). Published by GitHub Pages.
docs/app/index.html  The app (Springboard). Single file: styles, data and logic.
docs/analytics.js    PostHog setup, shared by both pages. Holds the public phc_ key.
server.py            Local server: serves docs/ and forwards /api/ai to OpenRouter.
.env                 Your private OpenRouter key (never committed). Copy from .env.example.
```
- The AI request flow: app button "Find tracks for this gap" → `POST /api/ai {prompt}` → `server.py` → OpenRouter → JSON list of songs → shown in the app.
- `GET /api/health` tells the app whether the AI is available. On GitHub Pages there is no server, so the AI button hides itself.

## 3. Commands
- **Install dependencies:** none (Python 3 standard library only).
- **Set up:** `cp .env.example .env`, then put your OpenRouter key in `.env`.
- **Run locally:** `python3 server.py`, then open http://localhost:8000/app/ (Product Page at http://localhost:8000/).
- **Run deterministic tests:** none yet. Manual check: pick a starting song, click "Find tracks for this gap", confirm songs appear and the terminal prints the token count.
- **Run model evals:** not yet (Build 4).

## 4. Non-Negotiable Engineering Rules
1. **Plan before coding:** Before touching multiple files, propose a brief plan and wait for approval.
2. **Small batches:** Make small, focused changes that can be reviewed and explained by a human in a single Pull Request.
3. **Explainability:** Avoid unnecessary abstractions or dependencies. Help the human builder understand the main components, what changed, why it matters, what could break, and how it was checked.
4. **Verify changes:** Run relevant checks. For a reproducible logic bug, use a failing test to demonstrate the fix when practical. Record manual checks and known limitations; follow the selected Build 4 evaluation track.
5. **Zero secrets in code:** Never hardcode API keys, tokens, or credentials. Always read from environment variables (`.env`) and update `.env.example` when new variables are needed. The PostHog `phc_` key is public and may be committed.
6. **Stop when looping:** If a fix fails twice in a row, stop, summarize what failed, and ask the human before trying a third approach.
