import json, unittest
from matchmind import agent_framework_adapter as A

class FakeClient:
    def as_agent(self, **kw): self.kw = kw; return kw

class Adapter(unittest.TestCase):
    def test_import_guard(self):
        self.assertIsInstance(A.AVAILABLE, bool)
        if not A.AVAILABLE:
            with self.assertRaises(RuntimeError): A.build_agent()
    def test_build_with_injected_client(self):
        agent = A.build_agent(FakeClient())
        self.assertEqual({f.__name__ for f in agent["tools"]}, {"get_score", "get_momentum", "get_key_moments", "explain_moment"})
        self.assertIn("SYNTHETIC", agent["instructions"])
    def test_tool_funcs_return_json(self):
        s = json.loads(A.get_score(7, 45)); self.assertEqual(s["match_id"], "SYN-7")
        mid = json.loads(A.get_key_moments(7, limit=1))["moments"][0]["id"]
        self.assertEqual(json.loads(A.explain_moment(mid, "it", "casual"))["lang"], "it")
        self.assertTrue(all(f.__doc__ for f in A.TOOL_FUNCS))

if __name__ == "__main__": unittest.main()
