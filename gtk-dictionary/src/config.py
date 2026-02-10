import os
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# --- STATIC PATHS ---
DEBIAN_PATH = Path("/usr/share/vocabolario")

# if DEBIAN_PATH.exists():
#     PROJECT_ROOT = DEBIAN_PATH
# else:
#     PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_PATH = PROJECT_ROOT / "assets"
PLACEHOLDER_PATH = ASSETS_PATH / "placeholder.html"
GTK_CSS_PATH = ASSETS_PATH / "gtk_css.css"
DICTIONARIES_CATALOG = PROJECT_ROOT / "data" / "catalog.json"
DICTIONARIES_FOLDER = PROJECT_ROOT / "data" / "dictionaries"

# --- DYNAMIC PATHS ---
HOME = Path.home()
DATA_DIR = HOME / ".local/share/vocabolario"
LOG_DIR = HOME / ".cache/vocabolario"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "dictionary.log"


def setup_logging() -> logging.Logger:
    """Logging"""
    # Max size of log file: 1.5 MB
    handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1500000, backupCount=2, encoding="utf-8"
    )

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger = logging.getLogger("vocabolario")
    logger.setLevel(logging.INFO)

    # Prevent double logging
    if not logger.handlers:
        logger.addHandler(handler)

    return logger
