<p align="center">
  <img src="assets/logo.svg" alt="Opositor: an answer sheet with one correct choice per row" width="260">
</p>

<h1 align="center">Opositor</h1>

<p align="center">Find, rank and package open study material for any public examination.</p>

Opositor is an [Agent Skill](https://agentskills.io/specification) that turns a syllabus into a study kit:
a ranked list of free sources per topic, and — if you ask for them — a printable multiple-choice exam and a
20-minute spoken summary.

It is not tied to any exam. **The exam and its syllabus are the first parameter.** The repository holds the
method (how to search, how to score, how to examine, how to sound); each exam contributes its own profile, which
lives outside version control.

## What it does

- **Resolves the exam.** `--exam <slug>`, `$OPOSITOR_EXAM`, a word in your prompt, or the only profile on disk.
  If several are ambiguous, it asks once.
- **Returns up to 10 sources per topic**, each with the entity, type, date, the sections it covers and a reason.
  Fewer than 10 is a valid answer; padding is not.
- **Builds a practice exam** on request: 100 four-option questions, scattered answers, sources, and a solutions
  section on a separate page.
- **Produces a 20-minute spoken summary** on request: a self-contained listen page that uses your browser voices,
  or an MP3 via local neural TTS.
- **Keeps your material out of the repository.** Syllabi, notes, past exams and generated files live in a
  per-user data directory.

## Install

### Claude Code (plugin, recommended)

Register the marketplace and install the plugin:

```text
/plugin marketplace add theTestTube/opositor
/plugin install opositor --marketplace theTestTube/opositor
```

The second line also works on its own on Claude Code 2.1.275 or later, because it adds the marketplace when
needed. Then use the `opositor` skill by name (`/opositor:opositor`) or just ask in natural language. The plugin
also loads `setup` and `speak-summary`.

If you prefer the panel, run `/plugin`, add the marketplace `theTestTube/opositor` and install **Opositor** from
the list.

### Any other Agent Skills harness

The repository root is itself a valid skill, so a clone and a symlink are enough:

```bash
git clone https://github.com/theTestTube/opositor.git ~/Code/opositor
ln -s ~/Code/opositor ~/.claude/skills/opositor     # or your harness's skills directory
```

`SKILL.md`, `skills/setup` and `skills/speak-summary` all validate against the specification
(`agentskills validate`). Python is only needed for the optional parts.

### Requirements

`python3` 3.10 or newer. Everything else is optional: `reportlab` for the PDF, `piper` plus `ffmpeg` for MP3.
**You never run setup commands** — the `setup` skill diagnoses the machine, installs what is missing into a
virtual environment in your data directory, and reports what works and what degraded.

## First use

Ask in natural language: "set yourself up" or "create the X exam". The skill diagnoses the environment and
scaffolds a profile in your data directory:

```text
<data root>/<slug>/
├── config.json          exam name and scope, language, codes, PDF texts
├── syllabus.md          topics with wording, sections and search terms
├── role.md              the role: regulation, literal definition, exercise format
├── sources.md           trusted domains and entry points, axis by axis
├── materials/
│   ├── own/             your notes and past exams
│   ├── third-party/     material from elsewhere
│   ├── generated/       PDFs, scripts, listen pages and MP3s
│   └── NOTES.md         inventory of the material you supplied
└── log.md
```

Then ask for what you need:

- "topics 3 and 4 of x"
- "hard exam on topic 7"
- "summary to listen to for topic 9"
- "is there a newer call for x?"

Your data lives in the directory that `python3 scripts/opositor.py home` prints
(`~/.local/share/opositor` on Linux, `~/Library/Application Support/opositor` on macOS,
`%LOCALAPPDATA%\opositor` on Windows). Set `$OPOSITOR_DATA` to put it somewhere else.

## Structure

```text
SKILL.md                  The method (steps 0–13)
references/               Versioned, exam-agnostic core
  _index.md               The three layers and why references is split
  syllabus.md             How to read and validate a syllabus
  sources.md              Authority levels and search protocol
  role.md                 How to document the role and the exercise
  setup.md                How to create or update a profile
  audio.md                Audio engines and script rules
  plantillas/             Skeletons written by `init`
scripts/
  opositor.py             init · check · path · home · pdf · tts-page · doctor
  exam_pdf.py             JSON question bank → PDF
  tts_page.py             Script → listen page using browser voices
skills/
  setup/                  Prepares the environment and profiles (agent-run)
  speak-summary/          Local neural TTS to MP3 (Piper), reused
assets/logo.svg
.claude-plugin/           Plugin and marketplace manifests
```

## Privacy

The repository names no specific exam. Profiles are stored outside it, and `check --privacy` compares the
versioned files against a local, unversioned term list:

```bash
printf '%s\n' "term-one" "term-two" > "$(python3 scripts/opositor.py home)/.privacy.txt"
python3 scripts/opositor.py check --privacy
```

The list lives with your data, so the check runs without the repository ever naming what it protects.

## Language

- The repository, its documentation and every `description` are in **English (en-US)**. No official translation
  is shipped.
- **Generated material follows your language.** The exam, notes, scripts, PDFs, pages and answers use
  `config.json → language` (default `en-US`); PDF labels come from `config.json → pdf.texts`, and the listen
  page accepts a JSON file of interface labels (`--ui`) so its UI can follow you too.
- Keywords in the skill description include Spanish trigger phrases because users type them; that is routing,
  not a translation.

## License

[MIT](LICENSE) © 2026 theTestTube
