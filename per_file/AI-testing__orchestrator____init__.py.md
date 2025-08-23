# File: AI-testing/orchestrator/__init__.py

- Size: 362 bytes
- Kind: text
- SHA256: fdaafe70957603b69432abb9a2c635f03d249459c0ec7436c41829942e04e8da

## Python Imports

```
os, sys
```

## Head (first 60 lines)

```
# Guard extras import during Alembic migrations or other non-app contexts
import os
if os.environ.get("ALEMBIC_RUNNING") != "1":
    try:
        from . import bootstrap_extras  # noqa: F401
    except Exception as _e:
        import sys
        # Keep quiet during non-critical contexts
        print(f"[orchestrator] extras not loaded: {_e}", file=sys.stderr)
```

