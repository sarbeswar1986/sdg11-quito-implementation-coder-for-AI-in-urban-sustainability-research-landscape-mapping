# SDG 11 Quito Implementation Theme Coder (Keyword-Based)

A transparent, reproducible keyword-matching workflow to classify and count papers (e.g., a Web of Science export) by **Quito Implementation Plan / New Urban Agenda** implementation themes and sub-themes.

## Inputs

- **Excel** file exported from Web of Science (example: `SDG_4724_Unique_Corpus.xlsx`)
- `config/schema.yaml` defining themes → sub-themes → keywords

## What the script searches

By default it concatenates these fields per paper:

- Article Title
- Abstract
- Author Keywords
- Keywords Plus

## Matching rule (methods-ready)

A paper is counted for a sub-theme if **any** keyword/phrase in that sub-theme list appears in the concatenated fields (**case-insensitive OR**). Keywords are treated literally (escaped). Multiple sub-theme assignments per paper are allowed.

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python -m src.count_subthemes \
  --input SDG_4724_Unique_Corpus.xlsx \
  --schema config/schema.yaml \
  --outdir out
```

Optional: specify the text columns to search

```bash
python -m src.count_subthemes \
  --input SDG_4724_Unique_Corpus.xlsx \
  --schema config/schema.yaml \
  --outdir out \
  --text-cols "Article Title,Abstract,Author Keywords,Keywords Plus"
```

## Outputs

- `out/subtheme_counts.csv` (counts by sub-theme)
- `out/subtheme_hits_long.csv` (paper-level matches; one row per match)
- `out/paper_level_flags_wide.csv` (paper-level boolean flags per sub-theme)

## Notes

- `paper_id` is inferred using a stable identifier column if present (`UT`, `DOI`, etc.); otherwise the row index is used.
- Update keywords by editing `config/schema.yaml`.
