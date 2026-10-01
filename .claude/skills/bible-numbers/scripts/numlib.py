"""
Shared helpers for the numbers-in-bible scripts (Python 3, stdlib only).

- the app's own verse text (BibleContestAndroidApp moko-resources assets/allChapters, UTF-16), which is
  the source of truth for both the verse text `t` and the numbering `c`/`v`
- the number files: formatted/<n>.json + minified/<n>.json, UTF-16 BE with a BOM
- a word-level view of `t` with one bold flag per word
"""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
APP_CHAPTERS = REPO.parent / "BibleContestAndroidApp/shared/src/commonMain/moko-resources/assets/allChapters"

# Same order as BibleCatalog.books in the app.
BOOKS = [
    "בראשית", "שמות", "ויקרא", "במדבר", "דברים", "יהושע", "שופטים", "שמואל א", "שמואל ב",
    "מלכים א", "מלכים ב", "ישעיהו", "ירמיהו", "יחזקאל", "הושע", "יואל", "עמוס", "עובדיה",
    "יונה", "מיכה", "נחום", "חבקוק", "צפניה", "חגי", "זכריה", "מלאכי", "תהילים", "משלי",
    "איוב", "שיר השירים", "רות", "איכה", "קהלת", "אסתר", "דניאל", "עזרא", "נחמיה",
    "דברי הימים א", "דברי הימים ב",
]
MAKAF, PASEQ, SOF_PASUK, NUN_HAFUCHA = "־", "׀", "׃", "׆"
FINALS = str.maketrans("ךםןףץ", "כמנפצ")
_GEM = dict(zip("אבגדהוזחטיכלמנסעפצקרשת",
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400]))


def letters(s: str) -> str:
    return re.sub(r"[^א-ת]", "", s)


def skeleton(s: str) -> str:
    """Consonants only, final letters normalized: used to compare words across editions."""
    return letters(s).translate(FINALS)


def gematria(s: str) -> int:
    return sum(_GEM[ch] for ch in skeleton(s))


def hebrew_numeral(n: int) -> str:
    """15 -> טו, 16 -> טז, 37 -> לז (the form used for c/v)."""
    out = ""
    for val, ch in [(400, "ת"), (300, "ש"), (200, "ר"), (100, "ק"), (90, "צ"), (80, "פ"), (70, "ע"),
                    (60, "ס"), (50, "נ"), (40, "מ"), (30, "ל"), (20, "כ"), (10, "י")]:
        while n >= val:
            out += ch
            n -= val
    if out.endswith("י") and n in (5, 6):
        return out[:-1] + ("טו" if n == 5 else "טז")
    return out + ("" if not n else "אבגדהוזחט"[n - 1])


def is_mark(ch: str) -> bool:
    """Nikud / te'amim (not makaf, paseq, sof pasuk or nun hafucha)."""
    return "֑" <= ch <= "ׇ" and ch not in (MAKAF, PASEQ, SOF_PASUK, NUN_HAFUCHA)


# ---------------------------------------------------------------- the app's text

_chapters: dict = {}


def app_chapter(book: int, chapter: int) -> dict:
    """{verse: [(kind, token)]}; kind 'w' plain word, 'k' ketiv (unpointed), 'q' qere (pointed, was in
    parentheses). A token keeps a trailing makaf ("אֶת־"); a paseq stands alone; sof pasuk stays on the
    last word."""
    key = (book, chapter)
    if key in _chapters:
        return _chapters[key]
    files = list(APP_CHAPTERS.glob(f"_{book + 1}_*-{chapter:0{3 if book == 26 else 2}d}.txt"))
    out: dict = {}
    if files:
        text = files[0].read_bytes().decode("utf-16")
        text = re.sub(r"\{[^}]*\}", " ", text.split("\n", 1)[1])  # title line, {פ} {ס}
        cur, expected = 0, 1
        for tok in text.split():
            if not any(is_mark(c) for c in tok) and re.fullmatch("[א-ת]{1,3}", tok) and gematria(tok) == expected:
                cur, expected = expected, expected + 1
                out[cur] = []
                continue
            if not cur or tok == NUN_HAFUCHA:
                continue
            for part in re.split(f"(?<={MAKAF})", tok):
                if not part:
                    continue
                prev = out[cur][-1] if out[cur] else None
                if part.startswith("(") or (prev and prev[0] == "q" and "(" in prev[2] and ")" not in prev[2]):
                    out[cur].append(("q", part.replace("(", "").replace(")", ""), part))
                elif letters(part) and not any(is_mark(c) for c in part):
                    out[cur].append(("k", part, part))
                else:
                    out[cur].append(("w", part, part))
        out = {v: [(k, t) for k, t, _ in toks] for v, toks in out.items()}
    _chapters[key] = out
    return out


def app_verse(book: int, chapter: int, verse: int):
    return app_chapter(book, chapter).get(verse)


def app_tokens(book: int, chapter: int, verse: int, with_ketiv: bool = False) -> list[str] | None:
    """The verse as the number files show it: the qere only (unless with_ketiv), makaf kept, and **no sof
    pasuk at the end** — the app appends "׃" to every verse it shows (addGershaimAndColon), so a stored
    one would be shown twice ("אֶחָד׃׃")."""
    av = app_verse(book, chapter, verse)
    if av is None:
        return None
    tokens = [t for k, t in av if k != "k" or with_ketiv]
    if tokens:
        tokens[-1] = tokens[-1].rstrip(SOF_PASUK)
    return tokens


# ---------------------------------------------------------------- verse text <-> words with bold flags

# letters and nikud/te'amim only: makaf (05BE), paseq (05C0), sof pasuk (05C3) and nun hafucha (05C6)
# are separators, so they never end up inside <b>…</b>
WORD = re.compile("[֑-ׇֽֿׁׂׅׄא-ת׳״‍]+")


def parse_t(t: str):
    """-> (words, seps, bold): seps[i] is the text before words[i], seps[-1] the tail. Makaf, paseq,
    brackets and spaces are separators, so a word never contains a makaf."""
    plain, flags, bold, i = [], [], False, 0
    while i < len(t):
        if t.startswith("<b>", i):
            bold, i = True, i + 3
        elif t.startswith("</b>", i):
            bold, i = False, i + 4
        else:
            plain.append(t[i])
            flags.append(bold)
            i += 1
    s = "".join(plain)
    words, seps, wb, pos = [], [], [], 0
    for m in WORD.finditer(s):
        a, b = m.span()
        if not letters(s[a:b]):  # a lone sof pasuk / mark: keep it in the separator
            continue
        seps.append(s[pos:a])
        words.append(s[a:b])
        wb.append(any(flags[a:b]))
        pos = b
    seps.append(s[pos:])
    return words, seps, wb


def build_t(words, seps, bold) -> str:
    out = []
    for i, w in enumerate(words):
        out.append(seps[i])
        out.append(f"<b>{w}</b>" if bold[i] else w)
    out.append(seps[-1])
    return "".join(out)


def app_t_parts(tokens: list[str]):
    """App tokens -> (words, seps) in parse_t's shape: space between tokens, nothing after a makaf."""
    s = ""
    for tok in tokens:
        if s and not s.endswith(MAKAF):
            s += " "
        s += tok
    words, seps, _ = parse_t(s)
    return words, seps


# ---------------------------------------------------------------- number files

STYLES = {"formatted": dict(indent=2), "minified": dict(separators=(",", ":"))}
SORT_KEY = lambda x: (BOOKS.index(x["b"]), gematria(x["c"]), gematria(x["v"]))  # noqa: E731


def numbers(repo: Path = REPO) -> list[int]:
    return sorted(int(p.stem) for p in (repo / "formatted").glob("*.json") if p.stem.isdigit())


def read_file(path: Path) -> str:
    b = path.read_bytes()
    if b[:2] != b"\xfe\xff":
        raise ValueError(f"{path}: not UTF-16 BE with a BOM")
    return b[2:].decode("utf-16-be")


def load(n: int, repo: Path = REPO) -> dict:
    formatted = json.loads(read_file(repo / "formatted" / f"{n}.json"))
    minified = json.loads(read_file(repo / "minified" / f"{n}.json"))
    if formatted != minified:
        raise ValueError(f"{n}: formatted and minified differ")
    return formatted


def dumps(data: dict, style: str) -> str:
    """The repo's file format: no escaping, key order as given, no trailing newline."""
    return json.dumps(data, ensure_ascii=False, **STYLES[style])


def save(n: int, data: dict, repo: Path = REPO):
    if data["times"] != len(data["verses"]):
        raise ValueError(f"{n}: times={data['times']} but {len(data['verses'])} verses")
    for style in STYLES:
        (repo / style / f"{n}.json").write_bytes(b"\xfe\xff" + dumps(data, style).encode("utf-16-be"))


# ---------------------------------------------------------------- data/all-numbers*.json + all_numbers.js

def rebuild_aggregates(repo: Path = REPO) -> list[int]:
    """Regenerate data/all-numbers.json (indent 2) and data/all-numbers.min.json from the individual files
    ({"<n>": {"times", "verses"}}, numbers ascending), and the website's number list in all_numbers.js."""
    nums = numbers(repo)
    agg = {str(n): load(n, repo) for n in nums}
    for name, style in (("all-numbers.json", dict(indent=2)), ("all-numbers.min.json", dict(separators=(",", ":")))):
        text = json.dumps(agg, ensure_ascii=False, **style)
        (repo / "data" / name).write_bytes(b"\xfe\xff" + text.encode("utf-16-be"))
    js = repo / "all_numbers.js"
    m = re.match(r"(let numbers = \[\n)(.*?)(\n\];?\s*)$", js.read_text(encoding="utf-8"), re.S)
    if not m:
        raise ValueError("all_numbers.js: unexpected format")
    js.write_text(m.group(1) + ",\n".join(f"  {n}" for n in nums) + m.group(3), encoding="utf-8")
    return nums
