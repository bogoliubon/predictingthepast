"""
Run swap inference for all regions in swap_place/ and save a combined summary.

Usage:
    python run_all_swap_inference.py
    python run_all_swap_inference.py --swap_dir swap_place --checkpoint checkpoint.pkl

Iterates over every subfolder in swap_place/ that has both original.json and
swapped.json, runs inference, and saves results.json in each. At the end,
writes a combined summary to swap_place/summary.json.
"""

import argparse
import json
import os
from collections import Counter

from run_swap_inference import load_checkpoint, run_inference_for_region, LOCATIONS_LL


def run_all(swap_dir, checkpoint_path):
    """
    Run swap inference for every region folder in swap_dir.

    Loads the model once and reuses it across all regions. Skips folders that
    already have a results.json (so the script is safe to re-run after
    interruption). Writes per-region results.json files and a combined
    swap_place/summary.json at the end.

    Args:
        swap_dir:        path to the swap_place folder
        checkpoint_path: path to checkpoint.pkl
    """
    regions = sorted([
        d for d in os.listdir(swap_dir)
        if os.path.isdir(os.path.join(swap_dir, d))
        and os.path.exists(os.path.join(swap_dir, d, 'original.json'))
        and os.path.exists(os.path.join(swap_dir, d, 'swapped.json'))
    ])

    print(f"Found {len(regions)} regions to process.")
    print(f"Loading model from {checkpoint_path}...")
    model_config, region_map, alphabet, params, forward = load_checkpoint(checkpoint_path)
    print("Model loaded.\n")

    summary = []
    for region in regions:
        results_path = os.path.join(swap_dir, region, 'results.json')
        if os.path.exists(results_path):
            print(f"[SKIP] {region} — results.json already exists")
            results = json.load(open(results_path))
        else:
            print(f"\n{'='*60}")
            print(f"Processing: {region}")
            print('='*60)
            try:
                run_inference_for_region(region, swap_dir, model_config, alphabet, params, forward)
                results = json.load(open(results_path))
            except Exception as e:
                print(f"[ERROR] {region}: {e}")
                continue

        n = len(results)
        changed = sum(1 for r in results if r['changed'])
        summary.append({
            'region': region,
            'total': n,
            'changed': changed,
            'changed_pct': round(100 * changed / n, 1) if n else 0,
            'orig_top_prediction': Counter(r['orig_prediction'] for r in results).most_common(1)[0][0] if results else None,
            'swap_top_prediction': Counter(r['swap_prediction'] for r in results).most_common(1)[0][0] if results else None,
        })

    summary_path = os.path.join(swap_dir, 'summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print("OVERALL SUMMARY")
    print('='*60)
    print(f"{'Region':<40} {'N':>5} {'Changed':>8} {'%':>6}")
    print('-'*60)
    for s in sorted(summary, key=lambda x: -x['changed_pct']):
        print(f"{s['region']:<40} {s['total']:>5} {s['changed']:>8} {s['changed_pct']:>5.1f}%")
    print(f"\nSaved summary to {summary_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run swap inference for all regions.')
    parser.add_argument('--swap_dir', default='swap_place', help='Path to swap_place folder')
    parser.add_argument('--checkpoint', default='checkpoint.pkl', help='Path to checkpoint.pkl')
    args = parser.parse_args()

    run_all(args.swap_dir, args.checkpoint)
