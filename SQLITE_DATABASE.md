# Faliscan Corpus SQLite Database

This file documents the standalone SQLite database `faliscan.sqlite`.

The database is a research corpus of Faliscan and related inscriptions. It
contains structured inscription metadata, edited text fields, source references,
page references, and review-status information. It is designed to be opened
directly with SQLite tools, spreadsheet/data-analysis software, or programming
languages such as Python and R.

## Contents

Current database contents:

- 456 inscription records
- 456 text records
- 456 source-evidence records
- 2 source records

Current review-status distribution:

| review_status | count |
|---|---:|
| checked_against_pdf | 449 |
| parsed | 7 |

The database does not include source PDFs or images.

## Scope

The corpus currently centers on Bakkum's epigraphic material and preserves
Bakkum identifiers, sigla, page references, and source-evidence notes where
available. Bakkum is treated as a source witness, not as the final authority for
all future use of the corpus.

Several categories are included:

- Faliscan inscriptions
- Latino-Faliscan inscriptions
- Latin inscriptions relevant to the Faliscan area
- Etruscan and Capenate material included in the source corpus
- rejected, uncertain, imported, or mixed-classification records where relevant

Users should check `review_status`, uncertainty flags, and evidence notes before
using a record for linguistic, epigraphic, or statistical analysis.

## Rights And Citation

This SQLite database is intended as a research data file. It includes structured
metadata and short source-identifying snippets, but not the underlying source
PDFs or images.

Suggested source acknowledgement:

```text
Faliscan Corpus SQLite Database. Primary indexed witness: G. C. L. M. Bakkum,
The Latin Dialect of the Ager Faliscus, Part 2, 2009.
```

For formal publication, add the database release date, version, maintainer, and
any repository or DOI information supplied with the release.

Do not redistribute copyrighted source PDFs, page images, or long extracted
source passages unless rights have been clarified.

## Opening The Database

With the SQLite command-line client:

```bash
sqlite3 faliscan.sqlite
```

Useful startup commands:

```sql
.tables
.schema inscriptions
.headers on
.mode column
```

The database uses plain SQLite tables and JSON-encoded text columns for arrays
such as line divisions, page ranges, and classification candidates.

## Table Overview

The user-facing tables are:

| table | description |
|---|---|
| `sources` | registered source witnesses |
| `inscriptions` | one row per inscription or corpus record |
| `texts` | text fields linked to inscriptions |
| `source_evidence` | source-page evidence linked to inscriptions |

Table relationships:

```text
sources.source_id
  -> source_evidence.source_id

inscriptions.id
  -> texts.inscription_id
  -> source_evidence.inscription_id
```

## Table: `sources`

The `sources` table describes bibliographic or documentary witnesses.

Columns:

| column | meaning |
|---|---|
| `source_id` | stable source identifier |
| `type` | source type, such as `pdf` |
| `citation` | bibliographic citation |
| `file_path` | source locator recorded by the data maintainer |
| `page_count` | page count of the source file |
| `rights_note` | rights and redistribution note |
| `extraction_method` | how the source was indexed or extracted |
| `import_date` | date the source was registered |
| `status` | source status |

The `file_path` column is informational. It is not required for querying the
released SQLite database and may not resolve for external users.

## Table: `inscriptions`

The `inscriptions` table contains the main metadata for each corpus record.

Columns:

| column | meaning |
|---|---|
| `id` | canonical corpus identifier |
| `bakkum_number` | Bakkum lemma number or Roman numeral |
| `bakkum_siglum` | Bakkum siglum where available |
| `classification_candidates_json` | JSON array of possible sigla |
| `title` | short descriptive title |
| `period_group` | broad period or category |
| `alphabet` | alphabet classification |
| `language_group` | language/siglum grouping |
| `uncertain` | `1` if classification or record is uncertain |
| `falsum` | `1` if treated as false/falsum |
| `rejected` | `1` if rejected by the source or editor |
| `import_flag` | `1` if treated as imported/non-local |
| `provenance_raw` | source-backed provenance description |
| `place_id` | normalized place identifier where available |
| `site` | site or find location |
| `context` | find context or source context |
| `object_type` | object category |
| `object_description` | object description |
| `date_label` | human-readable date label |
| `start_bce` | start of date range, when available |
| `end_bce` | end of date range, when available |
| `review_status` | review state of the record |
| `source_path` | record locator retained for traceability |
| `notes_json` | JSON array of record-level notes |
| `updated` | last recorded update date |

Date fields are not yet normalized for statistical chronology. Some records use
different numeric conventions for BCE ranges. For chronological analysis, check
`date_label` and inspect the relevant records directly.

## Table: `texts`

The `texts` table contains inscription text fields.

Columns:

| column | meaning |
|---|---|
| `inscription_id` | joins to `inscriptions.id` |
| `diplomatic` | diplomatic or transliterated text when stored as one field |
| `normalized` | normalized text for search or downstream processing |
| `lines_json` | JSON array of line-divided text |
| `raw_candidates_json` | JSON array of draft or alternative candidate readings |
| `direction` | ductus/direction, such as `dextroverse` or `sinistroverse` |
| `notes` | text-level notes |
| `search_text` | preferred searchable text assembled from available text fields |

Do not treat `raw_candidates_json` as final text. It may contain draft readings,
alternatives, or extraction artifacts.

## Table: `source_evidence`

The `source_evidence` table links each corpus record to its source location.

Columns:

| column | meaning |
|---|---|
| `id` | numeric evidence-row identifier |
| `inscription_id` | joins to `inscriptions.id` |
| `source_id` | joins to `sources.source_id` |
| `pdf_pages_json` | JSON array containing the PDF page range |
| `printed_pages_json` | JSON array containing the printed page range |
| `chapter` | source chapter |
| `section` | source section |
| `snippet` | short source-identifying snippet |
| `notes` | evidence and review notes |

Page ranges are stored as JSON arrays. For example, `[39, 53]` indicates a range
from page 39 to page 53.

## Review Status

`review_status` describes the editorial state of a record:

| status | meaning |
|---|---|
| `raw_extracted` | machine draft; not structurally reviewed |
| `parsed` | structurally reviewed but not promoted beyond that state |
| `checked_against_pdf` | checked against the source PDF text layer or page |
| `philologically_reviewed` | reviewed for stronger downstream reuse |

In this release, most records are `checked_against_pdf`. This means the record
has been checked against the indexed source witness, but it may still require
photographic, drawing-based, or philological review. It should not automatically
be treated as a final critical edition.

Some `parsed` records are intentionally retained because they are context-only
source records, suspect witnesses, or records without a stable diplomatic
reading.

## Common Queries

Count records by review status:

```sql
select review_status, count(*) as n
from inscriptions
group by review_status
order by review_status;
```

Find a record by canonical ID:

```sql
select i.id, i.title, i.period_group, i.language_group, t.search_text
from inscriptions i
left join texts t on t.inscription_id = i.id
where i.id = 'EF 1';
```

Search inscription text:

```sql
select i.id, i.title, t.search_text
from inscriptions i
join texts t on t.inscription_id = i.id
where t.search_text like '%mercui%';
```

List records by language group:

```sql
select id, title, period_group, review_status
from inscriptions
where language_group = 'MF'
order by id;
```

List records from a site or provenance string:

```sql
select id, title, site, provenance_raw
from inscriptions
where coalesce(site, '') like '%Narce%'
   or coalesce(provenance_raw, '') like '%Narce%';
```

Join inscriptions to source pages:

```sql
select
  i.id,
  i.bakkum_siglum,
  i.bakkum_number,
  se.source_id,
  se.printed_pages_json,
  se.pdf_pages_json,
  se.notes
from inscriptions i
join source_evidence se on se.inscription_id = i.id
where i.id = 'Cap 388';
```

Find records with uncertainty or special flags:

```sql
select id, title, uncertain, falsum, rejected, import_flag, review_status
from inscriptions
where uncertain = 1
   or falsum = 1
   or rejected = 1
   or import_flag = 1
order by id;
```

Export a query result with the SQLite CLI:

```sql
.headers on
.mode csv
.once faliscan_texts.csv
select i.id, i.period_group, i.language_group, t.search_text
from inscriptions i
join texts t on t.inscription_id = i.id
where i.review_status = 'checked_against_pdf';
```

## Python Example

```python
import sqlite3

conn = sqlite3.connect("faliscan.sqlite")
conn.row_factory = sqlite3.Row

rows = conn.execute(
    """
    select i.id, i.title, i.period_group, t.search_text
    from inscriptions i
    join texts t on t.inscription_id = i.id
    where i.language_group = ?
    order by i.id
    """,
    ("MF",),
).fetchall()

for row in rows[:10]:
    print(row["id"], row["title"], row["search_text"])

conn.close()
```

## Notes For Data Users

- Prefer `search_text` for simple search.
- Use `lines_json` when line divisions matter.
- Use `normalized` only where a normalized text is actually supplied.
- Check `source_evidence.notes` before relying on uncertain or damaged readings.
- Treat `classification_candidates_json` as evidence of classification history,
  not necessarily as the final classification.
- Treat `checked_against_pdf` as a source-check state, not as a full critical
  review state.

## Known Limitations

- Bibliographic references are not normalized into a separate bibliography table
  in this SQLite release.
- Places are represented through text fields and `place_id`; there is no separate
  normalized places table in this SQLite release.
- Some special characters, damaged-letter conventions, underdots, lacunae, and
  private-use glyphs may require specialist checking.
- Date fields should be used cautiously for quantitative analysis.
- The database is designed for research access and transparent source reference,
  not as a substitute for consulting editions, photographs, drawings, or objects.
