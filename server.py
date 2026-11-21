"""Springboard server.

Serves the docs/ folder (Product Page + app) and forwards the app's AI requests
to OpenRouter, so the API key stays on the server and never reaches the browser.
Uses only the Python standard library: nothing to install.

Local:  python3 server.py   then open http://localhost:8000/app/
Render: start command `python3 server.py`; set OPENROUTER_API_KEY in Render's
        Environment settings (Render provides PORT automatically).
"""
import json, os, re, time, threading, urllib.request, urllib.error
from collections import defaultdict, deque
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent

def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()
KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
PORT = int(os.environ.get("PORT", "8000"))
HOST = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"  # public only on the host

# --- Safety limits (see SECURITY.md)
PER_VISITOR = 20          # AI requests per visitor...
WINDOW = 10 * 60          # ...per 10 minutes
DAILY_TOTAL = 300         # AI requests per day across everyone (spend backstop)
MAX_BODY = 4_000_000      # bytes; a shrunk screenshot is well under this
MAX_PROMPT = 6_000        # characters
MAX_TOKENS = 1_500        # cap on each AI reply

lock = threading.Lock()
hits = defaultdict(deque)
day = {"date": time.strftime("%Y-%m-%d"), "count": 0}

def rate_limited(ip):
    now = time.time()
    with lock:
        q = hits[ip]
        while q and now - q[0] > WINDOW:
            q.popleft()
        if len(q) >= PER_VISITOR:
            return "Too many requests. Wait a few minutes and try again."
        today = time.strftime("%Y-%m-%d")
        if day["date"] != today:
            day.update(date=today, count=0)
        if day["count"] >= DAILY_TOTAL:
            return "The app has reached today's AI limit. Try again tomorrow."
        q.append(now)
        day["count"] += 1
    return None

def key_ok():
    return bool(KEY) and "replace" not in KEY

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT / "docs"), **kw)  # only docs/ is ever served

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "DENY")
        super().end_headers()

    def client_ip(self):
        fwd = self.headers.get("X-Forwarded-For", "")
        return fwd.split(",")[0].strip() if fwd else self.client_address[0]

    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/health":
            return self.send_json(200 if key_ok() else 503, {"ok": key_ok()})
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/ai":
            return self.send_json(404, {"error": "not found"})
        limited = rate_limited(self.client_ip())  # counted before anything else
        if limited:
            return self.send_json(429, {"error": limited})
        if not key_ok():
            return self.send_json(503, {"error": "The AI isn't set up on this server."})
        size = int(self.headers.get("Content-Length", 0) or 0)
        if size <= 0 or size > MAX_BODY:
            return self.send_json(413 if size > MAX_BODY else 400, {"error": "Request too large or empty."})
        try:
            body = json.loads(self.rfile.read(size))
            prompt = str(body["prompt"])[:MAX_PROMPT]
            image = body.get("image")
            if image is not None and not (isinstance(image, str) and image.startswith("data:image/")):
                raise ValueError
            model = MODEL + (":online" if body.get("web") else "")  # :online = OpenRouter web search
        except Exception:
            return self.send_json(400, {"error": "bad request"})
        content = [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image}}] if image else prompt
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps({"model": model, "max_tokens": MAX_TOKENS,
                             "messages": [{"role": "user", "content": content}]}).encode(),
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            print("OpenRouter error", e.code, e.read()[:300])  # details stay in the server log
            msg = "The AI account is out of credit." if e.code == 402 else "The AI service returned an error."
            return self.send_json(502, {"error": msg})
        except Exception as e:
            print("OpenRouter unreachable:", e)
            return self.send_json(502, {"error": "Couldn't reach the AI service."})
        text = data["choices"][0]["message"]["content"] or ""
        usage = data.get("usage", {})
        print(f"AI call: {usage.get('prompt_tokens')} in / {usage.get('completion_tokens')} out tokens")
        m = re.search(r"\[.*\]", text, re.S)  # pull the JSON list out of the reply
        try:
            result = json.loads(m.group(0)) if m else []
        except Exception:
            result = []
        return self.send_json(200, {"result": result})

if __name__ == "__main__":
    print(f"Springboard running: http://localhost:{PORT}/app/  (model: {MODEL})")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
