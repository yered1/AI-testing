import os, json, time

from .base import Provider

class OpenAIChatProvider(Provider):
    name = "openai_chat"
    def _client(self):
        # Lazy dependency; use requests only if configured
        key = os.environ.get("OPENAI_API_KEY")
        base = os.environ.get("OPENAI_BASE_URL","https://api.openai.com/v1")
        model = os.environ.get("OPENAI_MODEL","gpt-4o-mini")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set")
        import requests
        return requests.Session(), base, model, key

    def plan(self, engagement: dict, scope: dict, preferences: dict) -> dict:
        try:
            s, base, model, key = self._client()
        except Exception as e:
            # fallback to heuristic if not configured
            from .heuristic import HeuristicProvider
            return HeuristicProvider().plan(engagement, scope, preferences)
        prompt = {
            "role":"system",
            "content":"You are a pentest planner. Propose safe plan steps using our test ids."
        }
        user = {
            "role":"user",
            "content": json.dumps({"engagement":engagement,"scope":scope,"preferences":preferences,
                                   "available_tests":[
                                       "web_httpx_probe","web_zap_baseline","web_nuclei_default",
                                       "network_dnsx_resolve","network_nmap_tcp_top_1000",
                                       "web_owasp_top10_core","network_discovery_ping_sweep"
                                   ]})
        }
        try:
            r = s.post(f"{base}/chat/completions",
                       headers={"Authorization": f"Bearer {key}","Content-Type":"application/json"},
                       json={"model": model, "messages":[prompt,user],
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

    def enrich(self, engagement: dict, selected_tests: list, scope: dict) -> dict:
        try:
            s, base, model, key = self._client()
        except Exception:
            from .heuristic import HeuristicProvider
            return HeuristicProvider().enrich(engagement, selected_tests, scope)
        user = {"role":"user","content": json.dumps({"engagement":engagement,"scope":scope,"selected_tests":selected_tests})}
        try:
            r = s.post(f"{base}/chat/completions",
                       headers={"Authorization": f"Bearer {key}","Content-Type":"application/json"},
                       json={"model": model, "messages":[{"role":"system","content":"Enrich params per step; reply JSON."}, user],
                             "temperature":0.1, "response_format":{"type":"json_object"}},
                       timeout=60)
            r.raise_for_status()
            data = r.json()
            txt = data.get("choices",[{}])[0].get("message",{}).get("content","{}")
            resp = json.loads(txt)
            if "selected_tests" in resp:
                return resp
        except Exception:
            pass
        from .heuristic import HeuristicProvider
        return HeuristicProvider().enrich(engagement, selected_tests, scope)
