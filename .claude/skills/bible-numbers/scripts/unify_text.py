#!/usr/bin/env python3
"""
Rewrite every verse text `t` from the app's own text (the source of truth), keeping the bold words.

The app's text keeps makaf, shows the qere only, and drops the final sof pasuk (the app adds it). The bold flags are carried over word
by word: the file's words and the app's words are aligned by their consonants, and a bolded word maps
to the app word in the same aligned position (a spelling difference between editions, e.g. מאות/מאת,
still maps one-to-one). A verse whose bold can't be mapped unambiguously is left untouched and listed.

Dry run by default; --write rewrites the files (also normalizing the JSON: no \\/ escaping, no
trailing newline, key order b,c,t,v[,i]).
"""

import argparse
import difflib
import re
import sys

import numlib as L

KEY_ORDER = ["b", "c", "t", "v", "i"]


def plene(w: str) -> str:
    return re.sub("[וי]", "", w)


def convert(x: dict):
    """-> (new_t, note) or (None, reason)."""
    b, c, v = L.BOOKS.index(x["b"]), L.gematria(x["c"]), L.gematria(x["v"])
    tokens = L.app_tokens(b, c, v)
    if tokens is None:
        return None, "verse not in the app"
    aw, aseps = L.app_t_parts(tokens)
    fw, _, fb = L.parse_t(x["t"])
    A = [L.skeleton(w) for w in aw]
    F = [L.skeleton(w) for w in fw]
    bold = [False] * len(aw)
    notes = []
    sm = difflib.SequenceMatcher(None, F, A, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                if fb[i1 + k]:
                    bold[j1 + k] = True
                    if F[i1 + k] != A[j1 + k]:
                        notes.append(f"{F[i1 + k]}→{A[j1 + k]}")
        elif any(fb[i1:i2]):
            return None, f"bold inside an unaligned span: file[{' '.join(F[i1:i2])}] app[{' '.join(A[j1:j2])}]"
    if sum(bold) != sum(fb):
        return None, "bold count changed"
    for f, a in zip([F[i] for i in range(len(F)) if fb[i]], [A[j] for j in range(len(A)) if bold[j]]):
        if f != a and plene(f) != plene(a) and sum(p != q for p, q in zip(f, a)) + abs(len(f) - len(a)) > 1:
            return None, f"bold word differs too much: {f} vs {a}"
    return L.build_t(aw, aseps, bold), "; ".join(notes)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", type=int, action="append", help="only these numbers")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--show", type=int, default=0, help="print N example conversions")
    args = ap.parse_args()

    changed = same = 0
    failed, noted, shown = [], [], 0
    for n in args.only or L.numbers():
        data = L.load(n)
        for x in data["verses"]:
            new, note = convert(x)
            ref = f"{n} {x['b']} {x['c']}:{x['v']}"
            if new is None:
                failed.append(f"{ref}: {note}")
                continue
            if note:
                noted.append(f"{ref}: {note}")
            if new == x["t"]:
                same += 1
            else:
                changed += 1
                if shown < args.show:
                    print(f"{ref}\n  old: {x['t']}\n  new: {new}\n")
                    shown += 1
                x["t"] = new
        data["verses"] = [{k: x[k] for k in KEY_ORDER if k in x} for x in data["verses"]]
        if args.write:
            L.save(n, data)
    print(f"changed {changed}, already identical {same}, left untouched {len(failed)}")
    print(f"\nbold word spelled differently in the app ({len(noted)}):")
    for s in noted:
        print("  " + s)
    print(f"\nleft untouched ({len(failed)}):")
    for s in failed:
        print("  " + s)
    if not args.write:
        print("\nDry run — pass --write to rewrite the files.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
