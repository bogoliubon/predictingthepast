"""Analyse the activations saved by rule_contrast.py (24 versions per pair).

Notation, for one pair at one layer and position: h_lat is the Latin text,
h_x the text with letter x written at the rule site. x is the Faliscan
letter or one of the 22 alternatives, so there are 23 replacements.

  d_x = h_x - h_lat                      the shift caused by writing x
  b   = mean of d_x over the 22 alternatives   the average random swap
  s   = d_fal - b                        the Faliscan-specific shift

For a fair comparison every alternative letter also gets a specific shift,
s_x = d_x - mean of d_y over the other 22 replacements (for the Faliscan
letter this is exactly s).

Reported per rule and layer, at the rewritten letters (site):

  absorb       median over pairs of survival(fal) / mean survival(alts),
               where survival(x) = ||d_x|| at this layer / ||d_x|| at the
               embedding. Below 1: the Faliscan letter is pulled back
               toward the Latin more than an average letter.
  dist_rank    where the Faliscan letter falls among the 23 replacements
               when letters are ordered by median ||d_x|| (1 = closest to
               the Latin), and the share of pairs in which it is among the
               three closest. No normalisation by the embedding.
  abs_rank     where the Faliscan letter falls among the 23 replacements
               when letters are ordered by median survival (1 = most
               absorbed), and the three most absorbed letters.
  generic      median cosine between d_fal and b: how much of the Faliscan
               shift points the way any replacement does.
  spec_share   median ||s|| / ||d_fal||.
  align        mean cosine of each pair's s with the mean s of the other
               pairs: how consistent the Faliscan-specific direction is.
               Given as Faliscan / median of the 22 alternatives / rank of
               Faliscan among the 23 (1 = most consistent).
  one_draw     median cosine, per pair, between s and the one-draw version
               d_fal - d_rand of the first run (how noisy one draw was);
               then the cosine between the two mean directions.
  freq         cosine between the mean s with a uniform average over the
               alternatives and with a Latin-letter-frequency average.

  lat_cons     how consistent the site itself is across pairs, before any
  fal_cons     shift is taken: mean cosine of each pair's Latin (lat_cons)
  shift_cons   or Faliscan (fal_cons) site representation, minus the average
               character representation of Latin text at that layer, with
               the mean of the other pairs. shift_cons is the same for the
               raw shift d_fal.

At the start-of-sequence position (sos): align as above, and `real`, the
cosine between the mean s and (mean real Faliscan - mean length-matched
Latin), next to the range of the same cosine for the 22 alternatives.

Usage (from colabs/):
    python analyze_rule_contrast.py rule_contrast/v2
"""

import json
import os
import sys

import numpy as np

SHOW = ['emb', 'block3', 'block7', 'block11', 'block15', 'final']


def unit(x):
  return x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-8)


def specific(d):
  """d: [pairs, 23, dim] -> s_x for every replacement x."""
  others = (d.sum(1, keepdims=True) - d) / (d.shape[1] - 1)
  return d - others


def loo_alignment(s):
  """s: [pairs, 23, dim] -> mean cosine with the other pairs' mean, per x."""
  loo = s.sum(0, keepdims=True) - s
  return np.sum(unit(s) * unit(loo), -1).mean(0)


def loo_cos(x):
  """x: [pairs, dim] -> mean cosine of each row with the others' mean."""
  return float(np.sum(unit(x) * unit(x.sum(0, keepdims=True) - x), -1).mean())


def rank_of_first(values, descending):
  order = np.argsort(-values if descending else values)
  return int(np.where(order == 0)[0][0]) + 1


def main(run_dir):
  meta = json.load(open(os.path.join(run_dir, 'meta.json')))
  z = np.load(os.path.join(run_dir, 'acts.npz'))
  layers = meta['layers']
  pairs = meta['pairs']
  rules = np.array([p['rule'] for p in pairs])
  site, sos = z['site'], z['sos']
  real = (z['real_faliscan_sos'].astype(np.float32).mean(0)
          - z['real_latin_sos'].astype(np.float32).mean(0))  # [L, D]

  # average character representation of Latin text, per layer [L, D]
  char_mean = z['real_latin_mean'].astype(np.float32).mean(0)

  report = {'layers': layers, 'rules': {}}
  for rule, info in meta['rules'].items():
    sel = np.where(rules == rule)[0]
    if not len(sel):
      continue
    alts = pairs[sel[0]]['alts']
    letters = [info['faliscan']] + list(alts)
    rand_idx = np.array([1 + alts.index(pairs[i]['rand'][pairs[i]['start']])
                         for i in sel])
    w = np.array([meta['letter_freqs'][c] for c in alts])
    w = w / w.sum()
    rep = report['rules'][rule] = {'n_pairs': len(sel), 'letters': letters,
                                   'layers': {}}

    def shifts(arr, li):
      h = arr[sel][:, :, li].astype(np.float32)  # [n, 24, D]
      return h[:, 1:] - h[:, :1]                 # [n, 23, D]

    emb_norm = np.linalg.norm(shifts(site, 0), axis=-1)  # [n, 23]
    for li, layer in enumerate(layers):
      d = shifts(site, li)
      surv = np.linalg.norm(d, axis=-1) / emb_norm
      s_all = specific(d)
      s = s_all[:, 0]
      al = loo_alignment(s_all)
      one = d[:, 0] - d[np.arange(len(sel)), rand_idx]
      s_freq = d[:, 0] - np.einsum('k,nkd->nd', w, d[:, 1:])
      med_surv = np.median(surv, 0)
      dist = np.linalg.norm(d, axis=-1)
      pair_rank = (dist < dist[:, :1]).sum(1) + 1
      order = np.argsort(med_surv)
      e = {
          'absorb': float(np.median(surv[:, 0] / surv[:, 1:].mean(1))),
          'abs_rank': rank_of_first(med_surv, descending=False),
          'dist_rank': rank_of_first(np.median(dist, 0), descending=False),
          'dist_top3': float(np.mean(pair_rank <= 3)),
          'closest': [letters[k] for k in np.argsort(np.median(dist, 0))[:3]],
          'most_absorbed': [letters[k] for k in order[:3]],
          'generic': float(np.median(np.sum(
              unit(d[:, 0]) * unit(d[:, 1:].mean(1)), -1))),
          'spec_share': float(np.median(
              np.linalg.norm(s, axis=-1) / np.linalg.norm(d[:, 0], axis=-1))),
          'align': float(al[0]),
          'align_alts_median': float(np.median(al[1:])),
          'align_rank': rank_of_first(al, descending=True),
          'one_draw_pair': float(np.median(np.sum(unit(s) * unit(one), -1))),
          'one_draw_mean': float(unit(s.mean(0)) @ unit(one.mean(0))),
          'freq': float(unit(s.mean(0)) @ unit(s_freq.mean(0))),
      }
      h = site[sel][:, :2, li].astype(np.float32) - char_mean[li]
      e.update({'lat_cons': loo_cos(h[:, 0]), 'fal_cons': loo_cos(h[:, 1]),
                'shift_cons': loo_cos(d[:, 0])})
      # start-of-sequence position
      if li > 0:
        s_sos = specific(shifts(sos, li))
        al_sos = loo_alignment(s_sos)
        cos_real = unit(s_sos.mean(0)) @ unit(real[li])  # [23]
        e.update({
            'sos_align': float(al_sos[0]),
            'sos_align_alts_median': float(np.median(al_sos[1:])),
            'sos_align_rank': rank_of_first(al_sos, descending=True),
            'sos_real': float(cos_real[0]),
            'sos_real_alts_min': float(cos_real[1:].min()),
            'sos_real_alts_max': float(cos_real[1:].max()),
        })
      rep['layers'][layer] = e

  with open(os.path.join(run_dir, 'report.json'), 'w') as f:
    json.dump(report, f, indent=1)
  print_tables(report)


def print_tables(report):
  for rule, r in report['rules'].items():
    print(f"\n## {rule}  ({r['n_pairs']} pairs; Faliscan letter "
          f"'{r['letters'][0]}')")
    print('  site consistency (lat/fal/shift): ' + '  '.join(
        f"{layer} {e['lat_cons']:.2f}/{e['fal_cons']:.2f}/{e['shift_cons']:.2f}"
        for layer in SHOW if (e := r['layers'].get(layer))))
    print('  layer     dist rank/top3/closest   absorb rank top3   generic spec_share  '
          'align fal/alts/rank   one_draw pair/mean  freq  |  '
          'sos align fal/alts/rank   real fal [alts min..max]')
    for layer in SHOW:
      e = r['layers'].get(layer)
      if e is None:
        continue
      row = (f"  {layer:8s}  {e['dist_rank']:3d} {e['dist_top3']:4.2f} "
             f"{''.join(e['closest'])}        {e['absorb']:5.2f} {e['abs_rank']:3d}  "
             f"{''.join(e['most_absorbed'])}    {e['generic']:5.2f}   "
             f"{e['spec_share']:5.2f}      {e['align']:5.2f} "
             f"{e['align_alts_median']:5.2f} {e['align_rank']:3d}      "
             f"{e['one_draw_pair']:5.2f} {e['one_draw_mean']:5.2f}    "
             f"{e['freq']:5.2f}")
      if 'sos_align' in e:
        row += (f"  |  {e['sos_align']:5.2f} {e['sos_align_alts_median']:5.2f} "
                f"{e['sos_align_rank']:3d}      {e['sos_real']:+.2f} "
                f"[{e['sos_real_alts_min']:+.2f}..{e['sos_real_alts_max']:+.2f}]")
      print(row)


if __name__ == '__main__':
  main(sys.argv[1])
