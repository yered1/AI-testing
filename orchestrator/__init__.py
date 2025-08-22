# Auto-load v2 routers without touching existing app files
try:
    from . import bootstrap_extras  # noqa: F401
except Exception as _e:
    import sys
    print(f"[orchestrator] extras not loaded: {_e}", file=sys.stderr)
