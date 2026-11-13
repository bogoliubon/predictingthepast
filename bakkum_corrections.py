"""Corrections to faliscan.sqlite, taken from Bakkum (2009) Part 2.

Used by convert_faliscan_to_led.py. See FALISCAN_LED_CONVERSION.md §2e.

1. GROUPS: Bakkum's period/alphabet group of every inscription number, as
   listed in Part 2 §11.1.3 (pp. 365-8). His index of inscriptions (from
   p. 655) gives the same labels. About 25 database records disagree.
2. SPLITS: database records that join two inscriptions of different groups.
3. ADDED: inscriptions Bakkum edits that the database lacks, transcribed by
   hand from the PDF (page images checked). Tile numbers and interpuncts are
   kept as Bakkum prints them, as in the database's `diplomatic` field; the
   converter's normal rules then apply.
"""

import re

# Part 2 §11.1.3. Some numbers appear under two groups in Bakkum's own
# lists (232, 252, 253, 277-278, 459); for those, a database label that
# matches either is kept.
_SPEC = {
    'EF': '1-4, 6-10, 467',
    'EF/Etr': '5, 385',
    'MF': ('11-20, 22-27, 31-32, 34-36, 39-43, 45, 47-60, 62, 65, 69-75, '
           '79-110, 113-127, 132, 135-139, 141-170, 175-198, 200-201, '
           '257-260, 263, 265-266, 269-276, 367-376, 469-473'),
    'MF?': ('28-30, 33, 38, 44, 46, 68, 76, 78, 111, 128-131, 133-134, '
            '202-204, 253-255, 261-262, 281, 283-284'),
    'MF/Etr': '37, 61, 64, 66-67, 77, 199, 256, 264, 267, 279-280, 282, 287',
    'MF/LtF': '21, 252, 253, 277-278',
    'MLF': ('206-207, 210-212, 285-286, 293, 297-298, 302-324, 338-339, '
            '346-355, 358-366, 459-460, 463-464'),
    'MLF/Cap': '474-476',
    'MLF/Etr': '208-209, 289, 356-357',
    'MLF/LtF': '241, 252',
    'LF': '112, 213, 220-230, 232, 234-236, 242-249, 329-337, 378-380, 382-384',
    'LF?': '381',
    'LtF': ('63, 140, 171-174, 205, 215, 231-233, 239, 277-278, 288, 290, '
            '292, 294, 299-301, 325-328, 340-345, 377'),
    'Cap': ('386-392, 394-431, 433, 435, 437, 439-455, 457-459, 461-462, '
            '465-466'),
    'Lat': ('216-219, 237-238, 240, 250, 251, 268, 291, 295-296, 393, 432, '
            '434, 436, 438, 456, 477-478'),
    'LF/Lat': '214',
    'Sab': '468',
}

PERIOD = {
    'EF': 'Early Faliscan', 'MF': 'Middle Faliscan',
    'MLF': 'Middle or Late Faliscan', 'LF': 'Late Faliscan',
    'LtF': 'Latino-Faliscan', 'Cap': 'Capenate', 'Lat': 'Latin',
    'Etr': 'Etruscan', 'Sab': 'Sabellic',
}


def _expand(spec):
  out = []
  for part in spec.split(','):
    a, _, b = part.strip().partition('-')
    out += [str(i) for i in range(int(a), int(b or a) + 1)]
  return out


GROUPS = {}
for _label, _spec in _SPEC.items():
  for _n in _expand(_spec):
    GROUPS.setdefault(_n, []).append(_label)


def bakkum_group(number, db_label):
  """Bakkum's group for a database `bakkum_number` (e.g. '336', '367-370').

  Returns db_label when Bakkum doesn't list the number (Etruscan roman
  numerals, rejected † records) or lists it under the database's label.
  """
  m = re.fullmatch(r'(\d+)(?:-(\d+))?', (number or '').strip().rstrip('*†'))
  if not m:
    return db_label
  labels = set()
  for i in range(int(m[1]), int(m[2] or m[1]) + 1):
    options = GROUPS.get(str(i))
    if options is None:
      continue
    labels.add(db_label if db_label in options else options[0])
  if len(labels) != 1:
    return db_label  # unlisted, or a range spanning several groups
  return labels.pop()


def period_name(label):
  if not label:
    return None
  return PERIOD.get(label.split('/')[0].rstrip('?'))


# Records that join two inscriptions Bakkum keeps apart.
# {db id: [(bakkum number, diplomatic text), ...]}
SPLITS = {
    # A saucer with two owners' inscriptions: 63 dextroverse in Latin
    # letters (LtF), 64 sinistroverse in Faliscan letters (MF/Etr)
    # (Part 2, p. 437).
    'MF 63-64': [('63', 'anni'), ('64', 'ulties')],
}

# Inscriptions edited by Bakkum but missing from the database.
# Dates only where Bakkum gives one; signed years (negative = BCE).
ADDED = [
    dict(number='79', site='Civita Castellana (Ponte Terrano)',
         object_type='rock_cut_inscription', page=441,
         text='leiueliopạrtis\nuolti['),
    dict(number='135', site='Civita Castellana', object_type='tile', page=467,
         text='cincia',
         note='no edition: unpublished tile reported by Colonna; Bakkum '
              'cannot say whether cincia is the whole text'),
    dict(number='140', site='Civita Castellana', object_type='tile', page=468,
         text='cẹịṣ[i.]\nholc[osi]\nar·p[...]'),
    dict(number='144-145', site='Civita Castellana', object_type='tile',
         page=470, text='[.?]ạ*ịạ\nlepuia\nuoltilia\n[u]ọlt[---]',
         note='titulus prior (3 lines) and titulus posterior (last line)'),
    dict(number='152', site='Civita Castellana', object_type='tile', page=474,
         text='1uolti[o:]marc[2][---]\n1putellio [2]['),
    dict(number='155', site='Civita Castellana', object_type='tile', page=475,
         text='1ṭị[·]ṭịrialo[2][?---]\n1l[e]a:cs:f [2]['),
    dict(number='156-157', site='Civita Castellana', object_type='tile',
         page=476,
         text='[1][---]2ronio:uol3[t---]\n[1][---]2a*ome 3[\niu·uiụi[---]',
         note='titulus prior (2 lines) and titulus posterior (last line)'),
    dict(number='363', site='Rignano Flaminio', object_type='tile', page=556,
         text='[iu]na:upreciano'),
    dict(number='364', site='Rignano Flaminio', object_type='tile', page=556,
         text='[---]upreciano'),
    dict(number='365-366', site='Rignano Flaminio', object_type='tile',
         page=556, text='[---]are·*[---]\n[---]uịnụ[---]',
         note='titulus prior and titulus posterior'),
    dict(number='467', site=None, object_type='cup', page=577,
         date=(-600, -501), text='aịṃiosioeqo'),
    dict(number='468', site=None, object_type='cup', page=578,
         text='pa‹qu›isblaisiís'),
    dict(number='469', site=None, object_type='cup', page=579,
         text='uolti:catinei'),
    dict(number='470', site=None, object_type='vase', page=579,
         date=(-350, -301), text='oufilo:clipeaio:letei:fileo:met:facet'),
    dict(number='471', site=None, object_type='crater', page=580,
         date=(-325, -250), text='cauiosfrenaiosfaced'),
    dict(number='472', site=None, object_type='pottery_fragment', page=580,
         date=(-325, -275), text='marci:anel[i ?---]'),
    dict(number='473', site=None, object_type='plate', page=580,
         date=(-325, -275), text='cauio:peṭṛọṇẹọ'),
    dict(number='474', site=None, object_type='statuette_base', page=581,
         text='caui:tertinei:|posticnu'),
    dict(number='475', site=None, object_type='cup', page=581, text='iunai'),
    dict(number='476', site=None, object_type='vessel', page=581,
         text='setorio'),
    dict(number='477', site=None, object_type='bowl', page=582,
         date=(-225, -175), text='l·quinti'),
    dict(number='478', site=None, object_type='bowl', page=582,
         date=(-230, -150), text='[c·]popili'),
]
