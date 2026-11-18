#!/usr/bin/env python3
"""Watch for new Castilian Spanish voices usable with pocket-tts.

Weekly cron-style check. Compares three sources against the previous snapshot:

  1. the kyutai/tts-voices repository (donated / public voice samples)
  2. Hugging Face models matching "pocket-tts" that mention Spanish
  3. the pocket-tts model card voice catalogue

A change does not mean a better accent: it means there is something new worth
listening to. Nothing is downloaded and nothing is installed; this only reports.

Usage:
    python3 voice-watch.py            # check, report changes
    python3 voice-watch.py --status   # show last snapshot summary only

State lives in $SPEAK_VOICE_WATCH_DIR (default ~/.cache/opositor/voice-watch).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

STATE_DIR = Path(
    os.environ.get("SPEAK_VOICE_WATCH_DIR", Path.home() / ".cache/opositor/voice-watch")
).expanduser()
SNAPSHOT = STATE_DIR / "snapshot.txt"
REPORTS = STATE_DIR / "reports"
LOG = STATE_DIR / "log.md"

TTL_HOURS = 24  # allow skipping a re-fetch if a check already ran today
TIMEOUT = 60

# A voice counts as Spanish-relevant if its path or name says so. Deliberately
# narrow: plain "es" would match half the internet.
SPANISH_RE = re.compile(r"(spanish|espa[nñ]ol|castell|castilian|\bes[-_](es|ES)\b|lola)", re.I)

SOURCES = {
    "tts-voices": "https://huggingface.co/kyutai/tts-voices/resolve/main/README.md",
}

PIPER_TREE = "https://huggingface.co/api/models/rhasspy/piper-voices/tree/main/es?recursive=true&limit=1000"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "speak-summary-voice-watch/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def next_cursor(link_header: str) -> str | None:
    m = re.search(r'[?&]cursor=([^&>]+)[^>]*>;\s*rel="next"', link_header or "")
    return m.group(1) if m else None


def tts_voice_files() -> list[str]:
    """Every file path in kyutai/tts-voices, paginated."""
    paths: list[str] = []
    url: str | None = (
        "https://huggingface.co/api/models/kyutai/tts-voices/tree/main?recursive=true&limit=1000"
    )
    seen = 0
    while url and seen < 20:
        req = urllib.request.Request(url, headers={"User-Agent": "speak-summary-voice-watch/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            entries = json.load(r)
            cursor = next_cursor(r.headers.get("link", ""))
        paths.extend(e["path"] for e in entries)
        url = (
            f"https://huggingface.co/api/models/kyutai/tts-voices/tree/main"
            f"?recursive=true&limit=1000&cursor={cursor}"
            if cursor
            else None
        )
        seen += 1
    return paths


def hf_pocket_models() -> list[str]:
    """Community pocket-tts models whose name suggests Spanish."""
    data = json.loads(fetch("https://huggingface.co/api/models?search=pocket-tts&limit=200"))
    return [m["id"] for m in data if SPANISH_RE.search(m["id"])]


def piper_es_voices() -> list[str]:
    """Castilian (es_ES) voices in rhasspy/piper-voices. Ungated, no login."""
    out: list[str] = []
    url: str | None = PIPER_TREE
    seen = 0
    while url and seen < 20:
        req = urllib.request.Request(url, headers={"User-Agent": "speak-summary-voice-watch/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            entries = json.load(r)
            cursor = next_cursor(r.headers.get("link", ""))
        out.extend(
            e["path"] for e in entries if e["path"].endswith(".onnx") and "/es_ES/" in e["path"]
        )
        url = (
            "https://huggingface.co/api/models/rhasspy/piper-voices/tree/main/es"
            f"?recursive=true&limit=1000&cursor={cursor}"
            if cursor
            else None
        )
        seen += 1
    return out


def collect() -> tuple[list[str], list[str]]:
    """Gather Spanish candidates. One failing source must not kill the check."""
    snap: list[str] = []
    errors: list[str] = []
    steps = (
        ("tts-voices", lambda: [f"tts-voices::{p}" for p in tts_voice_files() if SPANISH_RE.search(p)]),
        ("hf-model", lambda: [f"hf-model::{m}" for m in hf_pocket_models()]),
        ("piper-es_ES", lambda: [f"piper::{p}" for p in piper_es_voices()]),
    )
    for name, step in steps:
        try:
            snap += step()
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append(f"{name}: {exc}")
    return sorted(set(snap)), errors


def notify(title: str, body: str) -> None:
    if shutil.which("notify-send") and (
        os.environ.get("DBUS_SESSION_BUS_ADDRESS") or os.environ.get("DISPLAY")
    ):
        subprocess.run(["notify-send", "-a", "speak-summary", title, body], check=False)


def main() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()

    if "--status" in sys.argv:
        if not SNAPSHOT.exists():
            print("No snapshot yet: run without --status first.")
            return 0
        lines = SNAPSHOT.read_text().splitlines()
        print(f"{len(lines)} known Spanish candidates (snapshot {SNAPSHOT})")
        print("\n".join(lines[:20]))
        return 0

    try:
        current, errors = collect()
    except Exception as exc:  # noqa: BLE001 - never fail the timer
        print(f"voice-watch: check aborted ({exc})", file=sys.stderr)
        return 0
    for err in errors:
        print(f"voice-watch: aviso, fuente no disponible -> {err}", file=sys.stderr)

    previous = SNAPSHOT.read_text().splitlines() if SNAPSHOT.exists() else []
    new = [l for l in current if l not in previous]
    gone = [l for l in previous if l not in current]

    SNAPSHOT.write_text("\n".join(current) + "\n")

    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"- {stamp} · {len(current)} candidatos · {len(new)} nuevos · {len(gone)} desaparecidos\n")

    if not new and not gone:
        print(f"voice-watch: sin cambios ({len(current)} candidatos).")
        return 0

    report = REPORTS / f"{today}.md"
    body = [f"# Voces españolas: cambios {stamp}", ""]
    if new:
        body += ["## Nuevas", ""] + [f"- `{l}`" for l in new] + [""]
    if gone:
        body += ["## Ya no están", ""] + [f"- `{l}`" for l in gone] + [""]
    body += [
        "## Siguiente paso",
        "",
        "Escuchar las muestras nuevas y quedarse con la que suene castellana",
        "(distinción /θ/ en *z*, *ce*, *ci*; sin seseo ni ceceo).",
        "",
    ]
    report.write_text("\n".join(body), encoding="utf-8")

    notify(
        "speak-summary: voces nuevas",
        f"{len(new)} candidata(s) en español. Abre {report}",
    )
    print(f"voice-watch: {len(new)} nuevas, {len(gone)} desaparecidas -> {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
