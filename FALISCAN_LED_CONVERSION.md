# Converting `faliscan.sqlite` to led.json format

Status: **implemented** in `convert_faliscan_to_led.py`, output
`faliscan_led.json` (441 records). Text rules follow the linguists' answers
in `conversion.md`, checked against Bakkum's own conventions (§3). A few
points are still open (§7).

Source: `faliscan.sqlite` (456 inscriptions, see `SQLITE_DATABASE.md`).
Target shape: `led.json` records as consumed by `train/dataloader.py`.

```
python convert_faliscan_to_led.py [--db faliscan.sqlite] [--out faliscan_led.json]
```

---

## 0. Update for the linguists (2026-11-12)

Thank you for the answers in `conversion.md`. We have implemented them and
converted the corpus. Since then we read Bakkum's own key to his notation
(*Conventions in the representation of epigraphic texts*, Part 1, p. LII).
It confirms most of the rules, but it shows that **two things we told you
earlier were wrong**, and it raises a few new questions.

### Corrections to what we sent you

1. **`[1]`, `[2]`, `[3]` are not gaps.** Our table described a bracketed
   number as "exactly *n* lost letters", and you approved that row. Bakkum
   uses them for something else: "superscript numbers between square
   brackets … indicate the arrangement of the text over tiles that have not
   been seen by any editor of the text" (e.g. `LF 247`:
   `[1] [---]2pret[3][or]`). Plain `1 2 3` likewise mark the arrangement
   over tiles. We now **delete** all of these as layout markers. Only
   ranges such as `[4-5]` are treated as gaps.
2. **Underdots mean "ambiguous", not "legible".** We described an
   underdotted letter as "damaged but legible". Bakkum: "subpunction
   denotes that a letter is damaged and can be read in different ways.
   This is always explained in the text." We still convert it to the plain
   letter, i.e. Bakkum's preferred reading. **Please confirm this is still
   what you want** (see question 3 below).

### Things Bakkum confirmed

- `ᛂ` and `ᛍ` are interpuncts ("these dots represent the various types of
  interpuncts"), so converting them to a space, as you suggested, is right.
- `*` is one damaged letter per asterisk → one missing-letter token each.
- `[...]` is one missing letter per dot; `[4-5]` is a range of missing
  letters.
- The broken character at the end of `EF 3` is a **double interpunct** "added
  to divide the beginning and the end of this circular inscription" (Part 2,
  p. 409 and §11.1.4). It is now treated as a word divider, and EF 3 is
  included.
- `‹abc›` can mean either a letter left out by mistake or a letter written
  wrongly where another was intended. Keeping the letters (your choice)
  gives the intended spelling in both cases.

### Range gaps

For gaps like `[5-6]` we keep **all** possible lengths. At inference time the
model scores each version and we keep the most probable one. 8 records have
ranges (`EF 1` has five ranges and so 216 versions; the others 2–5).

### Questions for you

1. **`[---?]` and `[?---]` (18 records).** Bakkum: they "indicate the
   possibility that more letters either preceded (`[---?]`) or followed
   (`[?---]`) the preserved text". Your answer maps them to the unknown-gap
   token, which tells the model that letters **are** missing. Should these
   uncertain cases instead be treated as complete at that edge (marker
   deleted)? Records: Etr III-IV, Lat 240, LF 227, LF 234, LF 337,
   LtF 173, LtF 292, MF 123, MF 136-137, MF 158, MF 17, MF 183, MF 184,
   MF 96, MF? 128, MF? 130, MLF 310, MLF 318.
2. **Repeated texts.** Some objects carry the same text several times, e.g.
   `MF 22-27` (*turia* six times) and `MF 59-60` (two versions of *foied uino
   pipafo cra carefo*, the second with `‹pi›` and `[f]`). We currently keep
   every copy as written. Should we keep only one?
3. **Underdotted letters** (see correction 2): keep Bakkum's preferred
   reading as a plain letter, or treat the letter as missing?
4. **Excluded records.** All of these are in Bakkum's edition, but he marks
   them as doubtful or non-Faliscan:
   - 2 **possible forgeries**, which Bakkum heads *falsum?* and cites only
     conditionally ("if not a falsum"): `Etr XXXI` (mirror, `turṃṣ tinia
     apulu`) and `MLF 464` (saucer, `ueiụeto`).
   - 4 **rejected** inscriptions (marked †), which he includes only to
     argue they are not Faliscan: `Lat 482†`, `Lat 483†`, `Lat 484†` (Latin,
     from Ardea) and `Sab? 481†` (possibly Sabellic, from Foglia).

   Leaving out the 4 rejected ones seems clear. Should the 2 possible
   forgeries be left out too, or included?

---

## 1. The model's token vocabulary

Aeneas is a **character-level** model. The Latin model's vocabulary is
defined in `predictingthepast/util/alphabet.py` (`LatinAlphabet`) and has
exactly **32 tokens** (`vocab_char_size=32` in `train/config_latin.py`):

| idx | token | meaning |
|---:|---|---|
| 0 | `#` | padding |
| 1 | `<` | start of sentence (prepended automatically) |
| 2 | `^` | unknown character |
| 3 | ` ` | space / word boundary |
| 4 | `-` | one missing character (known-length gap) |
| 5 | `_` | missing span of unknown length |
| 6–29 | `a b c d e f g h i k l m n o p q r s t u v x y z` | 24 letters, **no `j`, no `w`** |
| 30 | `0` | numeral placeholder (never actually occurs in led.json) |
| 31 | `.` | the only punctuation token; also the sentence delimiter |

`[` and `]` are defined as attributes on the class (`sog`/`eog`) but are
**not** in the vocabulary, so the model never sees them.

### How text is preprocessed before tokenisation

From `train/dataloader.py` and `LatinAlphabet.filter`:

1. `filter()` **deletes** `! , ; ? ·`. Note that `·` is deleted, not turned
   into a space, so `c·f` would become `cf`. Interpuncts must therefore be
   converted to spaces *before* the text reaches the dataloader.
2. The text is lowercased.
3. `.` splits sentences. A `.` is appended if the text doesn't end in one.
4. Each character is looked up directly in `char2idx` (`util/text.py:162`).
   **There is no fallback to `^`**: any character outside the 32 tokens
   raises a `KeyError`. The converter therefore checks every output text.

At inference (`predictingthepast/eval/inference.py`), `?` marks a single
character to restore (becomes `-`) and `#` marks an unknown-length span to
restore (becomes `_`).

Because the vocabulary is baked into the checkpoint's embedding table, we
map everything onto these 32 tokens rather than adding new ones.

### What led.json itself looks like

180,205 records, 57 distinct characters: upper- and lowercase letters,
space, `_`, `-`, `. , ; ? ! ·`. No brackets, no diacritics, no digits, and
abbreviations are left unexpanded. `_` is never repeated (always a single
token), while runs of `-` are common (`---` etc., ~25,000 runs). Example:

```
_ Aristobulus Hispani XXII nat Graec ann XXI h s e s t t l _
```

---

## 2. Which Faliscan text field to use

All 456 inscriptions come from Bakkum (2009), *The Latin Dialect of the
Ager Faliscus*, Part 2, extracted from the PDF with `pdftotext` (see the
`sources` table). 449 records are `checked_against_pdf`, 7 only `parsed`.

| field | non-empty | distinct chars | notes |
|---|---:|---:|---|
| `diplomatic` | 407 | 89 | follows Bakkum's printed edition, including damage/lacuna notation |
| `normalized` | 340 | 46 | cleaned-up version; damage info removed (see 2b) |
| `lines_json` | 424 | – | the text line by line, in diplomatic notation; present for all 42 records that lack `diplomatic` |
| `search_text` | 449 | 86 | **not an independent field**: a fallback copy (see 2a) |

### 2a. `search_text` is a fallback copy

This rule holds for all 456 records, with no exceptions:

```
search_text = normalized    if it exists
              else diplomatic  if it exists
              else lines_json joined with " | "
```

| case | records |
|---|---:|
| `search_text` = `normalized` | 230 |
| `search_text` = `diplomatic` (no `normalized`, or the two are identical) | 188 |
| only `lines_json` exists (incl. EF 1–3) | 31 |
| no text at all | 7 |

So `search_text` mixes normalized and diplomatic records, and shouldn't be
used as training text.

### 2b. How `normalized` differs from `diplomatic`

| | records |
|---|---:|
| both exist and differ | 219 |
| both exist and are identical (short, undamaged texts like `cauios`) | 110 |
| `diplomatic` only | 78 |
| `normalized` only | 11 |

Comparing the 219 pairs that differ, `normalized` does the following:

| change | example (`diplomatic` → `normalized`) |
|---|---|
| **restored letters kept, brackets removed** | `Lat 432`: `[fe]ronea·dono` → `feronea dono` |
| **gaps deleted entirely, leaving no marker** | `MF 138-139`: `ucro[---]\n**[---]\nf̣af̣[---]` → `ucro faf` |
| lost single letters deleted or turned into a space | `Bakkum 357`: `me[.]uela` → `me uela`; `Etr XL`: `mialsi*ismi` → `mialsi ismi` |
| interpuncts and line breaks → space | `LtF 205`: `furc·t·p·c·ef·i·uei·` → `furc t p c ef i uei` |
| underdots removed | `MF 170`: `ocuẹ` → `ocue` |
| layout digits removed | `MF 170`: `[1] [---]2ịọ` → `io` |
| repeated copies collapsed | `MF 22-27`: six lines of `turia` → `turia` |

Nothing records who made the normalized version or what rules they used.
It looks automatic, probably produced by the processing script. **To confirm
with Tianhao.**

Why it matters: `normalized` loses the position and length of each gap,
which the restoration task needs, and it can join the words on either side
of a gap (`me[.]uela` → `me uela`), creating text that was never on the
stone.

**Used:** `diplomatic`; for the 42 records without it, `lines_json` joined
with a space.

---

## 3. Bakkum's notation (Part 1, p. LII)

Bakkum's own key, *Conventions in the representation of epigraphic texts*:

| sign | Bakkum's definition (abridged) |
|---|---|
| `*` | traces of a letter; one asterisk per damaged or illegible letter |
| `ạḅc̣` | subpunction: letter is damaged and can be read in different ways (explained in the commentary) |
| `[abc]` | no legible trace remains; letters supplied by a modern editor |
| `[...]` | no legible trace; one dot per letter assumed missing |
| `[4-5]` | no legible trace; number of missing letters as indicated (used when the number is large or uncertain) |
| `[---]` | unknown number of missing letters |
| `[---?]` / `[?---]` | possibly more letters preceded / followed the preserved text |
| `‹abc›` | letters (a) left out by mistake, or (b) written in error where another letter was intended |
| `{abc}` | letters added in error by the writer |
| `ᛍ ᛂ` (and other dots) | the various types of interpuncts |
| `\|` | regular line end, or lines turning around a corner of the object |
| `\|\|` | non-regular line division |
| `1 2 3` | arrangement of the text over separate tiles; if a letter is split over two tiles, the number follows the letter |
| `[1] [2] [3]` | arrangement over tiles not seen by any editor but assumed to belong to the inscription |

`(*)` and `?` inside brackets are not in this list; they appear to mean "a
possible extra letter" and "uncertain", and are handled as in §4.

---

## 4. Conversion rules (as implemented)

Applied in this order (see `convert()` in `convert_faliscan_to_led.py`):

| step | Faliscan | → | source of decision |
|---:|---|---|---|
| 1 | `[a-b]` ranges, e.g. `[5-6]`, `[1-2?]`, `[0-4?]` | `-` × each length from a to b (all kept as `text_variants`) | user (model picks most probable) |
| 2 | `[1]`, `[2]`, `[3?]` and all other digits | delete (tile/layout markers; EF 2–4 letter counters) | Bakkum p. LII |
| 3 | `?` | delete | linguists |
| 4 | dash runs: `[---]`, `[?---]`, `[---?]`, `[----------]` | `_` | linguists (`[---?]`/`[?---]` still open, §0 Q1) |
| 5 | `(*)` | `_` | linguists |
| 6 | `.` inside brackets: `[.]`, `[..]` | `-` per dot | user (matches led's `-` runs) |
| 7 | `*` | `-` per asterisk | user + Bakkum |
| 8 | `‹x›`, `{x}` | keep `x`, drop the marks | linguists |
| 9 | `( … )` (Latin abbreviation expansions, editorial comments) | delete with contents | linguists |
| 10 | `[abc]` restored letters | keep letters, drop brackets (option A) | linguists |
| 11 | `· : ⁝ ⁞ \| ᛂ ᛍ`, line breaks | space | linguists + Bakkum |
| 12 | `θ χ φ` | `th ch ph` | linguists |
| 13 | underdots, accents (`ạ`, `ú`, …), capitals | plain lowercase letter | linguists (§0 Q3) |
| 14 | `, ; !` | delete | model's own filter |
| 15 | adjacent `_` | merge into one `_` | led convention |

Hand fixes (`MANUAL_FIXES`): `EF 3` final `�` → space (double interpunct).

Every output text is checked against the 32-token vocabulary.

### Examples

```
Etr VIII   mialiqu⁝auvilesialeṣpuraθeṿnalθia⁝inpein⁝mlerusi⁝ateri⁝mlaχuta⁝…
        →  mialiqu auvilesialespurathevnalthia inpein mlerusi ateri mlachuta …
LF 247     [1] [---]2f·cue[3][stor]\n[1] [---]2pret[3][or]\n…
        →  _f cuestor _pretor _duumuir _-ar-_
Bakkum 357 me[.]uela\nu[.]suae:rfa\nzeuoc*na
        →  me-uela u-suae rfa zeuoc-na
Lat 250    Pu(blius) Fuluius C(aii) f(ilius) … co(n)s(ulibus).
        →  pu fuluius c f c n suto diem suo obiet a d x k dec c atilio q seruio cos.
Etr III-IV …ṭạm*(*)upesitatatuθacetu[5-6]ṭaθine[?---]
        →  …tam-_upesitatatuthacetu------tathine_   (+ a 5-dash variant)
```

---

## 5. Output

`faliscan_led.json`: a list of led-style records.

| field | value |
|---|---|
| `id` | 90,000,000 + row number (above led.json's max id ~82.9M) |
| `record_number` | Bakkum id, e.g. `MF 62` |
| `date_min`, `date_max` | signed years (see below) |
| `object_type` | from `inscriptions.object_type` |
| `inscription_type`, `monument_type` | `null` |
| `text` | converted text; for range gaps, the all-maximum version |
| `region_sub` | `null` (Faliscan sites don't map onto led's 62 Roman provinces; the dataloader then skips the region loss) |
| `region_main` | `inscriptions.site` |
| `ids_alt` | `{"bakkum": <number>}` |
| `faliscan` | extra info: `language_group`, `period_group`, `uncertain`, `review_status`, `direction`, `date_label`, `text_source`, original `diplomatic` text, `gap_ranges`, `text_variants` |

**Dates.** `start_bce`/`end_bce` use two conventions: already signed
(-700/-500), or positive years BCE with the older date first (300/100 →
-300/-100). Both are normalised. 56 records have only one bound (e.g.
"before 241 BC"); the other side stays `null`, and the dataloader treats
their date as unavailable.

### Numbers

| | records |
|---|---:|
| converted | **441** |
| at least 25 characters (the model's training minimum) | 81 |
| median length | 12 characters |
| with range gaps (several `text_variants`) | 8 |
| with both dates | 150 |
| text taken from `lines_json` | 42 |

By language group: MF 158, MLF 58, Cap 53, Etr 41, LF 33, LtF 26, MF? 21,
Lat 18, MF/Etr 12, EF 7, MLF/Etr 4, (none) 3, EF/Etr 2, MF/LtF 2, LF/Lat 1,
LF? 1, MLF/LtF 1.

Left out (15): 7 with no text (`Etr III-VII`, `Etr IX-X`, `Etr XXI-XXIII`,
`LF 335`, `LtF 288`, `MF/Etr 287`, `MF/Etr 61`); `Cap 422` (linguists:
letter-forms on a vase); 2 possible forgeries (Bakkum: *falsum?*); 4
rejected in Bakkum (†); `MF 177`
(`[---]:*[---]`, no letters left).

---

## 6. Language scope

`inscriptions.language_group` in the source: MF 159, MLF 59, Cap 54, Etr 45,
LF 34, LtF 27, Lat 21, MF? 21, MF/Etr 14, EF 7, MLF/Etr 4, (blank) 3,
EF/Etr 2, others ~6. Per the linguists, Etruscan records are **included**,
with `θ χ φ` written as `th ch ph`. `language_group` is kept in the output so
experiments can filter by it.

---

## 7. Open items

1. Linguists: questions in §0 (`[---?]`/`[?---]`, repeated texts,
   underdots, excluded records).
2. Tianhao: how `normalized` was produced (§2b). Not blocking, since we
   don't use it.
3. Tianhao: **inscription 336**. The database has it as `MF 336` (Middle
   Faliscan; `tito·marhio uoltilio·`), but Bakkum's index lists it as
   "336 (LF)" (Late Faliscan; text on Part 2, p. 546). Possibly a
   labelling error in the processing; it matters for experiments that
   filter or date by language group. Worth checking whether other ids have
   the same problem.
4. `EF 1`: the database has `para[i?1]douiad`, while Bakkum's discussion
   prints `para[i? .]` (i or one unknown letter). The `1` is deleted as a
   digit, so the output keeps the `i`. Minor; check if EF 1 matters for an
   experiment.
