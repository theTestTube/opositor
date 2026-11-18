---
name: setup
description: Prepare this plugin and a new examination profile so the opositor skill can run without the user typing commands. Detects Python, the PDF library, audio engines and browser voices, installs only what is missing, scaffolds a profile under the data root, and reports what works and what degraded.
---

# Preparing the environment

This skill is run by **the agent**, not the user. The user asks ("set yourself up", "install what is missing",
"create the X exam") and you run the commands, check the result and report what is left.

Hard rule: **never ask the user to run commands**. If something cannot be solved without privileges, explain it
in one line and continue with the closest degradation.

## 0. Diagnose before installing

Run this and keep the output:

```bash
python3 --version
python3 -c "import reportlab, sys; print('reportlab', reportlab.Version)" 2>&1 | tail -1
command -v ffmpeg ffprobe piper uv pipx
ls ~/.cache/opositor/voices 2>/dev/null
python3 scripts/opositor.py home
```

How to read it:

| Signal | Meaning | Action |
|---|---|---|
| `python3` ≥ 3.10 | Correct base | Continue |
| `python3` < 3.10 | Unsupported | Warn: the interpreter must be updated; the rest may work |
| `reportlab` imports | PDF available | Nothing to do |
| `ModuleNotFoundError` | PDF missing | Step 1 |
| `ffmpeg` and `ffprobe` present | MP3 and duration checks | Nothing to do |
| `piper` or voices in `~/.cache/opositor/voices` | MP3 without the browser | Nothing to do |
| No audio at all | Browser listen page only | That is valid: it is the default mode |

**Do not assume `uv`.** It is great if it is there, but the main path is the distribution's `venv` + `pip`. If
there is no `venv` either, the path is `pip install --user`, and if the system blocks installation (PEP 668),
the skill stays in degraded mode and says so.

**The data root is outside the repository.** `opositor.py home` prints it: `$OPOSITOR_DATA` when set, otherwise
a per-user directory (`~/.local/share/opositor` on Linux, `~/Library/Application Support/opositor` on macOS,
`%LOCALAPPDATA%\opositor` on Windows). Never write inside the plugin directory: plugin updates replace it.

## 1. PDF (optional, but needed for exams)

Create the environment inside the data root, so it survives plugin updates:

```bash
ROOT="$(python3 scripts/opositor.py home)"
python3 -m venv "$ROOT/venv" && "$ROOT/venv/bin/python" -m pip install --upgrade pip reportlab
```

If `python3 -m venv` fails because the system module is missing, try these in order and stop at the first that
works:

1. `python3 -m venv --without-pip "$ROOT/venv"` and then `python3 -m ensurepip --upgrade` inside the
   environment.
2. `pip install --user reportlab` (no environment).
3. `uv venv "$ROOT/venv" && uv pip install --python "$ROOT/venv/bin/python" reportlab`, only if `uv` exists.
4. `pipx` is no use here: reportlab is a library, not an application.

If nothing works, report that the exam will be HTML or will not be generated, and continue. **Do not install
system packages or use `sudo`** without the user's explicit permission.

Always verify with the same interpreter that will be used later:

```bash
"$ROOT/venv/bin/python" -c "import reportlab; print(reportlab.Version)"
```

The `opositor.py pdf` command finds that interpreter by itself, so in the final answer you only need to say
whether the PDF is available or degraded.

## 2. Audio

There are two routes and **the default one installs nothing**:

| Route | Requirements | Output | When |
|---|---|---|---|
| Listen page | Only a browser with system voices | Self-contained HTML | Default |
| MP3 with Piper | `piper` + voices + `ffmpeg` | `.mp3` | Car, phone, sharing, no browser |

1. **Check the browser.** Generate a test page and open it:

   ```bash
   python3 scripts/opositor.py tts-page --demo .scratchpad/voice-test.html
   ```

   The page itself lists the voices it detects. If it says "0 voices", explain the system fix
   (`speech-dispatcher` on Linux; Windows and macOS usually ship voices) and offer MP3.
2. **Install Piper only if the user wants MP3.** Separate environment, without touching the PDF one:

   ```bash
   python3 -m venv ~/.cache/opositor/piper-venv
   ~/.cache/opositor/piper-venv/bin/python -m pip install piper-tts
   ```

   Voices go to `~/.cache/opositor/voices` (one per profile language). Do not download voices without saying
   which one and why.
3. **Do not promise MP3 if Piper is missing.** The listen page cannot export audio: the browser synthesises and
   plays, it does not write files.

## 3. Creating an exam profile

With the environment ready, create the profile following `references/setup.md`:

```bash
python3 scripts/opositor.py init <slug> --name "<name>" --scope "<administration>" [--language en-US]
```

Then fill the files with official data (syllabus, role profile, sources and `materials/NOTES.md`) and validate:

```bash
python3 scripts/opositor.py check <slug>
```

If the user already had a profile from an earlier version, `check` is the first thing to run: it says which
fields are missing without touching anything.

## 4. Final verification

```bash
python3 scripts/opositor.py doctor
python3 scripts/opositor.py check --privacy
```

`doctor` summarises interpreter, PDF, audio and detected profiles. `check --privacy` compares the versioned
files with the local list of terms and warns about any leak before publishing.

## 5. What the agent reports

A short table, no jargon:

| Piece | Status | How it is used |
|---|---|---|
| Python 3.x | ✅ / ⚠️ | |
| PDF (`reportlab`) | ✅ / ❌ | Exam as PDF or degraded |
| Listen page | ✅ | Opens in the browser |
| MP3 (`piper`) | ✅ / ❌ | Downloadable audio |
| Profile `<slug>` | ✅ / pending | |

And one sentence with the concrete next step. No lists of commands to copy and paste.

## Known errors

- **`externally-managed-environment`** when installing: that is PEP 668. Use a virtual environment; do not force
  it with `--break-system-packages`.
- **`No module named venv`**: the system lacks `python3-venv`. Fall back to `pip --user`.
- **The listen page says nothing**: the browser has no voices or the audio is muted. On Linux, install
  `speech-dispatcher` and a voice; in snap browsers, confinement can block access.
- **Piper installs but cannot find the model**: the voice must be in the voices directory with its `.json` next
  to it.
