"""Run the real demo commands and write animated 'terminal' HTML pages (typed command, then its real output) for screen recording."""
import html, json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "media")
MCP_REQ = '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_score","arguments":{"seed":8,"minute":70}}}'
SESSIONS = {
    "term-dataset": [
        ("python -m matchmind.dataset --out data/ --seeds 0-199 --random-styles", None),
        ("head -c 600 data/events.jsonl", None),
        ("wc -l data/events.csv", None),
    ],
    "term-mcp": [
        ("printf '%s\\n' '" + MCP_REQ + "' | python -m matchmind.mcp_server", None),
        ("python -m matchmind.cli --lang es | tail -3", None),
    ],
}
PAGE = """<!doctype html><meta charset=utf-8><body style="margin:0;background:#0d1117;color:#c9d1d9;font:19px/1.45 'DejaVu Sans Mono',monospace">
<div style="background:#161b22;padding:10px 18px;color:#8b949e;font-size:16px">● ● ●&nbsp;&nbsp; matchmind — bash</div><pre id=t style="margin:0;padding:18px 22px;white-space:pre-wrap;word-break:break-all"></pre>
<script>const S=%s;const t=document.getElementById('t');let i=0;
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
async function run(){for(const [cmd,out] of S){t.innerHTML+='<span style="color:#7ee787">$ </span>';
 for(const ch of cmd){t.innerHTML+=esc(ch);await new Promise(r=>setTimeout(r,28))}
 await new Promise(r=>setTimeout(r,450));t.innerHTML+='\\n<span style="color:#d2a8ff">'+esc(out)+'</span>\\n';await new Promise(r=>setTimeout(r,2600))}}
setTimeout(run,600)</script>"""

def main():
    os.makedirs(OUT, exist_ok=True)
    shim = os.path.join(OUT, ".bin"); os.makedirs(shim, exist_ok=True)       # `python` -> current interpreter
    link = os.path.join(shim, "python")
    if not os.path.exists(link): os.symlink(sys.executable, link)
    env = dict(os.environ, PATH=shim + os.pathsep + os.environ.get("PATH", ""))
    for name, steps in SESSIONS.items():
        done = []
        for cmd, _ in steps:
            res = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=300, env=env)
            out = (res.stdout + res.stderr).strip()
            if len(out) > 900: out = out[:900] + " …"
            done.append([cmd, out])
        with open(os.path.join(OUT, name + ".html"), "w") as f: f.write(PAGE % json.dumps(done, ensure_ascii=False))
        print(os.path.join(OUT, name + ".html"))

if __name__ == "__main__": main()
