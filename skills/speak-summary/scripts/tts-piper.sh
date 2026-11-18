#!/usr/bin/env bash
# Convierte un guion de texto en un MP3 con Piper, síntesis neuronal local y rápida.
#
# Uso: tts-piper.sh <entrada.txt> <salida.mp3> [voz.onnx]
#
# Piper no necesita cuenta, funciona sin conexión y va muy por encima del tiempo real en CPU.
# Es el motor de MP3 de esta skill; la alternativa sin instalar nada es la página de escucha
# del navegador (`scripts/opositor.py tts-page`).
#
# Orden de elección de voz:
#   1. tercer argumento (ruta a un .onnx)
#   2. $SPEAK_PIPER_VOICE (nombre tipo es_ES-davefx-medium, o ruta)
#   3. la primera voz que empiece por $SPEAK_PIPER_LANG (por defecto «es»)
set -euo pipefail

IN="${1:?usage: tts-piper.sh <input.txt> <output.mp3> [voice.onnx]}"
OUT="${2:?usage: tts-piper.sh <input.txt> <output.mp3> [voice.onnx]}"
VOICE_ARG="${3:-}"

PIPER_HOME="${SPEAK_PIPER_HOME:-$HOME/.cache/opositor/piper-venv}"
VOICE_DIR="${SPEAK_PIPER_VOICES:-$HOME/.cache/opositor/voices}"
LANG_CODE="${SPEAK_PIPER_LANG:-es}"

PIPER_BIN="${SPEAK_PIPER_BIN:-$PIPER_HOME/bin/piper}"
[ -x "$PIPER_BIN" ] || {
  echo "piper no encontrado. Prepara el motor con:" >&2
  echo "  python3 -m venv $PIPER_HOME && $PIPER_HOME/bin/python -m pip install piper-tts" >&2
  echo "y deja al menos un modelo .onnx (con su .json) en $VOICE_DIR" >&2
  exit 1
}

resolve_voice() {
  local want="${1:-${SPEAK_PIPER_VOICE:-}}"
  if [ -z "$want" ]; then
    local primera
    primera="$(find "$VOICE_DIR" -maxdepth 1 -name "${LANG_CODE}_*.onnx" | sort | head -1)"
    [ -n "$primera" ] && { echo "$primera"; return 0; }
    primera="$(find "$VOICE_DIR" -maxdepth 1 -name '*.onnx' | sort | head -1)"
    [ -n "$primera" ] && { echo "$primera"; return 0; }
    echo "No hay ninguna voz en $VOICE_DIR (busca un .onnx de $LANG_CODE)" >&2
    return 1
  fi
  case "$want" in
    */*) echo "$want" ;;
    *) echo "$VOICE_DIR/$want.onnx" ;;
  esac
}

VOICE="$(resolve_voice "$VOICE_ARG")" || exit 1
[ -f "$VOICE" ] || { echo "Modelo de voz no encontrado: $VOICE" >&2; exit 1; }

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
  echo "Note: ffmpeg no disponible; escrito WAV en su lugar." >&2
fi

echo "Wrote $OUT ($(du -h "$OUT" | cut -f1), voz $(basename "$VOICE" .onnx))"
