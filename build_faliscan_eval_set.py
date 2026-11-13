"""Build the Faliscan evaluation set from faliscan_led.json.

Every record of the converted corpus gets a verdict (kept, or why not), so the
selection can be checked and argued with. Kept records are split into two
subsets: `faliscan` (the test set) and `latin` (Latin inscriptions from the
ager Faliscus, a check that adapted models still handle Latin).

For each kept record the output also gives the answer keys that let
restoration be scored without experts:

  bakkum_restorations  letters Bakkum restores in brackets, e.g. [fe]ronea:
                       hide them and compare the model with Bakkum.
  uncertain_letters    underdotted letters (damaged, reading uncertain).
  hideable_positions   letters that survive on the stone and are certain:
                       the positions the step-0 test may hide (exact answer).

Positions are character offsets into the record's `text`.

Filters, in order (see EVALUATION.md):
  1. no edition of its own (Bakkum only quotes or mentions the text)
  2. Etruscan or partly Etruscan (language group contains Etr, or Sab)
  3. a short text repeated (e.g. turia x6): kept once, then re-checked
  4. shorter than the model's minimum input (25 characters)
  5. mostly abbreviations (more than half the words have <= 2 letters)
  6. too little surviving text (< 20 certain letters, or < 70% of the
     letter positions survive unrestored)

Usage:
    python build_faliscan_eval_set.py [--input faliscan_led.json]
        [--out faliscan_eval_set.json] [--sample 0] [--seed 0]
"""

import argparse
import collections
import json
import random
import re
import unicodedata

from convert_faliscan_to_led import MANUAL_FIXES, convert

MIN_LEN = 25           # inference.MIN_TEXT_LEN of the Aeneas model
MIN_SURVIVING = 20     # certain, unrestored letters
MIN_SURVIVING_SHARE = 0.7
MAX_ABBREV_SHARE = 0.5

NO_EDITION = {
    'Lat 250': 'no edition; Bakkum quotes AE 1982, 286',
    'LF 246': 'no edition; mention of an unpublished tile',
    'MF 135': 'no edition; unpublished tile reported by Colonna',
}

# Private-use characters that mark spans through convert(); none of the
# conversion rules touch them.
R_OPEN, R_CLOSE, U_OPEN, U_CLOSE = '', '', '', ''
DOT_BELOW = '̣'


def mark_spans(raw):
  """Marks restorations [abc] and underdotted letters in a diplomatic text."""
  t = unicodedata.normalize('NFD', raw)
  t = re.sub(r'([A-Za-z])' + DOT_BELOW, U_OPEN + r'\1' + U_CLOSE, t)
  t = re.sub(r'\[([A-Za-z]+)\]', R_OPEN + r'\1' + R_CLOSE, t)
  return unicodedata.normalize('NFC', t)


def extract_spans(marked):
  """Removes markers; returns (text, restored spans, uncertain positions)."""
  out, restored, uncertain, start = [], [], [], None
  for c in marked:
    if c == R_OPEN:
      start = len(out)
    elif c == R_CLOSE:
      if start is not None and len(out) > start:
        restored.append((start, len(out)))
      start = None
    elif c == U_OPEN:
      uncertain.append(len(out))
    elif c == U_CLOSE:
      pass
    else:
      out.append(c)
  return ''.join(out), restored, uncertain


def answer_keys(rec):
  """Spans in rec['text'] from its diplomatic text, or None if unaligned."""
  raw = rec['faliscan']['diplomatic']
  for old, new in MANUAL_FIXES.get(rec['record_number'], []):
    raw = raw.replace(old, new)
  variants, _ = convert(mark_spans(raw))
  text, restored, uncertain = extract_spans(variants[0])
  if text != rec['text']:
    return None
  return restored, uncertain


def collapse_repeats(text):
  """'turia turia turia' -> ('turia', 3); otherwise (text, 1)."""
  words = text.split(' ')
  n = len(words)
  for p in range(1, n // 2 + 1):
    if n % p == 0 and words == words[:p] * (n // p):
      return ' '.join(words[:p]), n // p
  return text, 1


def evaluate(rec):
  """Returns (verdict, details). verdict is 'faliscan', 'latin' or a reason."""
  f = rec['faliscan']
  group = f['language_group'] or ''
  name = rec['record_number']
  if name in NO_EDITION or name.split(' ', 1)[-1] in {'135'}:
    return NO_EDITION.get(name, 'no edition'), {}
  if 'Etr' in group or group == 'Sab':
    return f'not Faliscan or Latin ({group})', {}

  keys = answer_keys(rec)
  if keys is None:
    return 'answer keys could not be aligned (check by hand)', {}
  restored, uncertain = keys

  text, copies = collapse_repeats(rec['text'])
  if copies > 1:  # keep the first copy and the spans inside it
    restored = [s for s in restored if s[1] <= len(text)]
    uncertain = [i for i in uncertain if i < len(text)]
  if len(text) < MIN_LEN:
    return (f'too short ({len(text)} characters'
            + (f' after removing {copies - 1} repeats)' if copies > 1 else ')'),
            {})

  words = [w for w in re.sub(r'[^a-z ]', '', text).split() if w]
  abbrev = sum(len(w) <= 2 for w in words) / max(len(words), 1)
  if abbrev > MAX_ABBREV_SHARE:
    return f'mostly abbreviations ({abbrev:.0%} of words <= 2 letters)', {}

  restored_pos = {i for a, b in restored for i in range(a, b)}
  letters = [i for i, c in enumerate(text) if c.isalpha()]
  hideable = [i for i in letters
              if i not in restored_pos and i not in set(uncertain)]
  lost = text.count('-')
  share = len(hideable) / max(len(letters) + lost, 1)
  if len(hideable) < MIN_SURVIVING or share < MIN_SURVIVING_SHARE:
    return (f'too little surviving text ({len(hideable)} certain letters, '
            f'{share:.0%} of letter positions)'), {}

  return ('latin' if group == 'Lat' else 'faliscan'), dict(
      text=text,
      repeats_removed=copies - 1,
      bakkum_restorations=[dict(start=a, end=b, gold=text[a:b])
                           for a, b in restored],
      uncertain_letters=uncertain,
      hideable_positions=hideable,
      surviving_share=round(share, 3),
  )


def stratified_sample(records, k, seed):
  """k records, spread over period groups in proportion (at least 1 each)."""
  by_group = collections.defaultdict(list)
  for r in records:
    by_group[r['language_group'].split('/')[0].rstrip('?')].append(r)
  rng = random.Random(seed)
  quota = {g: max(1, round(k * len(rs) / len(records)))
           for g, rs in by_group.items()}
  while sum(quota.values()) > k:  # trim the largest groups first
    g = max(quota, key=lambda g: (quota[g], g))
    quota[g] -= 1
  picked = []
  for g, rs in sorted(by_group.items()):
    picked += rng.sample(rs, min(quota[g], len(rs)))
  return sorted(r['record_number'] for r in picked)


def main():
  ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  ap.add_argument('--input', default='faliscan_led.json')
  ap.add_argument('--out', default='faliscan_eval_set.json')
  ap.add_argument('--sample', type=int, default=0,
                  help='texts whose retrieved parallels go to the experts '
                       '(0 = all of the Faliscan test set)')
  ap.add_argument('--seed', type=int, default=0)
  args = ap.parse_args()

  data = json.load(open(args.input, encoding='utf-8'))
  subsets = collections.defaultdict(list)
  excluded = []
  for rec in data:
    verdict, d = evaluate(rec)
    if verdict in ('faliscan', 'latin'):
      subsets[verdict].append(dict(
          id=rec['id'], record_number=rec['record_number'],
          language_group=rec['faliscan']['language_group'],
          date_min=rec['date_min'], date_max=rec['date_max'], **d))
    else:
      excluded.append(dict(record_number=rec['record_number'],
                           length=len(rec['text']), reason=verdict))

  sample = (stratified_sample(subsets['faliscan'], args.sample, args.seed)
            if args.sample else
            sorted(r['record_number'] for r in subsets['faliscan']))
  out = dict(
      source=args.input,
      settings=dict(min_len=MIN_LEN, min_surviving=MIN_SURVIVING,
                    min_surviving_share=MIN_SURVIVING_SHARE,
                    max_abbrev_share=MAX_ABBREV_SHARE, seed=args.seed),
      faliscan=subsets['faliscan'],
      latin=subsets['latin'],
      expert_parallels_sample=sample,
      excluded=excluded,
  )
  with open(args.out, 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)

  fal = subsets['faliscan']
  print(f'wrote {args.out}')
  print(f'  faliscan test set: {len(fal)} records '
        f'({sum(r["date_min"] is not None and r["date_max"] is not None for r in fal)} dated)')
  print('    by group: ' + ', '.join(
      f'{g} {n}' for g, n in collections.Counter(
          r['language_group'] for r in fal).most_common()))
  rest = [s for r in fal for s in r['bakkum_restorations']]
  print(f'    Bakkum restorations: {len(rest)} in {sum(bool(r["bakkum_restorations"]) for r in fal)} '
        f'records ({sum(len(s["gold"]) <= 3 for s in rest)} of 1-3 letters)')
  print(f'    hideable letters: {sum(len(r["hideable_positions"]) for r in fal)}')
  print(f'  latin subset: {len(subsets["latin"])} records')
  print(f'  expert sample for parallels: {len(sample)} texts')
  reasons = collections.Counter(re.sub(r' \(.*', '', e['reason']) for e in excluded)
  print(f'  excluded {len(excluded)}:')
  for why, n in reasons.most_common():
    print(f'    {n:4}  {why}')
  print('  excluded with >= 25 characters:')
  for e in excluded:
    if e['length'] >= MIN_LEN:
      print(f'    {e["record_number"]:16} {e["reason"]}')


if __name__ == '__main__':
  main()
