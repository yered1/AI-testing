# Guard extras import during Alembic migrations or other non-app contexts
import os
if os.environ.get("ALEMBIC_RUNNING") != "1":
    try:
        from . import bootstrap_extras  # noqa: F401
    except Exception as _e:
        import sys
        # Keep quiet during non-critical contexts
        print(f"[orchestrator] extras not loaded: {_e}", file=sys.stderr)
