import re
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

def create_declension_map(nominative_pairs: Dict[str, str]) -> Dict[str, str]:
    """
    Create a complete declension map from nominative forms.
    Handles common Latin declension patterns.
    
    Args:
        nominative_pairs: Dict of nominative forms, e.g., {"Dertona": "Hispalis"}
    
    Returns:
        Complete map with all case forms
    """
    
    full_map = {}
    
    for source_nom, target_nom in nominative_pairs.items():
        # Determine declension pattern based on nominative ending
        
        # First declension (-a nouns, like Dertona, Hispalis)
        if source_nom.endswith('a'):
            # Dertona → Hispalis declension
            source_stem = source_nom[:-1]  # "Derton"
            target_stem = target_nom[:-2] if target_nom.endswith('is') else target_nom[:-1]
            
            if target_nom.endswith('is'):
                # -is type (Hispalis): source 1st-decl (-a), target 3rd-decl (-is)
                # Nominative and Ablative of source are both -a (same form), so one key covers both.
                # Map it to the nominative of the target; ablative (Hispali) has no unique source key.
                full_map[source_nom] = target_nom           # Nominative/Ablative: Dertona → Hispalis
                full_map[source_stem + 'ae'] = target_stem + 'is'  # Genitive: Dertonae → Hispalis
                full_map[source_stem + 'am'] = target_stem + 'im'  # Accusative: Dertonam → Hispalim
            else:
                # Regular -a type: nom and abl are both -a, map to same target form
                full_map[source_nom] = target_nom           # Nominative/Ablative
                full_map[source_stem + 'ae'] = target_nom[:-1] + 'ae'  # Genitive
                full_map[source_stem + 'am'] = target_nom[:-1] + 'am'  # Accusative
        
        # Second declension (-us/-um nouns, like Corduba)
        elif source_nom.endswith('us') or source_nom.endswith('um'):
            source_stem = source_nom[:-2]
            target_stem = target_nom[:-2] if target_nom.endswith(('us', 'um', 'a')) else target_nom
            
            if target_nom.endswith('a'):
                # -a type (Corduba)
                full_map[source_nom] = target_nom           # Nominative: Pollentia → Corduba
                full_map[source_stem + 'i'] = target_stem + 'ae'   # Genitive: Pollenti → Cordubae
                full_map[source_stem + 'um'] = target_stem + 'am'  # Accusative: Pollentium → Cordubam
                full_map[source_stem + 'o'] = target_stem + 'a'    # Ablative: Pollentio → Corduba
                full_map[source_stem + 'us'] = target_nom          # Alt form
            else:
                # Regular -us type
                full_map[source_nom] = target_nom           # Nominative
                full_map[source_stem + 'i'] = target_stem + 'i'    # Genitive
                full_map[source_stem + 'um'] = target_stem + 'um'  # Accusative
                full_map[source_stem + 'o'] = target_stem + 'o'    # Ablative
        
        # Undeclined forms (like abbreviations)
        else:
            full_map[source_nom] = target_nom
    
    return full_map


def swap_geographic_terms(text: str, nominative_pairs: Dict[str, str]) -> str:
    """
    Swap geographic terms accounting for Latin declensions.
    
    Args:
        text: Inscription text
        nominative_pairs: Dict of place names in nominative, 
                         e.g., {"Dertona": "Hispalis", "Pollentia": "Corduba"}
    
    Returns:
        Text with swapped geographic terms in correct cases
    """
    
    # Generate full declension map
    full_swap_map = create_declension_map(nominative_pairs)
    
    # Sort by length (longest first) to avoid partial matches
    sorted_terms = sorted(full_swap_map.keys(), key=len, reverse=True)
    
    modified_text = text
    
    for source_term in sorted_terms:
        target_term = full_swap_map[source_term]
        
        # Match whole word with word boundaries
        pattern = r'\b' + re.escape(source_term) + r'\b'
        modified_text = re.sub(pattern, target_term, modified_text, flags=re.IGNORECASE)
    
    return modified_text


# Geographic swap maps: Liguria → Various Provinces
# Format: {source_nominative: target_nominative}

LIGURIA_TO_HISPANIA = {
    "Dertona": "Hispalis",      # Dertona → Hispalis (Seville)
    "Pollentia": "Corduba",     # Pollentia → Corduba (Córdoba)
    "Industria": "Tarraco",     # Industria → Tarraco (Tarragona)
    "Albingaunum": "Gades",     # Albingaunum → Gades (Cádiz)
    "Genua": "Carteia",         # Genua → Carteia
    "Dert": "Hispal",           # Abbreviated forms
    "Pollent": "Cordub",
    "Ind": "Tarracon",
}

LIGURIA_TO_BRITANNIA = {
    "Dertona": "Londinium",     # Dertona → Londinium (London)
    "Pollentia": "Eburacum",    # Pollentia → Eburacum (York)
    "Industria": "Lindum",      # Industria → Lindum (Lincoln)
    "Albingaunum": "Camulodunum",  # Albingaunum → Camulodunum (Colchester)
    "Genua": "Venta",           # Genua → Venta
    "Dert": "Londin",
    "Pollent": "Eburac",
    "Ind": "Lind",
}

LIGURIA_TO_AFRICA = {
    "Dertona": "Carthago",      # Dertona → Carthago
    "Pollentia": "Thugga",      # Pollentia → Thugga
    "Industria": "Leptis",      # Industria → Leptis Magna
    "Albingaunum": "Thapsus",   # Albingaunum → Thapsus
    "Genua": "Hadrumetum",      # Genua → Hadrumetum
    "Dert": "Carthag",
    "Pollent": "Thugg",
    "Ind": "Lept",
}


# Example usage and testing
if __name__ == "__main__":
    
    test_cases = [
        "Colonia Dertonae civibus",                    # Genitive
        "Marcus vir Dertona natus",                    # Ablative
        "Ad Dertonam profectus",                       # Accusative
        "VIvir Dert et Pollent",                       # Abbreviated
        "Ordo Dertonae decrevit",                      # Genitive
        "Municeps Pollentiae",                         # Genitive
        "Ex Pollentia oriundus",                       # Ablative
    ]
    
    print("="*70)
    print("GEOGRAPHIC SWAPPING WITH CASE HANDLING")
    print("="*70)
    print("\nLiguria → Hispania:\n")
    
    for text in test_cases:
        swapped = swap_geographic_terms(text, LIGURIA_TO_HISPANIA)
        print(f"Original:  {text}")
        print(f"Swapped:   {swapped}")
        print()
    
    print("\n" + "="*70)
    print("Apply to full dataset:")
    print("="*70)
    print("""
import json

# Load your filtered dataset
with open('filtered_liguria.json', 'r') as f:
    data = json.load(f)

# Create swapped versions for different provinces
datasets = {
    'hispania': {},
    'britannia': {},
    'africa': {}
}

for id_key, record in data.items():
    # Hispania version
    hispania_record = record.copy()
    hispania_record['text'] = swap_geographic_terms(
        record['text'], LIGURIA_TO_HISPANIA
    )
    datasets['hispania'][id_key] = hispania_record
    
    # Britannia version
    britannia_record = record.copy()
    britannia_record['text'] = swap_geographic_terms(
        record['text'], LIGURIA_TO_BRITANNIA
    )
    datasets['britannia'][id_key] = britannia_record
    
    # Africa version
    africa_record = record.copy()
    africa_record['text'] = swap_geographic_terms(
        record['text'], LIGURIA_TO_AFRICA
    )
    datasets['africa'][id_key] = africa_record

# Save swapped datasets
for province, dataset in datasets.items():
    with open(f'dataset_liguria_to_{province}.json', 'w') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"Saved: dataset_liguria_to_{province}.json")
    """)


def city_stem(name: str) -> str:
    """
    Return a short stem of a city name for fuzzy matching against inscription texts.

    Takes the first word of the name (e.g. "Iulia" from "Iulia Dertona") and
    strips the last 2 characters, keeping at least 4 characters. This catches
    most Latin declension variants (e.g. "Derton" matches "Dertonae", "Dertonam").

    Args:
        name: Canonical city name from dataset region_main field.

    Returns:
        Stem string for use in regex search.
    """
    word = name.split()[0]
    return word[:max(4, len(word) - 2)]


def analyze_placename_match_rate(dataset_path: str) -> None:
    """
    Analyze how often region_main city names appear in inscription texts,
    grouped by region_sub (province).

    For each inscription in the dataset, checks whether the city name
    (region_main) appears in the text either as an exact word-boundary match
    on the first word of the city name, or as a stem match (first word minus
    last 2 chars). This gives an estimate of how many inscriptions per province
    explicitly mention a placename and are therefore candidates for the
    placename-swapping experiment.

    Matching strategy:
        - Exact: regex word-boundary match on first word of city name (catches
          different declension endings, e.g. "Pollentia", "Pollentiae")
        - Stem: plain substring match on the stem (catches abbreviations and
          damaged text, e.g. "Derton" matches "Dert_")

    Args:
        dataset_path: Path to dataset.json (list of inscription dicts with
                      fields: id, text, region_sub, region_main).

    Prints:
        Table of region_sub | total inscriptions | matched | match% sorted
        by number of matched inscriptions descending.

    Example:
        >>> analyze_placename_match_rate('colabs/dataset.json')
        Region                                     Total  Matched  Match%
        -----------------------------------------------------------------
        Latium et Campania                          7963      448    5.6%
        ...
    """
    dataset = json.load(open(dataset_path))

    region_stats = defaultdict(lambda: {'total': 0, 'matched': 0})

    for entry in dataset:
        region_sub = entry.get('region_sub')
        city = entry.get('region_main')
        text = entry.get('text', '') or ''
        if not region_sub or not city:
            continue

        region_stats[region_sub]['total'] += 1

        first_word = city.split()[0]
        stem = city_stem(city)
        exact = bool(re.search(r'\b' + re.escape(first_word) + r'\w*\b', text, re.IGNORECASE))
        stem_match = bool(re.search(re.escape(stem), text, re.IGNORECASE))

        if exact or stem_match:
            region_stats[region_sub]['matched'] += 1

    print(f"{'Region':<40} {'Total':>7} {'Matched':>8} {'Match%':>7}")
    print('-' * 65)
    for region, s in sorted(region_stats.items(), key=lambda x: -x[1]['matched']):
        pct = 100 * s['matched'] / s['total']
        print(f"{region:<40} {s['total']:>7} {s['matched']:>8} {pct:>6.1f}%")


def extract_matched_originals(dataset_path: str, output_dir: str) -> None:
    """
    For each region_sub, find inscriptions whose text contains a city name
    (region_main) and save them to swap_place/<region>/original.json.

    Each saved entry is the original inscription dict enriched with:
        - matched_city: the canonical city name (region_main) that was found
        - match_type: "exact" if the first word matched with word boundary,
                      "stem" if only the stem matched (abbreviation/damage)
        - matched_term: the actual stem or first word used in the regex

    Args:
        dataset_path: Path to dataset.json.
        output_dir:   Path to the output folder (e.g. "swap_place"). One
                      subfolder per region_sub will be created inside it.
    """
    import os
    dataset = json.load(open(dataset_path))

    region_entries = defaultdict(list)

    for entry in dataset:
        region_sub = entry.get('region_sub')
        city = entry.get('region_main')
        text = entry.get('text', '') or ''
        if not region_sub or not city:
            continue

        first_word = city.split()[0]
        stem = city_stem(city)

        match_type = None
        matched_term = None

        if re.search(r'\b' + re.escape(first_word) + r'\w*\b', text, re.IGNORECASE):
            match_type = 'exact'
            matched_term = first_word
        elif re.search(re.escape(stem), text, re.IGNORECASE):
            match_type = 'stem'
            matched_term = stem

        if match_type:
            enriched = dict(entry)
            enriched['matched_city'] = city
            enriched['match_type'] = match_type
            enriched['matched_term'] = matched_term
            region_entries[region_sub].append(enriched)

    for region, entries in region_entries.items():
        region_dir = os.path.join(output_dir, region)
        os.makedirs(region_dir, exist_ok=True)
        out_path = os.path.join(region_dir, 'original.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        print(f"{region}: {len(entries)} entries → {out_path}")


def generate_swapped(dataset_path: str, swap_place_dir: str, seed: int = 42) -> None:
    """
    For each region's original.json, generate a swapped.json where the matched
    city term in each inscription text is replaced with a randomly chosen city
    from a different region.

    Replacement strategy:
        - The matched_term (e.g. "Uzali") is replaced with the first word of
          the replacement city name (e.g. "Dertona" → "Dertona"). Any Latin
          suffix in the original text is preserved, so "Uzalitanae" becomes
          "Dertonitanae". This is not perfect Latin but preserves the signal
          structure the model sees.
        - Replacement city is drawn uniformly at random from all cities that
          belong to a different region_sub.

    Each entry in swapped.json contains all original fields plus:
        - swap_original_city:      canonical city name that was matched
        - swap_original_term:      the term that was found/replaced in text
        - swap_replacement_city:   canonical name of the replacement city
        - swap_replacement_region: region_sub of the replacement city
        - swap_replacement_term:   the term inserted into the text (first word
                                   of replacement city name)
        - swapped_text:            inscription text after replacement

    Args:
        dataset_path:   Path to dataset.json.
        swap_place_dir: Path to the swap_place folder produced by
                        extract_matched_originals().
        seed:           Random seed for reproducibility.
    """
    import os
    import random
    random.seed(seed)

    dataset = json.load(open(dataset_path))

    # Build region_sub -> list of city names (deduplicated)
    region_cities = defaultdict(set)
    for entry in dataset:
        if entry.get('region_sub') and entry.get('region_main'):
            region_cities[entry['region_sub']].add(entry['region_main'])
    region_cities = {r: list(cities) for r, cities in region_cities.items()}
    all_regions = list(region_cities.keys())

    for region in os.listdir(swap_place_dir):
        original_path = os.path.join(swap_place_dir, region, 'original.json')
        if not os.path.exists(original_path):
            continue

        entries = json.load(open(original_path))
        other_regions = [r for r in all_regions if r != region]
        other_cities = [city for r in other_regions for city in region_cities[r]]

        swapped_entries = []
        for entry in entries:
            matched_term = entry['matched_term']
            text = entry['text'] or ''

            replacement_city = random.choice(other_cities)
            replacement_region = next(r for r, cities in region_cities.items() if replacement_city in cities)
            replacement_term = replacement_city.split()[0]

            if entry['match_type'] == 'exact':
                # Use declension-aware swap so inflected forms (e.g. Dertonae → Hispalis) are handled correctly
                swapped_text = swap_geographic_terms(text, {matched_term: replacement_term})
            else:
                # Stem match: replace the stem at a word boundary while preserving any trailing suffix
                pattern = r'(?<!\w)' + re.escape(matched_term) + r'(\w*)'
                swapped_text = re.sub(pattern, replacement_term + r'\1', text, flags=re.IGNORECASE)

            swapped_entry = dict(entry)
            swapped_entry['swap_original_city'] = entry['matched_city']
            swapped_entry['swap_original_term'] = matched_term
            swapped_entry['swap_replacement_city'] = replacement_city
            swapped_entry['swap_replacement_region'] = replacement_region
            swapped_entry['swap_replacement_term'] = replacement_term
            swapped_entry['swapped_text'] = swapped_text
            swapped_entries.append(swapped_entry)

        out_path = os.path.join(swap_place_dir, region, 'swapped.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(swapped_entries, f, indent=2, ensure_ascii=False)
        print(f"{region}: {len(swapped_entries)} entries → {out_path}")


def apply_spelling_change(text: str) -> str:
    """
    Apply classical-to-vulgar Latin spelling changes:
      - ae → e in non-final position only (preserves case endings like -ae)
      - au → o everywhere
    Case of the replacement vowel follows the first character of the digraph.
    """
    def _sub_ae(m):
        return 'E' if m.group(0)[0].isupper() else 'e'

    def _sub_au(m):
        return 'O' if m.group(0)[0].isupper() else 'o'

    text = re.sub(r'[Aa][Ee](?=[a-zA-Z])', _sub_ae, text)
    text = re.sub(r'[Aa][Uu]', _sub_au, text)
    return text


def prepare_spelling_dataset(dataset_path: str, output_base_dir: str,
                             max_samples: int = 2000, seed: int = 42) -> None:
    """
    Split dataset into three spelling-change conditions and save each to its
    own subdirectory under output_base_dir:
      - spelling_ae:   inscriptions with non-final ae only (ae→e applied)
      - spelling_au:   inscriptions with au only (au→o applied)
      - spelling_both: inscriptions with both (both changes applied)

    Each condition is randomly subsampled to max_samples entries. Each
    subdirectory gets original.json and changed.json; changed.json adds a
    changed_text field to every entry.

    Args:
        dataset_path:    Path to dataset.json.
        output_base_dir: Parent directory (e.g. 'spelling_change').
        max_samples:     Max inscriptions per condition (default 2000).
        seed:            Random seed for reproducibility.
    """
    import os
    import random
    random.seed(seed)

    dataset = json.load(open(dataset_path))

    buckets = {'ae': [], 'au': [], 'both': []}

    for entry in dataset:
        text = entry.get('text') or ''
        if not (25 <= len(text) <= 767):
            continue
        has_ae = bool(re.search(r'[Aa][Ee](?=[a-zA-Z])', text))
        has_au = bool(re.search(r'[Aa][Uu]', text))
        if has_ae and has_au:
            buckets['both'].append(entry)
        elif has_ae:
            buckets['ae'].append(entry)
        elif has_au:
            buckets['au'].append(entry)

    for condition, entries in buckets.items():
        # Oversample by 15% to absorb entries dropped by cleaned-text length
        # filtering at inference time (non-alphabet chars can shorten the text).
        n_draw = min(int(max_samples * 1.15), len(entries))
        sample = random.sample(entries, n_draw)
        out_dir = os.path.join(output_base_dir, f'spelling_{condition}')
        os.makedirs(out_dir, exist_ok=True)

        originals = sample
        changed_entries = []
        for entry in sample:
            changed_entry = dict(entry)
            changed_entry['changed_text'] = apply_spelling_change(entry['text'])
            changed_entries.append(changed_entry)

        with open(os.path.join(out_dir, 'original.json'), 'w', encoding='utf-8') as f:
            json.dump(originals, f, indent=2, ensure_ascii=False)
        with open(os.path.join(out_dir, 'changed.json'), 'w', encoding='utf-8') as f:
            json.dump(changed_entries, f, indent=2, ensure_ascii=False)

        print(f"spelling_{condition}: {len(sample)} entries → {out_dir}/")


if __name__ == "__main__":
    analyze_placename_match_rate('dataset.json')
    print()
    extract_matched_originals('dataset.json', 'swap_place')
    print()
    generate_swapped('dataset.json', 'swap_place')
