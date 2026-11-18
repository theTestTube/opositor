#!/usr/bin/env python3
"""Watch for new voices usable with the configured language.

Weekly cron-style check. Compares three sources against the previous snapshot:

  1. the kyutai/tts-voices repository (donated / public voice samples)
  2. Hugging Face models matching "pocket-tts" that mention the language
  3. the Piper voice catalogue for that language

A change does not mean a better voice: it means there is something new worth
listening to. Nothing is downloaded and nothing is installed; this only reports.

Usage:
    python3 voice-watch.py            # check, report changes
    python3 voice-watch.py --status   # show last snapshot summary only

Language: $SPEAK_WATCH_LANG (default "en"). State lives in
$SPEAK_VOICE_WATCH_DIR (default ~/.cache/opositor/voice-watch).
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
LANG_CODE = os.environ.get("SPEAK_WATCH_LANG", "en").split("-")[0].lower()

# English names for the languages pocket-tts and Piper publish. An unknown code
# still works: only the code itself is matched.
LANG_NAMES = {
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "de": "german",
    "it": "italian",
    "pt": "portuguese",
    "nl": "dutch",
}
LANG_NAME = LANG_NAMES.get(LANG_CODE, LANG_CODE)

# A voice counts as relevant if its path or name says so. Deliberately narrow:
# a bare two-letter code would match half the internet.
LANG_RE = re.compile(rf"({re.escape(LANG_NAME)}|(?<![a-z]){re.escape(LANG_CODE)}[-_][A-Z]{{2}})", re.I)

SOURCES = {
    "tts-voices": "https://huggingface.co/kyutai/tts-voices/resolve/main/README.md",
}

PIPER_TREE = (
    f"https://huggingface.co/api/models/rhasspy/piper-voices/tree/main/{LANG_CODE}"
    "?recursive=true&limit=1000"
)


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
    """Community pocket-tts models whose name suggests the language."""
    data = json.loads(fetch("https://huggingface.co/api/models?search=pocket-tts&limit=200"))
    return [m["id"] for m in data if LANG_RE.search(m["id"])]


def piper_lang_voices() -> list[str]:
    """Voices for the configured language in rhasspy/piper-voices. Ungated, no login."""
    out: list[str] = []
    url: str | None = PIPER_TREE
    seen = 0
    while url and seen < 20:
        req = urllib.request.Request(url, headers={"User-Agent": "speak-summary-voice-watch/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            entries = json.load(r)
            cursor = next_cursor(r.headers.get("link", ""))
        out.extend(
            e["path"] for e in entries
            if e["path"].endswith(".onnx") and f"/{LANG_CODE}_" in e["path"]
        )
        url = (
            f"https://huggingface.co/api/models/rhasspy/piper-voices/tree/main/{LANG_CODE}"
            f"?recursive=true&limit=1000&cursor={cursor}"
            if cursor
            else None
        )
        seen += 1
    return out


def collect() -> tuple[list[str], list[str]]:
    """Gather candidates for the language. One failing source must not kill the check."""
    snap: list[str] = []
    errors: list[str] = []
    steps = (
        ("tts-voices", lambda: [f"tts-voices::{p}" for p in tts_voice_files() if LANG_RE.search(p)]),
        ("hf-model", lambda: [f"hf-model::{m}" for m in hf_pocket_models()]),
        ("piper", lambda: [f"piper::{p}" for p in piper_lang_voices()]),
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
        print(f"{len(lines)} known {LANG_NAME} candidates (snapshot {SNAPSHOT})")
        print("\n".join(lines[:20]))
        return 0

    try:
        current, errors = collect()
    except Exception as exc:  # noqa: BLE001 - never fail the timer
        print(f"voice-watch: check aborted ({exc})", file=sys.stderr)
        return 0
    for err in errors:
        print(f"voice-watch: warning, source unavailable -> {err}", file=sys.stderr)

    previous = SNAPSHOT.read_text().splitlines() if SNAPSHOT.exists() else []
    new = [line for line in current if line not in previous]
    gone = [line for line in previous if line not in current]

    SNAPSHOT.write_text("\n".join(current) + "\n")

    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"- {stamp} · {len(current)} candidates · {len(new)} new · {len(gone)} gone\n")

    if not new and not gone:
        print(f"voice-watch: no changes ({len(current)} candidates).")
        return 0

    report = REPORTS / f"{today}.md"
    body = [f"# {LANG_NAME.capitalize()} voices: changes {stamp}", ""]
    if new:
        body += ["## New", ""] + [f"- `{line}`" for line in new] + [""]
    if gone:
        body += ["## Gone", ""] + [f"- `{line}`" for line in gone] + [""]
    body += [
        "## Next step",
        "",
        f"Listen to the new samples and keep the one that sounds right for {LANG_NAME}.",
        "Set it with SPEAK_PIPER_VOICE, or drop it in the voices directory.",
        "",
    ]
    report.write_text("\n".join(body), encoding="utf-8")

    notify(
        "speak-summary: new voices",
        f"{len(new)} {LANG_NAME} candidate(s). Open {report}",
    )
    print(f"voice-watch: {len(new)} new, {len(gone)} gone -> {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
