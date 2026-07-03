# Converting `faliscan.sqlite` to led.json format — open questions

Status: **draft, not implemented**. No conversion script exists yet. This
document records the mapping plan and, more importantly, the points that
need linguist sign-off before we write it, because several decisions affect
what the model actually sees as "the text."

Source: `faliscan.sqlite` (456 inscriptions, see `SQLITE_DATABASE.md`).
Target shape: `led.json` records as consumed by `train/dataloader.py`
(fields: `id`, `record_number`, `date_min`, `date_max`, `object_type`,
`inscription_type`, `monument_type`, `text`, `region_sub`, `region_main`,
`ids_alt`).

## Decisions that seem low-risk (no linguist input needed)

- `id`: synthetic sequential int, offset above led.json's current max id
  (~82.9M) to avoid collisions if datasets are ever combined.
- `date_min`/`date_max`: source `start_bce`/`end_bce` use two conventions —
  91 records already signed (`date_min <= date_max`, e.g. EF records:
  -700/-500), 68 records use plain positive "years BCE" with the older date
  first (e.g. 300/100 meaning 300-100 BCE, needs negate+swap). Both
  normalize cleanly to led's convention. 294 records have no dates at all
  and get `null`, same as undated led.json records.
- `region_sub`: left `null`. led's region loss only fires for the 62 fixed
  Roman provinces in `train/data/led-region-sub.txt`, and Faliscan sites
  don't map onto that list. The dataloader already degrades gracefully
  (`region_available = False`) when `region_sub` is absent/unrecognized, so
  leaving it null is safe rather than inventing a mapping.
- `region_main`: source `site` (free text), not validated against anything.

## Needs linguist review before we write the converter

### 1. Language scope — should non-Faliscan records be included at all?

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

65 records (Etr + MF/Etr + MLF/Etr + EF/Etr) are wholly or partly in the
**Etruscan** language/alphabet, not Faliscan-Latin. The model's
`LatinAlphabet` class (`predictingthepast/util/alphabet.py`) only supports
24 classical Latin letters (`abcdefghiklmnopqrstuvxyz`, no j/w). Question
for linguists: should these Etruscan-language records be excluded from a
"Latin dataset" conversion entirely, or is there a standard
transliteration into Latin letters that's meaningful for this model?

### 2. Character mapping for non-Latin-alphabet characters

`texts.normalized` (otherwise clean, space-separated) still contains these
characters, mostly but not exclusively in Etruscan-tagged records:

| char | count | example (inscription id, text) | likely meaning |
|---|---:|---|---|
| θ (theta) | 14 | `Etr VIII`: `mialiqu auvilesiales purathevnalθia...` | Etruscan aspirated /tʰ/ |
| χ (chi) | 3 | `Etr XVIII`: `micipaχ` | Etruscan aspirated /kʰ/ |
| φ (phi) | 1 | `Etr L-LI`: `φerse cerur purφiunas` | Etruscan aspirated /pʰ/ |
| í | 1 | `Cap 389`: `a írpios esú` | accented vowel — length mark? |
| ú | 2 | `Cap 404`: `k sares esú`; `Cap 465`: `aciuaiomesú` | accented vowel — length mark? |
| ḥ, ṛ, ṃ, ḷ, ẹ, ụ (combining dot below) | 1-2 each | `Etr I-II`: `abcdevzḥθik ara`; `MF/Etr 282`: `aṃẹ`; `MLF 207`: `cauio lulḷio` | epigraphic convention for damaged/uncertain letter |
| `[` `]` | 2 | `MLF 206`: `a[.]osenauẹnarionio`; `MLF 212`: `[---]nθia` | editorial lacuna markers leaking into a field named "normalized" |
| `.` `;` `*` `-` | 1-3 each | `MF 59-60`: `foied uino pipafo cra carefo; foied uino pipafo cra carefo` | stray punctuation |

Questions for linguists:

- For the dotted-underneath letters (uncertain/damaged reading marks): should
  these become the plain letter (what a naive accent-strip would do), or
  should they map to the model's own "uncertain char" convention? Note the
  model already has a missing-char alphabet (`-` = known-length gap, `_` =
  unknown-length gap, `[`/`]` = start/end of an editorial guess) — the `[`/`]`
  found in the data may be intended to mean exactly that, in which case they
  should be preserved/converted rather than stripped.
- For í/ú: plain i/u, or something else?
- For θ/χ/φ: only relevant if Etruscan records are in scope at all (see
  question 1) — if so, is there an agreed Latin-letter transliteration
  (e.g. th/kh/ph) or should these records simply be excluded?

### 3. Interpunct handling

The `·` word-divider is already collapsed to a space in `texts.normalized`
by the existing data pipeline. Worth a linguist sanity check that this is
the right normalization (vs. e.g. treating it as punctuation to drop
without inserting a word boundary) before we treat `normalized` as
ground truth for `text`.

## Next steps

Once the above is resolved, revisit `convert_faliscan_to_led.py` (a first
draft was written and then discarded pending this review) and implement
the agreed field mapping and character-handling rules.
