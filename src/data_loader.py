"""Download CSV resources from HDX (Humanitarian Data Exchange).

HDX exposes a CKAN-style API; given a dataset slug, ``package_show`` returns
metadata that includes the URL of every attached resource. We use that to grab
the CSVs without scraping.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import requests

from .config import HDX_DATASETS, RAW_DIR

HDX_API = "https://data.humdata.org/api/3/action/package_show"
HEADERS = {"User-Agent": "data420-malnutrition-project/0.1 (academic, UB)"}
TIMEOUT = 60

log = logging.getLogger(__name__)


def list_resources(dataset_slug: str) -> list[dict]:
    """Return the list of resources attached to an HDX dataset."""
    r = requests.get(HDX_API, params={"id": dataset_slug},
                     headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    payload = r.json()
    if not payload.get("success"):
        raise RuntimeError(f"HDX API failed for {dataset_slug}: {payload}")
    return payload["result"]["resources"]


def download_file(url: str, dest: Path) -> Path:
    """Stream a remote file to ``dest``; skip if it already exists."""
    if dest.exists() and dest.stat().st_size > 0:
        log.info("[skip] already downloaded: %s", dest.name)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    log.info("[get ] %s -> %s", url, dest.name)
    with requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True) as r:
        r.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 15):
                fh.write(chunk)
    return dest


def download_dataset(key: str, extensions: Iterable[str] = ("csv", "xlsx", "zip"),
                     max_files: int | None = None) -> list[Path]:
    """Download all matching resources for a known HDX dataset key."""
    slug = HDX_DATASETS[key]
    target_dir = RAW_DIR / key
    target_dir.mkdir(parents=True, exist_ok=True)

    downloaded: list[Path] = []
    try:
        resources = list_resources(slug)
    except Exception as exc:  # noqa: BLE001
        log.warning("could not list resources for %s: %s", slug, exc)
        return downloaded

    for res in resources:
        fmt = (res.get("format") or "").lower()
        url = res.get("url")
        name = res.get("name") or url.rsplit("/", 1)[-1]
        if not url or fmt not in {e.lower() for e in extensions}:
            continue
        safe_name = name.replace("/", "_").replace(" ", "_")
        if "." not in safe_name:
            safe_name = f"{safe_name}.{fmt}"
        dest = target_dir / safe_name
        try:
            download_file(url, dest)
            downloaded.append(dest)
        except Exception as exc:  # noqa: BLE001
            log.warning("failed %s: %s", url, exc)
        if max_files and len(downloaded) >= max_files:
            break
    return downloaded


def download_all() -> dict[str, list[Path]]:
    """Best-effort download of every dataset listed in the proposal."""
    out: dict[str, list[Path]] = {}
    for key in HDX_DATASETS:
        out[key] = download_dataset(key)
        log.info("dataset %s: %d files", key, len(out[key]))
    return out
