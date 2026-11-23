# Analysis scripts

Run in order from the repository root, with `RTB_DATA_ROOT` pointing at a local
folder that holds the raw data in `raw/`. Raw data never enters this repository;
scripts write intermediate files to `$RTB_DATA_ROOT/processed` and results to
`results/tables/` and `figures/`.

| Script | Chapter | Does | Status |
|---|---|---|---|
| `01_build_panel.py` | all | Country-year panel from V-Dem and ERT | Carried from Volume 2; extend once the V-Dem version is settled (prospectus Part IV), and add turnover, growth and recovery-conduct variables |
| `03_build_individual.py` | 6 | Volume 1 respondent file from the WVS and EVS trend files | Carried from Volume 2; add item-level AGP and birth-cohort exposure |

Planned next (prospectus Part III): exposure windows around episode and spell ends,
and the Chapter 3 event counts that decide which hypotheses can be tested formally.

`src/restoring_the_balance/erosion_v2.py` is Volume 2's quiet-erosion rule,
vendored unchanged, because Volume 3's population at risk includes Volume 2's spells.
