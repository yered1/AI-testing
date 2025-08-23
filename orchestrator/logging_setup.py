import logging, os
def setup_logging():
    level = os.environ.get("LOG_LEVEL","INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
