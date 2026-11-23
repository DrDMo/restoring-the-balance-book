"""Robustness grid for RB2, RB3, RB5a, RB6 across restoration rules, samples, and estimators. -> results/robustness.md"""
import numpy as np, pandas as pd, statsmodels.api as sm
from statsmodels.duration.hazard_regression import PHReg
from pathlib import Path
import episodes as EP

ROOT = Path(__file__).resolve().parents[1]
TERMS = {"RB2 dAGP": "dagp", "RB3 turnover": "turnover", "RB5a jucon": "jucon_end", "RB5b party": "party_end",
         "RB6 demmob": "demmob_l1"}


def fit(d, x, base=("log_gdp", "depth", "breakdown")):
    cols = [x, *base]
    d = d.dropna(subset=cols + ["event"]).copy()
    if d.event.sum() < 3:
        return None
    if x == "dagp":
        d[x] = d[x] / d[x].std()
    d["log_t"] = np.log(d.t_since)
    X = sm.add_constant(d[cols + ["log_t"]].astype(float))
    try:
        m = sm.Logit(d.event, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": pd.factorize(d.country)[0]})
    except Exception:
        return None
    ci = m.conf_int().loc[x]
    return f"{m.params[x]:.2f} [{ci[0]:.2f}, {ci[1]:.2f}] ({int(d.event.sum())}/{len(d)})"


def row(label, d, base=("log_gdp", "depth", "breakdown")):
    return [label] + [fit(d, x, base) or "n/a" for x in TERMS.values()]


def main():
    rows = []
    r = pd.read_csv(ROOT / "results/riskset.csv")
    rows.append(row("Primary", r))
    for rule in ["rest_tol02", "rest_tol10", "rest_nocred", "rest_half", "uturn"]:
        EP.build(risk_on=rule, suffix="_" + rule)
        rows.append(row(f"Rule: {rule}", pd.read_csv(ROOT / f"results/riskset_{rule}.csv")))
    rows.append(row("Episodes ending 1990+", r[r.end_year >= 1990]))
    rows.append(row("Episodes ending 1945+", r[r.end_year >= 1945]))
    rows.append(row("No GDP control", r, base=("depth", "breakdown")))
    rf = r.sort_values(["country", "year"]).copy()
    rf["log_gdp"] = rf.groupby("country").log_gdp.ffill()  # shortcut: GDP ends 2019 in V-Dem v14; carried forward
    rows.append(row("GDP carried forward", rf))
    rows.append(row("Breakdown episodes only", r[r.breakdown == 1], base=("log_gdp", "depth")))
    rows.append(row("Non-breakdown only", r[r.breakdown == 0], base=("log_gdp", "depth")))
    hdr = "| Specification | " + " | ".join(TERMS) + " |\n|---|" + "---|" * len(TERMS)
    out = ["# Robustness grid (logit, country-clustered; coef [95% CI] (events/N))", "", hdr]
    out += ["| " + " | ".join(x) + " |" for x in rows]

    # Cox, counting-process form: one row per at-risk year (entry t-1, exit t), time-varying covariates valid
    out.append("\n## Cox proportional hazards, counting-process form (time = years since end; Breslow ties; model-based SE)")
    for name, x in TERMS.items():
        d = r.dropna(subset=[x, "log_gdp", "depth", "breakdown"]).copy()
        if x == "dagp":
            d[x] = d[x] / d[x].std()
        try:
            m = PHReg(d.t_since.astype(float), d[[x, "log_gdp", "depth", "breakdown"]].astype(float), status=d.event,
                      entry=(d.t_since - 1).astype(float)).fit()  # model-based SE: clustered PHReg with entry times is unstable
            ci = m.conf_int()[0]
            out.append(f"- {name}: coef {m.params[0]:.2f} [{ci[0]:.2f}, {ci[1]:.2f}], p = {m.pvalues[0]:.3f}, country-years {len(d)}, events {int(d.event.sum())}")
        except Exception as ex:
            out.append(f"- {name}: not estimable ({ex.__class__.__name__})")

    # RB7 windows
    e = pd.read_csv(ROOT / "results/episodes.csv")
    p = pd.read_parquet(ROOT / "data/processed/panel.parquet")
    out.append("\n## RB7 relapse windows")
    rs = e[e.restoration.notna()]
    for w in (5, 10, 15):
        rel, obs_h, obs_n = [], [], []
        for _, x in rs.iterrows():
            g = p[(p.country_text_id == x.country) & (p.year > x.restoration) & (p.aut_ep == 1)]
            first = g.aut_ep_start_year.min() if len(g) else None
            rl = first is not None and first - x.restoration <= w
            if rl or x.restoration + w <= 2023:
                rel.append((x.horiz_restored_at_rest, rl))
        d = pd.DataFrame(rel, columns=["h", "rel"])
        t = d.groupby("h").rel.agg(["sum", "size"])
        out.append(f"- {w}-year window: n={len(d)}; relapse with horizontal restored {t.loc[True,'sum']}/{t.loc[True,'size']}, "
                   f"without {t.loc[False,'sum']}/{t.loc[False,'size']}")
    (ROOT / "results/robustness.md").write_text("\n".join(out), encoding="utf8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
