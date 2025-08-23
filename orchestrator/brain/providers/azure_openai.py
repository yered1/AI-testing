import os, json
from .base import Provider

class AzureOpenAIProvider(Provider):
    name = "azure_openai"
    def plan(self, engagement, scope, preferences):
        if not os.environ.get("AZURE_OPENAI_KEY"):
            from .heuristic import HeuristicProvider
            return HeuristicProvider().plan(engagement, scope, preferences)
        try:
            import requests
            endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
            dep = os.environ.get("AZURE_OPENAI_DEPLOYMENT","gpt-4o-mini")
            api = f"{endpoint}/openai/deployments/{dep}/chat/completions?api-version=2024-02-15-preview"
            r = requests.post(api,
                              headers={"api-key": os.environ["AZURE_OPENAI_KEY"], "Content-Type":"application/json"},
                              json={"messages":[{"role":"system","content":"Pentest planner; JSON only."},
                                                {"role":"user","content":json.dumps({"engagement":engagement,"scope":scope,"preferences":preferences})}],
                                    "temperature":0.1, "response_format":{"type":"json_object"}},
                              timeout=60)
            r.raise_for_status()
            data = r.json()
            txt = data.get("choices",[{}])[0].get("message",{}).get("content","{}")
            plan = json.loads(txt)
            if "selected_tests" in plan:
                return plan
        except Exception:
            pass
        from .heuristic import HeuristicProvider
        return HeuristicProvider().plan(engagement, scope, preferences)

    def enrich(self, engagement, selected_tests, scope):
        from .heuristic import HeuristicProvider
        return HeuristicProvider().enrich(engagement, selected_tests, scope)
