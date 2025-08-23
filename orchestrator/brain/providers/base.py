import os, importlib

class Provider:
    name = "base"
    def plan(self, engagement: dict, scope: dict, preferences: dict) -> dict:
        raise NotImplementedError
    def enrich(self, engagement: dict, selected_tests: list, scope: dict) -> dict:
        # Optionally fill params per test
        return {"selected_tests": selected_tests, "notes": "no enrichment"}

def list_providers():
    return ["heuristic","openai_chat","anthropic","azure_openai"]

def load_provider(name: str) -> Provider:
    name = (name or os.environ.get("BRAIN_PROVIDER","heuristic")).lower()
    if name == "heuristic":
        from .heuristic import HeuristicProvider
        return HeuristicProvider()
    try:
        if name == "openai_chat":
            mod = importlib.import_module("orchestrator.brain.providers.openai_chat")
            return mod.OpenAIChatProvider()
        if name == "anthropic":
            mod = importlib.import_module("orchestrator.brain.providers.anthropic")
            return mod.AnthropicProvider()
        if name == "azure_openai":
            mod = importlib.import_module("orchestrator.brain.providers.azure_openai")
            return mod.AzureOpenAIProvider()
    except Exception as e:
        # Fallback
        from .heuristic import HeuristicProvider
        return HeuristicProvider()
    from .heuristic import HeuristicProvider
    return HeuristicProvider()
