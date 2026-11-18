---
title: Audio and players
description: How a script becomes something listenable. Two engines in use (browser voice and Piper to MP3), why the browser cannot export its own voice, what a WASM engine would cost, and the rules of the spoken script.
layer: core
---

# Audio and players

Two ways to listen to a topic, at different costs. The default one installs nothing.

| | Listen page | Local MP3 (Piper) |
|---|---|---|
| Requirements | A browser with voices | `piper`, voices and `ffmpeg` |
| Output | Self-contained HTML | `.mp3` |
| Installation | None | Python environment + voice download |
| Voice | The system's, selectable | Fixed neural model |
| Offline | Yes | Yes |
| Exportable | **No** | Yes |
| Typical use | Reviewing on the desktop, following the script | Car, phone, sharing |

## The listen page

```bash
python3 scripts/opositor.py tts-page script.txt <profile>/materials/generated/audio/E7_summary.html \
  --title "Topic E7 · Summary"
```

It generates a dependency-free HTML file that opens in Edge, Chrome, Firefox or Brave. It uses the **Web Speech
API** (`speechSynthesis`), which every modern desktop browser implements:

| Browser | Voices | Note |
|---|---|---|
| Edge | System + high-quality online voices | Online voices may need a connection |
| Chrome | System voices | On Linux it goes through `speech-dispatcher` |
| Brave | Chromium voices | Same as Chrome; reading mode does not replace the page |
| Firefox | System voices | On Linux, without `speech-dispatcher` it may have no voices |
| Safari | System voices | Works, with a different voice selection |

The page has a voice selector (filtered by the profile's language), speed, the current paragraph highlighted,
click a paragraph to start there, and keyboard shortcuts. If it detects zero voices, it says so and offers MP3.

The page chrome is in English. If the user works in another language, write a small JSON file with the labels
and pass it with `--ui:` the accepted keys are `play`, `pause`, `resume`, `previous`, `next`, `stop`, `voice`,
`speed`, `ready`, `finished`, `stopped`, `paused`, `resumed`, `paragraph`, `of`, `error`, `no_voices` and
`footer`. Missing keys keep the English default, so a partial file is fine.

### What the browser cannot do

**It cannot export the audio it synthesises.** `speechSynthesis` plays directly to the output device; it does
not expose a `MediaStream`, so `MediaRecorder` cannot capture it. The `chrome.tts` API can deliver audio chunks,
but only to extensions, not to a normal page. Recording the system output with a virtual device is possible
outside the browser, and it is not portable: it is not proposed.

Capturing the tab does not help either. Tab audio capture (`getDisplayMedia({audio: true})`) records the audio
of the tab's graph, and in Chromium the synthesised voice does not go through it: it comes out of the system
speech engine, outside the tab. It is documented in issue
[40753195](https://issues.chromium.org/issues/40753195), open since 2021. Only **full-screen capture with system
audio** picks up that voice, and that forces sharing the desktop, mixes in every other sound and depends on the
operating system.

And even if it were captured, it would not be an MP3: `MediaRecorder` returns WebM/Opus, and **no browser encodes
MP3** (`AudioEncoder` with `mp3` has 0% support in the WebCodecs table; it only decodes). Converting it requires
a third-party JavaScript library.

Practical consequence: if the user asks for "an MP3", generate it with Piper. If they ask to "listen to it", the
page is enough and is instant.

### The third route: MP3 with an engine inside the page

There is a way to generate audio — and MP3 — inside a page: **do not use the system voice, use a synthesis
engine compiled to WebAssembly**. Projects such as `piper-tts-web` (MIT) return a WAV ready to download, and
with a JavaScript encoder (`lamejs`) it becomes an MP3.

What it costs, measured with the figures published by those projects:

| Piece | Size | Note |
|---|---|---|
| Piper voice (`.onnx` + `.json`) | 30–75 MB | One per language, browser cache |
| `onnxruntime-web` | ~10 MB | Inference engine |
| espeak-ng data | ~17 MB | Phonemisation |
| MP3 encoder in JS | ~150 KB | Required: the browser does not encode MP3 |

Two consequences that postpone it, not that make it impossible:

1. **It does not save the installation, it moves it.** The first time ~90 MB must be downloaded, and it cannot
   be cached if the page is opened with `file://`: that origin is opaque and the browser gives it no persistent
   storage. It has to be served over `http://localhost`, that is, a static server.
2. **It is slower and sounds worse than the system voice.** CPU inference runs at 3–5× real time; the current
   page is instant and uses the voice the user already has installed.

That is why the listen page has no download button: a button that only works in half the cases and after a
90 MB download is worse than telling the truth. The WASM route stays as an open door for a Python-free mode,
not as a feature of this page. If it is ever implemented, it goes as a separate page with its own contract: size
warning, cache on an `http` origin and optional MP3.

### Feasibility check

- **Chromium and Brave in headless mode return zero voices** (there is no audio device), so feasibility cannot
  be verified from an agent without a display. The page includes its own diagnostic: when opened, it shows how
  many voices it finds.
- **Linux:** the browser speaks through `speech-dispatcher`. If it is not installed, or the browser is confined
  (snap), the voice list may be empty even when the system has voices.
- **Windows and macOS:** system voices are available out of the box; it is the simplest case.

## MP3 with Piper

```bash
skills/speak-summary/scripts/tts.sh script.txt <profile>/materials/generated/audio/E7_summary_2026-11-15.mp3
```

- A 20-minute summary takes under a minute of CPU.
- Check duration and size with `ffprobe`. If it drifts from 20 minutes (under 18, over 22), adjust the script
  and regenerate.
- The voice is chosen by the profile's language (`SPEAK_PIPER_LANG`, default `en`). Do not invent voice names or
  change the voice unless the user asks.

## The script

The script is what makes the audio useful. It is written for the ear, not read from the notes.

- **Fixed duration, variable density.** 20 minutes. At roughly 167 words per minute, that is 3,200–3,500 words.
  In another language, measure the chosen voice's speed once and adjust the range.
- **No visual marks.** No bullets, no tables, no code, no URLs. Nothing the listener cannot see.
- **Opening with orientation:** which topic it is, which sections it covers and how long it lasts.
- **Explicit connectors:** "First…", "The delicate point is…", "To finish…".
- **Abbreviations expanded** the first time; figures and dates the way they are spoken.
- **Sentences under 25 words.** Audio is not re-read.
- **Close with what to retain** and a review question.
- **80/20 split:** if there is own material, its structure and concepts lead; every figure is verified against
  an open source before it is said out loud.

## Known errors

| Symptom | Cause | Fix |
|---|---|---|
| The page is silent | Zero voices | Install system voices; use MP3 |
| It speaks in another language | The system's default voice | Choose a voice in the selector |
| It cuts off mid-sentence | Paragraph too long | Shorter paragraphs in the script |
| It mispronounces a name | Opaque spelling | Write it phonetically in the script |
| The MP3 lasts 12 minutes | Short script | Expand the content, do not stretch the filler |
| No download button on the page | Deliberate: the browser cannot capture its voice or encode MP3 | Generate the MP3 with Piper |
