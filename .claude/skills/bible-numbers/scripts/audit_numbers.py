#!/usr/bin/env python3
"""
Audit numbers-in-bible. Read-only: prints a report by category (and writes it with --out).

Structure (must all be zero):
  format       BOM, formatted == minified, no \\/ escaping, no trailing newline, key order, times == #verses
  order        verses sorted by the app's book order, chapter, verse; no duplicate verse; known book names
  aggregates   data/all-numbers*.json and all_numbers.js match the number files
  text         `t` without tags == the app's verse text (qere, makaf, sof pasuk), in the app's numbering
  bold_punct   a makaf / sof pasuk / paseq / space inside <b>…</b>

Content (candidates to review — the detector in numparse.py only knows cardinal numbers):
  bold_other_value   a fully bolded cardinal phrase whose value is not the file's number
  bold_partial       only part of a cardinal phrase is bolded
  unbolded           the file's number appears in an included verse without bold
  missing_verse      the detector finds n in a verse that n.json doesn't have
  no_file            the detector finds a value that has no file

Findings already reviewed with the user live in reviewed.json (same "category|n|ref" keys as printed);
they are counted but not listed. Add a finding there only after it was reviewed.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numlib as L
import numparse as P

HERE = Path(__file__).resolve().parent
STRUCTURAL = ["format", "order", "aggregates", "text", "bold_punct"]
CONTENT = ["bold_other_value", "bold_partial", "unbolded", "missing_verse", "no_file"]


def ref(b, c, v) -> str:
    return f"{b} {c}:{v}"


def app_string(b: int, c: int, v: int) -> str | None:
    tokens = L.app_tokens(b, c, v)
    if tokens is None:
        return None
    s = ""
    for tok in tokens:
        if s and not s.endswith(L.MAKAF):
            s += " "
        s += tok
    return s


def audit():
    F = defaultdict(list)
    nums = L.numbers()
    data = {}
    for n in nums:
        for style in L.STYLES:
            raw = L.read_file(L.REPO / style / f"{n}.json")
            if "\\/" in raw or raw.endswith("\n") or raw != L.dumps(json.loads(raw), style):
                F["format"].append((n, "", f"{style}/{n}.json is not in the canonical format"))
        try:
            d = data[n] = L.load(n)
        except ValueError as e:
            F["format"].append((n, "", str(e)))
            continue
        if list(d) != ["times", "verses"] or d["times"] != len(d["verses"]):
            F["format"].append((n, "", f"times={d['times']} verses={len(d['verses'])}"))
        for x in d["verses"]:
            if list(x) not in (["b", "c", "t", "v"], ["b", "c", "t", "v", "i"]):
                F["format"].append((n, ref(x["b"], x["c"], x["v"]), f"key order {list(x)}"))
        if any(x["b"] not in L.BOOKS for x in d["verses"]):
            F["order"].append((n, "", "unknown book name"))
            continue
        keys = [L.SORT_KEY(x) for x in d["verses"]]
        if keys != sorted(keys):
            F["order"].append((n, "", "verses not sorted"))
        if len(set(keys)) != len(keys):
            F["order"].append((n, "", "duplicate verse"))

    # aggregates
    for name in ("all-numbers.json", "all-numbers.min.json"):
        try:
            agg = json.loads(L.read_file(L.REPO / "data" / name))
        except ValueError as e:
            F["aggregates"].append((0, "", f"{name}: {e}"))
            continue
        if agg != {str(n): data.get(n) for n in nums}:
            F["aggregates"].append((0, "", f"data/{name} is out of date (run rebuild_aggregates.py)"))
    js = [int(x) for x in re.findall(r"\d+", (L.REPO / "all_numbers.js").read_text(encoding="utf-8"))]
    if js != nums:
        F["aggregates"].append((0, "", "all_numbers.js is out of date (run rebuild_aggregates.py)"))

    # text, bold
    found_in_file = defaultdict(set)
    for n, d in data.items():
        for x in d["verses"]:
            r = ref(x["b"], x["c"], x["v"])
            b, c, v = L.BOOKS.index(x["b"]), L.gematria(x["c"]), L.gematria(x["v"])
            found_in_file[n].add((b, c, v))
            app = app_string(b, c, v)
            if app is None:
                F["text"].append((n, r, "verse not in the app"))
            elif re.sub("</?b>", "", x["t"]) != app:
                F["text"].append((n, r, "text differs from the app (run unify_text.py)"))
            for span in re.findall("<b>(.*?)</b>", x["t"]):
                if re.search(f"[{L.MAKAF}{L.SOF_PASUK}{L.PASEQ} ]", span) or not L.letters(span):
                    F["bold_punct"].append((n, r, span))
            words, _, bold = L.parse_t(x["t"])
            for value, idx in P.phrases(words, b):
                flags = [bold[i] for i in idx]
                text = " ".join(L.skeleton(words[i]) for i in idx)
                if all(flags) and value != n:
                    F["bold_other_value"].append((n, r, f"{text} = {value}"))
                elif any(flags) and not all(flags):
                    bw = " ".join(L.skeleton(words[i]) for i in idx if bold[i])
                    F["bold_partial"].append((n, r, f"[{text}] = {value}, bold [{bw}]"))
                elif value == n and not any(flags):
                    F["unbolded"].append((n, r, text))

    # completeness
    for b, c, v, value, idx in P.scan_tanakh():
        r = ref(L.BOOKS[b], L.hebrew_numeral(c), L.hebrew_numeral(v))
        words = P.verse_words(b, c, v)
        text = " ".join(L.skeleton(words[i]) for i in idx)
        if value not in data:
            F["no_file"].append((value, r, text))
        elif (b, c, v) not in found_in_file[value]:
            F["missing_verse"].append((value, r, text))
    return F


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="also write the report to this file")
    ap.add_argument("--all", action="store_true", help="list reviewed findings too")
    ap.add_argument("--save-reviewed", action="store_true",
                    help="mark every current content finding as reviewed (only after reviewing them!)")
    args = ap.parse_args()

    reviewed_file = HERE / "reviewed.json"
    reviewed = json.loads(reviewed_file.read_text(encoding="utf-8")) if reviewed_file.exists() else {}
    F = audit()
    key = lambda cat, f: f"{cat}|{f[0]}|{f[1]}|{f[2]}"  # noqa: E731

    lines, open_issues = [], 0
    for cat in STRUCTURAL + CONTENT:
        items = F.get(cat, [])
        new = [f for f in items if key(cat, f) not in reviewed]
        open_issues += len(new)
        lines.append(f"== {cat}: {len(items)}" + (f" ({len(items) - len(new)} reviewed)" if cat in CONTENT else ""))
        for f in sorted(items if args.all else new, key=lambda f: (f[0], f[1])):
            note = reviewed.get(key(cat, f))
            lines.append(f"   {f[0]:>7}  {f[1]:<22} {f[2]}" + (f"   [reviewed: {note}]" if note else ""))
    report = "\n".join(lines)
    print(report)
    if args.out:
        Path(args.out).write_text(report + "\n", encoding="utf-8")
    if args.save_reviewed:
        for cat in CONTENT:
            for f in F.get(cat, []):
                reviewed.setdefault(key(cat, f), "reviewed")
        reviewed_file.write_text(json.dumps(dict(sorted(reviewed.items())), ensure_ascii=False, indent=1) + "\n",
                                 encoding="utf-8")
        print(f"\n{len(reviewed)} finding(s) marked as reviewed in {reviewed_file.name}")
    return 1 if open_issues else 0


if __name__ == "__main__":
    sys.exit(main())
