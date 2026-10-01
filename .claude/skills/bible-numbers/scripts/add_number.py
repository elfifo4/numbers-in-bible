#!/usr/bin/env python3
"""
Create (or extend) a number file from the app's own verse text.

Each --verse names a verse and the words to bold, written without nikud, in the order they appear:

  add_number.py 372 --verse "עזרא:ב:ד=שלש מאות שבעים ושנים" --verse "נחמיה:ז:ט=שלש מאות שבעים ושנים"

Chapter/verse may be Hebrew numerals or digits, in the app's numbering. The verse text `t` is taken from
the app (qere only, makaf and sof pasuk kept), the given words are wrapped in <b>…</b> one by one, and
formatted/<n>.json + minified/<n>.json are written (UTF-16 BE + BOM), and data/all-numbers*.json and
all_numbers.js are rebuilt. Dry run unless --write.
"""

import argparse
import sys

import numlib as L


def parse_ref(spec: str):
    ref, words = spec.split("=", 1)
    book, c, v = ref.split(":")
    if book not in L.BOOKS:
        raise SystemExit(f"unknown book {book!r}")
    num = lambda s: int(s) if s.isdigit() else L.gematria(s)  # noqa: E731
    return book, num(c), num(v), [L.skeleton(w) for w in words.split()]


def make_verse(book: str, c: int, v: int, bold_words: list[str]) -> dict:
    tokens = L.app_tokens(L.BOOKS.index(book), c, v)
    if tokens is None:
        raise SystemExit(f"{book} {c}:{v} is not in the app's text")
    words, seps = L.app_t_parts(tokens)
    bold = [False] * len(words)
    pos = 0
    for target in bold_words:  # in order, each after the previous one
        while pos < len(words) and L.skeleton(words[pos]) != target:
            pos += 1
        if pos == len(words):
            raise SystemExit(f"{book} {c}:{v}: word {target!r} not found (in order) in: "
                             + " ".join(L.skeleton(w) for w in words))
        bold[pos] = True
        pos += 1
    return {"b": book, "c": L.hebrew_numeral(c), "t": L.build_t(words, seps, bold), "v": L.hebrew_numeral(v)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("number", type=int)
    ap.add_argument("--verse", action="append", required=True, help="'ספר:פרק:פסוק=מילים להדגשה'")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    path = L.REPO / "formatted" / f"{args.number}.json"
    data = L.load(args.number) if path.exists() else {"times": 0, "verses": []}
    have = {(x["b"], x["c"], x["v"]) for x in data["verses"]}
    for spec in args.verse:
        x = make_verse(*parse_ref(spec))
        if (x["b"], x["c"], x["v"]) in have:
            raise SystemExit(f"{x['b']} {x['c']}:{x['v']} is already in {args.number}.json")
        data["verses"].append(x)
        print(f"{x['b']} {x['c']}:{x['v']}: {x['t']}")
    data["verses"].sort(key=L.SORT_KEY)
    data["times"] = len(data["verses"])
    print(f"\n{args.number}.json: {data['times']} verse(s)" + ("" if path.exists() else " (new file)"))
    if args.write:
        L.save(args.number, data)
        L.rebuild_aggregates()
        print("written (and data/all-numbers*.json + all_numbers.js rebuilt)")
    else:
        print("Dry run — pass --write to write the files.")


if __name__ == "__main__":
    sys.exit(main())
