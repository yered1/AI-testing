
import logging
import os

_level = os.environ.get("LOG_LEVEL", "INFO").upper()
fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
logging.basicConfig(level=getattr(logging, _level, logging.INFO), format=fmt)
logging.getLogger("uvicorn").setLevel(getattr(logging, _level, logging.INFO))
