"""Convert faliscan.sqlite (Bakkum 2009, Part 2) into led.json-style records.

Text rules follow conversion.md (linguist-approved) and
FALISCAN_LED_CONVERSION.md. Every output text is checked to contain only the
32 tokens of the Aeneas Latin vocabulary.

Gaps whose length is a range in Bakkum (e.g. `[5-6]`) are kept as all
possible lengths: `faliscan.text_variants` lists one text per combination,
so at inference time the model can score each and the most probable one
can be chosen. `text` holds the variant that uses the maximum length for
every range.

Usage:
    python convert_faliscan_to_led.py [--db faliscan.sqlite] [--out faliscan_led.json]
"""

import argparse
import itertools
import json
import re
import sqlite3
import unicodedata

from bakkum_corrections import ADDED, SPLITS, bakkum_group, period_name

# Aeneas LatinAlphabet tokens that may appear in a text (pad/sos/unk excluded).
VOCAB = set('abcdefghiklmnopqrstuvxyz') | set(' -_.0')

ID_OFFSET = 90_000_000  # above led.json's max id (~82.9M)
SPLIT_OFFSET = 100_000  # second half of a split database record
ADDED_OFFSET = 200_000  # inscriptions added from Bakkum (bakkum_corrections)

# Records left out on purpose (besides those without any text).
EXCLUDE_IDS = {
    'Cap 422': 'letter-form transcription on a vase (ΓYIHLILI); linguist: ignore',
}

# Hand fixes for PDF extraction errors: {inscription_id: [(old, new), ...]}.
MANUAL_FIXES = {
    # The final U+FFFD is a double interpunct dividing the beginning and end
    # of this circular inscription (Bakkum Part 2, p. 409 and §11.1.4(4)).
    'EF 3': [('\ufffd', ' ')],
    # The edition line extracts as `para[i?1]douiad`, but Bakkum's own
    # quotations of it print `para[i? .]` (i?, then one more lost letter;
    # "the width of the lacuna shows that more is missing than one i",
    # Part 2, edition p. 395, discussion p. 404).
    'EF 1': [('[i?1]', '[i?.]')],
}

RANGE_RE = re.compile(r'\[(\d+)-(\d+)\??\]')   # [5-6], [1-2?], [0-4?]
RANGE_MARK = '\x00'                               # placeholder for a range gap
COLUMN_MARKER_RE = re.compile(r'\[\d\??\]')       # [1], [3?]: tile column numbers
GREEK = {'θ': 'th', 'χ': 'ch', 'φ': 'ph'}
# Interpuncts and line ends -> space. ᛂ ᛍ are Bakkum's interpunct glyphs
# (Part 1, p. LII).
DIVIDERS = '·:⁝⁞|ᛂᛍ'


def strip_marks(t):
  """Removes underdots/accents (combining marks); keeps base letters."""
  return ''.join(
      c for c in unicodedata.normalize('NFD', t)
      if unicodedata.category(c) != 'Mn'
  )


def dots_in_brackets_to_missing(t):
  """`[.]`, `[..]` -> one `-` per dot; dots outside brackets are kept.

  Brackets in the data are sometimes nested or unbalanced, so this tracks
  depth instead of matching pairs.
  """
  out, depth = [], 0
  for c in t:
    if c == '[':
      depth += 1
    elif c == ']':
      depth = max(0, depth - 1)
    elif c == '.' and depth > 0:
      out.append('-')
      continue
    out.append(c)
  return ''.join(out)


def finish_text(t):
  """Everything after range/marker handling. Returns the final text."""
  # Additions/deletions by the editor: keep the letters, drop the marks.
  t = re.sub(r'[‹›{}]', '', t)
  # Expanded abbreviations (Latin records) and editorial comments in ( ).
  t = re.sub(r'\([^()]*\)', '', t)
  t = re.sub(r'[()]', '', t)
  # Restored letters [abc] are kept as text (option A): drop the brackets.
  t = re.sub(r'[\[\]]', '', t)
  # Word dividers and line breaks.
  t = re.sub(f'[{re.escape(DIVIDERS)}]', ' ', t)
  t = t.replace('\n', ' ')
  # Etruscan aspirates.
  for g, lat in GREEK.items():
    t = t.replace(g, lat)
  t = strip_marks(t).lower()
  # Punctuation the model's filter would delete anyway.
  t = re.sub(r'[,;!]', '', t)
  # Tidy: merge adjacent unknown-length gaps, collapse spaces.
  t = re.sub(r'_+', '_', t)
  t = re.sub(r' +', ' ', t).strip()
  return t


def convert(raw):
  """Converts one diplomatic text. Returns (text_variants, ranges)."""
  t = unicodedata.normalize('NFC', raw)

  ranges = []

  def _range(m):
    ranges.append((int(m.group(1)), int(m.group(2))))
    return RANGE_MARK
  t = RANGE_RE.sub(_range, t)

  t = COLUMN_MARKER_RE.sub('', t)
  t = re.sub(r'\d', '', t)
  t = t.replace('?', '')

  # Bakkum's dash runs ([---], [----------]) are lacunae of unknown length.
  # Convert them first so the single-letter '-' produced below is not
  # mistaken for a lacuna.
  t = re.sub(r'-+', '_', t)

  t = t.replace('(*)', '_')
  t = dots_in_brackets_to_missing(t)
  t = t.replace('*', '-')

  t = finish_text(t)

  if not ranges:
    return [t], ranges
  parts = t.split(RANGE_MARK)
  assert len(parts) == len(ranges) + 1, (raw, t)
  variants = []
  # Order: all-maximum first, so variants[0] is the default `text`.
  choices = [range(hi, lo - 1, -1) for lo, hi in ranges]
  for combo in itertools.product(*choices):
    v = parts[0]
    for n, part in zip(combo, parts[1:]):
      v += '-' * n + part
    variants.append(re.sub(r' +', ' ', v).strip())
  return variants, ranges


def convert_dates(start, end):
  """Bakkum's start_bce/end_bce -> led's signed (date_min, date_max).

  Two conventions occur: already signed (-700/-500), or positive years BCE
  with the older first (300/100). One-sided bounds keep the other side None
  (the dataloader then treats the date as unavailable).
  """
  def signed(x):
    return None if x is None else (-x if x > 0 else x)
  a, b = signed(start), signed(end)
  if a is not None and b is not None and a > b:
    a, b = b, a
  return a, b


def main():
  ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  ap.add_argument('--db', default='faliscan.sqlite')
  ap.add_argument('--out', default='faliscan_led.json')
  args = ap.parse_args()

  con = sqlite3.connect(args.db)
  con.row_factory = sqlite3.Row
  rows = con.execute("""
      select i.*, t.diplomatic, t.lines_json, t.direction
      from inscriptions i left join texts t on t.inscription_id = i.id
      order by i.rowid""").fetchall()

  # Gather (id, metadata, raw text, text source) for every inscription:
  # database rows (with Bakkum's corrections), then the added ones.
  items, skipped = [], []
  for n, r in enumerate(rows):
    r = dict(r)
    iid = r['id']
    if iid in EXCLUDE_IDS:
      skipped.append((iid, EXCLUDE_IDS[iid])); continue
    if r['falsum']:
      skipped.append((iid, 'falsum? (possible forgery)')); continue
    if r['rejected']:
      skipped.append((iid, 'rejected in Bakkum')); continue

    source, raw = 'diplomatic', r['diplomatic']
    if not raw:
      lines = json.loads(r['lines_json'] or '[]')
      source, raw = 'lines_json', '\n'.join(lines)
    if not raw:
      skipped.append((iid, 'no text')); continue
    for old, new in MANUAL_FIXES.get(iid, []):
      raw = raw.replace(old, new)

    parts = SPLITS.get(iid, [(r['bakkum_number'], raw)])
    for k, (number, text) in enumerate(parts):
      rec_id = ID_OFFSET + n if k == 0 else ID_OFFSET + SPLIT_OFFSET + n
      name = (iid if len(parts) == 1 else
              f'{bakkum_group(number, r["language_group"])} {number}')
      items.append((rec_id, name, dict(r, bakkum_number=number), text,
                    source if len(parts) == 1 else f'{source} (split)'))

  for k, a in enumerate(ADDED):
    label = bakkum_group(a['number'], None)
    lo, hi = a.get('date', (None, None))
    meta = {
        'bakkum_number': a['number'], 'language_group': None,
        'period_group': None, 'uncertain': False, 'review_status': None,
        'direction': None, 'date_label': None, 'object_type': a['object_type'],
        'site': a['site'], 'start_bce': lo, 'end_bce': hi,
    }
    items.append((ID_OFFSET + ADDED_OFFSET + k, f'{label} {a["number"]}',
                  meta, a['text'], f'added from Bakkum Part 2, p. {a["page"]}'))

  out, invalid = [], []
  for rec_id, iid, r, raw, source in items:
    variants, ranges = convert(raw)
    bad = sorted({c for v in variants for c in v} - VOCAB)
    if bad or not variants[0].strip(' _-'):
      invalid.append((iid, bad or 'empty after conversion', raw)); continue

    label = bakkum_group(r['bakkum_number'], r['language_group'])
    date_min, date_max = convert_dates(r['start_bce'], r['end_bce'])
    out.append({
        'id': rec_id,
        'record_number': iid,
        'date_min': date_min,
        'date_max': date_max,
        'object_type': r['object_type'],
        'inscription_type': None,
        'monument_type': None,
        'text': variants[0],
        'region_sub': None,
        'region_main': r['site'],
        'ids_alt': {'bakkum': r['bakkum_number']},
        'faliscan': {
            # Bakkum's group (Part 2 §11.1.3); the database's own label is
            # kept in language_group_db.
            'language_group': label,
            'language_group_db': r['language_group'],
            'period_group': (period_name(label) if label != r['language_group']
                             else r['period_group']) or r['period_group'],
            'uncertain': bool(r['uncertain']),
            'review_status': r['review_status'],
            'direction': r['direction'],
            'date_label': r['date_label'],
            'text_source': source,
            'diplomatic': raw,
            'gap_ranges': ranges,
            'text_variants': variants,
        },
    })

  with open(args.out, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

  lens = [len(r['text']) for r in out]
  print(f'wrote {len(out)} records to {args.out}')
  print(f'  with >=25 chars (model training minimum): '
        f'{sum(l >= 25 for l in lens)}')
  print(f'  with range gaps (several variants): '
        f'{sum(len(r["faliscan"]["text_variants"]) > 1 for r in out)}')
  print(f'  with both dates usable: '
        f'{sum(r["date_min"] is not None and r["date_max"] is not None for r in out)}')
  relabelled = [r for r in out if r['faliscan']['language_group']
                != r['faliscan']['language_group_db']
                and r['faliscan']['language_group_db'] is not None]
  print(f'  relabelled to Bakkum\'s group: {len(relabelled)}; '
        f'added from Bakkum: {sum(r["id"] >= ID_OFFSET + ADDED_OFFSET for r in out)}; '
        f'split: {len(SPLITS)}')
  print(f'skipped {len(skipped)}:')
  for iid, why in skipped:
    print(f'  {iid}: {why}')
  print(f'invalid {len(invalid)} (characters outside the vocabulary):')
  for iid, bad, raw in invalid:
    print(f'  {iid}: {bad}  <- {raw!r}')


if __name__ == '__main__':
  main()
