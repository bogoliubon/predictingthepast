"""Activations of the Aeneas model on Latin -> Faliscan minimal pairs.

For every rule in faliscan_rules.RULES, Latin LED test-split texts get one
site rewritten. Each pair is run through the unchanged model in 24 versions:

  0      latin     the LED text
  1      faliscan  the rule site rewritten (e.g. quintus -> cuintus)
  2..23  alts      the same site rewritten to each of the 22 other letters
                   (every letter except the rule's and the original's)

The average over the 22 alternatives is the "average random swap" at that
site, computed exactly instead of sampled. The fixed pseudo-rule (q -> d,
...) and the single frequency-weighted random draw of the first run are two
of the 22; meta.json records which.

The residual stream is captured after the character embedding (and its
layer norm), after each encoder block (16 in the released checkpoint), and
after the final layer norm. Saved per pair, per version and per layer:

  site   mean over the rewritten span's positions (Latin: the original span)
  sos    the start-of-sequence position (what date and region read from)
  ctx    relative change ||h_v - h_latin|| / ||h_latin|| at aligned
         characters 1..K before and 1..K after the span (NaN off the text),
         for versions 1..23

Also saved: start-of-sequence and mean-over-text activations for the real
Faliscan test set (faliscan_eval_set.json) and a length-matched Latin
control, so the rule directions can be checked against real Faliscan.

Usage (from colabs/):
    python rule_contrast.py --name v2            # 400 pairs per rule
    python rule_contrast.py --n_per_rule 4 --name smoke
"""

import argparse
import json
import os
import time

import jax
import jax.numpy as jnp
import numpy as np

from predictingthepast.eval import inference
from predictingthepast.models.model import Model
from predictingthepast.util import text as util_text
from faliscan_rules import RULES, align, build_pairs, letter_freqs, rewrite
from run_faliscan_baseline import latin_control_texts
from run_swap_inference import load_checkpoint

LETTERS = set('abcdefghiklmnopqrstuvxyz')
N_ALTS = 22
N_VERSIONS = 2 + N_ALTS


def layer_names(n):
  """(our labels, Flax module names) for an n-layer model."""
  return ((['emb'] + [f'block{i}' for i in range(n)] + ['final']),
          (['text_char_emb_norm'] + [f'encoderblock_{i}' for i in range(n)]
           + [f'encoder_norm_{n - 1}']))


def clean(t):
  t = ''.join(c for c in t.lower() if c in LETTERS or c in ' -_.')
  return ' '.join(t.split())


def make_forward(model, modules):
  def capture(mdl, method_name):
    return method_name == '__call__' and mdl.name in modules

  @jax.jit
  def fwd(params, text_char):
    _, state = model.apply(params, text_char=text_char,
                           capture_intermediates=capture,
                           mutable=['intermediates'])
    inter = state['intermediates']
    return jnp.stack([inter[m]['__call__'][0] for m in modules], 1)
  return fwd  # [batch, layer, length, dim]


def encode(texts, alphabet, len_step=64):
  """SOS + text, padded to a multiple of len_step."""
  n = max(len(t) for t in texts) + 1
  lp = min(-(-n // len_step) * len_step, inference.TEXT_LEN)
  rows = [util_text.text_to_idx(alphabet.sos + t + alphabet.pad * (lp - len(t) - 1),
                                alphabet) for t in texts]
  return np.stack(rows)


def run(fwd, params, alphabet, texts, batch):
  for i in range(0, len(texts), batch):
    chunk = texts[i:i + batch]
    yield i, np.asarray(fwd(params, encode(chunk, alphabet)), np.float32)


def versions(pair):
  """The 24 texts of a pair: latin, faliscan, then one per alternative."""
  s, e = pair['start'], pair['end']
  assert len(pair['alts']) == N_ALTS and pair['out_len'] == 1
  return ([pair['latin'], pair['faliscan']]
          + [rewrite(pair['latin'], s, e, c) for c in pair['alts']])


def pair_features(acts, pair, k_ctx):
  """acts: [24 versions, layer, length, dim] for one pair."""
  s, e, ol = pair['start'], pair['end'], pair['out_len']
  n = len(pair['latin'])
  amap = align(n, s, e, ol)
  V = acts.shape[0]
  lat_span, new_span = list(range(s + 1, e + 1)), list(range(s + 1, s + 1 + ol))
  site = np.concatenate([acts[:1, :, lat_span].mean(2),      # +1 = SOS
                         acts[1:, :, new_span].mean(2)])
  sos = acts[:, :, 0]
  # aligned context: Latin positions s-1..s-k (before) and e..e+k-1 (after)
  lat_pos = [s - j for j in range(1, k_ctx + 1)] + [e + j for j in range(k_ctx)]
  ctx = np.full((V - 1, acts.shape[1], 2 * k_ctx), np.nan, np.float32)
  for c, i in enumerate(lat_pos):
    if 0 <= i < n:
      ref = acts[0][:, i + 1]
      d = acts[1:, :, amap[i] + 1] - ref
      ctx[:, :, c] = np.linalg.norm(d, axis=-1) / np.linalg.norm(ref, axis=-1)
  return site, sos, ctx


def main():
  ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  ap.add_argument('--name', default='v2')
  ap.add_argument('--out_dir', default='rule_contrast')
  ap.add_argument('--checkpoint', default='checkpoint.pkl')
  ap.add_argument('--dataset', default='dataset.json')
  ap.add_argument('--eval_set', default='../faliscan_eval_set.json')
  ap.add_argument('--n_per_rule', type=int, default=400)
  ap.add_argument('--max_len', type=int, default=250,
                  help='longest Latin text used for pairs')
  ap.add_argument('--k_ctx', type=int, default=10)
  ap.add_argument('--pairs_per_batch', type=int, default=4)
  ap.add_argument('--seed', type=int, default=0)
  args = ap.parse_args()
  out_dir = os.path.join(args.out_dir, args.name)
  os.makedirs(out_dir, exist_ok=True)

  model_config, _, alphabet, params, _ = load_checkpoint(args.checkpoint)
  layers, modules = layer_names(model_config['num_layers'])
  fwd = make_forward(Model(**model_config), modules)

  dataset = json.load(open(args.dataset))
  latin = [clean(d['text']) for d in dataset if str(d['id'])[-1] in '34']
  latin = [t for t in latin if inference.MIN_TEXT_LEN <= len(t) <= args.max_len]
  pairs = build_pairs(latin, args.n_per_rule, args.seed)
  print(f'{len(latin)} Latin test-split texts; {len(pairs)} pairs '
        f'x {N_VERSIONS} versions')

  # ---- minimal pairs ----
  texts = [t for p in pairs for t in versions(p)]  # 24 consecutive per pair
  P, L, D = len(pairs), len(layers), model_config['emb_dim']
  site = np.zeros((P, N_VERSIONS, L, D), np.float16)
  sos = np.zeros_like(site)
  ctx = np.zeros((P, N_VERSIONS - 1, L, 2 * args.k_ctx), np.float32)
  batch = args.pairs_per_batch * N_VERSIONS
  t0 = time.time()
  for i, acts in run(fwd, params, alphabet, texts, batch):
    for j in range(0, len(acts), N_VERSIONS):
      p = (i + j) // N_VERSIONS
      site[p], sos[p], ctx[p] = pair_features(
          acts[j:j + N_VERSIONS], pairs[p], args.k_ctx)
    if (i // batch) % 25 == 0:
      print(f'  pairs {i // N_VERSIONS}/{P}  {time.time() - t0:.0f}s', flush=True)

  # ---- real Faliscan test set and length-matched Latin ----
  ev = json.load(open(args.eval_set))
  fal_texts = [r['text'] for r in ev['faliscan']]
  ctrl = latin_control_texts({i: d for i, d in enumerate(dataset)},
                             [len(t) for t in fal_texts], args.seed)
  lat_texts = [t for _, t in ctrl]
  real = {}
  for key, ts in [('real_faliscan', fal_texts), ('real_latin', lat_texts)]:
    s_, m_ = [], []
    for i, acts in run(fwd, params, alphabet, ts, 32):
      for j, t in enumerate(ts[i:i + 32]):
        s_.append(acts[j][:, 0])
        m_.append(acts[j][:, 1:len(t) + 1].mean(1))
    real[key + '_sos'] = np.stack(s_).astype(np.float16)
    real[key + '_mean'] = np.stack(m_).astype(np.float16)

  np.savez(os.path.join(out_dir, 'acts.npz'), site=site, sos=sos, ctx=ctx,
           **real)
  meta = {
      'layers': layers, 'k_ctx': args.k_ctx,
      'versions': 'latin, faliscan, then one per letter of the pair\'s alts',
      'letter_freqs': letter_freqs(latin),
      'rules': {r: {'pattern': v[0], 'faliscan': v[1], 'fixed_control': v[2],
                    'bakkum': v[3]} for r, v in RULES.items()},
      'pairs': pairs,
      'real_faliscan': [r['record_number'] for r in ev['faliscan']],
      'real_latin': [{'id': i, 'text': t} for i, t in ctrl],
  }
  json.dump(meta, open(os.path.join(out_dir, 'meta.json'), 'w'),
            ensure_ascii=False, indent=1)
  print(f'Done in {time.time() - t0:.0f}s; saved to {out_dir}/')


if __name__ == '__main__':
  main()
