"""Rebuild the Volume 1 respondent file (carried forward from Volume 2; Volume 3 adds item-level AGP and cohort variables).

Rebuilds the Demanding Strongmen respondent file from the WVS and EVS
trend files under the same rules (WVS precedence where both cover a
country-wave, the same missing-value codes, the same AGP recodes), and
adds the items Quiet Erosions needs that Volume 1 did not keep:

  confidence (E069_*; recoded 1 = none at all .. 4 = a great deal)
    02 armed forces, 04 press, 06 police, 07 parliament,
    08 civil service, 11 government, 12 political parties, 17 justice system
  essential characteristics of democracy (E224-E229, E233; 0-10)
    224 tax the rich, 225 religious authorities interpret laws,
    226 free elections, 227 unemployment aid, 228 army takes over when
    government is incompetent, 229 civil rights protect liberty,
    233 women have the same rights
  E235 importance of democracy, E236 democraticness of own country

Output: RTB_DATA_ROOT/processed/qe_individual.parquet (never committed)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from restoring_the_balance.paths import PROC_DIR, RAW_DIR

WAVE_YEAR = {1: 1982, 2: 1991, 3: 1997, 4: 2001, 5: 2007, 6: 2013, 7: 2019}
CONF = ["E069_02", "E069_04", "E069_06", "E069_07", "E069_08", "E069_11", "E069_12", "E069_17"]
ESS = ["E224", "E225", "E226", "E227", "E228", "E229", "E233"]
AGP = ["E114", "E116", "E117"]
CTRL = ["X001", "X003", "X025R", "X045", "E023", "E033"]
KEEP = AGP + CONF + ESS + ["E235", "E236"] + CTRL
MISSING = {"WVS": [-1, -2, -4, -5], "EVS": [-1, -2, -3, -4, -5]}


def _load(survey: str) -> pd.DataFrame:
    if survey == "WVS":
        f, wave = RAW_DIR / "wvs_trend" / "wvs_trend_full.parquet", "S002VS"
    else:
        f, wave = RAW_DIR / "evs_trend" / "evs_trend_full.parquet", "s002vs"
    cols = [wave, "S003", "S020", "S017", *KEEP]
    import pyarrow.parquet as pq

    have = set(pq.read_schema(f).names)
    df = pd.read_parquet(f, columns=[c for c in cols if c in have])
    for c in cols:
        if c not in df:
            df[c] = np.nan
    df = df.rename(
        columns={wave: "wave_chron", "S003": "country_num", "S020": "year", "S017": "weight"}
    )
    for c in KEEP:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df[c] = df[c].where(~df[c].isin(MISSING[survey]))
    df["survey"] = survey
    return df


def main() -> None:
    wvs, evs = _load("WVS"), _load("EVS")
    cells = set(zip(wvs.country_num, wvs.wave_chron, strict=True))
    keep = [(c, w) not in cells for c, w in zip(evs.country_num, evs.wave_chron, strict=True)]
    df = pd.concat([wvs, evs[keep]], ignore_index=True)

    # AGP exactly as Volume 1: higher = more authoritarian
    df["agp_leader"] = 5 - df.E114
    df["agp_army"] = 5 - df.E116
    df["agp_nodem"] = df.E117
    df["agp_mean"] = df[["agp_leader", "agp_army", "agp_nodem"]].mean(axis=1, skipna=False)
    for c in CONF:  # 1 = a great deal ... 4 = none at all  ->  higher = more confidence
        df[f"conf_{c[-2:]}"] = 5 - df[c]
    for c in ESS:
        df[f"ess_{c[1:]}"] = df[c]
    df["wave_year"] = df.wave_chron.map(WAVE_YEAR)
    df = df[df.wave_chron >= 3]  # AGP battery begins in wave 3
    out = df.drop(columns=AGP + CONF + ESS)

    # Attach Volume 1's individual factor scores. agp_individual holds one row
    # per valid-AGP respondent in the same within-cell order, so a stable sort
    # on (country, wave) aligns the two files; the check below guards it.
    fs = pd.read_parquet(PROC_DIR / "agp_individual.parquet")
    fs = fs.sort_values(["country_num", "wave_chron"], kind="stable").reset_index(drop=True)
    out = out.sort_values(["country_num", "wave_chron"], kind="stable").reset_index(drop=True)
    valid = out.agp_mean.notna().to_numpy()
    sub = out.loc[valid, ["country_num", "wave_chron", "agp_mean"]].reset_index(drop=True)
    assert len(sub) == len(fs)
    assert (sub.country_num.to_numpy() == fs.country_num.to_numpy()).all()
    r = np.corrcoef(sub.agp_mean, fs.fs)[0, 1]
    assert r > 0.95, f"factor scores misaligned (r = {r:.3f})"
    out["agp_fs"] = np.nan
    out.loc[valid, "agp_fs"] = fs.fs.to_numpy()
    print(f"Volume 1 factor scores attached: r(agp_mean, agp_fs) = {r:.3f}")
    out.to_parquet(PROC_DIR / "qe_individual.parquet", index=False)

    cov = out.groupby("wave_chron").agg(
        respondents=("agp_mean", "size"),
        countries=("country_num", "nunique"),
        **{
            f"{c}_valid": (c, "count")
            for c in ["agp_mean", "conf_17", "conf_07", "conf_04", "ess_226", "ess_229"]
        },
    )
    print(cov.to_string())


if __name__ == "__main__":
    main()
