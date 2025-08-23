# File: AI-testing/orchestrator/logging_setup.py

- Size: 246 bytes
- Kind: text
- SHA256: 955f3dd034cb4f6d2176a6bf580738bf63bc2be65a90e8713860bbe655f0cacb

## Python Imports

```
logging, os
```

## Head (first 60 lines)

```
import logging, os
def setup_logging():
    level = os.environ.get("LOG_LEVEL","INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
```

