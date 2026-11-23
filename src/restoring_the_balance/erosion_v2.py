# Quiet-erosion rule from Volume 2, vendored unchanged from DrDMo/quiet-erosions-book@9e27fb1
# (src/quiet_erosions/erosion.py). Volume 3 uses Volume 2's erosion spells as part of its
# population at risk, so the rule must be identical. Do not edit; change Volume 2 and re-vendor.
"""Operational definition of quiet erosion (Quiet Erosions, Chapter 4).

The rule is fixed in Chapter 4 before any outcome is examined against
authoritarian governance preference. Amendment 1 (22 Nov 2026, made before
any AGP linkage) moved the primary rule from the 0-1 _osp scale with
delta=0.05 and HPD non-overlap to the latent scale with delta=0.15 and the
point credibility condition, because the _osp transform compresses the
upper range where democracies sit and V-Dem's 68% intervals (median width
0.26-0.51 latent units) made HPD non-overlap exclude almost every decline.
The original rule is retained as a robustness specification. Parameters:

  delta  minimum decline over the window (primary 0.15 latent units, about
         one SD of four-year change among at-risk democracies)
  k      window length in years (primary 4)
  m      persistence years after the window (primary 2)
  cred   credibility condition: "point" (end point estimate below the start
         year's lower 68% bound, primary), "hpd" (68% intervals do not
         overlap), or "none"

A candidate onset year t qualifies on index A when:
  1. population: v2x_regime >= 2 and aut_ep == 0 in year t
  2. magnitude:  A(t+k) <= A(t) - delta
  3. credibility (see above)
  4. persistence: A(s) <= A(t) - delta/2 for s in t+k+1 .. t+k+m
  5. sub-threshold: aut_ep == 0 for every year t..t+k, and
     polyarchy(t) - polyarchy(t+k) < 0.10

Windows whose persistence years run past the last observed year are
flagged ``provisional`` and kept out of onset models.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

PATHWAYS = {
    "vertical": "v2x_veracc_osp",
    "horizontal": "v2x_horacc_osp",
    "diagonal": "v2x_diagacc_osp",
}


@dataclass(frozen=True)
class Rule:
    delta: float = 0.15
    k: int = 4
    m: int = 2
    cred: str = "point"
    edi_threshold: float = 0.10
    scale: str = "latent"  # "latent" (unbounded V-Dem scale) or "osp" (0-1)
    min_year: int = 1995  # first onset year (study period 1995-2023)


PRIMARY = Rule()
ORIGINAL = Rule(delta=0.05, cred="hpd", scale="osp")


def _var(pathway: str, rule: Rule) -> str:
    v = PATHWAYS[pathway]
    return v if rule.scale == "osp" else v.replace("_osp", "")


def _country_candidates(g: pd.DataFrame, var: str, rule: Rule, last_year: int) -> pd.DataFrame:
    g = g.set_index("year").sort_index()
    years = g.index.to_numpy()
    out = []
    for t in years:
        tk = t + rule.k
        if tk not in g.index or t < rule.min_year:
            continue
        row_t, row_k = g.loc[t], g.loc[tk]
        window = g.loc[t:tk]
        at_risk = (row_t["v2x_regime"] >= 2) and (row_t["aut_ep"] == 0)
        a0, ak = row_t[var], row_k[var]
        if not at_risk or pd.isna(a0) or pd.isna(ak):
            continue
        magnitude = ak <= a0 - rule.delta
        if rule.cred == "hpd":
            credible = row_k[f"{var}_codehigh"] < row_t[f"{var}_codelow"]
        elif rule.cred == "point":
            credible = ak < row_t[f"{var}_codelow"]
        else:
            credible = True
        no_episode = bool((window["aut_ep"].fillna(0) == 0).all()) and len(window) == rule.k + 1
        edi_drop = row_t["v2x_polyarchy"] - row_k["v2x_polyarchy"]
        sub_threshold = no_episode and (edi_drop < rule.edi_threshold)
        post = [s for s in range(tk + 1, tk + rule.m + 1)]
        provisional = post[-1] > last_year if post else False
        observed_post = [s for s in post if s in g.index]
        persistent = all(g.loc[s, var] <= a0 - rule.delta / 2 for s in observed_post)
        out.append(
            dict(
                year=t,
                a0=a0,
                ak=ak,
                decline=a0 - ak,
                magnitude=magnitude,
                credible=credible,
                persistent=persistent,
                sub_threshold=sub_threshold,
                no_episode=no_episode,
                edi_drop=edi_drop,
                provisional=provisional,
            )
        )
    return pd.DataFrame(out)


def candidates(panel: pd.DataFrame, pathway: str, rule: Rule = PRIMARY) -> pd.DataFrame:
    """Every at-risk (country, year) window with each condition evaluated."""
    var = _var(pathway, rule)
    last_year = int(panel.year.max())
    frames = []
    for cid, g in panel.groupby("country_text_id", sort=False):
        c = _country_candidates(g, var, rule, last_year)
        if len(c):
            c.insert(0, "country_text_id", cid)
            frames.append(c)
    c = pd.concat(frames, ignore_index=True)
    c["qualifies"] = c.magnitude & c.credible & c.persistent & c.sub_threshold
    c["pathway"] = pathway
    return c


def spells(cand: pd.DataFrame, panel: pd.DataFrame, rule: Rule = PRIMARY) -> pd.DataFrame:
    """Merge consecutive qualifying onset years into spells with depth and duration."""
    var = _var(cand.pathway.iloc[0], rule)
    q = cand[cand.qualifies].sort_values(["country_text_id", "year"])
    rows = []
    for cid, g in q.groupby("country_text_id"):
        yrs = g.year.to_list()
        starts = [yrs[0]] + [y for prev, y in zip(yrs, yrs[1:], strict=False) if y != prev + 1]
        series = panel[panel.country_text_id == cid].set_index("year")[var]
        last = int(series.index.max())
        prev_end = -1
        for s in starts:
            if s <= prev_end:  # still inside the previous spell: not a new onset
                continue
            a0 = series.loc[s]
            recovery = None
            for yr in range(s + rule.k + rule.m + 1, last + 1):
                if yr in series.index and series.loc[yr] > a0 - rule.delta / 2:
                    recovery = yr
                    break
            end = recovery if recovery is not None else last
            prev_end = end
            seg = series.loc[s:end]
            rows.append(
                dict(
                    country_text_id=cid,
                    pathway=cand.pathway.iloc[0],
                    onset=s,
                    a0=a0,
                    depth=float(a0 - seg.min()),
                    recovery_year=recovery,
                    duration=(end - s),
                    censored=recovery is None,
                    provisional=bool(g.loc[g.year == s, "provisional"].iloc[0]),
                )
            )
    return pd.DataFrame(rows)


def onset_panel(panel: pd.DataFrame, rule: Rule = PRIMARY) -> pd.DataFrame:
    """Country-year frame with at-risk flag and onset indicator for each pathway."""
    base = panel[["country_text_id", "year"]].copy()
    for pw in PATHWAYS:
        c = candidates(panel, pw, rule)
        sp = spells(c, panel, rule)
        risk = c[["country_text_id", "year"]].assign(**{f"risk_{pw}": 1})
        base = base.merge(risk, on=["country_text_id", "year"], how="left")
        on = sp[~sp.provisional][["country_text_id", "onset"]].rename(columns={"onset": "year"})
        base = base.merge(
            on.assign(**{f"onset_{pw}": 1}), on=["country_text_id", "year"], how="left"
        )
        base[f"risk_{pw}"] = base[f"risk_{pw}"].fillna(0).astype(int)
        base[f"onset_{pw}"] = base[f"onset_{pw}"].fillna(0).astype(int)
    return base


def summarize(cand: pd.DataFrame) -> dict:
    """Counts required by the Chapter 4 reporting standards."""
    return dict(
        pathway=cand.pathway.iloc[0],
        at_risk_windows=int(len(cand)),
        magnitude_met=int(cand.magnitude.sum()),
        failed_credibility=int((cand.magnitude & ~cand.credible).sum()),
        excluded_episode=int((cand.magnitude & cand.credible & ~cand.sub_threshold).sum()),
        failed_persistence=int(
            (cand.magnitude & cand.credible & cand.sub_threshold & ~cand.persistent).sum()
        ),
        qualifying_windows=int(cand.qualifies.sum()),
    )


__all__ = [
    "PATHWAYS",
    "Rule",
    "PRIMARY",
    "ORIGINAL",
    "candidates",
    "spells",
    "onset_panel",
    "summarize",
]
