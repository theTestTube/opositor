#!/usr/bin/env python3
"""Check a new question bank against the exams already generated for the same topic.

Usage:
    python3 overlap.py new_bank.json previous1.json previous2.pdf ... [--json report.json]

A previous exam can be a JSON bank or a PDF built by exam_pdf.py (read with `pdftotext`,
from poppler-utils). The rule it enforces (SKILL.md, section 9, "No repeats across levels"):

- A question may come back, but never as "same question + same answer". When a new question is
  close to an earlier one (same stem, or the same idea worded alike), its correct answer must be
  worded another way and none of its four options may reuse an option of the earlier question.
- Two different questions that happen to share a correct answer are fine.

Similarity is the higher of two measures on normalised text (lower case, no accents, no
punctuation): the character ratio of difflib and the overlap of content words. Thresholds:

    stem   >= 0.60  the questions are "the same question"
    option >= 0.75  two options are "the same option"

Exit status 1 if there is any conflict, so the caller can fix the bank and run it again.
Both bank schemas are accepted: English (blocks/questions/answer/distractors) and Spanish
(bloques/preguntas/ok/mal).
"""
import argparse
import difflib
import json
import re
import subprocess
import sys
import unicodedata

STEM, OPTION = 0.60, 0.75
STOP = set("""a al ante con de del desde e el en entre la las lo los o para por que se segun sin
sobre su sus un una uno y the of to in on for and or is are be by with as at an its which what
cual cuales es son como esta este esto""".split())


def norm(text):
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9%]+", " ", text).strip()


def words(text):
    return {w for w in norm(text).split() if w not in STOP and len(w) > 2}


def similarity(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    wa, wb = words(a), words(b)
    overlap = len(wa & wb) / min(len(wa), len(wb)) if wa and wb else 0.0
    # Word overlap on very short texts ("3", "Grave") says little; weigh it only from 3 words.
    if min(len(wa), len(wb)) < 3:
        overlap = 0.0
    return max(ratio, overlap)


def from_json(path):
    with open(path, encoding="utf-8") as f:
        bank = json.load(f)
    items = []
    for block in bank.get("blocks", bank.get("bloques", [])):
        scenario = block.get("scenario", block.get("supuesto", ""))
        for q in block.get("questions", block.get("preguntas", [])):
            answer = q.get("answer", q.get("ok"))
            wrong = q.get("distractors", q.get("mal", []))
            items.append({"q": q["q"], "answer": answer, "options": [answer, *wrong],
                          "scenario": scenario})
    return items


def from_pdf(path):
    """Questions with their options, then the solutions section (number -> correct text)."""
    text = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True,
                          check=True).stdout
    text = re.sub(r"\f", "\n", text)
    # The solutions section is the last one, and its lines end with the check mark.
    cut = max(text.rfind("\nSoluciones\n"), text.rfind("\nSolutions\n"))
    body, tail = (text[:cut], text[cut:]) if cut > 0 else (text, "")
    answers = {}
    for m in re.finditer(r"(?m)^(\d{1,3})\. ([a-d])\) (.+?)\s*(?:✔|\(correcta\)|\(correct\))",
                         tail, re.S):
        answers.setdefault(int(m.group(1)), " ".join(m.group(3).split()))
    items, current = [], None
    for line in body.splitlines():
        line = line.strip()
        if m := re.match(r"^(\d{1,3})\. (.+)", line):
            current = {"n": int(m.group(1)), "q": m.group(2), "options": [], "scenario": ""}
            items.append(current)
        elif current and (m := re.match(r"^([a-d])\) (.+)", line)):
            current["options"].append(m.group(2))
        elif current and line and not re.match(r"^(Bloque|Block|Página|Page)\b", line):
            if current["options"]:
                current["options"][-1] += " " + line
            elif len(current["options"]) == 0:
                current["q"] += " " + line
    out = []
    for it in items:
        # Older PDFs mark the correct option in place instead of in a solutions section.
        # The page footer can be glued after the mark, so cut everything that follows it.
        marked = [o for o in it["options"] if "✔" in o]
        if marked and it["n"] not in answers:
            it["options"] = [re.sub(r"\s*✔.*$", "", o) for o in it["options"]]
            answers[it["n"]] = re.sub(r"\s*✔.*$", "", marked[0])
        if it["n"] in answers and len(it["options"]) == 4:
            out.append({"q": it["q"], "answer": answers[it["n"]], "options": it["options"],
                        "scenario": ""})
    return out


def load(path):
    return from_pdf(path) if path.lower().endswith(".pdf") else from_json(path)


def check(new, previous):
    conflicts = []
    for i, q in enumerate(new, 1):
        for source, items in previous.items():
            for old in items:
                s = similarity(q["q"], old["q"])
                if s < STEM:
                    continue
                same_answer = similarity(q["answer"], old["answer"])
                reused = [o for o in q["options"]
                          if any(similarity(o, p) >= OPTION for p in old["options"])]
                if same_answer >= OPTION or reused:
                    conflicts.append({
                        "question": i, "stem": q["q"][:90], "source": source,
                        "previous": old["q"][:90], "stem_similarity": round(s, 2),
                        "answer_similarity": round(same_answer, 2),
                        "reused_options": [r[:60] for r in reused]})
    return conflicts


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bank", help="new question bank (JSON)")
    ap.add_argument("previous", nargs="+", help="earlier banks (JSON) or exam PDFs of the topic")
    ap.add_argument("--json", help="write the full report to this file")
    args = ap.parse_args()

    new = load(args.bank)
    previous = {p: load(p) for p in args.previous}
    for p, items in previous.items():
        print(f"{p}: {len(items)} earlier questions read", file=sys.stderr)
        if not items:
            sys.exit(f"Could not read any question from {p}: check the file before trusting the result.")
        if p.lower().endswith(".pdf") and len(items) % 10:
            print(f"Warning: {p} gave {len(items)} questions; some may not have been read.",
                  file=sys.stderr)
    conflicts = check(new, previous)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(conflicts, f, ensure_ascii=False, indent=1)
    for c in conflicts:
        why = "same answer" if c["answer_similarity"] >= OPTION else "reused options"
        print(f"Q{c['question']} ~ {c['source']} ({why}, stem {c['stem_similarity']}):\n"
              f"   new: {c['stem']}\n   old: {c['previous']}\n"
              f"   reused: {'; '.join(c['reused_options']) or '-'}")
    print(f"{len(new)} new questions · {sum(len(v) for v in previous.values())} earlier · "
          f"{len(conflicts)} conflicts", file=sys.stderr)
    sys.exit(1 if conflicts else 0)


if __name__ == "__main__":
    main()
