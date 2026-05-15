"""
Run inference on original vs. spelling-changed inscription texts and save
comparison results per condition.

Three conditions are run: spelling_ae (ae→e only), spelling_au (au→o only),
spelling_both (both changes). Each condition gets its own subdirectory under
spelling_dir with original.json, changed.json, and results.json.

Usage:
    python run_spelling_inference.py
    python run_spelling_inference.py --spelling_dir spelling_change --checkpoint checkpoint.pkl

If the condition subdirectories don't exist yet, prepare_spelling_dataset()
is called automatically to generate them (2000 samples per condition).
"""

import argparse
import json
import os

import numpy as np
from tqdm import tqdm

from predictingthepast.eval import inference
from run_swap_inference import LOCATIONS_LL, load_checkpoint
from utils import prepare_spelling_dataset

DATE_MIN = -800
DATE_MAX = 800
DATE_INTERVAL = 10
DATE_BINS = np.arange(DATE_MIN + DATE_INTERVAL / 2, DATE_MAX, DATE_INTERVAL)

CONDITIONS = ['spelling_ae', 'spelling_au', 'spelling_both']


def mean_date(year_scores):
    scores = np.array(year_scores)
    total = scores.sum()
    return float(np.dot(DATE_BINS, scores) / total) if total > 0 else 0.0


def run_condition(condition_dir, model_config, alphabet, params, forward):
    original_path = os.path.join(condition_dir, 'original.json')
    changed_path = os.path.join(condition_dir, 'changed.json')

    original_data = json.load(open(original_path))
    changed_data = json.load(open(changed_path))
    changed_by_id = {str(e['id']): e for e in changed_data}

    vocab_char_size = model_config['vocab_char_size']

    def clean(text):
        return ''.join(c for c in (text or '') if c in alphabet.char2idx)

    max_samples = 2000
    valid_entries = [
        e for e in original_data
        if 25 <= len(clean(e['text'])) <= 767
    ][:max_samples]

    results = []
    for entry in tqdm(valid_entries, desc=os.path.basename(condition_dir)):
        id_ = str(entry['id'])
        changed_entry = changed_by_id.get(id_)
        if changed_entry is None:
            continue

        orig_text = clean(entry['text'])
        changed_text = clean(changed_entry['changed_text'])
        if not (25 <= len(changed_text) <= 767):
            continue

        orig_attr = inference.attribute(
            text=orig_text, forward=forward, params=params,
            alphabet=alphabet, vocab_char_size=vocab_char_size,
        )
        changed_attr = inference.attribute(
            text=changed_text, forward=forward, params=params,
            alphabet=alphabet, vocab_char_size=vocab_char_size,
        )

        orig_region = LOCATIONS_LL[orig_attr.locations[0].location_id]['name']
        changed_region = LOCATIONS_LL[changed_attr.locations[0].location_id]['name']
        orig_date = mean_date(orig_attr.year_scores)
        changed_date = mean_date(changed_attr.year_scores)

        results.append({
            'id': id_,
            'orig_text': orig_text,
            'changed_text': changed_text,
            'orig_region': orig_region,
            'orig_region_score': orig_attr.locations[0].score,
            'changed_region': changed_region,
            'changed_region_score': changed_attr.locations[0].score,
            'region_changed': orig_region != changed_region,
            'orig_mean_date': orig_date,
            'changed_mean_date': changed_date,
            'date_shift': changed_date - orig_date,
            'orig_year_scores': [float(x) for x in orig_attr.year_scores],
            'changed_year_scores': [float(x) for x in changed_attr.year_scores],
        })

    out_path = os.path.join(condition_dir, 'results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    n = len(results)
    if n == 0:
        print(f"  No results.")
        return

    region_changed = sum(1 for r in results if r['region_changed'])
    date_shifts = [r['date_shift'] for r in results]
    print(f"  Inscriptions:              {n}")
    print(f"  Geographic pred changed:   {region_changed} / {n} ({100 * region_changed / n:.1f}%)")
    print(f"  Mean date shift:           {np.mean(date_shifts):+.1f} years")
    print(f"  Median date shift:         {np.median(date_shifts):+.1f} years")
    print(f"  Shifted later  (> 0):      {sum(1 for d in date_shifts if d > 0)} / {n}")
    print(f"  Shifted earlier (< 0):     {sum(1 for d in date_shifts if d < 0)} / {n}")


def run_all(spelling_dir, checkpoint_path):
    # Prepare datasets if missing
    needs_prep = any(
        not os.path.exists(os.path.join(spelling_dir, c, 'original.json'))
        for c in CONDITIONS
    )
    if needs_prep:
        print("Preparing spelling datasets (2000 samples per condition)...")
        prepare_spelling_dataset('dataset.json', spelling_dir)
        print()

    print(f"Loading model from {checkpoint_path}...")
    model_config, region_map, alphabet, params, forward = load_checkpoint(checkpoint_path)
    print("Model loaded.\n")

    for condition in CONDITIONS:
        condition_dir = os.path.join(spelling_dir, condition)
        results_path = os.path.join(condition_dir, 'results.json')

        print(f"{'='*50}")
        print(f"Condition: {condition}")
        print(f"{'='*50}")

        if os.path.exists(results_path):
            print(f"  [SKIP] results.json already exists\n")
            continue

        if not os.path.exists(condition_dir):
            print(f"  [SKIP] directory not found\n")
            continue

        run_condition(condition_dir, model_config, alphabet, params, forward)
        print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run spelling-change inference.')
    parser.add_argument('--spelling_dir', default='spelling_change',
                        help='Parent directory for spelling condition subdirs')
    parser.add_argument('--checkpoint', default='checkpoint.pkl',
                        help='Path to Aeneas checkpoint.pkl')
    args = parser.parse_args()

    run_all(args.spelling_dir, args.checkpoint)
