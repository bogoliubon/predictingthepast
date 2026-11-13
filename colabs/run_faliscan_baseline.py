"""Step 0 baseline: run the unchanged Aeneas Latin model on Faliscan text.

For every Faliscan record with at least 25 characters (the model's minimum
input length), this records the model's four outputs:

  1. Restoration: letters that survive on the stone are hidden and the model
     has to restore them. Scored as top-1 / top-20 exact match of the hidden
     span and top-1 character accuracy.
  2. Dating: predicted date distribution, compared with Bakkum's date range
     where both bounds are known.
  3. Region: the 62 Roman regions, with the probability of Etruria (where
     the Ager Faliscus lies), Latium et Campania and Roma reported.
  4. Retrieved parallels: the most similar inscriptions in the LED.

A Latin control runs the same restoration test on Latin LED test-split
inscriptions with the same length distribution, so the Faliscan scores can be
compared against what the model does on short Latin texts.

Later conditions (e.g. Faliscan rewritten into Latin spelling) can reuse the
script with --input pointing at a converted file and a different --name.

Usage (from colabs/):
    python run_faliscan_baseline.py
    python run_faliscan_baseline.py --limit 2          # quick timing test
    python run_faliscan_baseline.py --name step0_raw --input ../faliscan_led.json
"""

import argparse
import json
import os
import random
import time

import jax
import numpy as np
from tqdm import tqdm

from predictingthepast.eval import inference
import predictingthepast.util.eval as eval_util
from run_swap_inference import load_checkpoint

DATE_MIN, DATE_MAX, DATE_INTERVAL = -800, 800, 10
DATE_BINS = np.arange(DATE_MIN + DATE_INTERVAL / 2, DATE_MAX, DATE_INTERVAL)
MIN_LEN, MAX_LEN = inference.MIN_TEXT_LEN, inference.TEXT_LEN - 1
LETTERS = set('abcdefghiklmnopqrstuvxyz')
REGIONS_OF_INTEREST = ['Etruria', 'Latium et Campania', 'Roma']


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def mean_date(year_scores):
  s = np.asarray(year_scores)
  return float(np.dot(DATE_BINS, s) / s.sum()) if s.sum() > 0 else None


def date_distance(pred, lo, hi):
  """Years between a predicted date and a gold interval (0 if inside)."""
  if pred is None or lo is None or hi is None:
    return None
  if lo <= pred <= hi:
    return 0.0
  return float(min(abs(pred - lo), abs(pred - hi)))


def _bucket(n, step):
  return -(-n // step) * step


def _pow2(n):
  return 1 << max(0, n - 1).bit_length()


class PaddedForward:
  """Compiled model forward pass for beam search, at a few fixed shapes.

  Beam search calls the model with a different (beam size, text length) on
  almost every step, and each new shape is compiled again. This pads the
  length up to a multiple of `len_step` with the pad token (index 0) and the
  batch up to a power of two (repeating the first row), then cuts the
  outputs back. Pad tokens are masked out of attention, so the outputs for
  the real rows and positions are the same up to floating-point rounding.
  """

  def __init__(self, forward, len_step=64):
    self.len_step = len_step
    self._jitted = jax.jit(
        lambda params, text_char: forward(params, text_char=text_char))

  def __call__(self, params, text_char, text_char_onehot=None,
               vision_img=None, vision_available=None):
    assert text_char_onehot is None and vision_img is None
    b, l = text_char.shape
    bp, lp = _pow2(b), min(_bucket(l, self.len_step), inference.TEXT_LEN)
    x = np.pad(text_char, ((0, 0), (0, lp - l)), constant_values=0)
    x = np.pad(x, ((0, bp - b), (0, 0)), mode='edge')
    outs = self._jitted(params, x)
    return tuple(o[:b, :l] if o is not None and o.ndim >= 2 and
                 o.shape[:2] == (bp, lp) else
                 (o[:b] if o is not None and o.ndim >= 1 and o.shape[0] == bp
                  else o)
                 for o in outs)


def fast_restore(masked, forward, params, alphabet, beam_width,
                 return_scores=False):
  """inference.restore() without the saliency maps (which we don't use).

  Returns beam predictions, best first (with their log-probabilities if
  return_scores).
  """
  (_, _, text_padded, _, text_len, _, restore_mask_idx) = (
      inference._prepare_text(masked, alphabet))
  beam = eval_util.beam_search_batch(
      forward, params, alphabet, text_padded, restore_mask_idx,
      max_len=text_len[0], beam_width=beam_width,
      temperature=inference.RESTORATION_TEMPERATURE,
      sequential_decoding=False, a_penalty=inference.A_PENALTY)
  texts = [b.text_pred[1:].rstrip(alphabet.pad) for b in beam]
  if return_scores:
    return list(zip(texts, [float(b.pred_logprob) for b in beam]))
  return texts


def fast_attribute(text, forward, params, alphabet):
  """inference.attribute() without the saliency maps.

  Returns (region probabilities [62], date probabilities [160]).
  """
  (_, _, _, text_char, _, _, _) = inference._prepare_text(text, alphabet)
  date_logits, region_logits, _, _, _ = forward(
      params, text_char=text_char,
      vision_img=np.zeros((1, 224, 224, 1)), vision_available=np.zeros((1,)),
      rngs={'dropout': jax.random.PRNGKey(inference.SEED)}, is_training=False)
  return (eval_util.softmax(np.array(region_logits)[0]),
          eval_util.softmax(np.array(date_logits)[0]))


def hide_spans(text, span_len, n_trials, rng):
  """Picks up to n_trials distinct spans of `span_len` surviving letters.

  A span must consist only of letters (no space, gap or punctuation), so we
  only ever hide letters that are actually on the stone.
  """
  starts = [
      i for i in range(len(text) - span_len + 1)
      if all(c in LETTERS for c in text[i:i + span_len])
  ]
  rng.shuffle(starts)
  return sorted(starts[:n_trials])


def restoration_trials(text, model, span_lens, n_trials, rng, beam_width):
  """Hides letter spans and scores the model's restorations."""
  _, params, alphabet, vocab, restore_forward = model
  trials = []
  for span_len in span_lens:
    for start in hide_spans(text, span_len, n_trials, rng):
      truth = text[start:start + span_len]
      masked = (text[:start] + inference.ALPHABET_MISSING_RESTORE * span_len
                + text[start + span_len:])
      preds = [p[start:start + span_len] for p in
               fast_restore(masked, restore_forward, params, alphabet, beam_width)]
      top1 = preds[0] if preds else ''
      trials.append({
          'start': start,
          'span_len': span_len,
          'truth': truth,
          'top1': top1,
          'top1_correct': top1 == truth,
          'top20_correct': truth in preds[:20],
          'rank': preds.index(truth) + 1 if truth in preds else None,
          'char_acc': sum(a == b for a, b in zip(top1, truth)) / span_len,
          'top5': preds[:5],
      })
  return trials


def attribution(text, model, region_names):
  forward, params, alphabet, vocab, _ = model
  region_probs, date_probs = fast_attribute(text, forward, params, alphabet)
  order = np.argsort(-region_probs)
  ranked = [region_names[i] for i in order]
  probs = {region_names[i]: float(p) for i, p in enumerate(region_probs)}
  return {
      'region_top5': [{'region': ranked[k], 'score': probs[ranked[k]]}
                      for k in range(5)],
      'region_of_interest': {r: probs.get(r) for r in REGIONS_OF_INTEREST},
      'etruria_rank': ranked.index('Etruria') + 1,
      'mean_date': mean_date(date_probs),
      'year_scores': [float(x) for x in date_probs],
  }


def parallels(text, model, dataset, retrieval, region_map, top_k):
  forward, params, alphabet, _, _ = model
  ctx = inference.contextualize(
      text, dataset, retrieval, forward=forward, params=params,
      alphabet=alphabet, region_map=region_map, top_k=top_k)
  return [
      {
          'id': i,
          'text': t,
          'region': (region_map['names'][loc] if loc is not None else None),
          'date_min': dmin,
          'date_max': dmax,
          'score': s,
      }
      for i, t, loc, dmin, dmax, s in zip(
          ctx.ids, ctx.text, ctx.location_ids, ctx.date_min, ctx.date_max,
          ctx.score)
  ]


def summarize_restoration(records):
  trials = [t for r in records for t in r['restoration']]
  out = {'n_trials': len(trials)}
  for L in sorted({t['span_len'] for t in trials}):
    ts = [t for t in trials if t['span_len'] == L]
    out[f'span_{L}'] = {
        'n': len(ts),
        'top1': float(np.mean([t['top1_correct'] for t in ts])),
        'top20': float(np.mean([t['top20_correct'] for t in ts])),
        'char_acc': float(np.mean([t['char_acc'] for t in ts])),
    }
  return out


def latin_control_texts(dataset, lengths, seed):
  """One Latin LED test-split text per Faliscan text, matched on length.

  Test split = ids ending in 3 or 4, as in inference.load_retrieval.
  LED text is cleaned the same way the model's filter would clean it.
  """
  def clean(t):
    t = ''.join(c for c in t.lower() if c in LETTERS or c in ' -_.')
    return ' '.join(t.split())
  pool = {}
  for d in dataset.values():
    if str(d['id'])[-1] not in '34':
      continue
    t = clean(d['text'])
    if MIN_LEN <= len(t) <= MAX_LEN:
      pool.setdefault(len(t), []).append((d['id'], t))
  rng = random.Random(seed)
  chosen = []
  for L in lengths:
    for delta in range(0, 50):  # nearest available length
      cands = pool.get(L + delta) or pool.get(L - delta)
      if cands:
        chosen.append(rng.choice(cands))
        break
  return chosen


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
  ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  ap.add_argument('--name', default='step0_raw', help='condition name')
  ap.add_argument('--input', default='../faliscan_led.json')
  ap.add_argument('--out_dir', default='faliscan_baseline')
  ap.add_argument('--checkpoint', default='checkpoint.pkl')
  ap.add_argument('--dataset', default='dataset.json', help='LED json')
  ap.add_argument('--retrieval', default='dataset_emb.pkl')
  ap.add_argument('--span_lens', default='1,2,3',
                  help='lengths of hidden letter spans')
  ap.add_argument('--n_trials', type=int, default=5,
                  help='hidden spans per text per span length')
  ap.add_argument('--beam_width', type=int, default=inference.RESTORATION_BEAM_WIDTH)
  ap.add_argument('--top_k', type=int, default=10, help='parallels to keep')
  ap.add_argument('--seed', type=int, default=0)
  ap.add_argument('--limit', type=int, default=None,
                  help='only the first N records (timing tests)')
  ap.add_argument('--no_latin_control', action='store_true')
  ap.add_argument('--no_pad', action='store_true',
                  help='run beam search without length/batch buckets '
                       '(slower; for checking the padding)')
  args = ap.parse_args()

  span_lens = [int(x) for x in args.span_lens.split(',')]
  out_dir = os.path.join(args.out_dir, args.name)
  os.makedirs(out_dir, exist_ok=True)

  print(f'Loading model from {args.checkpoint} ...')
  model_config, region_map, alphabet, params, forward = load_checkpoint(
      args.checkpoint)
  restore_forward = forward if args.no_pad else PaddedForward(forward)
  model = (forward, params, alphabet, model_config['vocab_char_size'],
           restore_forward)
  region_names = region_map['names']
  print(f'Loading LED dataset and retrieval embeddings ...')
  dataset = inference.load_dataset(args.dataset)
  retrieval = inference.load_retrieval(args.retrieval)

  faliscan = json.load(open(args.input))
  eligible = [r for r in faliscan if MIN_LEN <= len(r['text']) <= MAX_LEN]
  if args.limit:
    eligible = eligible[:args.limit]
  print(f'{len(eligible)} / {len(faliscan)} Faliscan records have '
        f'{MIN_LEN}-{MAX_LEN} characters')

  # ---- Faliscan ----
  rng = random.Random(args.seed)
  records, t0 = [], time.time()
  for r in tqdm(eligible, desc='faliscan'):
    text = r['text']
    attr = attribution(text, model, region_names)
    lo, hi = r['date_min'], r['date_max']
    records.append({
        'record_number': r['record_number'],
        'language_group': r['faliscan']['language_group'],
        'text': text,
        'n_text_variants': len(r['faliscan']['text_variants']),
        'gold_date_min': lo,
        'gold_date_max': hi,
        **attr,
        'date_distance': date_distance(attr['mean_date'], lo, hi),
        'restoration': restoration_trials(
            text, model, span_lens, args.n_trials, rng, args.beam_width),
        'parallels': parallels(
            text, model, dataset, retrieval, region_map, args.top_k),
    })
  print(f'Faliscan: {time.time() - t0:.0f}s for {len(records)} records')

  # ---- Latin control (restoration only) ----
  control = []
  if not args.no_latin_control:
    rng = random.Random(args.seed)
    for led_id, text in tqdm(
        latin_control_texts(dataset, [len(r['text']) for r in records],
                            args.seed),
        desc='latin control'):
      control.append({
          'id': led_id,
          'text': text,
          'restoration': restoration_trials(
              text, model, span_lens, args.n_trials, rng, args.beam_width),
      })

  # ---- Summary ----
  dated = [r for r in records if r['date_distance'] is not None]
  summary = {
      'condition': args.name,
      'input': args.input,
      'n_records': len(records),
      'span_lens': span_lens,
      'n_trials_per_span': args.n_trials,
      'beam_width': args.beam_width,
      'restoration_faliscan': summarize_restoration(records),
      'restoration_latin_control': (summarize_restoration(control)
                                    if control else None),
      'dating': {
          'n_with_gold_range': len(dated),
          'mean_distance_years': (float(np.mean([r['date_distance'] for r in dated]))
                                  if dated else None),
          'median_distance_years': (float(np.median([r['date_distance'] for r in dated]))
                                    if dated else None),
          'inside_gold_range': sum(r['date_distance'] == 0 for r in dated),
      },
      'region': {
          'top1_counts': _counts(r['region_top5'][0]['region'] for r in records),
          'etruria_top1': sum(r['etruria_rank'] == 1 for r in records),
          'etruria_top3': sum(r['etruria_rank'] <= 3 for r in records),
          'mean_prob': {
              reg: float(np.mean([r['region_of_interest'][reg] for r in records]))
              for reg in REGIONS_OF_INTEREST
          },
      },
      'parallels': {
          'region_counts': _counts(p['region'] for r in records
                                   for p in r['parallels']),
      },
  }

  with open(os.path.join(out_dir, 'results.json'), 'w', encoding='utf-8') as f:
    json.dump({'faliscan': records, 'latin_control': control}, f,
              ensure_ascii=False, indent=1)
  with open(os.path.join(out_dir, 'summary.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
  print(json.dumps(summary, indent=2, ensure_ascii=False))
  print(f'\nSaved to {out_dir}/')


def _counts(items):
  c = {}
  for x in items:
    c[x] = c.get(x, 0) + 1
  return dict(sorted(c.items(), key=lambda kv: -kv[1]))


if __name__ == '__main__':
  main()
