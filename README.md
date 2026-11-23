# Restoring the Balance

Public code archive for the book **_Restoring the Balance: Authoritarian Demand and the Institutional Recovery of Democracy_** (working title) by Darin R. Molnar, Volume 3 of the Shoreline Publishing Group Comparative Politics Series.

## Purpose

This repository holds the code, analysis scripts, and output tables behind every chart and statistic in the book, so that readers, reviewers, and other researchers can inspect, re-run, extend, or critique them. The author welcomes replication, validation, and expansion of this study.

Companion archives: [demanding-strongmen-book](https://github.com/DrDMo/demanding-strongmen-book) (Volume 1) and [quiet-erosions-book](https://github.com/DrDMo/quiet-erosions-book) (Volume 2).

## Repository layout

```
.
├── Data/                          # Local data root (git-ignored; never committed)
├── scripts/                       # Numbered analysis scripts, run in order
├── results/tables/                # Output tables (CSV)
├── figures/                       # Rendered figures (PNG/PDF)
├── notebooks/                     # Exploratory notebooks
├── src/restoring_the_balance/     # Shared utilities (paths, plot style, Volume 2 erosion rule)
├── tests/                         # Pytest suite
├── pyproject.toml
├── CITATION.cff
└── LICENSE
```

## Data

The book uses the series datasets only: the WVS Integrated Trend File and Wave 7, the EVS Trend File and the EVS/WVS Joint File, the V-Dem Country-Year dataset, and the V-Dem Episodes of Regime Transformation (ERT) dataset. None is redistributed here. Download each from its publisher and place it under `$RTB_DATA_ROOT/raw` (or `Data/raw`).

## Setup

Requires Python 3.11 or newer.

```bash
git clone https://github.com/DrDMo/restoring-the-balance-book.git
cd restoring-the-balance-book
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -e ".[analysis,notebook,dev]"
pytest -q
```

## License

Code is released under the MIT License (see [LICENSE](LICENSE)). The book's prose and narrative content are not covered; all rights to the book text are reserved by the author.

## Citation

If you use code from this repository, please cite the book. A formal citation entry will be added on publication.
