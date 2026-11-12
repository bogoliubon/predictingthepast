

| Faliscan | meaning (Bakkum's notation) | map to |
|---|---|---|
| underdotted letters `ạ ẹ ị ṃ ṛ ụ ṣ ṭ ḷ ọ ṇ ḳ ḥ ṿ ḍ` and combining U+0323 (~170 uses) | damaged but legible letter | plain letter |
| `ú í ś` | accented letter | plain letter |
| capitals (`Pu`, `C`, `ΓYIHLILI` …) | case only | lowercase (automatic) |
| `\n` | line break | space |
| `[---]`, `[?---]`, `[---?]` | lacuna of unknown length | `_` |
| `[.]`, `[..]`, `[....]` | *n* lost letters | `_` × *n* |
| `*` | one illegible letter | `_` |
| `[n]` (e.g. `[1]`) | exactly *n* lost letters | `-` × *n* |
| `[5-6]`, `[1-2?]` | roughly *n* lost letters | `_` (length not exact) we need to decide to use maximum or minimum, but that should not differ too much|
| `(*)` | possibly one more letter | `_` |
| `?` | editor's uncertainty | delete |
| digits `0-9` (54 records, 3 Etruscan) | **layout markers**, not text: letter counters every 10 letters on EF 2–4 (`propramom10 prameḍ…20…`) and column/tile numbers on LF/MLF tiles (`1 uo2ltio·uec3ineo`) | delete |
| `(blius)` inside Latin record `Lat 250` | expanded abbreviation | delete parentheses and contents, to match led.json's unexpanded style |
| `�` (1, `EF 3`, in `lines_json`) | broken character from the PDF | fix by hand against the PDF, but need chatGPT to locate the page |

### 3b. Needs linguist sign-off

| Faliscan | count | example | options |
|---|---:|---|---|
| `[abc]` letters restored by the editor | **75 records** (2 Etruscan) | `MF 11-12`: `ḷ[oc]ịes cela`; `Cap 431`: `[q]uod·a[fluc]` | **(A)** keep letters, drop brackets (treat restoration as ground truth); |
| `·` `:` `⁝` `⁞` `\|` interpuncts / dividers | `·` 343, `:` 116, `⁝` 10, `⁞` 3, `\|` 5 | `Etr VIII`: `mialiqu⁝auvilesiale…`; `Cap 431`: `p̣escoṣal \| [q]uod` | space |
| `‹x›` letter added by the editor (not on the stone) | 2 records | `MF 62`: `cupi‹d›o` | keep it (normalised) and delete the angular brackets |
| `{x}` letter on the stone that the editor deletes | 1 record | `LF 224-225`: `m{e}ania` | keep `x` (diplomatic) and delete the braces |
| `θ` | 26 | `Etr XXXIV`: `larθ:ceises` | `th` |
| `χ` | 15 | `Etr VIII`: `mlaχuta` | `ch` |
| `φ` | 3 | `Etr L-LI`: `φerse … purφiunạs` | `ph` |
| `ᛂ` (U+16C2), `ᛍ` (U+16CD) | 3, 2 | `MF 162`: `ma]2x̣ọmoᛂᛂuoltilio`; `LF 329`: `sestoᛍ` | probably space |
| `Γ` | 1 | `Cap 422`: `ΓYIHLILI` | we may ignore this example since it is on the vase and it is not very informative. |

