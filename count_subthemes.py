#!/usr/bin/env python3
"""
src/count_subthemes.py

Keyword-based screening and counting of papers by Quito implementation themes/sub-themes.

USAGE
-----
python -m src.count_subthemes --input /path/to/SDG_4724_Unique_Corpus.xlsx --schema config/schema.yaml --outdir out

WHAT IT SEARCHES
----------------
By default, the script concatenates these columns (if present):
- Article Title
- Abstract
- Author Keywords
- Keywords Plus

MATCH RULE
----------
A paper is counted for a sub-theme if ANY keyword/phrase in that sub-theme's list appears
in the concatenated text fields (case-insensitive OR match). Keywords are treated literally
(escaped) to prevent unintended regex behavior. Multiple sub-theme matches per paper are allowed.

OUTPUTS
-------
- out/subtheme_counts.csv
- out/subtheme_hits_long.csv       (one row per (paper, subtheme) match)
- out/paper_level_flags_wide.csv   (paper_id + boolean flags for all subthemes)
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import yaml


DEFAULT_TEXT_COLS = ["Article Title", "Abstract", "Author Keywords", "Keywords Plus"]


def load_schema(schema_path: Path) -> dict:
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_text(df: pd.DataFrame, cols: List[str]) -> pd.Series:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Input file is missing expected columns: {missing}. Found columns: {list(df.columns)}"
        )
    return df[cols].astype(str).agg(" ".join, axis=1)


def compile_pattern(keywords: List[str]) -> re.Pattern:
    # OR-match any keyword/phrase, case-insensitive; escape to treat keywords literally.
    return re.compile("|".join(re.escape(k) for k in keywords), re.IGNORECASE)


def subtheme_matches(text: pd.Series, keywords: List[str]) -> pd.Series:
    pat = compile_pattern(keywords)
    return text.apply(lambda x: bool(pat.search(x)))


def infer_paper_id_column(df: pd.DataFrame) -> str:
    """Pick a stable identifier if present; otherwise create 'paper_id' from row index."""
    for candidate in ["UT (Unique WOS ID)", "UT", "Accession Number", "DOI"]:
        if candidate in df.columns:
            return candidate
    df["paper_id"] = df.index.astype(str)
    return "paper_id"


def run_counts(df: pd.DataFrame, schema: dict, text_cols: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Returns:
      counts_df: Subtheme-level counts
      hits_long_df: paper-level long table of matches
      flags_wide_df: paper-level wide boolean flags per subtheme
    """
    df = df.copy()
    paper_id_col = infer_paper_id_column(df)
    text = build_text(df, text_cols)

    flags = {}
    count_rows = []
    long_rows = []

    for theme in schema["themes"]:
        theme_id = theme["theme_id"]
        theme_name = theme["theme_name"]
        for st in theme["subthemes"]:
            st_id = st["subtheme_id"]
            st_name = st["subtheme_name"]
            keywords = st["keywords"]

            m = subtheme_matches(text, keywords)
            col_name = f"{st_id}__{st_name}"
            flags[col_name] = m

            count_rows.append(
                dict(
                    theme_id=theme_id,
                    theme_name=theme_name,
                    subtheme_id=st_id,
                    subtheme_name=st_name,
                    paper_count=int(m.sum()),
                    keywords_count=len(keywords),
                )
            )

            for pid in df.loc[m, paper_id_col].tolist():
                long_rows.append(
                    dict(
                        paper_id=pid,
                        theme_id=theme_id,
                        theme_name=theme_name,
                        subtheme_id=st_id,
                        subtheme_name=st_name,
                    )
                )

    counts_df = pd.DataFrame(count_rows).sort_values(["theme_id", "subtheme_id"]).reset_index(drop=True)
    hits_long_df = pd.DataFrame(long_rows)
    flags_wide_df = pd.concat(
        [df[[paper_id_col]].rename(columns={paper_id_col: "paper_id"}), pd.DataFrame(flags)],
        axis=1,
    )

    return counts_df, hits_long_df, flags_wide_df


def main() -> None:
    ap = argparse.ArgumentParser(description="Count papers by Quito implementation sub-themes using keyword matching.")
    ap.add_argument("--input", required=True, help="Path to input Excel (.xlsx) exported from WoS.")
    ap.add_argument("--schema", required=True, help="Path to schema YAML defining themes/subthemes/keywords.")
    ap.add_argument("--outdir", default="out", help="Output directory (default: out).")
    ap.add_argument(
        "--text-cols",
        default=",".join(DEFAULT_TEXT_COLS),
        help="Comma-separated text columns to search. Default matches the schema meta.match_fields.",
    )
    args = ap.parse_args()

    in_path = Path(args.input)
    schema_path = Path(args.schema)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(in_path)
    schema = load_schema(schema_path)
    text_cols = [c.strip() for c in args.text_cols.split(",") if c.strip()]

    counts_df, hits_long_df, flags_wide_df = run_counts(df, schema, text_cols)

    counts_df.to_csv(outdir / "subtheme_counts.csv", index=False)
    hits_long_df.to_csv(outdir / "subtheme_hits_long.csv", index=False)
    flags_wide_df.to_csv(outdir / "paper_level_flags_wide.csv", index=False)

    print("Wrote:")
    print(" -", outdir / "subtheme_counts.csv")
    print(" -", outdir / "subtheme_hits_long.csv")
    print(" -", outdir / "paper_level_flags_wide.csv")


if __name__ == "__main__":
    main()
