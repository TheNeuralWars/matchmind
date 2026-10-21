"""Optional Azure AI Foundry / Azure OpenAI client. Falls back to deterministic templates (offline, $0)."""
import json, os, time, urllib.error, urllib.request

def foundry_enabled():
    return bool(os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_DEPLOYMENT"))

def chat(system, user, max_tokens=120, timeout=8):
    """Return model text or None (caller falls back). Never raises."""
    if not foundry_enabled():
        return None
    ep = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    url = f"{ep}/openai/deployments/{os.environ['AZURE_OPENAI_DEPLOYMENT']}/chat/completions?api-version={os.getenv('AZURE_OPENAI_API_VERSION', '2024-10-21')}"
    body = json.dumps({"messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "max_tokens": max_tokens, "temperature": 0.6}).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json", "api-key": os.environ["AZURE_OPENAI_API_KEY"]})
    for attempt in (0, 1):  # one retry on 429 (rate limit), honouring Retry-After up to 3 s
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt:
                _debug(f"HTTP {e.code}")
                return None
            try: wait = float(e.headers.get("Retry-After", "1"))
            except ValueError: wait = 1.0
            time.sleep(min(max(wait, 0.5), 3.0))
        except Exception as e:
            _debug(type(e).__name__)
            return None
    return None

def _debug(msg):
    if os.getenv("MATCHMIND_LLM_DEBUG"):
        import sys; print(f"[llm] fallback: {msg}", file=sys.stderr)
