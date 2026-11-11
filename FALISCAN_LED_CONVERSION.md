# Converting `faliscan.sqlite` to led.json format: tokens and open questions

Status: **draft, not implemented**. No conversion script exists yet. This
document records (a) exactly which tokens the Aeneas Latin model accepts,
(b) every character in the Faliscan data that falls outside them, and
(c) a proposed mapping, separating the rules we can apply now from the ones
that need linguist sign-off.

Source: `faliscan.sqlite` (456 inscriptions, see `SQLITE_DATABASE.md`).
Target shape: `led.json` records as consumed by `train/dataloader.py`
(fields: `id`, `record_number`, `date_min`, `date_max`, `object_type`,
`inscription_type`, `monument_type`, `text`, `region_sub`, `region_main`,
`ids_alt`).

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
2. The text is lowercased, so capitals are fine.
3. `.` splits sentences. A `.` is appended if the text doesn't end in one.
4. Each character is looked up directly in `char2idx` (`util/text.py:162`).
   **There is no fallback to `^`**: any character outside the 32 tokens
   raises a `KeyError`. Every converted text must therefore be strictly
   inside the vocabulary.

At inference (`predictingthepast/eval/inference.py`), `?` marks a single
character to restore (becomes `-`) and `#` marks an unknown-length span to
restore (becomes `_`).

Because the vocabulary is baked into the checkpoint's embedding table,
adding new tokens (e.g. `θ`) would mean changing the model and
retraining or fine-tuning. The practical route is to **map everything onto
these 32 tokens**.

### What led.json itself looks like

180,205 records, 57 distinct characters: upper- and lowercase letters,
space, `_` (114,770), `-` (67,390), `. , ; ? ! ·`. There are no brackets, no
diacritics, no digits, and abbreviations are left unexpanded. Example:

```
D M s Stratocleti Stratonici fil iuveni optimo et ingenio bono qui vixit nn XVII mens VII d VIII h V ...
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
| no text at all (e.g. `Etr III-VII`, `Etr IX-X`, `Etr XXI-XXIII`) | 7 |

So `search_text` mixes normalized and diplomatic records. It shouldn't be
used as training text: two records with the same damage would be written
differently depending on which field happened to exist. The 31
line-only records also contain ` | `, which isn't in the vocabulary.

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

Characters that disappear in `normalized` (number of records): `[ ]` 114,
`\n` 93, `·` 75, `-` 68, `:` 47, `*` 31, digits ~60, `?` 24, underdotted
letters ~100, `θ` 4, `χ` 3, `‹›` 2, `{}` 1, `ᛂ` 1, `ᛍ` 1.

Nothing records who made the normalized version or what rules they used,
and Bakkum doesn't provide one. It looks automatic, probably produced by
the processing script. **To confirm with Tianhao.**

### 2c. Why this matters

- **`normalized` loses where the damage is.** The restoration task needs
  the position and length of each gap, and `normalized` deletes them. It
  can also join the words on either side of a gap (`me[.]uela` →
  `me uela`, `ucro … faf`), creating text that was never on the stone.
- **`normalized` has already answered question 1 in §5.** It keeps the
  editor's restored letters as if they were on the stone (option A).

**Proposal:** use `diplomatic`. For the 42 records without it, use
`lines_json` joined with a **space** (not `search_text`, whose ` | ` is not a
model token). This gives the same 449 records, all in one consistent
diplomatic notation. 7 records have no text and are skipped.

---

## 3. Characters outside the vocabulary, and proposed mapping

Counts are from `diplomatic`. "Records" counts are over the chosen
diplomatic/search_text text.

### 3a. Low-risk rules (proposed to apply without linguist input)

| Faliscan | meaning (Bakkum's notation) | map to |
|---|---|---|
| underdotted letters `ạ ẹ ị ṃ ṛ ụ ṣ ṭ ḷ ọ ṇ ḳ ḥ ṿ ḍ` and combining U+0323 (~170 uses) | damaged but legible letter | plain letter |
| `ú í ś` | accented letter | plain letter |
| capitals (`Pu`, `C`, `ΓYIHLILI` …) | case only | lowercase (automatic) |
| `\n` | line break | space |
| `[---]`, `[?---]`, `[---?]` | lacuna of unknown length | `_` |
| `[.]`, `[..]`, `[....]` | *n* lost letters | `-` × *n* |
| `*` | one illegible letter | `-` |
| `[n]` (e.g. `[1]`) | exactly *n* lost letters | `-` × *n* |
| `[5-6]`, `[1-2?]` | roughly *n* lost letters | `_` (length not exact) |
| `(*)` | possibly one more letter | `_` |
| `?` | editor's uncertainty | delete |
| digits `0-9` (54 records, 3 Etruscan) | **layout markers**, not text: letter counters every 10 letters on EF 2–4 (`propramom10 prameḍ…20…`) and column/tile numbers on LF/MLF tiles (`1 uo2ltio·uec3ineo`) | delete |
| `(blius)` inside Latin record `Lat 250` | expanded abbreviation | delete parentheses and contents, to match led.json's unexpanded style |
| `�` (1, `EF 3`, in `lines_json`) | broken character from the PDF | fix by hand against the PDF |

### 3b. Needs linguist sign-off

| Faliscan | count | example | options |
|---|---:|---|---|
| `[abc]` letters restored by the editor | **75 records** (2 Etruscan) | `MF 11-12`: `ḷ[oc]ịes cela`; `Cap 431`: `[q]uod·a[fluc]` | **(A)** keep letters, drop brackets (treat restoration as ground truth); **(B)** mask as `-` × *n* (model sees only what is on the stone) |
| `·` `:` `⁝` `⁞` `\|` interpuncts / dividers | `·` 343, `:` 116, `⁝` 10, `⁞` 3, `\|` 5 | `Etr VIII`: `mialiqu⁝auvilesiale…`; `Cap 431`: `p̣escoṣal \| [q]uod` | space (proposed default), or delete without word boundary |
| `‹x›` letter added by the editor (not on the stone) | 2 records | `MF 62`: `cupi‹d›o` | drop `x` (diplomatic) or keep it (normalised) |
| `{x}` letter on the stone that the editor deletes | 1 record | `LF 224-225`: `m{e}ania` | keep `x` (diplomatic) or drop it |
| `θ` | 26 | `Etr XXXIV`: `larθ:ceises` | `t`, or two letters `th` |
| `χ` | 15 | `Etr VIII`: `mlaχuta` | `c`, `k`, or `ch` |
| `φ` | 3 | `Etr L-LI`: `φerse … purφiunạs` | `p`, or `ph` |
| `ᛂ` (U+16C2), `ᛍ` (U+16CD) | 3, 2 | `MF 162`: `ma]2x̣ọmoᛂᛂuoltilio`; `LF 329`: `sestoᛍ` | probably special letter-forms (or interpuncts) that came out of the PDF as look-alike runic symbols; check against Bakkum |
| `Γ` | 1 | `Cap 422`: `ΓYIHLILI` | probably a letter-form transcription; check against Bakkum, or exclude the record |

`θ χ φ` occur in 28 records, 22 of them Etruscan-tagged, so this question
largely collapses into the language-scope question below.

### 3c. Language scope: should non-Faliscan records be included at all?

`inscriptions.language_group` breakdown:

| language_group | count | notes |
|---|---:|---|
| MF | 159 | Middle Faliscan |
| MLF | 59 | |
| Cap | 54 | Capenate |
| **Etr** | **45** | pure Etruscan |
| LF | 34 | Late Faliscan |
| LtF | 27 | |
| Lat | 21 | Latin |
| MF? | 21 | uncertain |
| **MF/Etr** | **14** | mixed/uncertain Faliscan-Etruscan |
| EF | 7 | Early Faliscan |
| **MLF/Etr** | **4** | |
| (blank) | 3 | |
| **EF/Etr** | 2 | |
| others | ~6 | small mixed categories |

65 records (Etr + MF/Etr + MLF/Etr + EF/Etr) are wholly or partly Etruscan
in language and alphabet. Should they be excluded from the conversion, or
transliterated (see `θ χ φ` above)?

---

## 4. Dry-run result

Applying only the low-risk rules in §3a to `diplomatic` (this run fell back
to `search_text`; the proposed `lines_json` fallback gives the same 31
diplomatic-notation texts plus ` | `, so the counts are essentially the
same):

- 449 records have text. **157 still contain characters outside the
  vocabulary**, 135 of them non-Etruscan.
- Remaining characters: `[` `]` (~105 records; almost all are the
  restoration question), leftover digits not yet stripped by the draft
  regexes, `θ` 23, `χ` 8, `φ` 2, `ᛂ` 2, `ᛍ` 2, `‹›` 2, `{}` 1, `γ` 1, `(` `)` 2,
  `,` 1, `;` 1, `�` 1.

In other words, once §3a is applied, the **restoration decision (`[abc]`)
is by far the biggest open item**, followed by the Etruscan scope.

---

## 5. Questions for the linguists (summary)

1. **Restorations `[abc]` (75 records):** keep the restored letters as
   text, or mask them as missing characters? Masking keeps the model's input
   to what is physically on the stone, and makes the data usable for testing
   Aeneas's restoration on Faliscan.
2. **Etruscan scope (65 records):** exclude them, or transliterate
   `θ → t/th`, `χ → c/k/ch`, `φ → p/ph`?
3. **`ᛂ`, `ᛍ`, `Γ`:** what are these in Bakkum's edition?
4. **Interpuncts `· : ⁝ ⁞ |`:** is "treat all as word boundary (space)"
   correct?
5. **Editorial additions/deletions `‹x›` / `{x}`:** follow the stone
   (drop `‹x›`, keep `{x}`) or the editor's reading?
6. **Underdotted letters:** OK to treat damaged-but-legible letters as the
   plain letter (they are the editor's confident reading)?

---

## 6. Metadata fields (low-risk, no linguist input needed)

- `id`: synthetic sequential int, offset above led.json's current max id
  (~82.9M) to avoid collisions if datasets are ever combined.
- `date_min`/`date_max`: source `start_bce`/`end_bce` use two conventions.
  91 records are already signed (`date_min <= date_max`, e.g. EF records:
  -700/-500). 68 records use plain positive "years BCE" with the older date
  first (e.g. 300/100 meaning 300–100 BCE), which needs negate+swap. Both
  normalize cleanly to led's convention. 294 records have no dates and get
  `null`, the same as undated led.json records.
- `region_sub`: left `null`. led's region loss only fires for the 62 fixed
  Roman provinces in `train/data/led-region-sub.txt`, and Faliscan sites
  don't map onto that list. The dataloader already degrades gracefully
  (`region_available = False`) when `region_sub` is absent or unrecognized.
- `region_main`: source `site` (free text), not validated against anything.

---

## 7. Next steps

1. Get answers to §5, and ask Tianhao how `normalized` was produced (§2b).
2. Write `convert_faliscan_to_led.py`: apply §3a plus the agreed §3b rules,
   then **assert every output character is in the 32-token vocabulary**
   (otherwise the dataloader crashes with `KeyError`), and log any record
   that fails instead of silently dropping characters.
3. Spot-check ~20 converted records by eye against Bakkum.
