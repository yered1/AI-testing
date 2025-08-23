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
        sys_prompt = "You are a senior pentest planner. Reply with compact JSON only: {selected_tests: string[], params: object}"
        user_prompt = f"Engagement type: {engagement_type}\nScope: {json.dumps(scope)}\nPreferences: {json.dumps(preferences)}"
        body = {
            "messages":[
                {"role":"system","content": sys_prompt},
                {"role":"user","content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 800
        }
        r = requests.post(
            f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2024-02-15-preview",
            headers={"api-key": key, "content-type":"application/json"},
            json=body, timeout=60
        )
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
