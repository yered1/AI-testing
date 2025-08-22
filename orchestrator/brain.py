import os, json

class BrainResult:
    def __init__(self, tests, explanation, filtered=None):
        self.tests = tests or []
        self.explanation = explanation or ""
        self.filtered = filtered or []

class Brain:
    def __init__(self):
        self.provider = os.environ.get("LLM_PROVIDER", "heuristic")
        self.http_endpoint = os.environ.get("LLM_HTTP_ENDPOINT")
        self.http_token = os.environ.get("LLM_HTTP_TOKEN")

    def suggest(self, engagement: dict, catalog: dict) -> BrainResult:
        # 1) External HTTP provider (if configured)
        if self.http_endpoint:
            try:
                import requests
                r = requests.post(self.http_endpoint, json={
                    "engagement": engagement,
                    "catalog": catalog
                }, headers={"Authorization": f"Bearer {self.http_token}"} if self.http_token else {}, timeout=20)
                r.raise_for_status()
                data = r.json()
                return BrainResult(data.get("tests", []), data.get("explanation", "Provided by HTTP provider"))
            except Exception as e:
                return BrainResult([], f"HTTP provider error: {e}. Falling back to heuristic.")

        # 2) Heuristic provider (default)
        t = []
        typ = (engagement.get("type") or "").lower()
        scope = engagement.get("scope") or {}
        has_cidrs = bool(scope.get("in_scope_cidrs"))
        has_domains = bool(scope.get("in_scope_domains"))
        if typ in ("network","external","internal"):
            if has_cidrs:
                t += ["network.discovery.ping_sweep", "network.nmap.tcp_top_1000"]
            if has_domains:
                t += ["recon.dns.basic", "recon.subdomains.simple"]
        if typ in ("web","webapp"):
            t += ["web.owasp.top10.core"]
        if typ in ("mobile","android","ios"):
            t += ["mobile.static.basic"]
        # keep only tests present in catalog
        cat_ids = {i["id"] for i in catalog.get("items",[])}
        tests = [x for x in t if x in cat_ids]
        return BrainResult(tests, "Heuristic selection based on engagement type and scope.")
