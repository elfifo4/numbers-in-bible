#!/usr/bin/env python3
"""
List every verse where the detector (numparse.py) finds the number, with the words that form it, ready
to pass to add_number.py. Candidates only: review each one (homographs, names, separate counts).

  find_number.py 372
"""

import argparse

import numlib as L
import numparse as P


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("number", type=int)
    args = ap.parse_args()

    path = L.REPO / "formatted" / f"{args.number}.json"
    have = {(x["b"], x["c"], x["v"]) for x in L.load(args.number)["verses"]} if path.exists() else set()
    hits = 0
    for b, c, v, value, idx in P.scan_tanakh():
        if value != args.number:
            continue
        hits += 1
        words = P.verse_words(b, c, v)
        bc, vc = L.hebrew_numeral(c), L.hebrew_numeral(v)
        mark = "in file" if (L.BOOKS[b], bc, vc) in have else "NEW"
        spec = f'{L.BOOKS[b]}:{bc}:{vc}={" ".join(L.letters(words[i]) for i in idx)}'
        print(f'{mark:<8} --verse "{spec}"')
        print(f'         {" ".join(words)}')
    print(f"\n{hits} candidate(s); {len(have)} verse(s) already in {args.number}.json")


if __name__ == "__main__":
    main()
