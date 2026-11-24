# Restoring the Balance: Replication Archive

Code, design document, and outputs for **_Restoring the Balance: Authoritarian Demand and the Recovery of Democratic Constraint_** (Darin R. Molnar, Shoreline Publishing Group, 2026; Volume 3 of the Shoreline Publishing Group Comparative Politics Series).

Every table, figure, and estimate in the book is produced by a script in `analysis/`. The book's table and figure notes name the script responsible. Raw data are not redistributed: obtain them from the originating archives as described below.

Companion archives: [demanding-strongmen-book](https://github.com/DrDMo/demanding-strongmen-book) (Volume 1) and [quiet-erosions-book](https://github.com/DrDMo/quiet-erosions-book) (Volume 2).

## Pre-specified design

`analysis/DESIGN.md` states the hypotheses, criteria, sample, and controls. It was committed on 23 November 2026 at 14:37 (commit `2311858`), five minutes before the first analysis that linked a restoration outcome to a covariate (commit `247e63b`, 14:42). This repository carries that history unchanged from the manuscript repository; run `git log --date=iso -- analysis/DESIGN.md analysis/models.py` to check it. The first run departed from the design's window and controls; the departure was corrected in commit `d324409` and is reported in Chapters 4 and 12 of the book.

## Repository layout

```text
.
├── analysis/      # Design document and all analysis scripts
├── results/       # Outputs: episode file, risk sets, model results, case counts, chapter numbers
├── figures/       # The book's figures
├── requirements.txt
├── CITATION.cff
└── LICENSE
```

## Data sources

Set the `RTB_DATA` environment variable to a local folder with the layout below (without it, `data/` in this repository is used; it is git-ignored).

| Path under `$RTB_DATA` | Source | Read by |
|---|---|---|
| `raw/vdem_cy/V-Dem-CY-Full+Others-v14.csv` | V-Dem Country-Year dataset v14 | `vdem_subset.py` |
| `raw/vdem_ert/ert.csv` | V-Dem Episodes of Regime Transformation (ERT) v16 | `spells.py`, `cases.py`, `chapter_numbers.py` |
| `processed/agp_country_wave.parquet` | Volume 1 country-wave AGP scores | `episodes.py` |
| `processed/country_iso3_xwalk.parquet` | Volume 1 country crosswalk | `episodes.py` |

Download locations, versions, and citations for V-Dem v14 and ERT v16 are in the Volume 1 archive's [data sources documentation](https://github.com/DrDMo/demanding-strongmen-book/blob/main/docs/data_sources.md) (save the ERT CSV as `ert.csv`). The two Volume 1 files are produced by that archive's `code/04_agp_scores.py` (AGP scores, from the WVS and EVS trend files) and `code/07_ch6_hazard_models.py` (crosswalk).

## Reproducing the analyses

Requires Python 3.11 or newer.

```bash
git clone https://github.com/DrDMo/restoring-the-balance-book.git
cd restoring-the-balance-book
pip install -r requirements.txt
```

Then run, from the repository root:

| Script | Writes | Book |
|---|---|---|
| `analysis/vdem_subset.py` | `data/processed/vdem_subset.parquet` (the V-Dem columns used) | Ch. 3 |
| `analysis/spells.py` | `data/processed/panel.parquet`, `results/qe_spells.csv` (Volume 2's spells, reproduced) | Ch. 3 |
| `analysis/episodes.py` | `results/episodes.csv`, `results/riskset.csv` | Ch. 3–4, Appendix A |
| `analysis/models.py` | `results/results.md` (pre-specified sample), `results/results_extended.md` (1914–2022 extension) | Ch. 5–11 |
| `analysis/robustness.py` | `results/robustness.md`, `results/riskset_*.csv` (alternative rules) | Ch. 11–12 |
| `analysis/figures.py` | `figures/` | Figures 5.1–12.1 |
| `analysis/cases.py` | `results/cases.md`, `results/cases_prespec.md` (case lists and counts; 2024–2025 postscript) | Ch. 7, 9, 11, 13 |
| `analysis/chapter_numbers.py` | `results/chapter_numbers.md` (every remaining number in the text, by chapter and section) | Ch. 1, 3–13, Appendix A |

Run with the data above, the scripts reproduce every file in `results/` and `figures/` byte for byte (checked 24 November 2026 with the versions in `requirements.txt`).

## License

Code is released under the MIT License (see [LICENSE](LICENSE)). The book's text and figures are not covered by this license; all rights to the book are reserved by the author. Data remain subject to the terms of their originating archives.

## Citation

Molnar, D. R. (2026). *Restoring the Balance: Authoritarian Demand and the Recovery of Democratic Constraint*. Shoreline Publishing Group. See also [CITATION.cff](CITATION.cff).
