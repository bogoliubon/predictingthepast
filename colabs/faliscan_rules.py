"""Latin -> Faliscan spelling rules for building minimal pairs.

Only rules that can be applied from the Latin spelling alone are included:
the ones that do not depend on which older sound a Latin letter comes from
(Faliscan-Latin-sound-correspondences.md, from Bakkum 2009).

Each rule rewrites one site in a Latin text. A minimal pair is the Latin
text and the same text with one site rewritten; the controls rewrite the
same site to something else:

  alts   every other letter at the site: all letters except the rule output
         and the original span's first letter (22 of the 24). Their average
         is the "average random swap", with no sampling noise;
  rand   one of those letters, drawn from Latin letter frequencies;
  fixed  one of those letters, the same for every pair of the rule
         (a "pseudo-rule"), as consistent as the real rule.

`align` maps Latin character positions to positions in the rewritten text,
so that unchanged characters can be compared position by position.
"""

import random
import re

LETTERS = 'abcdefghiklmnopqrstuvxyz'

# name: (pattern matching the span to rewrite, Faliscan output,
#        fixed control output, source row in the correspondences table)
# Patterns are matched inside one word, so ^ and $ are the word's edges.
RULES = {
    # Spelling of kw: Faliscan cu, Latin qu (-cue / -que). Row 14, pp.77-78.
    'qu_cu': (r'q(?=u)', 'c', 'd', 'pp.77-78'),
    # Faliscan has no letter b and writes p (pi(s) / bis). Row 15, pp.78, 88-89.
    # Word-initial only: a Latin b inside a word often continues *bh or *dh,
    # where Faliscan has f (carefo / carebo, rows 6-8), and that cannot be
    # told from the spelling. One-letter abbreviations are skipped.
    'b_p': (r'^b(?=[a-z])', 'p', 'g', 'pp.78, 88-89'),
    # *ai: Faliscan e, Latin ae (efiles / aediles, celio / Caelius).
    # Row 21, pp.109-112. Not word-final: the case ending -ae continues the
    # long diphthong, which Faliscan keeps as -ai (row 25).
    'ae_e': (r'ae(?=[a-z])', 'e', 'u', 'pp.109-112'),
    # Second-declension nominative: Faliscan -o (final s not written, no
    # o > u), Latin -us. Rows 32-33, pp.93-94, 102. Not -bus (dative and
    # ablative plural); see also EXCLUDED_WORDS.
    'us_o': (r'(?<=[a-z]{2})(?<!b)us$', 'o', 'e', 'pp.93-94, 102'),
    # Accusative/neuter: Faliscan -o (final m not written, no o > u),
    # Latin -um (uino / vinum). Rows 31, 33, pp.89-90, 102. Not -orum/-arum
    # (genitive plural, a different ending historically).
    'um_o': (r'(?<=[a-z]{2})(?<![oa]r)um$', 'o', 'e', 'pp.89-90, 102'),
}

# Words whose ending looks like the rule's but is not the ending the rule is
# about: -us that is not from -os (fourth declension, pronoun genitives).
_U_STEMS = ('man dom trib id senat exercit magistrat consulat spirit obit '
            'cas grad port fruct sumpt us vult cult').split()
EXCLUDED_WORDS = {
    'us_o': {w + 'us' for w in _U_STEMS} | {'eius', 'huius', 'cuius', 'ipsius',
                                            'illius', 'unius', 'totius',
                                            'nullius', 'alterius'},
    'um_o': {w + 'um' for w in _U_STEMS},
}


def find_sites(text, rule):
  """(start, end) of every rule site inside a word made only of letters."""
  pattern = RULES[rule][0]
  sites = []
  for m in re.finditer(r'\S+', text):
    word = m.group()
    if not set(word) <= set(LETTERS):
      continue
    if word in EXCLUDED_WORDS.get(rule, ()):
      continue
    for s in re.finditer(pattern, word):
      sites.append((m.start() + s.start(), m.start() + s.end()))
  return sites


def rewrite(text, start, end, replacement):
  return text[:start] + replacement + text[end:]


def align(n_latin, start, end, out_len):
  """Latin position -> rewritten position for characters outside the span.

  Characters inside the rewritten span map to None.
  """
  delta = out_len - (end - start)
  return [i if i < start else (None if i < end else i + delta)
          for i in range(n_latin)]


def letter_freqs(texts):
  counts = {c: 1 for c in LETTERS}
  for t in texts:
    for c in t:
      if c in counts:
        counts[c] += 1
  total = sum(counts.values())
  return {c: n / total for c, n in counts.items()}


def alternatives(original, rule_out):
  """Every single-letter replacement except the rule's and the original's."""
  assert len(rule_out) == 1
  return ''.join(c for c in LETTERS if c not in (rule_out, original[0]))


def random_control(original, rule_out, freqs, rng):
  """Random letters, same length as the rule output, not equal to the rule
  output, and not starting with the original span's first letter."""
  letters, weights = zip(*freqs.items())
  while True:
    s = ''.join(rng.choices(letters, weights, k=len(rule_out)))
    if s != rule_out and s[0] != original[0]:
      return s


def make_pair(text, rule, site, freqs, rng):
  start, end = site
  _, out, fixed, _ = RULES[rule]
  original = text[start:end]
  return {
      'rule': rule,
      'start': start,
      'end': end,
      'out_len': len(out),
      'latin': text,
      'faliscan': rewrite(text, start, end, out),
      'alts': alternatives(original, out),
      'rand': rewrite(text, start, end,
                      random_control(original, out, freqs, rng)),
      'fixed': rewrite(text, start, end, fixed),
  }


def build_pairs(texts, n_per_rule, seed, rules=None):
  """One pair per text, n_per_rule texts per rule, one random site each."""
  rng = random.Random(seed)
  freqs = letter_freqs(texts)
  pairs = []
  for rule in rules or RULES:
    cands = [(t, s) for t in texts if (s := find_sites(t, rule))]
    rng.shuffle(cands)
    for text, sites in cands[:n_per_rule]:
      pairs.append(make_pair(text, rule, rng.choice(sites), freqs, rng))
  return pairs


if __name__ == '__main__':
  t = 'dis manibus sacrum quintus aelius felix vixit annis xxx bene merenti'
  rng = random.Random(0)
  f = letter_freqs([t])
  for r in RULES:
    for site in find_sites(t, r):
      p = make_pair(t, r, site, f, rng)
      a = align(len(t), p['start'], p['end'], p['out_len'])
      # every character outside the span must be unchanged after alignment
      assert all(p['faliscan'][j] == t[i] for i, j in enumerate(a)
                 if j is not None), r
      assert all(p['rand'][j] == t[i] for i, j in enumerate(a)
                 if j is not None), r
      assert len(p['alts']) == 22 and RULES[r][2] in p['alts'], r
      assert p['rand'][p['start']] in p['alts'], r
      print(f"{r:6s} {p['faliscan']}\n{'':6s} {p['rand']}  (rand)\n"
            f"{'':6s} {p['fixed']}  (fixed)")
