# Evaluating the Faliscan methods

All methods (step 0, the rule-based rewriting baseline, steering/low-rank
edits) are scored on the same test set, built by `build_faliscan_eval_set.py`
from `faliscan_led.json` and written to `faliscan_eval_set.json`.

Restoration and dating have known answers, so they are scored automatically.
Experts are needed only for the **retrieved parallels**.

## 1. Test set

Each record of the converted corpus (464) is kept or excluded for the first
reason that applies. The file lists every excluded record with its reason.

| Filter | Why | Excluded |
|---|---|---|
| No edition of its own (`Lat 250`, `LF 246`, `MF 135`) | Bakkum only quotes or mentions the text | 3 |
| Etruscan, partly Etruscan, Sabellic | not what we adapt to | 61 |
| A short text repeated (`turia` ×6, `uoltai` ×4, …) | kept once, then re-checked by the next filters | (counted below) |
| Shorter than 25 characters | the model's minimum input | 333 |
| Mostly abbreviations (> 50% of words have ≤ 2 letters) | e.g. `mr mr mr …`, `m f ce … c f`: little to restore or date | 8 |
| Too little surviving text (< 20 certain letters, or < 70% of letter positions survive unrestored) | the answer would rest on the editor, not the stone | 15 |

"Certain" letters are surviving letters that are neither restored by Bakkum
(`[abc]`) nor underdotted.

**Result:**
- **Faliscan test set: 35 records**, 20 of them dated: MF 10, LF 9, MLF 6, EF 4, LtF 3, Cap 2, LF/Lat 1.
- **Latin subset: 9 records**, the Latin inscriptions of the ager Faliscus. These check that an adapted model still handles Latin.

`MLF 315` (19 certain letters) and `LtF 290` (18) only just miss the
threshold. The thresholds are constants at the top of the script.

## 2. Automatic scoring (no experts)

| Task | Answer | Score |
|---|---|---|
| Restoration, hidden surviving letters | the letters on the stone: `hideable_positions` (1,367 letters) | top-1 / top-20 exact match, by span length 1–3 |
| Restoration, Bakkum's own restorations | Bakkum's letters: `bakkum_restorations` (22 spans in 12 records, 21 of 1–3 letters) | agreement with Bakkum, top-1 / top-20 |
| Dating | Bakkum's range (20 records) | years outside the range; share inside |
| Region | — (no Faliscan region among the 62) | rank of Etruria |

Agreement with Bakkum's restorations is a near-answer key rather than a true
one, because they are an editor's proposals. With only 22 spans it is
reported alongside the main restoration score, not instead of it.

The same tests run on the Latin subset and on the matched LED control texts
(see the step-0 script), so we can tell whether a method helps Faliscan
without hurting Latin.

## 3. Expert evaluation: retrieved parallels

For each text the model retrieves the most similar inscriptions in the
Latin corpus (LED). Whether a parallel is useful is a judgement call, so
this is where experts come in.

**Texts:** all 35 of the Faliscan test set (`expert_parallels_sample` in
the output file). Parallels need no date, so undated records count too. If
this proves too much work, `--sample N` draws N texts in proportion to
period group.

**Candidates:** the top 3 parallels from each method, merged into one list
per text. A parallel proposed by several methods appears once. The list is
shuffled and does not say which method proposed what.

**Judgement:** one per parallel:
- 0 = not relevant;
- 1 = related (formula, onomastics, object type or context);
- 2 = a close parallel, one a commentator would cite.

**Workload:** with 3–4 methods and some overlap, about 6–10 parallels per
text, so 210–350 quick judgements. About 2–3 hours per expert.

**Agreement:** a second expert also rates 6 of the 35 texts. We report how
far the two agree (weighted κ).

**Scores per method:**
- mean relevance of its top 3;
- share of texts with at least one parallel rated 2.

Because judgements are made per parallel, not per method, adding a method
later only costs the judgements for parallels nobody has rated yet.
