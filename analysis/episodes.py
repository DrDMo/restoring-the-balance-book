"""Build backsliding episodes, restoration outcomes, and the at-risk country-year panel (DESIGN.md)."""
import os
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("RTB_DATA", ROOT / "data"))  # raw V-Dem/ERT and Volume 1 outputs; see README
LAST = 2023
PATHS = {"vertical": "v2x_veracc", "horizontal": "v2x_horacc", "diagonal": "v2x_diagacc"}


def agp_by_country():
    a = pd.read_parquet(DATA / "processed/agp_country_wave.parquet")
    x = pd.read_parquet(DATA / "processed/country_iso3_xwalk.parquet")
    key = [c for c in x.columns if c != "iso3"][0] if "country_num" not in x.columns else "country_num"
    a = a.merge(x[[key, "iso3"]].drop_duplicates(), left_on="country_num", right_on=key, how="left")
    return a.dropna(subset=["iso3"])[["iso3", "wave_year", "agp_score"]].sort_values(["iso3", "wave_year"])


def demand_at(agp, iso, t):
    w = agp[(agp.iso3 == iso) & (agp.wave_year <= t)]
    lvl = w.agp_score.iloc[-1] if len(w) else np.nan
    d = w.agp_score.iloc[-1] - w.agp_score.iloc[-2] if len(w) >= 2 else np.nan
    return lvl, d


def restored(g, t0, P, trough_hi, tol=0.05, cred=True, end=LAST, rule="primary", trough=None):
    for t in range(t0, end + 1):
        if t not in g.index:
            continue
        r = g.loc[t]
        thr = trough + (P - trough) / 2 if rule == "half" else P - tol
        if r.edi >= thr and r.row_ert >= 2 and (not cred or r.edi > trough_hi):
            return t
    return None


def build(risk_on="restoration", suffix=""):
    p = pd.read_parquet(ROOT / "data/processed/panel.parquet")
    agp = agp_by_country()
    eps, risk = [], []
    for c, g in p.groupby("country_text_id"):
        g = g.set_index("year")
        ids = g.loc[(g.aut_ep == 1) & (g.aut_ep_prch == 1), "aut_ep_id"].dropna().unique()
        for eid in ids:
            rows = g[(g.aut_ep_id == eid) & (g.aut_ep == 1)]
            s, E = int(rows.aut_ep_start_year.dropna().iloc[0]), int(rows.aut_ep_end_year.dropna().iloc[0])
            if s < 1900 or (s - 1) not in g.index or pd.isna(g.loc[s - 1, "edi"]):
                continue
            seg = g.loc[s:E]
            P = g.loc[s - 1, "edi"]
            ty = seg.edi.idxmin()
            trough, trough_hi = seg.edi.min(), g.loc[ty, "edi_hi"]
            outcome = rows.aut_ep_outcome.dropna().max()
            cens = bool(rows.aut_ep_censored.max() == 1) or outcome == 6 or E >= LAST  # design: censored only if ERT censors it or no follow-up year exists
            # next autocratization episode after E (ends the risk period)
            nxt = g[(g.index > E) & (g.aut_ep == 1) & (g.aut_ep_id != eid)]
            stop = int(nxt.index.min()) - 1 if len(nxt) else LAST
            rec = None if cens else restored(g, E + 1, P, trough_hi, end=stop, trough=trough)
            alt = {}
            if not cens:
                alt["rest_tol02"] = restored(g, E + 1, P, trough_hi, tol=0.02, end=stop, trough=trough)
                alt["rest_tol10"] = restored(g, E + 1, P, trough_hi, tol=0.10, end=stop, trough=trough)
                alt["rest_nocred"] = restored(g, E + 1, P, trough_hi, cred=False, end=stop, trough=trough)
                alt["rest_half"] = restored(g, E + 1, P, trough_hi, rule="half", end=stop, trough=trough)
                d = g[(g.index > E) & (g.index <= E + 5) & (g.dem_ep == 1)]
                alt["uturn"] = int(d.index.min()) if len(d) else None
            # pathways
            pw = {}
            for name, col in PATHS.items():
                Pi, mi = g.loc[s - 1, col], seg[col].min()
                lost = Pi - mi >= 0.15
                ry = None
                if lost and not cens:
                    for t in range(E + 1, stop + 1):
                        if t in g.index and g.loc[t, col] >= Pi - 0.075:
                            ry = t
                            break
                pw[f"{name}_lost"], pw[f"{name}_rest"], pw[f"{name}_pre"] = lost, ry, Pi
            # relapse: new episode within 10 years of restoration
            relapse, relapse_obs = None, None
            if rec:
                n2 = g[(g.index > rec) & (g.aut_ep == 1) & (g.aut_ep_id != eid)]
                first = int(n2.aut_ep_start_year.min()) if len(n2) else None
                relapse = first is not None and first - rec <= 10
                relapse_obs = relapse or rec + 10 <= LAST
            h_at = g.loc[rec, "v2x_horacc"] >= pw["horizontal_pre"] - 0.075 if rec else None
            lvl, dd = demand_at(agp, c, rec) if rec else (np.nan, np.nan)
            eps.append(dict(country=c, name=g.country_name.iloc[0], ep_id=eid, start=s, end=E, duration=E - s + 1,
                            pre_edi=P, trough=trough, trough_year=ty, depth=P - trough, outcome=outcome,
                            breakdown=outcome == 1, censored=cens, restoration=rec, stop=stop,
                            horiz_restored_at_rest=h_at, relapse=relapse, relapse_observed=relapse_obs,
                            agp_at_rest=lvl, jucon_end=g.v2x_jucon.get(E), party_end=g.v2xps_party.get(E),
                            **alt, **pw))
            if cens:
                continue
            rec = {"restoration": rec, **alt}[risk_on] if risk_on != "restoration" else rec
            end_t = rec if rec else stop
            gdp = np.log(g.e_gdppc)
            turn = False
            for t in range(E + 1, end_t + 1):
                if t not in g.index:
                    continue
                turn = turn or g.loc[t, "v2eltvrexo"] == 2
                lvl, dd = demand_at(agp, c, t)
                risk.append(dict(country=c, ep_id=eid, year=t, event=int(t == rec), t_since=t - E,
                                 log_gdp=gdp.get(t - 1, np.nan), depth=P - trough, breakdown=int(outcome == 1),
                                 decade=(E // 10) * 10, jucon_end=g.loc[E, "v2x_jucon"],
                                 party_end=g.loc[E, "v2xps_party"], demmob_l1=g.v2cademmob.get(t - 1, np.nan),
                                 turnover=int(turn), turnover_l1=int(any(g.v2eltvrexo.get(u, 0) == 2 for u in range(E + 1, t))),
                                 agp=lvl, dagp=dd, end_year=E))
    e, r = pd.DataFrame(eps), pd.DataFrame(risk)
    if not suffix:
        e.to_csv(ROOT / "results/episodes.csv", index=False)
    r.to_csv(ROOT / f"results/riskset{suffix}.csv", index=False)
    return e, r


if __name__ == "__main__":
    e, r = build()
    print(len(e), "episodes;", (~e.censored).sum(), "ended;", e.restoration.notna().sum(), "restored")
    print(r.shape, r.event.sum(), r.agp.notna().sum(), r.dagp.notna().sum())
