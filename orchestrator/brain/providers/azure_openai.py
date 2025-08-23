import os, json, re, requests
from typing import Dict, Any
from .base import BaseProvider

class AzureOpenAIProvider(BaseProvider):
    name = "azure_openai"

    def plan(self, scope: Dict[str, Any], engagement_type: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        key = os.environ.get("AZURE_OPENAI_KEY")
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT","").rstrip("/")
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        if not (key and endpoint and deployment):
            raise RuntimeError("AZURE_OPENAI_* envs not set")
        body = {
            "messages":[
                {"role":"system","content": "You are a senior pentest planner. Output JSON only."},
                {"role":"user","content": f"Scope:\n{json.dumps(scope)}\nEngagement type: {engagement_type}\nReturn JSON { '{"selected_tests":[],"params":{}}' }"}
            ],
            "temperature": 0.2
        }
        r = requests.post(f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2024-02-15-preview",
                          headers={"api-key": key, "content-type":"application/json"},
                          json=body, timeout=60)
        r.raise_for_status()
        data = r.json()
        txt = data["choices"][0]["message"]["content"]
        m = re.search(r'\{[\s\S]*\}', txt)
        if not m:
            raise RuntimeError("no JSON in LLM output")
        plan = json.loads(m.group(0))
        plan.setdefault("params", {})
        plan.setdefault("selected_tests", [])
        return {"selected_tests": plan["selected_tests"], "params": plan["params"], "explanation": "azure_openai plan"}
