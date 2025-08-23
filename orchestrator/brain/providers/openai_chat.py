import os, json, re, requests
from typing import Dict, Any
from .base import BaseProvider

SYSTEM = "You are a senior penetration testing planner. Given scope and engagement type, output a minimal JSON with selected_tests and optional params. Prefer checks that match the scope. Keep it safe by default (baseline/passive)."

PROMPT = '''Scope JSON:
{scope}

Engagement type: {etype}

Return JSON only in this shape:
{{
  "selected_tests": ["test_id", ...],
  "params": {{"test_id": {{...}} }}
}}
'''

class OpenAIChatProvider(BaseProvider):
    name = "openai_chat"

    def plan(self, scope: Dict[str, Any], engagement_type: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set")
        body = {
            "model": model,
            "messages":[
                {"role":"system","content": SYSTEM},
                {"role":"user","content": PROMPT.format(scope=json.dumps(scope, indent=2), etype=engagement_type)}
            ],
            "temperature": 0.2
        }
        r = requests.post(f"{base}/chat/completions", headers={
            "Authorization": f"Bearer {key}", "Content-Type":"application/json"
        }, json=body, timeout=60)
        r.raise_for_status()
        data = r.json()
        txt = data["choices"][0]["message"]["content"]
        # Extract JSON block
        m = re.search(r'\{[\s\S]*\}', txt)
        if not m:
            raise RuntimeError("no JSON in LLM output")
        plan = json.loads(m.group(0))
        plan.setdefault("params", {})
        plan.setdefault("selected_tests", [])
        return {"selected_tests": plan["selected_tests"], "params": plan["params"], "explanation": "openai_chat plan"}
