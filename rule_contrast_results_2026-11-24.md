# Rule contrast: how the Latin model treats single Faliscan spellings

**Date: 2026-11-24, updated 2026-11-25.** All numbers are from the run `v3`
(2026-11-25), which uses tightened rules; `v1` (2026-11-23) and `v2` (2026-11-24)
used looser rules and gave the same picture (see "Changes from v2").
Status: first results on 5 rules. The next steps wait on YQ's review of the rules
(`faliscan_test_rule_check.md`).

## Summary

- We rewrote one spot in held-out Latin inscriptions according to a Faliscan spelling
  rule and compared the model's internal representation of the two versions.
- The model already pulls *cu* toward *qu*: *c* starts as the 16th closest letter to
  *q* at the input and is the 2nd closest of 23 from the middle layers on.
- Faliscan *-o* for *-us* and *-um* is also pulled close in the middle layers, but so
  are *-a* and *-i*. This looks like "still a Latin ending", not something about Faliscan.
- *p* for word-initial *b* is already the closest letter at the input and stays among
  the closest five. The layers do not pull it closer.
- Most of the shift caused by a Faliscan letter (cosine 0.60-0.77 in the middle layers)
  is the shift any replacement letter causes.
- The Latin text has a stable representation at each site, and the shift is consistent
  across texts. That is the minimum needed for undoing the shift.
- None of this yet shows that the directions are useful. That needs the steering test
  on the real Faliscan texts.

## Setup

- **Model.** The released Aeneas checkpoint, unchanged: 16 transformer blocks, 384
  dimensions, one token per character.
- **Latin texts.** LED test split (ids ending in 3 or 4), cleaned as in step 0, 25-250
  characters: 34,706 texts.
- **Rules.** Five Latin → Faliscan rewrites that can be applied from the Latin spelling
  alone (`colabs/faliscan_rules.py`, from `Faliscan-Latin-sound-correspondences.md`):

  | Rule | Rewrite | Example |
  |---|---|---|
  | Rule | Rewrite | Example | Not applied to |
  |---|---|---|---|
  | `qu_cu` | q → c before u | quintus → cuintus | |
  | `b_p` | word-initial b → p | bene → pene | b inside a word (Faliscan may have f there); the one-letter abbreviation *b* |
  | `ae_e` | ae → e, not word-final | aelius → elius | the case ending -ae (Faliscan -ai) |
  | `us_o` | word-final -us → -o | quintus → quinto | -bus; *eius*, *huius*, *cuius* and similar; fourth-declension words (*manus*, *domus*, *idus* ...) |
  | `um_o` | word-final -um → -o | sacrum → sacro | -orum, -arum; the same fourth-declension words |

  The rules match on spelling, so the conditions in the last column keep out endings
  that only look like the rule's. They are our reading of YQ's table and need YQ's
  confirmation. Third-declension neuters (*opus*) and adverbs in *-ius* still pass
  `us_o`. 28% of the `b_p` sites in the Latin texts are the word *bene*.

- **Pairs.** 400 texts per rule, one randomly chosen site rewritten in each: 2000
  pairs. Sites are only taken inside words with no gaps.
- **Versions per pair (24).** The Latin text, the Faliscan rewrite, and the same site
  rewritten to each of the 22 other letters (every letter except the Faliscan one and
  the original one). The 22 alternatives give the "average random swap" exactly.
- **What is recorded.** The residual stream after the embedding, after each of the 16
  blocks and after the final layer norm, at the rewritten letters (the site) and at the
  start-of-sequence position (which the date and region heads read). Positions after
  the site are re-aligned when the rewrite changes the length.

Definitions, for one pair at one layer:

- shift of letter x = (representation with x at the site) − (representation of the Latin text);
- average random swap = mean shift over the 22 alternatives;
- Faliscan-specific shift = Faliscan shift − average random swap.

## Results

### 1. Where the Faliscan letter ranks among the 23 possible replacements

Letters are ordered by their median distance from the Latin representation at the
site (1 = closest). "Top 3" is the share of pairs in which the Faliscan letter is among
the three closest.

| Rule | Input | Block 7 | Block 11 | Final layer |
|---|---|---|---|---|
| `qu_cu` (c) | 16th | 2nd (top 3 in 93%) | 2nd (93%) | 2nd (88%) |
| `um_o` (o) | 7th | 2nd (76%) | 1st (92%) | 3rd (32%) |
| `us_o` (o) | 8th | 2nd (61%) | 2nd (89%) | 5th (17%) |
| `b_p` (p) | 1st | 5th (45%) | 4th (23%) | 4th (18%) |

- `qu_cu`: only *o* is closer to *q* than *c* is.
- `us_o`, `um_o`: the closest letters are *o*, *a* and *i*, all of which make valid
  Latin endings. *s* (for -us) and *m* (for -um) also rank close, but only because
  they are part of the original ending. The ranks above count them, so among genuinely
  new letters *o* is one place higher in most cells.
- `ae_e` is left out: the *e* is part of the original *ae*, so it is closest by
  construction.

The same picture, as how much of the input-level difference survives, relative to the
mean over the 22 alternatives (below 1 = pulled back toward the Latin more than an
average letter):

| Rule | Block 7 | Block 11 | Final layer |
|---|---|---|---|
| `qu_cu` | 0.70 | 0.68 | 0.51 |
| `um_o` | 0.69 | 0.68 | 0.92 |
| `us_o` | 0.81 | 0.76 | 0.98 |
| `b_p` | 1.02 | 1.06 | 1.00 |

### 2. How much of the Faliscan shift is generic

Median cosine between the Faliscan shift and the average random swap, at the site:

| Rule | Block 7 | Block 11 |
|---|---|---|
| `qu_cu` | 0.77 | 0.77 |
| `b_p` | 0.77 | 0.75 |
| `us_o` | 0.75 | 0.75 |
| `um_o` | 0.60 | 0.61 |
| `ae_e` | 0.47 | 0.53 |

So most of "Faliscan minus Latin" at the site is what any replaced letter produces.

### 3. Consistency of the Faliscan-specific direction

Mean cosine between one pair's Faliscan-specific shift and the mean over the other
399 pairs, at block 7, next to the median of the same number for the 22 alternative
letters:

| Rule | Faliscan letter | Median alternative |
|---|---|---|
| `qu_cu` | 0.83 | 0.88 |
| `b_p` | 0.89 | 0.90 |
| `ae_e` | 0.83 | 0.89 |
| `us_o` | 0.83 | 0.89 |
| `um_o` | 0.86 | 0.88 |

Each rule has a clear, consistent direction, but so does every other letter. A
consistent direction is what any fixed substitution gives and is not by itself evidence
about Faliscan.

### 4. Consistency of the site itself, before and after the rewrite

Here no shift is taken. For each rule, the representation at the site is compared
across the 400 texts (mean cosine of one text with the mean of the others), after
subtracting the average character representation of Latin text at that layer. The
third number is the same measure for the raw shift, Faliscan minus Latin.

| Rule | Block 7: Latin / Faliscan / shift | Block 11 | Final layer |
|---|---|---|---|
| `qu_cu` | 0.66 / 0.66 / 0.79 | 0.65 / 0.71 / 0.76 | 0.88 / 0.85 / 0.56 |
| `b_p` | 0.70 / 0.76 / 0.83 | 0.69 / 0.81 / 0.77 | 0.80 / 0.69 / 0.60 |
| `ae_e` | 0.53 / 0.54 / 0.71 | 0.58 / 0.56 / 0.61 | 0.82 / 0.68 / 0.59 |
| `us_o` | 0.71 / 0.74 / 0.83 | 0.82 / 0.81 / 0.84 | 0.91 / 0.71 / 0.80 |
| `um_o` | 0.71 / 0.72 / 0.84 | 0.82 / 0.80 / 0.80 | 0.86 / 0.59 / 0.65 |

- The Latin site has a stable representation across texts, and it is specific to the
  site: the mean directions of different rules have cosine between -0.29 and +0.23
  with each other, except *-us* and *-um* (0.40 at block 7, 0.53 at the final layer).
- In the middle layers the shift is more consistent than the site itself; at the final
  layer the Latin site is the most consistent of the three.
- This shows that the model represents the same letters at the same kind of position
  alike in different texts. It does not show whether the direction encodes the letters
  or their grammatical role (*-us* and *-um* share the letter *u*). For undoing a
  Faliscan spelling the difference does not matter: either way there is a Latin target.
- The average character representation comes from only 35 Latin texts.

### 5. Effect on the whole-text representation

One rewritten site moves the start-of-sequence representation by 2-4% in the middle
layers and 9-25% at the final layer (`v1`, old rules).

### 6. Checks on the random baseline

- One random draw per pair and all 22 alternatives give nearly the same
  mean direction: cosine 0.93-0.99 across rules and layers.
- For a single pair, one draw is noisy: cosine 0.63-0.83 with the exhaustive version.
- Averaging the alternatives uniformly or by Latin letter frequency gives the same
  direction: cosine 0.93-0.99.

### Changes from v2

`v2` applied the rules on spelling alone. Of its 400 pairs per rule, the doubtful
sites were: `us_o` 41 in *-bus* (10 of them *manibus*) and about 15 others (*eius*,
*idus*); `um_o` 129 in *-orum*/*-arum*; `ae_e` 227 word-final *-ae*; `b_p` all but
about 70 (b inside a word, or the abbreviation *b*). With these removed (`v3`):

- `qu_cu`: the same pairs, the same numbers.
- `us_o`, `um_o`: unchanged within a few hundredths; rank of *o* at block 7 goes from
  3rd to 2nd for `us_o`.
- `b_p`: *p* is slightly less close (final layer: 4th, top 3 in 18%; before: 2nd, 29%)
  and still gets no pull from the layers.

So the doubtful sites were not driving the results.

## What this does and does not show

- **Working view.** The model knows Latin, and Faliscan is close to Latin except at the
  changed letters. We are not looking for Faliscan knowledge in the model; we are
  looking for the shift each change causes, so that it can be undone.
- **Vector to use.** For undoing a change, the vector is Faliscan minus Latin at the
  changed letters. The alternatives are a control for interpretation, and will be
  needed once more as the control in the steering test. A second option is to move
  the site toward the mean Latin representation for that site (result 4); the steering
  test should compare the two.
- **Comparison with real Faliscan: not a valid test yet.** At the start-of-sequence
  position, the Faliscan-specific directions point away from (real Faliscan − Latin)
  in the upper layers (cosine −0.31 to −0.68 at block 15, about the same in `v2` and `v3`; the alternative letters range
  from about −0.6 to +0.4). This compares one rule in one spot with 35 real texts that
  differ from the Latin texts in many rules and in content, and the two sets are
  different inscriptions. It says nothing for or against the rules.
- **`ae_e` needs a different measurement** (at the *e* alone) before its numbers can
  be read.

## Next steps (after YQ's review)

1. Add the rules the test set needs most: e → i before a vowel, c → g and z → s
   (in the Latin → Faliscan direction: i → e, g → c, s → z).
2. Rewrite every site of every rule in a text, to check whether the per-rule directions
   add up and how much of the restoration gap (83% on Latin, 42% on Faliscan for one
   hidden letter) these rules explain.
3. Steering test on the 35 real Faliscan texts: subtract the Faliscan-minus-Latin
   direction at the matching letters and compare restoration with step 0 and with
   subtracting another letter's direction of the same size.

## Files

| File | Contents |
|---|---|
| `colabs/faliscan_rules.py` | the rules, pair building, position alignment |
| `colabs/rule_contrast.py`, `colabs/run_rule_contrast.sub` | activation extraction (Slurm job) |
| `colabs/analyze_rule_contrast.py` | the analysis; writes `report.json` |
| `colabs/rule_contrast/v3/` | every pair in `meta.json`, `report.txt`, `report.json`; the activations (`acts.npz`, 1.4 GB) are not in git |
| `colabs/rule_contrast/v1/`, `v2/` | earlier runs with the looser rules; not in git |

To reproduce, from `colabs/`: `sbatch run_rule_contrast.sub --name v3` (about 4
minutes on one GPU), then `python analyze_rule_contrast.py rule_contrast/v3`.
