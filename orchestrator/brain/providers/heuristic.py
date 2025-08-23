from .base import Provider

class HeuristicProvider(Provider):
    name = "heuristic"
    def plan(self, engagement: dict, scope: dict, preferences: dict) -> dict:
        t = (engagement.get("type") or "").lower()
        risk = (preferences or {}).get("risk_tier","safe_active")
        sel = []
        # web modalities
        if t in ("web","webapp") or scope.get("in_scope_domains"):
            sel += ["web_httpx_probe","web_zap_baseline","web_nuclei_default"]
        # network modalities
        if t in ("network","external","internal") or scope.get("in_scope_cidrs"):
            sel += ["network_dnsx_resolve","network_nmap_tcp_top_1000"]
        # mobile / code left to existing flows
        dedup = []
        for s in sel:
            if s not in dedup:
                dedup.append(s)
        return {"selected_tests": [{"id": s, "params": {}} for s in dedup],
                "explanation": f"Heuristic selection by type={t}, risk={risk} using domain/CIDR presence."}
    
    def enrich(self, engagement: dict, selected_tests: list, scope: dict) -> dict:
        out = []
        domains = scope.get("in_scope_domains") or []
        cidrs = scope.get("in_scope_cidrs") or []
        for step in selected_tests or []:
            sid = step.get("id")
            params = dict(step.get("params") or {})
            if sid == "web_httpx_probe":
                if domains and not params.get("targets"):
                    params["targets"] = [d if d.startswith("http") else f"https://{d}" for d in domains]
            if sid == "network_dnsx_resolve":
                if domains and not params.get("domains"):
                    params["domains"] = domains
            if sid == "network_nmap_tcp_top_1000":
                if cidrs and not params.get("targets"):
                    params["targets"] = cidrs
            if sid == "web_zap_baseline":
                if domains and not params.get("domains"):
                    params["domains"] = domains
            if sid == "web_nuclei_default":
                if domains and not params.get("targets"):
                    params["targets"] = domains
            out.append({"id": sid, "params": params})
        return {"selected_tests": out, "notes": "Filled params from engagement scope where applicable."}
