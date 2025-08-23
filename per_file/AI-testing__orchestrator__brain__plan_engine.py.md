# File: AI-testing/orchestrator/brain/plan_engine.py

- Size: 3382 bytes
- Kind: text
- SHA256: 84b22100810118307b4d3fdc39f9c5cfa97b9851224c84c9b2a546542c82665f

## Python Imports

```
hashlib, json, os, providers, time, typing
```

## Head (first 60 lines)

```
import json, os, hashlib, time
from typing import Dict, Any, Tuple, List

from .providers.heuristic import HeuristicProvider
try:
    from .providers.openai_chat import OpenAIChatProvider
except Exception:
    OpenAIChatProvider = None
try:
    from .providers.anthropic import AnthropicProvider
except Exception:
    AnthropicProvider = None
try:
    from .providers.azure_openai import AzureOpenAIProvider
except Exception:
    AzureOpenAIProvider = None

PROVIDER_MAP = {
    "heuristic": HeuristicProvider,
    "openai_chat": OpenAIChatProvider,
    "anthropic": AnthropicProvider,
    "azure_openai": AzureOpenAIProvider,
}

def _fingerprint(scope: Dict[str, Any], engagement_type: str, tenant_id: str, version: str) -> str:
    data = json.dumps({"scope":scope,"engagement_type":engagement_type,"tenant_id":tenant_id,"version":version}, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()

def _cache_path() -> str:
    return os.environ.get("BRAIN_CACHE_PATH","/data/brain_cache.jsonl")

def _cache_get(fp: str) -> Dict[str, Any] | None:
    path = _cache_path()
    try:
        with open(path,"r",encoding="utf-8") as f:
            for line in f:
                try:
                    row=json.loads(line)
                    if row.get("fp")==fp:
                        return row.get("plan")
                except Exception:
                    continue
    except FileNotFoundError:
        return None
    return None

def _cache_put(fp: str, plan: Dict[str,Any]) -> None:
    path = _cache_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,"a",encoding="utf-8") as f:
        f.write(json.dumps({"ts":time.time(),"fp":fp,"plan":plan})+"\n")

def _load_provider(name: str):
    cls = PROVIDER_MAP.get((name or "").strip() or "heuristic")
    if cls is None:
        return HeuristicProvider()
    return cls() if cls else HeuristicProvider()

def decide_risk(selected_tests: List[str]) -> str:
    intrusive = {"web_zap_auth_full","network_nmap_tcp_full","network_nmap_udp_top_200"}
```

## Tail (last 60 lines)

```
    path = _cache_path()
    try:
        with open(path,"r",encoding="utf-8") as f:
            for line in f:
                try:
                    row=json.loads(line)
                    if row.get("fp")==fp:
                        return row.get("plan")
                except Exception:
                    continue
    except FileNotFoundError:
        return None
    return None

def _cache_put(fp: str, plan: Dict[str,Any]) -> None:
    path = _cache_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,"a",encoding="utf-8") as f:
        f.write(json.dumps({"ts":time.time(),"fp":fp,"plan":plan})+"\n")

def _load_provider(name: str):
    cls = PROVIDER_MAP.get((name or "").strip() or "heuristic")
    if cls is None:
        return HeuristicProvider()
    return cls() if cls else HeuristicProvider()

def decide_risk(selected_tests: List[str]) -> str:
    intrusive = {"web_zap_auth_full","network_nmap_tcp_full","network_nmap_udp_top_200"}
    active = {"web_nuclei_default","web_zap_baseline","web_httpx_probe"}
    if any(t in intrusive for t in selected_tests):
        return "intrusive"
    if any(t in active for t in selected_tests):
        return "safe_active"
    return "safe_passive"

def plan(scope: Dict[str,Any], engagement_type: str, tenant_id: str, preferences: Dict[str,Any]) -> Dict[str,Any]:
    version = os.environ.get("BRAIN_VERSION","v1.3.0")
    fp = _fingerprint(scope, engagement_type, tenant_id, version)
    cached = None if preferences.get("no_cache") else _cache_get(fp)
    if cached:
        cached.setdefault("risk_tier", decide_risk(cached.get("selected_tests",[])))
        cached.setdefault("explanation","cache hit")
        return cached

    provider = _load_provider(preferences.get("provider"))
    try:
        plan = provider.plan(scope, engagement_type, preferences)
    except Exception as e:
        # fallback
        plan = HeuristicProvider().plan(scope, engagement_type, preferences)
        plan["explanation"] = f"fallback to heuristic: {e}"
    try:
        plan = provider.enrich(scope, plan)  # may be noop
    except Exception:
        pass
    plan.setdefault("selected_tests",[])
    plan.setdefault("params",{})
    plan["risk_tier"] = decide_risk(plan["selected_tests"])
    _cache_put(fp, plan)
    return plan
```

