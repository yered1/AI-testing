from typing import Dict, Any, List
from .base import BaseProvider

WEB_DEFAULT = [ "web_httpx_probe", "web_zap_baseline", "web_nuclei_default" ]
NETWORK_INTERNAL = [ "network_discovery_ping_sweep", "network_nmap_tcp_full", "network_nmap_udp_top_200" ]
NETWORK_EXTERNAL = [ "network_discovery_ping_sweep", "network_nmap_tcp_top_1000" ]
CODE_DEFAULT = [ "code_semgrep_default" ]
MOBILE_DEFAULT = [ "mobile_apk_static_default" ]

class HeuristicProvider(BaseProvider):
    name = "heuristic"

    def plan(self, scope: Dict[str, Any], engagement_type: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        tests: List[str] = []
        params: Dict[str, Any] = {}
        et = (engagement_type or scope.get("type") or "").lower()
        domains = scope.get("in_scope_domains") or scope.get("domains") or []
        cidrs = scope.get("in_scope_cidrs") or scope.get("cidrs") or []
        code = scope.get("code") or {}
        mobile = scope.get("mobile") or {}
        packs = (preferences or {}).get("packs") or []

        def add_tests(ts):
            for t in ts:
                if t not in tests:
                    tests.append(t)

        if et in ("web","webapp"):
            add_tests(WEB_DEFAULT)
        if et in ("network","internal"):
            add_tests(NETWORK_INTERNAL if cidrs else NETWORK_EXTERNAL)
        if et in ("external","internet"):
            add_tests(NETWORK_EXTERNAL)
        if et in ("code","sast") or code:
            add_tests(CODE_DEFAULT)
        if et in ("mobile","apk") or mobile:
            add_tests(MOBILE_DEFAULT)
        # Packs
        for p in packs:
            if p == "default_web_active":
                add_tests(["web_zap_baseline","web_nuclei_default"])
            if p == "default_internal_network":
                add_tests(["network_discovery_ping_sweep","network_nmap_tcp_full","network_nmap_udp_top_200"])
            if p == "default_external_min":
                add_tests(["network_discovery_ping_sweep","web_httpx_probe","web_zap_baseline","web_nuclei_default"])
            if p == "default_code_review":
                add_tests(["code_semgrep_default"])
            if p == "default_mobile_static":
                add_tests(["mobile_apk_static_default"])

        explanation = f"Heuristic plan for {et}: {', '.join(tests)}"
        return {"selected_tests": tests, "params": params, "explanation": explanation}

    def enrich(self, scope: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        # Best-effort param fill-ins from scope (simple mapping)
        params = plan.get("params") or {}
        domains = scope.get("in_scope_domains") or scope.get("domains") or []
        cidrs = scope.get("in_scope_cidrs") or scope.get("cidrs") or []
        if "web_httpx_probe" in plan.get("selected_tests", []):
            params.setdefault("web_httpx_probe", {"targets": domains})
        if "web_zap_baseline" in plan.get("selected_tests", []):
            params.setdefault("web_zap_baseline", {"domains": domains, "mode": "baseline"})
        if "web_nuclei_default" in plan.get("selected_tests", []):
            params.setdefault("web_nuclei_default", {"targets": domains})
        if "network_discovery_ping_sweep" in plan.get("selected_tests", []):
            params.setdefault("network_discovery_ping_sweep", {"cidrs": cidrs})
        if "network_nmap_tcp_full" in plan.get("selected_tests", []):
            params.setdefault("network_nmap_tcp_full", {"cidrs": cidrs})
        if "network_nmap_udp_top_200" in plan.get("selected_tests", []):
            params.setdefault("network_nmap_udp_top_200", {"cidrs": cidrs})
        if "code_semgrep_default" in plan.get("selected_tests", []):
            params.setdefault("code_semgrep_default", {"config": "p/ci"})
        if "mobile_apk_static_default" in plan.get("selected_tests", []):
            params.setdefault("mobile_apk_static_default", {"artifact_label": "mobile_apk"})
        plan["params"] = params
        return plan
