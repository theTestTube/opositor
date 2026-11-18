#!/usr/bin/env python3
"""CLI for the opositor skill. Standard library only.

Usage:
    python3 scripts/opositor.py init <slug> --name "..." --scope "..." [--language en-US]
    python3 scripts/opositor.py check [<slug>] [--privacy]
    python3 scripts/opositor.py path [<slug>] [--json]
    python3 scripts/opositor.py home [--json]
    python3 scripts/opositor.py pdf <bank.json> <output.pdf> [--profile <config.json>] [--difficulty low|high|max]
    python3 scripts/opositor.py overlap <new_bank.json> <earlier.json|earlier.pdf>... [--json report.json]
    python3 scripts/opositor.py tts-page <script.txt> <output.html> [--title T] [--lang en] [--ui labels.json]
    python3 scripts/opositor.py tts-page --demo <output.html>
    python3 scripts/opositor.py doctor

The data root is $OPOSITOR_DATA or, if unset, a per-user directory outside the
repository (`~/.local/share/opositor` on Linux, `~/Library/Application Support/opositor` on macOS, `%LOCALAPPDATA%\\opositor` on Windows). Profiles and outputs
live there, never inside the plugin directory, so updates cannot wipe them.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "references" / "plantillas"
IGNORED = {".git", "oposiciones", ".scratchpad", "__pycache__", ".venv", "node_modules"}


def data_root() -> Path:
    env = os.environ.get("OPOSITOR_DATA")
    if env:
        return Path(env).expanduser()
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
        return Path(base) / "opositor"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "opositor"
    xdg = os.environ.get("XDG_DATA_HOME")
    return (Path(xdg) if xdg else Path.home() / ".local" / "share") / "opositor"


def profile_dir(slug: str) -> Path:
    return data_root() / slug


def profiles():
    base = data_root()
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith("."))


def resolve_slug(slug):
    if slug:
        return slug
    available = profiles()
    if len(available) == 1:
        return available[0]
    if not available:
        sys.exit("No profiles yet. Create one with: opositor.py init <slug> ...")
    sys.exit("Several profiles found; say which one: " + ", ".join(available))


def read_config(slug):
    path = profile_dir(slug) / "config.json"
    if not path.is_file():
        sys.exit(f"Missing {path}. Is the slug right?")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"config.json is not valid JSON: {e}")


def placeholders(text):
    return sorted(set(re.findall(r"\{\{\s*([a-z0-9_]+)\s*\}\}", text)))


def count_topics(text):
    """Real topics: ### headings whose title is no longer a template placeholder."""
    return len([m for m in re.finditer(r"^###\s+(.+)$", text, re.M) if "{{" not in m.group(1)])


def render(template_name, values):
    text = (TEMPLATES / template_name).read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def cmd_init(args):
    slug = args.slug
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        sys.exit("Invalid slug: lowercase letters, digits and hyphens (e.g. my-exam).")
    destination = profile_dir(slug)
    if destination.exists():
        sys.exit(f"{destination} already exists. Use check to review it, or pick another slug.")

    for sub in ("materials/own", "materials/third-party", "materials/generated/audio"):
        (destination / sub).mkdir(parents=True, exist_ok=True)

    today = datetime.date.today().isoformat()
    common = {"slug": slug, "name": args.name, "scope": args.scope, "language": args.language}
    config = {
        "slug": slug,
        "name": args.name,
        "scope": args.scope,
        "language": args.language,
        "created": today,
        "blocks": [{"name": "Common subjects", "prefix": "C"},
                   {"name": "Specific subjects", "prefix": "E"}],
        "role_synonyms": [],
        "pdf": {"texts": {}},
        "audio": {"engine": "browser", "lang": args.language.split("-")[0].lower()},
    }
    (destination / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n",
                                             encoding="utf-8")
    (destination / "syllabus.md").write_text(render("syllabus.md", common), encoding="utf-8")
    (destination / "role.md").write_text(render("role.md", common), encoding="utf-8")
    (destination / "sources.md").write_text(render("sources.md", common), encoding="utf-8")
    (destination / "materials" / "NOTES.md").write_text(render("materials-NOTES.md", common),
                                                        encoding="utf-8")
    (destination / "log.md").write_text(
        f"# Log for {args.name}\n\n## [{today}] created | Profile scaffolded from the empty template\n",
        encoding="utf-8")

    print(f"Profile created: {destination}")
    print("Next: fill syllabus.md with the official programme, role.md with the role regulation")
    print("and sources.md with the domains; then run `opositor.py check " + slug + "`.")


def cmd_check(args):
    errors, warnings = [], []
    slug = args.slug

    if not slug:
        available = profiles()
        if len(available) == 1:
            slug = available[0]
        elif not args.privacy:
            resolve_slug(None)  # no single profile and no privacy check: nothing to validate

    if slug:
        base = profile_dir(slug)
        if not base.is_dir():
            sys.exit(f"No such profile: {base}")

        try:
            config = read_config(slug)
        except SystemExit as e:
            print(e)
            return 1
        for field in ("slug", "name", "scope", "language"):
            if not str(config.get(field, "")).strip():
                errors.append(f"config.json: missing '{field}'")

        expected = {
            "syllabus.md": ("syllabus", count_topics, 1),
            "role.md": ("role profile", None, None),
            "sources.md": ("sources", None, None),
            "materials/NOTES.md": ("materials inventory", None, None),
        }
        for rel, (label, measure, minimum) in expected.items():
            path = base / rel
            if not path.is_file():
                errors.append(f"missing {rel} ({label})")
                continue
            text = path.read_text(encoding="utf-8")
            pending = placeholders(text)
            if pending:
                warnings.append(f"{rel}: {len(pending)} unreplaced placeholder(s): "
                                + ", ".join(pending[:6]))
            if measure and measure(text) < minimum:
                errors.append(f"{rel}: no topic detected (### ...)")

        sources = base / "sources.md"
        if sources.is_file() and "http" not in sources.read_text(encoding="utf-8"):
            warnings.append("sources.md: no starting URL")

        role_text = base / "role.md"
        if role_text.is_file():
            t = role_text.read_text(encoding="utf-8")
            if "Literal definition" not in t:
                warnings.append("role.md: missing the 'Literal definition' section")
            if re.search(r"Checked[^\n]*\{\{", t):
                warnings.append("role.md: missing the check date")

        topics = (count_topics((base / "syllabus.md").read_text(encoding="utf-8"))
                  if (base / "syllabus.md").is_file() else 0)
        print(f"Profile: {base}")
        print(f"Topics detected: {topics}")
        for e in errors:
            print(f"  ✗ {e}")
        for w in warnings:
            print(f"  · {w}")
        if not errors and not warnings:
            print("  ✓ Profile complete")

    if args.privacy:
        errors += review_privacy()
    return 1 if errors else 0


def versioned_files():
    try:
        output = subprocess.run(["git", "-C", str(ROOT), "ls-files"],
                                capture_output=True, text=True, check=True).stdout
        files = [ROOT / line for line in output.splitlines() if line.strip()]
        if files:
            return files
    except Exception:
        pass
    # No git, or nothing tracked yet: scan the tree, minus what is ignored.
    return [p for p in ROOT.rglob("*")
            if p.is_file() and not (set(p.relative_to(ROOT).parts) & IGNORED)]


def matches(term, text):
    """Short terms are matched as whole words so acronyms inside other words are not flagged."""
    t = term.strip()
    if len(t) <= 8 and " " not in t:
        return re.search(rf"(?<!\w){re.escape(t)}(?!\w)", text, re.I) is not None
    return t.lower() in text.lower()


def review_privacy():
    listing = data_root() / ".privacy.txt"
    if not listing.is_file():
        print(f"  · privacy: no term list at {listing}; nothing to check")
        return []
    terms = [t.strip() for t in listing.read_text(encoding="utf-8").splitlines()
             if t.strip() and not t.startswith("#")]
    if not terms:
        return []
    findings = []
    for path in versioned_files():
        if not path.is_file() or path.suffix.lower() in {".pdf", ".png", ".jpg", ".mp3", ".wav"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for term in terms:
            if matches(term, text):
                findings.append(f"privacy: '{term}' appears in {path.relative_to(ROOT)}")
    if findings:
        print("  ✗ Private terms leaked into versioned files:")
        for f in findings:
            print(f"    {f}")
    else:
        print(f"  ✓ Privacy: {len(terms)} term(s) searched in "
              f"{len(versioned_files())} versioned file(s), no matches")
    return findings


def cmd_path(args):
    slug = resolve_slug(args.slug)
    base = profile_dir(slug)
    if not base.is_dir():
        sys.exit(f"No such profile: {base}")
    data = {
        "profile": str(base),
        "config": str(base / "config.json"),
        "syllabus": str(base / "syllabus.md"),
        "role": str(base / "role.md"),
        "sources": str(base / "sources.md"),
        "materials": str(base / "materials"),
        "generated": str(base / "materials" / "generated"),
        "audio": str(base / "materials" / "generated" / "audio"),
        "own": str(base / "materials" / "own"),
        "third_party": str(base / "materials" / "third-party"),
    }
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for key, value in data.items():
            print(f"{key}: {value}")


def venv_python() -> Path:
    folder = "Scripts" if os.name == "nt" else "bin"
    name = "python.exe" if os.name == "nt" else "python"
    return data_root() / "venv" / folder / name


def cmd_home(args):
    root = data_root()
    python = venv_python()
    usable = python.is_file()
    if args.json:
        print(json.dumps({
            "data": str(root),
            "venv": str(root / "venv"),
            "python": str(python) if usable else sys.executable,
            "privacy_list": str(root / ".privacy.txt"),
        }, ensure_ascii=False, indent=2))
        return
    print(root)


def python_with_reportlab():
    for candidate in (venv_python(), Path(sys.executable)):
        if candidate.is_file() and subprocess.run(
                [str(candidate), "-c", "import reportlab"], capture_output=True).returncode == 0:
            return str(candidate)
    return None


def cmd_pdf(args):
    interpreter = python_with_reportlab()
    if not interpreter:
        sys.exit("reportlab is not available. Run skills/setup, step 1, and try again.")
    argv = [interpreter, str(ROOT / "scripts" / "exam_pdf.py"), args.bank, args.pdf]
    if args.profile:
        argv += ["--profile", args.profile]
    if args.difficulty:
        argv += ["--difficulty", args.difficulty]
    return subprocess.run(argv).returncode


def cmd_overlap(args):
    argv = [sys.executable, str(ROOT / "scripts" / "overlap.py"), args.bank, *args.previous]
    if args.json:
        argv += ["--json", args.json]
    return subprocess.run(argv).returncode


def cmd_tts_page(args):
    sys.path.insert(0, str(ROOT / "scripts"))
    from tts_page import build_page

    if args.demo:
        text = ("Voice test. If you can hear this, the browser has at least one voice installed "
                "and the page works. Change voice and speed with the controls.")
        title = args.title or "Browser voice test"
    else:
        if not args.text:
            sys.exit("Missing script: opositor.py tts-page <script.txt> <output.html>")
        source = Path(args.text)
        if not source.is_file():
            sys.exit(f"No such script: {source}")
        text = source.read_text(encoding="utf-8")
        title = args.title or source.stem

    labels = None
    if args.ui:
        ui_path = Path(args.ui)
        if not ui_path.is_file():
            sys.exit(f"No such labels file: {ui_path}")
        labels = json.loads(ui_path.read_text(encoding="utf-8"))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_page(text, title, args.lang, labels), encoding="utf-8")
    words = len(text.split())
    print(f"{output}: {words} words ~ {round(words / 167)} min at 167 wpm")
    print("Open it in Edge, Chrome, Firefox or Brave. If there are no voices, the page will say so.")


def cmd_doctor(args):
    def status(ok, detail=""):
        return f"{'✓' if ok else '✗'} {detail}".strip()

    print(f"Repository: {ROOT}")
    print(f"Data: {data_root()}")
    v = sys.version_info
    print(status(v >= (3, 10), f"Python {v.major}.{v.minor}.{v.micro}"))
    interpreter = python_with_reportlab()
    if interpreter:
        version = subprocess.run([interpreter, "-c", "import reportlab; print(reportlab.Version)"],
                                 capture_output=True, text=True).stdout.strip()
        print(status(True, f"reportlab {version} (PDF available, {interpreter})"))
    else:
        print(status(False, "reportlab missing -> run skills/setup, step 1"))
    for binary in ("ffmpeg", "ffprobe", "piper"):
        path = shutil.which(binary)
        print(status(bool(path), f"{binary}: {path or 'not found'}"))
    voices = Path.home() / ".cache" / "opositor" / "voices"
    n = len(list(voices.glob("*.onnx"))) if voices.is_dir() else 0
    print(status(bool(n), f"Piper voices: {n} in {voices}"))
    browsers = [b for b in ("microsoft-edge", "google-chrome", "chromium", "brave-browser", "firefox")
                if shutil.which(b)]
    print(status(bool(browsers),
                 "browsers: " + (", ".join(browsers) or "none -> listen page cannot be verified")))
    available = profiles()
    print(status(bool(available), "profiles: " + (", ".join(available) or "none")))
    print("\nMP3 and PDF are optional. Without them: sources yes, exam degraded, audio through the browser.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="create a profile from the templates")
    p.add_argument("slug")
    p.add_argument("--name", required=True)
    p.add_argument("--scope", required=True)
    p.add_argument("--language", default="en-US")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("check", help="validate a profile and, on request, the core's privacy")
    p.add_argument("slug", nargs="?")
    p.add_argument("--privacy", action="store_true")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("path", help="resolved profile paths")
    p.add_argument("slug", nargs="?")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_path)

    p = sub.add_parser("home", help="print the data root")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_home)

    p = sub.add_parser("pdf", help="build the practice exam PDF with the right interpreter")
    p.add_argument("bank")
    p.add_argument("pdf")
    p.add_argument("--profile", help="config.json of the profile (name, scope and document texts)")
    p.add_argument("--difficulty", choices=("low", "high", "max"))
    p.set_defaults(func=cmd_pdf)

    p = sub.add_parser("overlap", help="check a new bank against the topic's earlier exams")
    p.add_argument("bank", help="new question bank (JSON)")
    p.add_argument("previous", nargs="+", help="earlier banks (JSON) or exam PDFs of the same topic")
    p.add_argument("--json", help="write the full report to this file")
    p.set_defaults(func=cmd_overlap)

    p = sub.add_parser("tts-page", help="generate the browser listen page")
    p.add_argument("text", nargs="?")
    p.add_argument("output")
    p.add_argument("--title")
    p.add_argument("--lang", default="en")
    p.add_argument("--ui", help="JSON file with interface labels in the user's language")
    p.add_argument("--demo", action="store_true", help="test text to check the voices")
    p.set_defaults(func=cmd_tts_page)

    p = sub.add_parser("doctor", help="environment status")
    p.set_defaults(func=cmd_doctor)

    args = ap.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()

