"""Optional Azure AI Foundry / Azure OpenAI client. Falls back to deterministic templates (offline, $0)."""
import json, os, urllib.request

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
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
