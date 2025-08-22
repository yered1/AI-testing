# Auto-load v2 extras (routers) without modifying existing app files.
try:
    from . import bootstrap_extras  # noqa: F401
except Exception as _e:
    # Best-effort: do not crash the app if extras fail to import.
    import sys
    print(f"[orchestrator] extras not loaded: {_e}", file=sys.stderr)
