---
name: bible-numbers
description: Add a number to the numbers-in-bible repo (find its verses, bold the words that form it, write formatted/ + minified/ JSON and the aggregate files), or audit/fix the existing number files against the Bible Contest app's text. Use whenever the user asks to add/create a number ("הוסף את המספר X", "תוסיף קובץ למספר", "צור 372.json"), to fix a verse/bold in a number file, to check or audit the numbers data ("תבדוק את המספרים", "ביקורת"), or when a number search in the app shows a wrong/missing verse.
---

# numbers-in-bible

The Bible Contest app loads `https://raw.githubusercontent.com/elfifo4/numbers-in-bible/master/minified/<n>.json`
for a number search and **shows `t` as is**, highlighting the words wrapped in `<b>…</b>`. Pushing to
`master` changes what users see immediately, so **never push without the user's explicit OK**.

```json
{"times":2,"verses":[{"b":"עזרא","c":"ב","t":"בְּנֵ֣י שְׁפַטְיָ֔ה <b>שְׁלֹ֥שׁ</b> <b>מֵא֖וֹת</b> <b>שִׁבְעִ֥ים</b> <b>וּשְׁנָֽיִם</b>׃","v":"ד"}, …]}
```

- `b`: book name exactly as in the app's `BibleCatalog` (שמואל א, דברי הימים ב…). `c`/`v`: Hebrew numerals
  (טו, טז), **in the app's numbering**. `i` (optional, almost always `""`): parsed by the app, not shown.
- `times` = number of verses (not occurrences). Verses sorted by the app's book order, then chapter, verse.
- `t` = the verse **exactly as the app's own text** (`BibleContestAndroidApp/shared/src/commonMain/
  moko-resources/assets/allChapters`): qere only, makaf and sof pasuk kept. Each number word is wrapped
  separately; makaf, sof pasuk and paseq stay **outside** `<b>` (`<b>שְׁלֹשׁ</b>־<b>מֵא֥וֹת</b>`).
- Files: UTF-16 BE with BOM, no `\/` escaping, no trailing newline, key order `b,c,t,v[,i]`;
  `formatted/` is indent 2, `minified/` compact. `data/all-numbers.json` / `.min.json` (every number in one
  object) and `all_numbers.js` (the website's dropdown) are generated from the number files.

**Don't write these files by hand** — `scripts/numlib.py` does all of the above.

## Scripts (`.claude/skills/bible-numbers/scripts/`, Python 3, stdlib only)

| script | does |
|---|---|
| `find_number.py N` | every verse where the detector finds N, as ready `--verse` specs, marked `in file` / `NEW` |
| `add_number.py N --verse "ספר:פרק:פסוק=מילים" … [--write]` | creates/extends N.json from the app's text, bolds the given words (in order, no nikud), sorts, rebuilds the aggregates |
| `audit_numbers.py [--out f] [--all]` | read-only audit (below); exit 1 if there are unreviewed findings |
| `unify_text.py [--write]` | rewrites every `t` from the app's text, carrying the bold over word by word |
| `rebuild_aggregates.py` | regenerates `data/all-numbers*.json` and `all_numbers.js` |
| `numlib.py`, `numparse.py` | shared: app text, file I/O, `parse_t`/`build_t` (bold per word), number-phrase detector |

The scripts expect the app checkout next to this repo (`../BibleContestAndroidApp`).

## Adding a number

1. `find_number.py N` and review every candidate with the user (see "What counts" below).
   Detector misses are possible for ordinals/derived words — search for those explicitly if relevant.
2. `add_number.py N --verse "…" --verse "…"` (dry run), show the result, then `--write`.
3. `audit_numbers.py` must exit 0 (or every new finding reviewed with the user).
4. Commit to `master` in the repo's style (`add 372.json`), staging only the number files, `data/`,
   `all_numbers.js` (and the skill if changed). Never `.DS_Store`, `.idea`, `__pycache__`, `.dicta-cache`.
   **Push only when the user says so.**

## What counts as an occurrence of N (decided with the user, 2026-09/10 audit)

- **The app is the source of truth**: its text, its qere, its versification. A verse the app doesn't have
  (e.g. Joshua 21:36-37 in other editions) is not in any file; numbering differences (Ten Commandments,
  Joshua 21, 1 Samuel 24) use the app's numbers, so tapping a result highlights the right verse.
- **Plain text, not commentaries**: 2 Samuel 15:7 "מִקֵּץ אַרְבָּעִים שָׁנָה" is 40 (not 4, as some ancient
  versions read). When it's a real judgment call, show the user the sources (Sefaria API:
  `https://www.sefaria.org/api/v3/texts/Rashi_on_I_Samuel.6.19?version=hebrew`) — but the text decides.
- **A compound counting one thing is one number** (840 = "אַרְבָּעִים שָׁנָה וּשְׁמֹנֶה מֵאוֹת שָׁנָה", 1365,
  151450). **Numbers counting different things are separate**: "שְׁלֹשׁ מֵאוֹת כֶּסֶף וְחָמֵשׁ חֲלִפֹת" = 300 + 5;
  "שִׁבְעִים אִישׁ חֲמִשִּׁים אֶלֶף אִישׁ" (1 Samuel 6:19) = 70 + 50000; "אֶלֶף וּשְׁבַע מֵאוֹת רֶכֶב וְעֶשְׂרִים אֶלֶף
  אִישׁ" = 1700 + 20000. A word of one number is never bolded in another number's file.
- **Each file is broad on purpose**: ordinals (הָרִאשׁוֹן, הַשְּׁלִישִׁי, Aramaic תַּלְתָּא "the third"), duals
  (יוֹמַיִם, אַמָּתַיִם), derived words (שְׁנֵיהֶם, עֶשְׂרוֹנִים, מַעֲשֵׂר), Aramaic numerals, "שָׂרֵי אֲלָפִים" /
  "אַלְפֵי יִשְׂרָאֵל" (thousand as a unit) — all count.
- **Names and other meanings don't**: בְּאֵר שֶׁבַע, בַּת־שֶׁבַע, שֶׁבַע בֶּן־בִּכְרִי, the well שִׁבְעָה (Genesis
  26:33), קִרְיַת אַרְבַּע, the town הָאֶלֶף; שֵׁשׁ = linen/marble; שְׁבוּעָה/נִשְׁבַּע = oath; שָׂבַע = satiety;
  אֲלָפִים/אֲלָפֶיךָ = cattle ("שְׁגַר אֲלָפֶיךָ", Psalms 8:8, Proverbs 14:4); שְׁנֵי חַיֵּי = "years of".
- Every occurrence in a verse is bolded, also the second one ("אַרְבָּעִים יוֹם וְאַרְבָּעִים לַיְלָה").

## Auditing

`audit_numbers.py` checks structure (must be 0): format, order, aggregates in sync, `t` identical to the
app's text, nothing but letters inside `<b>`. Then content candidates from the detector: a bolded phrase
with another value, a half-bolded phrase, an unbolded occurrence, verses/values the files don't have.
Findings reviewed with the user are stored in `scripts/reviewed.json` (key `category|n|ref|text`) and only
counted; `--save-reviewed` adds all current ones — use it **only after** going through them.

## Lessons (why things are the way they are)

- **Dicta can't build a number file.** Its search is by letters/root, not meaning: the query "שבע" returns
  882 verses, all 32 בְּאֵר שֶׁבַע and 12 בַּת־שֶׁבַע, oaths (נִשְׁבַּע), satiety (וְשָׂבָעְתָּ), ordinals and 70s;
  what it highlights depends on the query (for "שבע" it marks בְּאֵר *שֶׁבַע* in Genesis 26:33, for "שבעה"
  the well's name). Use it only to find candidates; the detector over the app's own text is more precise.
  (Endpoint: POST `https://tanach-search-3-0.loadbalancer.dicta.org.il/download`, form-urlencoded,
  `downloadType=TXT, showNikudAndTeamim=BOTH, replaceShemos=false, sort=corpus_order_path, query=…`; cache
  responses in `.dicta-cache/`, ≤5 parallel requests.) With `replaceShemos=false` Dicta still censors divine
  names with a makaf (`יְ־וָה`, `אֱ־ֹהִים`) — never copy Dicta text into `t`; take it from the app.
- The files were originally built (2019) from another edition: holam before vav (`מֵאֹות`), makaf replaced by
  a space, sof pasuk removed; later files kept the makaf, 830/840 came straight from Dicta. In October 2026
  every `t` was rewritten from the app's text (`unify_text.py`), keeping all 7,248 bold tags.
- The old generator bolded **the wrong occurrence or a neighboring word** when a number repeated in a verse:
  the second "אַרְבָּעִים" ended up in 4.json, the second "חֲמִשָּׁה וְעֶשְׂרִים אֶלֶף" split into 5 + 20, "אֶחָת" of
  "קְעָרַת כֶּסֶף אַחַת" in 130.json, "מַחֲלֻקְתּוֹ" bolded instead of "אֶלֶף". The audit's bold checks catch these.
- Detector homographs that only meaning can settle are listed in `numparse.py`'s docstring; keep regression
  cases there in mind when changing it (e.g. 840, 2172, 4500 from "חֲמֵשׁ מֵאוֹת וְאַרְבַּעַת אֲלָפִים", 42360).
- The app sorts results by book, chapter and verse via gematria (BibleContestMultiPlatformApp PR #210); before
  that it only sorted by book and kept the file's order, so file order still matters for older app versions.
- Keep scripts and caches in the repo, not `/tmp` — macOS cleans `/tmp` and the first audit's scripts were lost.
