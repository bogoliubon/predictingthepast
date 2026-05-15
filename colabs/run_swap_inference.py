"""
Run inference on original vs. swapped inscription texts for a given region
and save comparison results to swap_place/<region>/results.json.

Usage:
    python run_swap_inference.py --region "Africa Proconsularis"
    python run_swap_inference.py --region "Africa Proconsularis" --swap_dir swap_place --checkpoint checkpoint.pkl

The script loads original.json and swapped.json from swap_place/<region>/,
runs the Aeneas model on each inscription's original and swapped text, and
saves results to swap_place/<region>/results.json with a summary printed at
the end.
"""

import argparse
import json
import os
import pickle
from collections import Counter

import jax
from tqdm import tqdm

from predictingthepast.eval import inference
from predictingthepast.models.model import Model
from predictingthepast.util.alphabet import LatinAlphabet


# Latin region coordinates (from notebook) — used for location_id -> name lookup
LOCATIONS_LL = [
    {"name": "Achaia", "lat": 38.099043, "lng": 22.4314905},
    {"name": "Aegyptus", "lat": 31.2001, "lng": 29.9187},
    {"name": "Aemilia", "lat": 44.4949, "lng": 11.3426},
    {"name": "Africa Proconsularis", "lat": 32.5, "lng": 12.5},
    {"name": "Alpes Cottiae", "lat": 45.1396, "lng": 7.0703},
    {"name": "Alpes Graiae", "lat": 45.62, "lng": 6.6819},
    {"name": "Alpes Maritimae", "lat": 43.7102, "lng": 7.262},
    {"name": "Alpes Poeninae", "lat": 46.1036, "lng": 7.0731},
    {"name": "Apulia et Calabria", "lat": 40.4748, "lng": 17.2385},
    {"name": "Aquitania", "lat": 44.8378, "lng": -0.5792},
    {"name": "Arabia", "lat": 32.5, "lng": 37.5},
    {"name": "Armenia", "lat": 39.5, "lng": 40.5},
    {"name": "Asia", "lat": 37.945, "lng": 27.3417},
    {"name": "Baetica", "lat": 37.8882, "lng": -4.7794},
    {"name": "Barbaricum", "lat": 51.3127, "lng": 9.4797},
    {"name": "Belgica", "lat": 49.2583, "lng": 4.0317},
    {"name": "Bithynia et Pontus", "lat": 40.7667, "lng": 29.9167},
    {"name": "Britannia", "lat": 52.5, "lng": -2.5},
    {"name": "Bruttium et Lucania", "lat": 38.1105, "lng": 15.6501},
    {"name": "Cappadocia", "lat": 39.25, "lng": 35.75},
    {"name": "Cilicia", "lat": 36.25, "lng": 33.25},
    {"name": "Corsica", "lat": 42.0978, "lng": 9.4544},
    {"name": "Creta", "lat": 35.20052306, "lng": 25.00709816},
    {"name": "Cyprus", "lat": 34.7768, "lng": 32.4245},
    {"name": "Cyrene", "lat": 32.49965333, "lng": 20.87174333},
    {"name": "Dacia", "lat": 45.5, "lng": 22.5},
    {"name": "Dalmatia", "lat": 43.5225, "lng": 16.4739},
    {"name": "Epirus", "lat": 39.54648402, "lng": 20.78770214},
    {"name": "Etruria", "lat": 43.7696, "lng": 11.2558},
    {"name": "Galatia", "lat": 39.75, "lng": 32.75},
    {"name": "Germania inferior", "lat": 50.9375, "lng": 6.9603},
    {"name": "Germania superior", "lat": 50.0011, "lng": 8.267},
    {"name": "Hispania citerior", "lat": 41.1189, "lng": 1.245},
    {"name": "Iudaea", "lat": 32.5183, "lng": 34.9083},
    {"name": "Latium et Campania", "lat": 40.8518, "lng": 14.2681},
    {"name": "Liguria", "lat": 44.4056, "lng": 8.9463},
    {"name": "Lugdunensis", "lat": 45.757, "lng": 4.832},
    {"name": "Lusitania", "lat": 38.9159, "lng": -6.3437},
    {"name": "Lycia et Pamphylia", "lat": 36.8969, "lng": 30.7133},
    {"name": "Macedonia", "lat": 41.25, "lng": 21.75},
    {"name": "Mauretania Caesariensis", "lat": 36.52285575, "lng": 3.6414695},
    {"name": "Mauretania Tingitana", "lat": 34.0725, "lng": -5.5548},
    {"name": "Mesopotamia", "lat": 37.5, "lng": 39.5},
    {"name": "Moesia inferior", "lat": 44.1728, "lng": 28.635},
    {"name": "Moesia superior", "lat": 42.5, "lng": 22.5},
    {"name": "Narbonensis", "lat": 43.1838, "lng": 3.0045},
    {"name": "Noricum", "lat": 46.7167, "lng": 14.4167},
    {"name": "Numidia", "lat": 36.607058, "lng": 2.1918495},
    {"name": "Pannonia inferior", "lat": 47.5333, "lng": 19.05},
    {"name": "Pannonia superior", "lat": 48.0772, "lng": 16.8583},
    {"name": "Picenum", "lat": 42.8542, "lng": 13.575},
    {"name": "Raetia", "lat": 48.3705, "lng": 10.8978},
    {"name": "Regnum Bospori", "lat": 45.3564, "lng": 36.4718},
    {"name": "Roma", "lat": 41.9028, "lng": 12.4964},
    {"name": "Sabina et Samnium", "lat": 41.1385, "lng": 14.775},
    {"name": "Sardinia", "lat": 39.2238, "lng": 9.1217},
    {"name": "Sicilia, Melita", "lat": 37.0692, "lng": 15.2875},
    {"name": "Syria", "lat": 36.2021, "lng": 36.16},
    {"name": "Thracia", "lat": 41.5, "lng": 25.0},
    {"name": "Transpadana", "lat": 45.4642, "lng": 9.19},
    {"name": "Umbria", "lat": 43.1122, "lng": 12.3888},
    {"name": "Venetia et Histria", "lat": 45.7722, "lng": 13.37},
]


def load_checkpoint(path):
    """Load Aeneas checkpoint and return (model_config, region_map, alphabet, params, forward)."""
    with open(path, 'rb') as f:
        checkpoint = pickle.load(f)

    params = jax.device_put(checkpoint['params'])
    model = Model(**checkpoint['model_config'])
    forward = model.apply
    region_map = checkpoint['region_map']
    alphabet = LatinAlphabet()
    return checkpoint['model_config'], region_map, alphabet, params, forward


def run_inference_for_region(region, swap_dir, model_config, alphabet, params, forward):
    """
    Run Aeneas inference on original and swapped inscriptions for one region.

    Loads original.json and swapped.json from swap_dir/<region>/, runs the
    model on each pair, and saves results to swap_dir/<region>/results.json.

    Only inscriptions whose cleaned text is between 25 and 767 characters are
    included (the model's valid input range).

    Args:
        region:       region_sub name, e.g. "Africa Proconsularis"
        swap_dir:     path to the swap_place folder
        model_config: model config dict from load_checkpoint
        alphabet:     Alphabet instance from load_checkpoint
        params:       model params from load_checkpoint
        forward:      model forward function from load_checkpoint
    """
    region_dir = os.path.join(swap_dir, region)
    original_path = os.path.join(region_dir, 'original.json')
    swapped_path = os.path.join(region_dir, 'swapped.json')

    if not os.path.exists(original_path) or not os.path.exists(swapped_path):
        raise FileNotFoundError(f"Missing original.json or swapped.json in {region_dir}")

    original_data = json.load(open(original_path))
    swapped_data = json.load(open(swapped_path))

    # Index swapped entries by inscription id for fast lookup
    swapped_by_id = {str(e['id']): e for e in swapped_data}

    vocab_char_size = model_config['vocab_char_size']

    def clean(text):
        return ''.join(c for c in (text or '') if c in alphabet.char2idx)

    # Filter to valid text length after cleaning
    valid_entries = [
        e for e in original_data
        if 25 <= len(clean(e['text'])) <= 767
    ]
    print(f"Running inference on {len(valid_entries)} / {len(original_data)} inscriptions...")

    results = []
    for entry in tqdm(valid_entries):
        id_ = str(entry['id'])
        orig_text = clean(entry['text'])
        swap_entry = swapped_by_id.get(id_)
        if swap_entry is None:
            continue
        swap_text = clean(swap_entry['swapped_text'])

        orig_attr = inference.attribute(
            text=orig_text, forward=forward, params=params,
            alphabet=alphabet, vocab_char_size=vocab_char_size,
        )
        swap_attr = inference.attribute(
            text=swap_text, forward=forward, params=params,
            alphabet=alphabet, vocab_char_size=vocab_char_size,
        )

        orig_top = LOCATIONS_LL[orig_attr.locations[0].location_id]['name']
        swap_top = LOCATIONS_LL[swap_attr.locations[0].location_id]['name']

        results.append({
            'id': id_,
            'orig_text': orig_text,
            'swap_text': swap_text,
            'swap_original_city': swap_entry['swap_original_city'],
            'swap_original_term': swap_entry['swap_original_term'],
            'swap_replacement_city': swap_entry['swap_replacement_city'],
            'swap_replacement_region': swap_entry['swap_replacement_region'],
            'swap_replacement_term': swap_entry['swap_replacement_term'],
            'orig_prediction': orig_top,
            'orig_score': orig_attr.locations[0].score,
            'orig_top10': [{'region': LOCATIONS_LL[l.location_id]['name'], 'score': l.score}
                           for l in orig_attr.locations[:10]],
            'swap_prediction': swap_top,
            'swap_score': swap_attr.locations[0].score,
            'swap_top10': [{'region': LOCATIONS_LL[l.location_id]['name'], 'score': l.score}
                           for l in swap_attr.locations[:10]],
            'changed': orig_top != swap_top,
        })

    out_path = os.path.join(region_dir, 'results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved results to {out_path}")

    # Summary
    n = len(results)
    changed = [r for r in results if r['changed']]
    print(f"\n=== Summary: {region} ({n} inscriptions) ===")
    print(f"Prediction changed after swap: {len(changed)} / {n} ({100*len(changed)/n:.1f}%)")

    print("\n--- Original top predictions ---")
    for reg, count in Counter(r['orig_prediction'] for r in results).most_common(10):
        print(f"  {reg}: {count}")

    print("\n--- Swapped top predictions ---")
    for reg, count in Counter(r['swap_prediction'] for r in results).most_common(10):
        print(f"  {reg}: {count}")

    print("\n--- Changed predictions (sample) ---")
    for r in changed[:10]:
        print(f"  [{r['id']}] {r['orig_prediction']} ({r['orig_score']:.2f})"
              f" -> {r['swap_prediction']} ({r['swap_score']:.2f})"
              f"  [{r['swap_original_term']} -> {r['swap_replacement_term']} ({r['swap_replacement_region']})]")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run swap inference for a region.')
    parser.add_argument('--region', required=True, help='Region name, e.g. "Africa Proconsularis"')
    parser.add_argument('--swap_dir', default='swap_place', help='Path to swap_place folder')
    parser.add_argument('--checkpoint', default='checkpoint.pkl', help='Path to checkpoint.pkl')
    args = parser.parse_args()

    print(f"Loading model from {args.checkpoint}...")
    model_config, region_map, alphabet, params, forward = load_checkpoint(args.checkpoint)
    run_inference_for_region(args.region, args.swap_dir, model_config, alphabet, params, forward)
