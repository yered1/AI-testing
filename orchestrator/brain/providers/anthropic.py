import os, json, re, requests
from typing import Dict, Any
from .base import BaseProvider

# Minimal Anthropic client via HTTP
class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def plan(self, scope: Dict[str, Any], engagement_type: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        key = os.environ.get("ANTHROPIC_API_KEY")
        model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        sys_prompt = "You are a senior penetration testing planner producing JSON only."
        user = f"Scope JSON:\n{json.dumps(scope)}\nEngagement type: {engagement_type}\nReturn JSON {{\"selected_tests\":[],\"params\":{{}}}} only."
        r = requests.post("https://api.anthropic.com/v1/messages",
                          headers={"x-api-key": key, "anthropic-version":"2023-06-01", "content-type":"application/json"},
                          json={"model": model, "max_tokens": 700, "system": sys_prompt, "messages":[{"role":"user","content": user}]},
                          timeout=60)
        r.raise_for_status()
        out = r.json()
        txt = "".join([b.get("text","") for b in out["content"] if b.get("type")=="text"])
        m = re.search(r'\{[\s\S]*\}', txt)
        if not m:
            raise RuntimeError("no JSON in LLM output")
        plan = json.loads(m.group(0))
        plan.setdefault("params", {})
        plan.setdefault("selected_tests", [])
        return {"selected_tests": plan["selected_tests"], "params": plan["params"], "explanation": "anthropic plan"}
