#!/usr/bin/env bash
# Turn a text script into an MP3 with Piper, fast local neural synthesis.
#
# Usage: tts-piper.sh <input.txt> <output.mp3> [voice.onnx]
#
# Piper needs no account, works offline and runs far above real time on CPU.
# It is this skill's MP3 engine; the alternative that installs nothing is the browser
# listen page (`scripts/opositor.py tts-page`).
#
# Voice selection order:
#   1. third argument (path to an .onnx)
#   2. $SPEAK_PIPER_VOICE (a name such as en_US-lessac-medium, or a path)
#   3. the first voice that starts with $SPEAK_PIPER_LANG (default "en")
set -euo pipefail

IN="${1:?usage: tts-piper.sh <input.txt> <output.mp3> [voice.onnx]}"
OUT="${2:?usage: tts-piper.sh <input.txt> <output.mp3> [voice.onnx]}"
VOICE_ARG="${3:-}"

PIPER_HOME="${SPEAK_PIPER_HOME:-$HOME/.cache/opositor/piper-venv}"
VOICE_DIR="${SPEAK_PIPER_VOICES:-$HOME/.cache/opositor/voices}"
LANG_CODE="${SPEAK_PIPER_LANG:-en}"

PIPER_BIN="${SPEAK_PIPER_BIN:-$PIPER_HOME/bin/piper}"
[ -x "$PIPER_BIN" ] || {
  echo "piper not found. Prepare the engine with:" >&2
  echo "  python3 -m venv $PIPER_HOME && $PIPER_HOME/bin/python -m pip install piper-tts" >&2
  echo "and leave at least one .onnx model (with its .json) in $VOICE_DIR" >&2
  exit 1
}

resolve_voice() {
  local want="${1:-${SPEAK_PIPER_VOICE:-}}"
  if [ -z "$want" ]; then
    local first
    first="$(find "$VOICE_DIR" -maxdepth 1 -name "${LANG_CODE}_*.onnx" | sort | head -1)"
    [ -n "$first" ] && { echo "$first"; return 0; }
    first="$(find "$VOICE_DIR" -maxdepth 1 -name '*.onnx' | sort | head -1)"
    [ -n "$first" ] && { echo "$first"; return 0; }
    echo "No voice in $VOICE_DIR (looking for an $LANG_CODE .onnx)" >&2
    return 1
  fi
  case "$want" in
    */*) echo "$want" ;;
    *) echo "$VOICE_DIR/$want.onnx" ;;
  esac
}

VOICE="$(resolve_voice "$VOICE_ARG")" || exit 1
[ -f "$VOICE" ] || { echo "Voice model not found: $VOICE" >&2; exit 1; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Strip markdown that would otherwise be read aloud as noise.
python3 - "$IN" "$WORK/speech.txt" <<'PY'
import re, sys, pathlib
src = pathlib.Path(sys.argv[1]).read_text()
src = re.sub(r'```.*?```', ' ', src, flags=re.S)
src = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', src)
src = re.sub(r'^\s*#{1,6}\s*', '', src, flags=re.M)
src = re.sub(r'^\s*[-*+]\s+', '', src, flags=re.M)
src = re.sub(r'[*_`>|~]+', '', src)
src = re.sub(r'https?://\S+', '', src)
src = re.sub(r'[ \t]+', ' ', src)
src = re.sub(r'\n{2,}', '\n\n', src).strip()
if not src:
    raise SystemExit("No speakable text found in input.")
pathlib.Path(sys.argv[2]).write_text(src)
PY

"$PIPER_BIN" --model "$VOICE" --output-file "$WORK/speech.wav" \
  --sentence-silence 0.35 --input-file "$WORK/speech.txt"

mkdir -p "$(dirname "$OUT")"
if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -hide_banner -loglevel error -y -i "$WORK/speech.wav" \
    -c:a libmp3lame -b:a 96k -ac 1 "$OUT"
else
  OUT="${OUT%.mp3}.wav"
  cp "$WORK/speech.wav" "$OUT"
  echo "Note: ffmpeg not available; wrote WAV instead." >&2
fi

echo "Wrote $OUT ($(du -h "$OUT" | cut -f1), voice $(basename "$VOICE" .onnx))"
