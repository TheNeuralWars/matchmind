"""Optional Microsoft Agent Framework adapter (pip install agent-framework). Import-guarded: MatchMind never requires it.

    from matchmind.agent_framework_adapter import build_agent, AVAILABLE
    agent = build_agent()                          # Azure OpenAI from env (AZURE_OPENAI_ENDPOINT, ..._API_KEY or az login)
    print((await agent.run("Who is on top at minute 60 of seed 7? Answer in Italian.")).text)

The same match-state functions back the MCP server (matchmind.mcp_server), so both surfaces stay in sync.
"""
import json, os
from typing import Annotated, Optional
from . import tools as T

try:  # pragma: no cover - depends on optional package
    import agent_framework as _af
    AVAILABLE = True
except Exception:  # ImportError, or a broken install
    _af = None
    AVAILABLE = False

INSTRUCTIONS = ("You are MatchMind, a football match analyst for a SYNTHETIC match. Use the tools for every fact; never invent "
                "numbers. Explain WHY moments matter. Answer in the user's language (en/es/it).")

# Plain, typed callables: Agent Framework turns them into function tools from their signature + docstring.
def get_score(seed: Annotated[int, "Synthetic match seed"] = 8, minute: Annotated[Optional[float], "Game minute; omit for full time"] = None) -> str:
    """Score, xG and possession of a synthetic match at a given minute."""
    return json.dumps(T.get_score(seed, minute))

def get_momentum(seed: Annotated[int, "Synthetic match seed"] = 8, minute: Annotated[Optional[float], "Game minute; omit for full time"] = None) -> str:
    """Momentum (-1..1, positive = home on top) and control-vs-chaos index."""
    return json.dumps(T.get_momentum(seed, minute))

def get_key_moments(seed: Annotated[int, "Synthetic match seed"] = 8, minute: Annotated[Optional[float], "Up to this minute"] = None,
                    limit: Annotated[int, "Max moments"] = 20) -> str:
    """Key moments detected by the Analyst agent (goals, big chances, penalties, red cards, momentum swings)."""
    return json.dumps(T.get_key_moments(seed, minute, limit=limit), ensure_ascii=False)

def explain_moment(moment_id: Annotated[str, "id from get_key_moments"], lang: Annotated[str, "en, es or it"] = "en",
                   persona: Annotated[str, "analyst or casual"] = "analyst") -> str:
    """Explain why a key moment matters, localised, for an analyst or a casual fan."""
    return json.dumps(T.explain_moment(moment_id, lang, persona), ensure_ascii=False)

TOOL_FUNCS = [get_score, get_momentum, get_key_moments, explain_moment]

def _default_client():
    from agent_framework.azure import AzureOpenAIChatClient  # optional
    kw = {k: v for k, v in {"endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"), "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                            "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")}.items() if v}
    if "api_key" not in kw:
        from azure.identity import AzureCliCredential
        kw["credential"] = AzureCliCredential()
    return AzureOpenAIChatClient(**kw)

def build_agent(chat_client=None, name="MatchMind"):
    """Return an Agent Framework agent wired to MatchMind tools. Raises RuntimeError if agent-framework isn't installed."""
    if not AVAILABLE and chat_client is None:
        raise RuntimeError("agent-framework not installed: pip install agent-framework (optional; MatchMind works without it)")
    client = chat_client or _default_client()
    if hasattr(client, "as_agent"):                        # newer releases
        return client.as_agent(name=name, instructions=INSTRUCTIONS, tools=TOOL_FUNCS)
    if hasattr(client, "create_agent"):                    # earlier releases
        return client.create_agent(name=name, instructions=INSTRUCTIONS, tools=TOOL_FUNCS)
    return _af.ChatAgent(chat_client=client, name=name, instructions=INSTRUCTIONS, tools=TOOL_FUNCS)
