import os
from pathlib import Path

# Base directory is the workspace root
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
RESEARCH_DIR = BASE_DIR / "research"
RAW_DIR = RESEARCH_DIR / "raw"

# Ensure directories exist
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

def get_apify_token() -> str:
    """Retrieve the Apify API token from .env or environment variable."""
    # Check environment variable first
    token = os.getenv("APIFY_TOKEN")
    if token and token.strip():
        return token.strip()
        
    # Check .env file
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("APIFY_TOKEN="):
                    val = line.split("=", 1)[1].strip()
                    if val:
                        return val
    return ""

def save_apify_token(token: str):
    """Save or update Apify API token in .env."""
    token = token.strip()
    lines = []
    found = False
    
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("APIFY_TOKEN="):
                    lines.append(f"APIFY_TOKEN={token}\n")
                    found = True
                else:
                    lines.append(line)
                    
    if not found:
        lines.append(f"APIFY_TOKEN={token}\n")
        
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)
