#!/usr/bin/env python3
"""Pings Qdrant so the free-tier cluster doesn't get suspended for inactivity.
Standalone - only needs QDRANT_URL/QDRANT_API_KEY (+ optional
QDRANT_COLLECTION_NAME) as env vars or a .env file next to this script, so it
can run on its own server independent of the rest of this app. Run on a
schedule (cron). Appends each run's result to qdrant_monitoring.txt."""

import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient

SCRIPT_DIR = Path(__file__).parent
LOG_PATH = SCRIPT_DIR / "qdrant_monitoring.txt"

load_dotenv(SCRIPT_DIR / ".env")
load_dotenv(SCRIPT_DIR.parent / ".env")

QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
QDRANT_COLLECTION_NAME = os.environ.get("QDRANT_COLLECTION_NAME", "FoundationX")


def log(message: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {message}"
    print(line)
    with open(LOG_PATH, "a") as log_file:
        log_file.write(line + "\n")


def main():
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        count = client.count(collection_name=QDRANT_COLLECTION_NAME).count
        log(f"OK - collection '{QDRANT_COLLECTION_NAME}' has {count} points")
    except Exception as error:
        log(f"FAILED - {error}")
        raise


if __name__ == "__main__":
    main()
