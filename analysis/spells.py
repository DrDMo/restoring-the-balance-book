"""Quiet-erosion spells, reimplemented from Quiet Erosions Ch. 4 (primary rule), plus recovery status.

Rule (latent scale): population v2x_regime>=2 & aut_ep==0 at t; A(t+k) <= A(t)-delta; A(t+k) < codelow(t);
A(s) <= A(t)-delta/2 for s in t+k+1..t+k+m; no aut_ep in t..t+k and EDI drop over window < 0.10.
delta=0.15, k=4, m=2, onset >= 1995. Consecutive onset years on one index merge into one spell.
Recovery: index returns above A(t)-delta/2 after the persistence period.
"""
import pandas as pd, numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path("C:/Users/darin/Documents/Claude/Projects/Strongmen Book/Data")
INDICES = {"vertical": "v2x_veracc", "horizontal": "v2x_horacc", "diagonal": "v2x_diagacc"}
LAST = 2023


def panel():
    v = pd.read_parquet(ROOT / "data/processed/vdem_subset.parquet")
    e = pd.read_csv(DATA / "raw/vdem_ert/ert.csv", usecols=lambda c: c != "Unnamed: 0", low_memory=False)
    e = e[["country_text_id", "year", "aut_ep", "aut_ep_id", "dem_ep", "dem_ep_id", "reg_type",
           "aut_ep_start_year", "aut_ep_end_year", "aut_pre_ep_year", "aut_ep_outcome", "aut_ep_censored",
           "aut_ep_subreg", "aut_ep_termination", "dem_ep_start_year", "dem_ep_end_year", "dem_ep_outcome"]]
    return v.merge(e, on=["country_text_id", "year"], how="left").sort_values(["country_text_id", "year"])


def spells(p, delta=0.15, k=4, m=2, start=1995, credibility=True, scale=""):
    out = []
    for c, g in p.groupby("country_text_id"):
        g = g.set_index("year")
        for path, base in INDICES.items():
            col = base + scale
            A, lo = g[col], g[base + "_codelow"]
            onsets = []
            for t in g.index:
                if t < start or t + k > LAST:
                    continue
                r = g.loc[t]
                if not (r.v2x_regime >= 2 and r.aut_ep == 0) or pd.isna(A.get(t)) or pd.isna(A.get(t + k)):
                    continue
                if A[t + k] > A[t] - delta:
                    continue
                if credibility and not scale and not A[t + k] < lo[t]:
                    continue
                win = g.loc[t:t + k]
                if (win.aut_ep == 1).any() or (g.v2x_polyarchy[t] - g.v2x_polyarchy[t + k] >= 0.10):
                    continue
                post = [s for s in range(t + k + 1, t + k + m + 1) if s <= LAST]
                if any(A[s] > A[t] - delta / 2 for s in post):
                    continue
                onsets.append(t)
            # merge onsets whose windows overlap (gap <= k); reproduces Vol. 2 Table 4.1 (16/20/29)
            for i, t in enumerate(onsets):
                if i and t - onsets[i - 1] <= k:
                    continue
                base_val = A[t]
                prov = t + k + m > LAST
                rec = None
                for s in range(t + k + m + 1, LAST + 1):
                    if A.get(s, np.nan) > base_val - delta / 2:
                        rec = s
                        break
                seg = A.loc[t:(rec or LAST)]
                out.append(dict(country=c, pathway=path, onset=t, provisional=prov, recovered=rec is not None,
                                recovery_year=rec, depth=base_val - seg.min(), start_value=base_val,
                                duration=(rec or LAST) - t))
    return pd.DataFrame(out)


if __name__ == "__main__":
    p = panel()
    p.to_parquet(ROOT / "data/processed/panel.parquet")
    s = spells(p)
    s.to_csv(ROOT / "results/qe_spells.csv", index=False)
    np_ = s[~s.provisional]
    print("spells", len(s), "non-provisional", len(np_), "recovered", int(np_.recovered.sum()))
    print(s.groupby("pathway").size())
