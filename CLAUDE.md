# Working on this analysis archive

- Public replication archive for *Restoring the Balance* (Volume 3). It holds analysis code, output tables and figures only. Never commit raw datasets (WVS, EVS, V-Dem, ERT) or processed data files; point `RTB_DATA_ROOT` at a local folder with `raw/` and `processed/`.
- Never commit manuscript prose. The book text lives in the private repo DrDMo/restoring-the-balance, whose `outline/prospectus.md` defines the hypotheses (R1-R7) and the rebalancing rule.
- Use the series datasets only. Volume 1's country-wave AGP scores are reused, not re-estimated. `src/restoring_the_balance/erosion_v2.py` is Volume 2's rule, vendored unchanged; do not edit it.
- One numbered script per analysis step (`scripts/NN_*.py`), writing to `results/tables/` and `figures/`. Fix hypotheses and definitions before estimating, and report results that fail as plainly as those that hold.
- No figure or table may reproduce one from Volume 1 or Volume 2.
