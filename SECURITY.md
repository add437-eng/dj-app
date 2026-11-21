# SECURITY.md — Springboard

**Lane:** Beginner
**App type:** AI app, no database. No sign-in. Sets are saved only in each visitor's own browser (localStorage); the server stores nothing.
**Live URL:** https://dj-app-6xjr.onrender.com/app/

## What I checked and found

| Check | How | Result |
|---|---|---|
| Secret keys in the repo | Searched the repo for `sk-or-`, `sk-ant-`, `sk-proj-`, `sk_live_`, `sb_secret_`, `service_role` and my OpenRouter key | Clean. The key lives only in Render's Environment settings and my local `.env`, which `.gitignore` excludes. |
| Secret keys on the live site | Viewed source of `/`, `/app/` and `/analytics.js` and searched for the same strings | Clean. Only the PostHog `phc_` key appears, which is meant to be public. |
| Rate limit on the AI route | Called `POST /api/ai` 30 times in a row from Terminal with curl (snippet below) | Requests 1–20 returned 400 (empty test body), requests 21–30 returned **429**. See screenshot. |
| Private files reachable over the web | Requested `/.env`, `/../.env`, `/%2e%2e/.env`, `/../server.py` | All 404. The server only serves the `docs/` folder. |
| Spending cap | OpenRouter key has a hard credit limit; server caps each reply at 1,500 tokens and the whole app at 300 AI calls per day | In place. |
| Dependencies | `pip-audit -r requirements.txt` | No third-party packages, so nothing to patch. |
| File storage | Screenshots are sent to the AI and never saved | No storage buckets. |

### Rate-limit test snippet (paste into the browser console on the live `/app/` page)
```js
for (let i = 1; i <= 30; i++) {
  const r = await fetch('/api/ai', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
  console.log(i, r.status);
}
```
The empty body means none of these calls reach the AI, so the test costs nothing.

## Agent security review: what it found and what I fixed
1. **No rate limit on `/api/ai`.** Anyone could call it in a loop and spend my credit. *Fixed:* 20 requests per visitor per 10 minutes, and 300 per day for the whole app; extra requests get a 429 with a friendly message.
2. **No request size limit.** A huge upload could tie up the server. *Fixed:* bodies over 4 MB are refused (413) and prompts are cut to 6,000 characters.
3. **No cap on AI reply length.** *Fixed:* `max_tokens` is 1,500 per call.
4. **Error messages leaked OpenRouter's raw error text to the browser.** *Fixed:* the browser now gets a short generic message; details go to the server log only.
5. **Image field accepted any value.** *Fixed:* it must be a `data:image/...` URL or it's rejected.
6. **No basic security headers.** *Fixed:* added `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` and a `Referrer-Policy`.
7. **AI output shown on the page (XSS risk).** Checked: every AI value is escaped before display, and source links must start with `http(s)://`. No change needed.

## Remaining issues
- The rate limit is kept in memory, so it resets when Render restarts the free server, and someone rotating IP addresses could get around it. The OpenRouter credit limit and the daily cap are the backstops.
- Anyone who knows the URL can use the AI (there's no sign-in). Acceptable for a class demo with the caps above.
- BPM and key data come from AI and web sources and can be wrong; the app labels them "verified", "likely" or "estimate".
- Render's free tier sleeps after inactivity, so the first visit can take ~50 seconds to load.
