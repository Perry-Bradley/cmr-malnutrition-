"""Best-effort download of all HDX datasets listed in the project proposal."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# allow running as a script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_loader import download_all  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

if __name__ == "__main__":
    results = download_all()
    print("\n=== Download summary ===")
    for key, files in results.items():
        print(f"  {key:24s}  {len(files):3d} files")
