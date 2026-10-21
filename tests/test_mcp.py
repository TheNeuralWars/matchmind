import json, subprocess, sys, unittest
from matchmind.mcp_server import handle
from matchmind.tools import get_score, get_key_moments, get_momentum, explain_moment

def call(name, **args):
    r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}})["result"]
    return r

class Tools(unittest.TestCase):
    def test_score_over_time(self):
        ht, ft = get_score(7, 45), get_score(7)
        self.assertLessEqual(sum(ht["score"].values()), sum(ft["score"].values()))
        self.assertLessEqual(ht["minute"], 45)
    def test_key_moments_and_explain(self):
        ms = get_key_moments(7, limit=500)["moments"]
        self.assertTrue(ms and all(m["minute"] <= 95 for m in ms))
        goals = get_key_moments(7, kinds=["goal"])
        self.assertEqual(goals["count"], sum(get_score(7)["score"].values()))
        mid = ms[0]["id"]
        es, it = explain_moment(mid, "es", "casual"), explain_moment(mid, "it", "analyst")
        self.assertEqual((es["lang"], it["lang"]), ("es", "it")); self.assertNotEqual(es["text"], it["text"])
        self.assertEqual(get_key_moments(7, minute=30)["moments"][-1]["minute"] <= 30, True)
    def test_momentum(self):
        m = get_momentum(7, 60); self.assertTrue(-1 <= m["momentum"] <= 1)

class Protocol(unittest.TestCase):
    def test_initialize_list_call_errors(self):
        init = handle({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
        self.assertIn("tools", init["result"]["capabilities"])
        self.assertIsNone(handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        names = {t["name"] for t in handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]}
        self.assertEqual(names, {"get_score", "get_key_moments", "explain_moment", "get_momentum"})
        r = call("get_score", seed=7); self.assertFalse(r["isError"]); self.assertEqual(json.loads(r["content"][0]["text"])["match_id"], "SYN-7")
        self.assertTrue(call("explain_moment", moment_id="SYN-7-999999-goal")["isError"])
        self.assertEqual(handle({"jsonrpc": "2.0", "id": 3, "method": "nope"})["error"]["code"], -32601)
    def test_stdio_subprocess(self):
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "get_momentum", "arguments": {"seed": 3, "minute": 70}}}]
        out = subprocess.run([sys.executable, "-m", "matchmind.mcp_server"], input="\n".join(map(json.dumps, msgs)) + "\nnot json\n",
                             capture_output=True, text=True, timeout=60).stdout.strip().splitlines()
        self.assertEqual(len(out), 3)
        self.assertEqual(json.loads(out[1])["result"]["structuredContent"]["minute"] <= 70, True)
        self.assertEqual(json.loads(out[2])["error"]["code"], -32700)

if __name__ == "__main__": unittest.main()
