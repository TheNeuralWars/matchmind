"""Minimal MCP server (JSON-RPC 2.0, newline-delimited over stdio). Stdlib only.

Claude/Copilot/VS Code config:  {"command": "python", "args": ["-m", "matchmind.mcp_server"]}
"""
import json, sys
from .tools import TOOLS

PROTOCOL = "2025-06-18"
SERVER_INFO = {"name": "matchmind", "version": "0.3.0"}

def handle(msg):
    """Return a response dict, or None for notifications."""
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
    def ok(result): return {"jsonrpc": "2.0", "id": mid, "result": result}
    def err(code, text): return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": text}}
    if mid is None: return None                       # notification (e.g. notifications/initialized)
    if method == "initialize":
        return ok({"protocolVersion": params.get("protocolVersion", PROTOCOL), "capabilities": {"tools": {"listChanged": False}}, "serverInfo": SERVER_INFO})
    if method == "ping": return ok({})
    if method == "tools/list":
        return ok({"tools": [{"name": n, "description": d, "inputSchema": s} for n, (_, d, s) in TOOLS.items()]})
    if method == "tools/call":
        name = params.get("name")
        if name not in TOOLS: return err(-32602, f"unknown tool {name}")
        try:
            data = TOOLS[name][0](**(params.get("arguments") or {}))
            return ok({"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}], "structuredContent": data, "isError": False})
        except Exception as ex:                       # tool errors are results, not protocol errors (MCP spec)
            return ok({"content": [{"type": "text", "text": f"{type(ex).__name__}: {ex}"}], "isError": True})
    return err(-32601, f"method not found: {method}")

def serve(inp=sys.stdin, out=sys.stdout):
    for line in inp:
        line = line.strip()
        if not line: continue
        try: msg = json.loads(line)
        except json.JSONDecodeError:
            resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            resp = handle(msg)
        if resp is not None:
            out.write(json.dumps(resp, ensure_ascii=False) + "\n"); out.flush()

if __name__ == "__main__": serve()
