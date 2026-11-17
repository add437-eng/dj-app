"""Springboard local server.

Serves the docs/ folder (Product Page + app) and forwards the app's AI requests
to OpenRouter, so the API key stays on your laptop and never reaches the browser.
Uses only the Python standard library: nothing to install.

Run:  python3 server.py   then open http://localhost:8000/app/
"""
import json, os, re, urllib.request, urllib.error
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

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT / "docs"), **kw)

    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/health":
            return self.send_json(200 if KEY and "replace" not in KEY else 503,
                                  {"ok": bool(KEY), "model": MODEL})
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/ai":
            return self.send_json(404, {"error": "not found"})
        if not KEY or "replace" in KEY:
            return self.send_json(503, {"error": "Add OPENROUTER_API_KEY to .env"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            prompt = body["prompt"]
            image = body.get("image")  # optional data URL (playlist screenshot)
            model = MODEL + (":online" if body.get("web") else "")  # :online = OpenRouter web search
        except Exception:
            return self.send_json(400, {"error": "bad request"})
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps({"model": model, "messages": [{"role": "user", "content":
                [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image}}] if image else prompt}]}).encode(),
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            return self.send_json(e.code, {"error": e.read().decode()[:300]})
        except Exception as e:
            return self.send_json(502, {"error": str(e)})
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        print(f"AI call: {usage.get('prompt_tokens')} in / {usage.get('completion_tokens')} out tokens")
        m = re.search(r"\[.*\]", text, re.S)  # pull the JSON list out of the reply
        try:
            result = json.loads(m.group(0)) if m else []
        except Exception:
            result = []
        return self.send_json(200, {"result": result})

if __name__ == "__main__":
    print(f"Springboard running: http://localhost:8000/app/  (model: {MODEL})")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
