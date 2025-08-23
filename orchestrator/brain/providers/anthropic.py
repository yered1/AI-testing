import os, json
from .base import Provider

class AnthropicProvider(Provider):
    name = "anthropic"
    def plan(self, engagement, scope, preferences):
        # Lazy import only if configured
        if not os.environ.get("ANTHROPIC_API_KEY"):
            from .heuristic import HeuristicProvider
            return HeuristicProvider().plan(engagement, scope, preferences)
        try:
            import requests
            base = os.environ.get("ANTHROPIC_BASE_URL","https://api.anthropic.com/v1")
            key = os.environ["ANTHROPIC_API_KEY"]
            r = requests.post(f"{base}/messages",
                              headers={"x-api-key": key, "anthropic-version":"2023-06-01","Content-Type":"application/json"},
                              json={"model": os.environ.get("ANTHROPIC_MODEL","claude-3-5-sonnet-20240620"),
                                    "system":"You are a pentest planner; emit JSON with selected_tests[].",
                                    "messages":[{"role":"user","content":json.dumps({"engagement":engagement,"scope":scope,"preferences":preferences})}]},
                              timeout=60)
            r.raise_for_status()
            data = r.json()
            content = (data.get("content") or [{}])[0].get("text","{}")
            plan = json.loads(content)
            if "selected_tests" in plan:
                return plan
        except Exception:
            pass
        from .heuristic import HeuristicProvider
        return HeuristicProvider().plan(engagement, scope, preferences)

    def enrich(self, engagement, selected_tests, scope):
        from .heuristic import HeuristicProvider
        return HeuristicProvider().enrich(engagement, selected_tests, scope)
