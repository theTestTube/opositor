---
name: speak-summary
description: 'Convert text, markdown, or a summary produced by another skill into a listenable MP3 using local CPU-only neural text-to-speech. Rewrites written prose for the ear before synthesising. Use when the user asks to "read this out", "turn this into audio", "make an MP3", "I want to listen to this", "podcast version", or wants a spoken digest for a commute or breakfast.'
---

# Speak Summary

Turn written text into audio someone will actually want to listen to.

This skill is deliberately a **terminal step in a chain**. Another skill (or you)
produces the text; this one makes it listenable. It pairs naturally with
`roundup`, `daily-prep`, `meeting-minutes`, or any summarisation work.

Everything runs locally on CPU. No text is sent to a cloud speech service, which
matters when the content is confidential, and it means the skill works in a
headless cloud agent or CI container just as well as on a laptop.

## Prerequisites

This copy ships **two engines**, and the default one is [Piper](https://github.com/rhasspy/piper):

| Engine | Voices | Account | Speed |
|---|---|---|---|
| **Piper** (default) | One neural model per language, no login | None | Far above real time |
| [`pocket-tts`](https://github.com/kyutai-labs/pocket-tts) (upstream) | Multilingual, short catalogue, voice cloning | Hugging Face login for cloning | Similar or slower |

Piper needs `piper` and at least one voice model. The `setup` skill installs both
for you; by hand it is:

```bash
python3 -m venv ~/.cache/opositor/piper-venv
~/.cache/opositor/piper-venv/bin/python -m pip install piper-tts
```

Voice models (`.onnx` plus a `.json` beside it) go in `~/.cache/opositor/voices`.
The engine picks the first model whose name starts with `SPEAK_PIPER_LANG`
(default `en`), so a profile in another language sets that variable.

To use the upstream engine instead, install it and set `SPEAK_ENGINE=pocket`:

```bash
pip install pocket-tts          # any platform
brew install pocket-tts         # macOS, if preferred
```

`pocket-tts` requires **Python >=3.10 and <3.15**. The script searches for a
compatible interpreter rather than assuming `python3` is one — worth knowing if
you are on a very new Python, where installation would otherwise fail.

You also need an encoder. `ffmpeg` is strongly preferred (`brew install ffmpeg`
or `apt-get install -y ffmpeg`); on macOS the script falls back to the built-in
`afconvert` and emits `.m4a` instead of `.mp3`. Without any encoder, the Piper
route writes a `.wav`.

The first `pocket-tts` run downloads its model (~1GB) from Hugging Face. After
that it is fully offline and synthesises roughly 6x faster than real-time.

## The important step: rewrite for the ear

**Do not feed written text straight into the synthesiser.** Prose that reads well
on screen is tiring to listen to. Rewriting it first is what separates a useful
audio digest from an unlistenable one.

Produce a spoken script that:

- **Opens with orientation.** What this is, what it covers, roughly how long it runs.
- **Replaces bullets with connective prose.** "First… The bigger one is… Finally…" — a listener has no visual structure to lean on, so carry it in the language.
- **Expands abbreviations on first use.** "PR" becomes "pull request", "CI" becomes "continuous integration". Acronyms that read fine are noise when spoken.
- **Speaks dates and numbers naturally.** "the twentieth of August", not "2026-08-20". "About three thousand", not "2,847".
- **Never reads URLs aloud.** Say "linked in the written version" instead.
- **Uses short sentences.** Split anything past roughly 25 words.
- **Signposts transitions.** "Turning to the product side…", "Two things need your attention…".
- **Ends with the actions.** Recap what the listener should do, since that is what they need to retain and they cannot scroll back.
- **Drops anything purely visual.** Tables, code blocks, and diagrams should be summarised in a sentence or omitted, never read out.

Write this spoken script to its own `.txt` file. Keep the original written
version with its links intact — the audio is a companion to it, not a
replacement. The user will want to click through later.

## Synthesise

```bash
./scripts/tts.sh <input.txt> <output.mp3> [voice.safetensors]
```

The script strips any residual markdown, splits the text on sentence boundaries
into ~600 character chunks (quality degrades on long single inputs), synthesises
each chunk, and concatenates the result into a mono MP3 at 96kbps — small enough
to sync to a phone, good enough for speech.

By default the script delegates to `tts-piper.sh`, which synthesises in one pass.
Set `SPEAK_ENGINE=pocket` to use the upstream chunking path described above.

Environment overrides:

| Variable | Purpose |
|---|---|
| `SPEAK_ENGINE` | `piper` (default) or `pocket`. |
| `SPEAK_PIPER_BIN` | Path to the `piper` binary. Default `~/.cache/opositor/piper-venv/bin/piper`. |
| `SPEAK_PIPER_VOICES` | Voice model directory. Default `~/.cache/opositor/voices`. |
| `SPEAK_PIPER_LANG` | Language prefix used to pick a voice. Default `en`. |
| `SPEAK_TTS_BIN` | Path to a specific `pocket-tts` binary; skips all auto-detection. |
| `SPEAK_TTS_HOME` | Where to create/find the cached virtualenv. Default `~/.cache/speak-summary/venv`. |

## Voices

With Piper, pass a model as the third argument, or set `SPEAK_PIPER_VOICE`.
With `pocket-tts`, the default English voice is `alba`, and voice cloning from a
short clean audio sample is available:

```bash
pocket-tts export-voice --help
```

Pass the resulting `.safetensors` file as the third argument to the script.

Only clone a voice you have the rights to use. Do not clone a real person's
voice — colleague, customer, or public figure — without their explicit consent.

## Output

- Default to `~/Music/Briefings/` unless the user says otherwise; it is easy to point a phone or podcast app at.
  When the text comes from the `opositor` skill, write to `<profile>/materials/generated/audio/` instead, next
  to the script.
- Name files `<subject>-<YYYY-MM-DD>.mp3`.
- Report the path, duration, and size.
- Offer to play it: `afplay <path>` on macOS, `ffplay -nodisp -autoexit <path>` elsewhere.

## Length guidance

Aim for 4–6 minutes for a routine digest, which is roughly 600–900 spoken words
at a natural pace. If the source would run past about 10 minutes, say so and
offer either a tighter edit or a split into multiple files — attention drops off
sharply beyond that for informational audio.

## Chaining onto other skills

The natural pattern is *gather → summarise → speak*:

- `roundup` → `speak-summary` — a spoken version of the status briefing.
- `daily-prep` → `speak-summary` — tomorrow's schedule, listened to tonight.
- `meeting-minutes` → `speak-summary` — catch up on a meeting you missed.

When invoked as part of a chain, do not re-summarise. The upstream skill owns
what to say; this skill owns how it sounds. Take its output, rewrite it for the
ear, and synthesise.

To run unattended (a briefing waiting before breakfast), schedule the upstream
skill with a workflow and have it finish by calling this one.

## Troubleshooting

**Audio cuts off mid-sentence.** A chunk exceeded the model's comfortable length.
Shorten the sentences in the spoken script.

**Words mispronounced.** Spell them phonetically in the input — "Kubernetes" as
"koo-ber-net-eez". This is a normal part of preparing a spoken script.

**First run is slow.** That is the one-off model download. Later runs start in
about a second.

**`pocket-tts` not found after install.** The virtualenv may be stale, or your
`python3` may be outside the supported 3.10–3.14 range. Delete
`~/.cache/speak-summary/venv` and re-run, or point `SPEAK_TTS_BIN` at a known binary.
