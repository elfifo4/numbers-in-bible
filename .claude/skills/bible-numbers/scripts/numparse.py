"""
Find cardinal number phrases in pointed Hebrew/Aramaic verse text and compute their values.

This is a *detector* for audits and for suggesting verses — not an authority. It only knows cardinal
numbers (the files also hold ordinals, duals and derived words on purpose, see SKILL.md), and a few
homographs can only be told apart by meaning. Every hit is a candidate to review.

Hard cases it handles (each one was a false positive or a miss in the 2026 audit):
- homographs told apart by nikud: שְׁנֵי/שְׁתֵּי (two) vs שֵׁנִי (second) and שְׁנִי (scarlet); שִׁבְעָה (seven) vs
  שָׁבֻעַ/שְׁבֻעָה (week/oath); עֶשֶׂר vs עֹשֶׁר (wealth) and מַעֲשַׂר (tithe); מֵאָה (100) vs מֵאֵת (from);
  אֶלֶף vs אַלּוּף (chief); שְׁלֹשִׁים (30) vs שָׁלִשִׁים (officers)
- names and words by context: בְּאֵר/בַּת שֶׁבַע, קִרְיַת אַרְבַּע, linen שֵׁשׁ (בגדי שש, שש משזר), שְׁנֵי חַיֵּי (years of)
- compounds with counted nouns in between: אַרְבָּעִים שָׁנָה וּשְׁמֹנֶה מֵאוֹת שָׁנָה = 840
- descending compounds without ו (Ezra 2 / Nehemiah 7): אַלְפַּיִם מֵאָה שִׁבְעִים וּשְׁנָיִם = 2172
- ascending order: שֶׁבַע וְעֶשְׂרִים וּמֵאָה = 127
- separate numbers that look like one: a magnitude never repeats inside one number, so
  "שֶׁבַע פָּרֹת... וְשֶׁבַע שִׁבֳּלִים" is 7 and 7, and "שִׁבְעַת אֲלָפִים... וְאַרְבָּעִים אֶלֶף" is 7000 and 40000
"""

import re

import numlib as L

SHVA, HATAF_PATAH, PATAH, QAMATS, TSERE, SEGOL, HIRIQ, HOLAM, QUBUTS, DAGESH, SHIN, SIN = (
    "ְ", "ֲ", "ַ", "ָ", "ֵ", "ֶ", "ִ", "ֹ", "ֻ", "ּ", "ׁ", "ׂ")
VOWELS = set("ְֱֲֳִֵֶַָׇֹֺֻּׁׂ")
ARAMAIC_BOOKS = (34, 35)  # Daniel, Ezra
_ctx = {"book": None}


def units(tok: str):
    """[(letter, vowel marks)] with final letters normalized."""
    out = []
    for ch in tok:
        if "א" <= ch <= "ת":
            out.append([ch.translate(L.FINALS), ""])
        elif ch in VOWELS and out:
            out[-1][1] += ch
    return out


def has(u, i, *marks) -> bool:
    return i < len(u) and any(m in u[i][1] for m in marks)


ANY = lambda u: True  # noqa: E731
ARAM = lambda u: _ctx["book"] in ARAMAIC_BOOKS  # noqa: E731
first_shva = lambda u: has(u, 0, SHVA)  # noqa: E731
hiriq0 = lambda u: has(u, 0, HIRIQ)  # noqa: E731
shin0 = lambda u: not has(u, 0, SIN)  # noqa: E731
holam1 = lambda u: has(u, 1, HOLAM) or (len(u) > 2 and u[2][0] == "ו" and has(u, 2, HOLAM))  # noqa: E731

LEX: dict[str, list] = {}


def add(words: str, value: int, kind: str, check=ANY):
    for w in words.split():
        LEX.setdefault(w, []).append((value, kind, check))


# kinds: unit, ten10 (עשר/עשרה of the teens), ashtei (עשתי), ten, hundred, hundreds (מאות, after a unit),
#        thousand, thousands, myriad
add("אחד אחת", 1, "unit")
add("חד", 1, "unit", ARAM)
add("עשתי", 1, "ashtei")
add("שנימ שתימ", 2, "unit", lambda u: first_shva(u) and (has(u, 1, PATAH) or has(u, 1, QAMATS) or has(u, 1, TSERE)))
add("שני שתי", 2, "unit", lambda u: first_shva(u) and has(u, 1, TSERE))
add("תרינ תרתינ", 2, "unit", ARAM)
add("שלש שלשה שלשת שלוש שלושה שלושת", 3, "unit", holam1)
add("תלת תלתא תלתה", 3, "unit", ARAM)
add("ארבע ארבעה ארבעת", 4, "unit")
add("חמש חמשה חמשת", 5, "unit", lambda u: not has(u, 0, HOLAM))
add("שש ששה ששת", 6, "unit", lambda u: not has(u, 0, PATAH) and not has(u, 0, SIN) and not has(u, 0, HOLAM))
add("שת", 6, "unit", lambda u: ARAM(u) and hiriq0(u))
add("שבע שבעה שבעת", 7, "unit",
    lambda u: shin0(u) and (has(u, 0, HIRIQ) or has(u, 0, SEGOL) or has(u, 0, SHVA)) and not has(u, 1, QUBUTS))
add("שמנה שמונה שמנת שמונת", 8, "unit", holam1)
add("תמניא תמנה", 8, "unit", ARAM)
add("תשע תשעה תשעת", 9, "unit", lambda u: not has(u, 1, QUBUTS) and not (len(u) == 4 and has(u, 2, SEGOL)))
add("עשר עשרה עשרת", 10, "ten10", lambda u: not has(u, 0, HOLAM) and not has(u, 1, PATAH) and not has(u, 0, PATAH))
add("עשרימ עשרינ", 20, "ten", lambda u: has(u, 0, SEGOL))
add("שלשימ שלושימ", 30, "ten", holam1)
add("תלתינ", 30, "ten", ARAM)
add("ארבעימ", 40, "ten")
add("חמשימ", 50, "ten", lambda u: has(u, 1, HIRIQ) or (has(u, 0, HATAF_PATAH) and not has(u, 1, QUBUTS)))
add("ששימ", 60, "ten")
add("שתינ", 60, "ten", lambda u: ARAM(u) and hiriq0(u))
add("שבעימ", 70, "ten", lambda u: shin0(u) and hiriq0(u))
add("שמנימ שמונימ", 80, "ten", holam1)
add("תשעימ", 90, "ten")
add("מאה", 100, "hundred", lambda u: has(u, 1, QAMATS))
add("מאת", 100, "hundred", lambda u: has(u, 0, SHVA) and not has(u, 1, HOLAM))  # מְאַת (construct)
add("מאת", 100, "hundreds", lambda u: has(u, 1, HOLAM))  # מֵאֹת = מֵאוֹת written defectively
add("מאות", 100, "hundreds")
add("מאתימ מאתינ", 200, "hundred")
add("אלפ", 1000, "thousand", lambda u: (has(u, 0, SEGOL) or has(u, 0, PATAH) or has(u, 0, QAMATS)) and not has(u, 1, QUBUTS))
add("אלפימ אלפי אלפינ", 1000, "thousands", lambda u: not has(u, 1, QUBUTS))
add("רבוא רבו רבבה רבבות רבות רבאות רבונ", 10000, "myriad", hiriq0)
add("רבתימ", 20000, "myriad", hiriq0)

PREFIX = set("והבכלמ")
SKIP_PREV = {"שבע": ("באר", "בת"), "ארבע": ("קרית",), "שש": ("בגדי", "שני")}  # names / linen
SKIP_NEXT = {"שבע": ("בנ",)}  # שֶׁבַע בֶּן־בִּכְרִי
MAG = {"unit": 1, "ashtei": 1, "ten": 10, "ten10": 10, "hundred": 100}
FILLER_MAX = 2


def is_word(sk: str, stems) -> bool:
    """sk is one of stems, optionally with prefix letters (בְּאֵר, וּבְאֵר; not הַטֹּבֹת for בת)."""
    return any(sk == x or (sk.endswith(x) and set(sk[:-len(x)]) <= PREFIX and len(sk) - len(x) <= 2) for x in stems)  # counted-noun words allowed between parts of one number


def parse_word(tok: str):
    """-> (value, kind, prefix letters) or None."""
    u = units(tok)
    cons = "".join(c for c, _ in u)
    for p in range(0, 3):
        if p and (p > len(cons) or cons[p - 1] not in PREFIX):
            break
        for value, kind, check in LEX.get(cons[p:], []):
            if check(u[p:]):
                return value, kind, cons[:p]
    return None


def phrases(words: list[str], book: int | None = None) -> list[tuple[int, list[int]]]:
    """Pointed words of one verse (qere, no makaf) -> [(value, [indexes of its words])]."""
    _ctx["book"] = book
    sk = [L.skeleton(w) for w in words]
    parsed = []
    for i, w in enumerate(words):
        p = parse_word(w)
        if p:
            stem, nxt, prv = sk[i][len(p[2]):], (sk[i + 1] if i + 1 < len(words) else ""), (sk[i - 1] if i else "")
            if stem == "שני" and ((parsed and parsed[-1] and not p[2].startswith("ו"))
                                  or prv.endswith("ימי") or nxt.startswith("חי") or prv == "כמה"):
                p = None  # שֶׁבַע שְׁנֵי רָעָב / יְמֵי שְׁנֵי חַיָּיו: "years of"
            elif is_word(prv, SKIP_PREV.get(stem, ())) or is_word(nxt, SKIP_NEXT.get(stem, ())) \
                    or (stem == "שש" and (is_word(nxt, ("משזר",)) or is_word(prv, ("ארגמנ", "בוצ")))):
                p = None
            elif p[1] == "ashtei" and not (nxt.startswith("עשר") or nxt[1:].startswith("עשר")):
                p = None  # וְעָשִׂתִי (I made)
        parsed.append(p)

    out, st = [], None

    def emit():
        nonlocal st
        if st:
            out.append((st["total"] + st["cur"], st["idx"]))
        st = None

    def new(i, v, kind):
        nonlocal st
        st = {"total": 0, "cur": 0, "last": 0, "used": set(), "closed": [], "idx": [], "since": 0}
        feed(i, v, kind)

    def feed(i, v, kind):
        s = st
        s["idx"].append(i)
        if kind == "ten10" and 0 < s["last"] < 10:  # שְׁנֵים עָשָׂר
            s["cur"] += 10
            s["last"] += 10
            s["used"].add(10)
        elif kind == "hundreds" and 0 < s["last"] < 10:  # שְׁלֹשׁ מֵאוֹת
            s["cur"] += s["last"] * 99
            s["last"] *= 100
            s["used"].discard(1)
            s["used"].add(100)
        elif (kind in ("thousand", "thousands") and s["cur"] > s["last"] and 0 < s["last"] <= 10
              and len(s["idx"]) > 1 and sk[s["idx"][-2]].endswith("ת")):
            # a construct unit multiplies only itself: חֲמֵשׁ מֵאוֹת וְאַרְבַּעַת אֲלָפִים = 500 + 4000
            s["cur"] += s["last"] * 999
            s["last"] *= 1000
            s["used"].add(1000)
        elif kind in ("thousand", "thousands", "myriad") and s["cur"]:  # אַרְבָּעִים אֶלֶף
            mult = 1000 if kind != "myriad" else v
            s["since"] = len(s["idx"])
            s["closed"].append(s["cur"] * mult)
            s["total"] += s["cur"] * mult
            s["cur"] = s["last"] = 0
            s["used"] = set()
        else:
            if kind == "thousands" and not s["cur"]:  # אַלְפַּיִם alone = 2000, אַלְפֵי / הָאֲלָפִים = thousands
                v = 2000 if re.fullmatch("[וכב]?אלפימ", sk[i]) else 1000
            if kind == "hundreds":
                kind = "hundred"
            s["cur"] += v
            s["last"] = v
            s["used"].add(MAG.get(kind, 1000))

    def fits(i, v, kind, vav):
        s = st
        if kind in ("ten10", "hundreds") and 0 < s["last"] < 10:
            return True
        if kind in ("thousand", "thousands", "myriad") and s["cur"]:
            value = s["cur"] * (1000 if kind != "myriad" else v)
            return not s["closed"] or value < s["closed"][-1]
        mag = MAG.get(kind if kind != "hundreds" else "hundred", 1000)
        nx = parsed[i + 1] if i + 1 < len(parsed) else None
        if kind == "unit" and nx and nx[1] == "hundreds":
            mag = 100  # וַחֲמֵשׁ מֵאֹת
        elif kind == "unit" and nx and nx[1] == "ten10":
            mag = 10
        if mag in s["used"]:
            return False
        if s["total"] and not s["cur"]:
            return mag * 10 <= min(s["closed"])
        if not vav:
            last = s["last"]
            last_mag = 1 if last < 10 else 10 if last < 100 else 100 if last < 1000 else 1000
            return mag < last_mag  # descending without ו: אַלְפַּיִם מֵאָה שִׁבְעִים
        return True

    gap = 0
    for i, p in enumerate(parsed):
        if p is None:
            if st:
                gap += 1
            continue
        v, kind, pre = p
        vav = pre.startswith("ו")
        if st and (gap == 0 or (gap <= FILLER_MAX and vav)) and fits(i, v, kind, vav):
            feed(i, v, kind)
        elif st and kind in ("thousand", "thousands", "myriad") and st["cur"] and st["closed"] and gap <= FILLER_MAX:
            # 7000 ... and 40000: close the first number, the pending part starts the next one
            pending = st["idx"][st["since"]:]
            st["idx"] = st["idx"][:st["since"]]
            st["cur"] = 0
            emit()
            for j in pending:
                pv, pk, _ = parsed[j]
                if st is None:
                    new(j, pv, pk)
                else:
                    feed(j, pv, pk)
            feed(i, v, kind)
        else:
            emit()
            new(i, v, kind)
        gap = 0
    emit()
    return out


def verse_words(book: int, chapter: int, verse: int) -> list[str] | None:
    """The app's verse as words (qere only, makaf split, no punctuation)."""
    tokens = L.app_tokens(book, chapter, verse)
    if tokens is None:
        return None
    return L.app_t_parts(tokens)[0]


def scan_tanakh():
    """Yield (book, chapter, verse, value, [word indexes]) for every cardinal phrase in the app's text."""
    for b in range(len(L.BOOKS)):
        c = 1
        while L.app_chapter(b, c):
            for v in L.app_chapter(b, c):
                words = verse_words(b, c, v)
                for value, idx in phrases(words, b):
                    yield b, c, v, value, idx
            c += 1
