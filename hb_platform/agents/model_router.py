"""Model Router — routes inference requests to Ollama (local) or Claude (API).

Routine tasks go local (free, fast).  Complex tasks go to Claude (costs
money, smarter).  Unknown tasks default to local with a review flag.
"""
from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, Optional

from .. import config

ROUTINE_TASKS = frozenset({
    "classify_submission",
    "moderate_forum_post",
    "generate_heartbeat_report",
    "summarize_thread",
})

COMPLEX_TASKS = frozenset({
    "evaluate_constitutional_question",
    "analyze_security_threat",
    "draft_governance_proposal",
    "resolve_guild_dispute",
})


def route(task_type: str, payload: Dict[str, Any]) -> str:
    """Route an inference request to the appropriate model."""
    if task_type in ROUTINE_TASKS:
        return call_ollama(payload)
    elif task_type in COMPLEX_TASKS:
        return call_claude(payload)
    else:
        # Unknown — default to local, flag for review
        return call_ollama(payload)


def call_ollama(payload: Dict[str, Any]) -> str:
    """Call local Ollama model.  Returns model response text."""
    prompt = payload.get("prompt", json.dumps(payload))
    try:
        result = subprocess.run(
            ["curl", "-s", f"{config.OLLAMA_URL}/api/generate",
             "-d", json.dumps({"model": config.OLLAMA_MODEL, "prompt": prompt,
                               "stream": False})],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            resp = json.loads(result.stdout)
            return resp.get("response", "")
    except Exception:
        pass
    return "[ollama unavailable]"


def call_claude(payload: Dict[str, Any]) -> str:
    """Call Claude API via anthropic SDK.  Returns model response text.

    Requires ANTHROPIC_API_KEY in environment.
    """
    prompt = payload.get("prompt", json.dumps(payload))
    try:
        import anthropic
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        return f"[claude unavailable: {e}]"
