"""Numbers the chapters report that no other script prints. Writes results/chapter_numbers.md: one labelled line per
number, grouped by chapter, citing the chapter file and the passage it supports. Run after episodes.py and models.py.
Inputs: results/episodes.csv, results/riskset*.csv, results/qe_spells.csv, data/processed/panel.parquet,
Volume 1 AGP estimates ($RTB_DATA/processed), ERT ($RTB_DATA/raw/vdem_ert/ert.csv)."""
import os, sys
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("RTB_DATA", ROOT / "data"))
sys.path.insert(0, str(ROOT / "analysis"))
from episodes import agp_by_country  # noqa: E402
from models import km  # noqa: E402

OUT = []
PATHS = ["vertical", "horizontal", "diagonal"]


def chapter(title, f):
    OUT.append(f"\n## {title} (manuscript/{f})")


def say(where, label, value):
    OUT.append(f"- {where} | {label}: {value}")


def med(s):
    return f"{s.median():g}"


def fe(x, k=3):
    return f"{x:.{k}f}"


e = pd.read_csv(ROOT / "results/episodes.csv")
r_all = pd.read_csv(ROOT / "results/riskset.csv")
P = pd.read_parquet(ROOT / "data/processed/panel.parquet")
Pi = P.set_index(["country_text_id", "year"])
ended_all = e[~e.censored].copy()
x = ended_all[ended_all.end >= 1950].copy()          # pre-specified at-risk set
ext_pre = ended_all[ended_all.end < 1950]
r = r_all[(r_all.end_year >= 1950) & (r_all.end_year <= 2022)].copy()
for d in (x, ended_all):
    d["ev"] = d.restoration.notna().astype(int)
    d["ttr"] = np.where(d.ev == 1, d.restoration - d.end, d.stop - d.end)
rest = x[x.ev == 1]
gdp = r.dropna(subset=["log_gdp", "depth", "breakdown"])


def ep(country, start):
    return e[(e.country == country) & (e.start == start)].iloc[0]


def edi(c, y, col="edi"):
    return Pi.loc[(c, int(y)), col]


# ---------------------------------------------------------------- Chapter 1
chapter("Chapter 1", "ch01.md")
for c_, s_ in [("PER", 1990), ("CHL", 1972)]:
    k = ep(c_, s_)
    say("§1.1", f"{k['name']} {k.start}-{k.end}", f"pre-episode EDI {k.pre_edi:.3f}, trough {k.trough:.3f}, restored {k.restoration:g}")

# ---------------------------------------------------------------- Chapter 3
chapter("Chapter 3", "ch03.md")
say("Table 3.1", "countries in V-Dem extract (panel)", P.country_text_id.nunique())
ag = pd.read_parquet(DATA / "processed/agp_country_wave.parquet")
xw = pd.read_parquet(DATA / "processed/country_iso3_xwalk.parquet")
say("Table 3.1; §3.6", "AGP country-waves", len(ag))
say("Table 3.1", "AGP countries", ag.country_num.nunique())
agl = agp_by_country()
say("§3.6", "country-waves linked by crosswalk", len(agl))
say("§3.6", "countries linked", agl.iso3.nunique())
say("§3.6", "unlinked country-waves", len(ag) - len(agl))
say("§3.3", "Vol. 2 spells total / vertical / horizontal / diagonal",
    f"{len(s := pd.read_csv(ROOT / 'results/qe_spells.csv'))} / " + " / ".join(str((s.pathway == p).sum()) for p in PATHS))
pv = s[s.provisional]
say("§3.3", "provisional spells (vertical/horizontal/diagonal)",
    f"{len(pv)} ({' / '.join(str((pv.pathway == p).sum()) for p in PATHS)})")
say("§3.4", "population: episodes / countries", f"{len(e)} / {e.country.nunique()}")
say("§3.4", "pre-specified ended episodes / countries / final years",
    f"{len(x)} / {x.country.nunique()} / {x.end.min()}-{x.end.max()}")
say("§3.4", "censored or ongoing", int(e.censored.sum()))
say("§3.4", "ended before 1950: episodes / countries / ended 1939-44",
    f"{len(ext_pre)} / {ext_pre.country.nunique()} / {ext_pre.end.between(1939, 1944).sum()}")
say("§3.4", "extension ended episodes", len(ended_all))
oc = x.outcome.value_counts().to_dict()
say("§3.4", "outcomes: breakdown / averted / preempted / diminished",
    f"{oc.get(1.0, 0)} / {oc.get(4.0, 0)} / {oc.get(2.0, 0)} / {oc.get(3.0, 0)}")
say("§3.4", "median pre-episode EDI / trough / depth / duration",
    f"{x.pre_edi.median():.3f} / {x.trough.median():.3f} / {x.depth.median():.3f} / {med(x.duration)}")
say("§3.4", "ended 1959-1999 / 2000+", f"{(x.end < 2000).sum()} / {(x.end >= 2000).sum()}")
say("§3.4", "risk set: country-years / countries / events / years",
    f"{len(r)} / {r.country.nunique()} / {r.event.sum()} / {r.year.min()}-{r.year.max()}")
say("§3.4", "complete-covariate models: country-years / countries / events",
    f"{len(gdp)} / {gdp.country.nunique()} / {gdp.event.sum()}")
say("§3.4", "extended risk set: country-years / first year", f"{len(r_all)} / {r_all.year.min()}")
say("§3.5.2", "episodes with judicial constraints at end", f"{x.jucon_end.notna().sum()} of {len(x)}")
pm = x[x.party_end.isna()]
say("§3.5.2", "party missing at end / of which ended before 1990", f"{len(pm)} / {(pm.end < 1990).sum()}")
rp = r.dropna(subset=["party_end"]); rpg = rp.dropna(subset=["log_gdp"])
say("§3.5.2", "party rows: country-years / countries / events (no GDP)", f"{len(rp)} / {rp.country.nunique()} / {rp.event.sum()}")
say("§3.5.2", "party rows with GDP: country-years / countries / events", f"{len(rpg)} / {rpg.country.nunique()} / {rpg.event.sum()}")
say("§3.5.3", "rows with lagged mobilization", f"{r.demmob_l1.notna().sum()} of {len(r)}")
ng = r[r.log_gdp.isna()]
say("§3.5.4", "GDP missing: 2021-23 rows / other rows (country, years)",
    f"{(ng.year >= 2021).sum()} / {(ng.year < 2021).sum()} ({', '.join(sorted(ng[ng.year < 2021].country.unique()))}, "
    f"{ng[ng.year < 2021].year.min()}-{ng[ng.year < 2021].year.max()})")
say("§3.6", "SD of dAGP, pre-specified risk set / extended risk set", f"{r.dagp.std():.3f} / {r_all.dagp.std():.3f}")
say("§3.6", "at-risk years before 1997 / from 1997", f"{(r.year < 1997).sum()} / {(r.year >= 1997).sum()}")
r97 = r[r.year >= 1997]
say("§3.6", "from 1997: rows with AGP level / countries; rows with dAGP",
    f"{r97.agp.notna().sum()} / {r97[r97.agp.notna()].country.nunique()}; {r97.dagp.notna().sum()}")
waves = set(zip(agl.iso3, agl.wave_year))
r5 = r97[r97.t_since <= 5]
say("§3.6", "post-1997 rows within 5 years of end / with a wave in that year",
    f"{len(r5)} / {sum((c, y) in waves for c, y in zip(r5.country, r5.year))}")
dd = r[r.dagp.notna()].copy()
say("§3.6", "dAGP rows: country-years / episodes / countries / events",
    f"{len(dd)} / {dd.ep_id.nunique()} / {dd.country.nunique()} / {dd.event.sum()}")
say("§3.6", "dAGP countries", ", ".join(sorted(x.set_index("country").loc[dd.country.unique(), "name"].unique())))


def two_waves(c, t):
    w = agl[(agl.iso3 == c) & (agl.wave_year <= t)].wave_year
    return w.iloc[-1], w.iloc[-2]


dd[["w1", "w0"]] = [two_waves(c, t) for c, t in zip(dd.country, dd.year)]
say("§3.6", "dAGP rows whose newer wave is no later than episode end / both waves after end",
    f"{(dd.w1 <= dd.end_year).sum()} / {(dd.w0 > dd.end_year).sum()}")
say("§3.6", "age of newer wave: median / max", f"{med(dd.year - dd.w1)} / {(dd.year - dd.w1).max()}")
x["hi"] = [edi(c, y, "edi_hi") for c, y in zip(x.country, x.trough_year)]
x["lo"] = [edi(c, y, "edi_lo") for c, y in zip(x.country, x.trough_year)]
w = x.hi - x.lo
say("§3.9; §4.3", "trough 68% interval width: median / min / max", f"{w.median():.3f} / {w.min():.3f} / {w.max():.3f}")

# ---------------------------------------------------------------- Chapter 4
chapter("Chapter 4", "ch04.md")
gap = x.pre_edi - 0.05 - x.hi
say("§4.3.2", "threshold above trough upper bound: episodes / median margin", f"{(gap > 0).sum()} of {len(x)} / {gap[gap > 0].median():.3f} (all: {gap.median():.3f})")
say("§4.3.2", "threshold within trough interval", ", ".join(f"{a} ({b}-{c})" for a, b, c in x[gap <= 0][["name", "start", "end"]].values))
say("§4.3.1; §4.3.3", "pre-episode EDI range / episodes starting below 0.55",
    f"{x.pre_edi.min():.3f}-{x.pre_edi.max():.3f} / {(x.pre_edi < 0.55).sum()}")
nl = x[[f"{p}_lost" for p in PATHS]].sum(axis=1).value_counts()
say("§4.4", "episodes losing 3 / 2 / 1 / 0 pathways", " / ".join(str(nl.get(k, 0)) for k in (3, 2, 1, 0)))
say("§4.5", "relapse observable / restorations not observable (years)",
    f"{int(rest.relapse_observed.sum())} / {sorted(rest[rest.relapse_observed != True].restoration.astype(int))}")
bk = x.breakdown.astype(bool)
for c in ["restoration", "rest_tol02", "rest_tol10", "rest_nocred", "rest_half", "uturn"]:
    a, pr = x[c].notna(), x.restoration.notna()
    both = a & pr
    say("Table 4.1", f"{c}: restored / % / breakdown / other / both / primary only / alt only / same year / extension",
        f"{a.sum()} / {100 * a.mean():.1f} / {(a & bk).sum()} / {(a & ~bk).sum()} / {both.sum()} / {(pr & ~a).sum()} / "
        f"{(a & ~pr).sum()} / {(x.loc[both, c] == x.loc[both, 'restoration']).sum()} / {ended_all[c].notna().sum()}")
say("§4.6", "Bangladesh 2002-07: pre-episode EDI / first democratization-episode year after end / stop",
    f"{ep('BGD', 2002).pre_edi:.3f} / {ep('BGD', 2002).uturn} / {ep('BGD', 2002).stop}")
for c_, s_ in [("URY", 1963), ("MDA", 1998), ("MDA", 2013), ("MDA", 2023), ("VEN", 1998), ("BLR", 1994),
               ("CZE", 2013), ("ECU", 2007), ("HND", 2006), ("ZMB", 2011)]:
    k = ep(c_, s_)
    pw = "; ".join(f"{p} lost={k[p + '_lost']} rest={k[p + '_rest']}" for p in PATHS)
    say("§4.7", f"{k['name']} {k.start}-{k.end}",
        f"pre {k.pre_edi:.3f}, trough {k.trough:.3f}, depth {k.depth:.3f}, threshold {k.pre_edi - 0.05:.3f}, "
        f"restored {k.restoration}, uturn {k.uturn}, stop {k.stop}, outcome {k.outcome}, jucon_end {k.jucon_end}, "
        f"duration {k.duration}; {pw}")
say("§4.7", "lowest jucon_end among ended", x.sort_values("jucon_end").iloc[0][["name", "jucon_end"]].tolist())
say("§4.7", "EDI 2023: Venezuela / Belarus", f"{edi('VEN', 2023):.3f} / {edi('BLR', 2023):.3f}")
say("§4.7", "restored in 2022", ", ".join(f"{a} ({b}-{c})" for a, b, c in x[x.restoration == 2022][["name", "start", "end"]].values))

# ---------------------------------------------------------------- Chapter 5
chapter("Chapter 5", "ch05.md")


def km_median(d, ev):
    """First time at which KM share restored reaches one half."""
    d, ev, s = np.asarray(d), np.asarray(ev), 1.0
    for t in sorted(set(d[ev == 1])):
        s *= 1 - ((d == t) & (ev == 1)).sum() / (d >= t).sum()
        if s <= 0.5:
            return t


ended_all["cause"] = np.where(ended_all.ev == 1, 1, np.where(ended_all.stop < 2023, 2, 0))  # 2 = new episode began
x["cause"] = ended_all.loc[x.index, "cause"]


def cif(d, c, at):
    """Cumulative incidence of restoration with a new episode as competing event (Aalen-Johansen)."""
    s, f = 1.0, 0.0
    for t in sorted(set(d[c > 0])):
        if t > at:
            break
        n, d1, d2 = (d >= t).sum(), ((d == t) & (c == 1)).sum(), ((d == t) & (c == 2)).sum()
        f += s * d1 / n
        s *= 1 - (d1 + d2) / n
    return f


groups = {"All (pre-specified)": x, "Ended in breakdown": x[x.breakdown], "Ended without breakdown": x[~x.breakdown],
          "Ended 1950-1989": x[x.end < 1990], "Ended 1990-2022": x[x.end >= 1990], "Ended 2010-2022": x[x.end >= 2010],
          "Ended 1914-1949": ended_all[ended_all.end < 1950], "All ending 1914-2022": ended_all}
for k, g in groups.items():
    rr = g[g.ev == 1]
    say("Table 5.1", f"{k}: n / restored / % / KM5 / KM10 / KM median / restored median (IQR) / median duration restored",
        f"{len(g)} / {g.ev.sum()} / {100 * g.ev.mean():.1f} / {1 - km(g.ttr, g.ev, 5):.3f} / {1 - km(g.ttr, g.ev, 10):.3f} / "
        f"{km_median(g.ttr, g.ev)} / {med(rr.ttr)} ({rr.ttr.quantile(.25):g}-{rr.ttr.quantile(.75):g}) / {med(rr.duration)}")
say("§5.5", "extension KM share restored 1/3/5/10/20 years",
    " / ".join(f"{100 * (1 - km(ended_all.ttr, ended_all.ev, k)):.1f}" for k in (1, 3, 5, 10, 20)))
say("§5.4", "restorations more than 10 years after end / longest", f"{(rest.ttr > 10).sum()} / {rest.ttr.max():g}")
say("§5.4", "episodes still at risk at the longest restoration time", (x.ttr >= rest.ttr.max()).sum())
say("§5.4", "median end-minus-start years, restored episodes", med(rest.end - rest.start))
say("§5.4", "max possible restoration time for episodes ending 2015 / 2019", f"{2023 - 2015} / {2023 - 2019}")
say("Fig. 5.2; §5.5", "ended episodes by decade of end (restored)",
    "; ".join(f"{k}s: {v['size']} ({v['sum']})" for k, v in x.groupby((x.end // 10) * 10).ev.agg(["size", "sum"]).to_dict("index").items()))
say("§5.3", "episodes ending in 2022 (one at-risk year)", (x.end == 2022).sum())
xp = ended_all[ended_all.end < 1950]
say("§5.5", "extension: end years / restored", f"{xp.end.min()}-{xp.end.max()} / {xp.ev.sum()}")
lib = xp[xp.restoration.between(1945, 1947)]
say("§5.5", "extension restorations 1945-47", f"{len(lib)}: " + ", ".join(sorted(lib.name)))
say("§5.5", "years end->restoration: Estonia / Lithuania / Poland (restored 1990); Spain restored",
    " / ".join(f"{xp[xp.country == c].iloc[0].ttr:g}" for c in ("EST", "LTU", "POL")) + f"; {xp[xp.country == 'ESP'].iloc[0].restoration:g}")
say("§5.5", "extension restorations: ttr at KM median 5-6 years (count)", (xp.ttr.between(5, 6) & (xp.ev == 1)).sum())
ns = s[~s.provisional]
say("§5.7", "Vol. 2 non-provisional spells recovered %", f"{100 * ns.recovered.mean():.0f}")
say("§5.7", "restored share 31/54 % / ratio to spells", f"{100 * rest.shape[0] / len(x):.0f} / {(rest.shape[0] / len(x)) / ns.recovered.mean():.2f}")
say("§5.7", "non-provisional spell onsets: range / median / began 2008+", f"{ns.onset.min()}-{ns.onset.max()} / {med(ns.onset)} / {(ns.onset >= 2008).sum()} of {len(ns)}")
say("§5.7", "half-loss rule restored", f"{x.rest_half.notna().sum()} of {len(x)} ({100 * x.rest_half.notna().mean():.0f}%)")
g10 = x[x.end >= 2010]
say("§5.7", "ended 2010+ restored", f"{g10.ev.sum()} of {len(g10)} ({100 * g10.ev.mean():.0f}%)")
ong = e[e.censored]
say("§5.8", "ongoing: started 2010+ / 2000-09 / 1990s / pre-1950",
    f"{(ong.start >= 2010).sum()} / {ong.start.between(2000, 2009).sum()} ({', '.join(ong[ong.start.between(2000, 2009)].name)}) / "
    f"{ong.start.between(1990, 1999).sum()} / {(ong.start < 1950).sum()} ({', '.join(ong[ong.start < 1950].name)})")
say("§5.8", "ongoing: median duration to date / breakdown-coded", f"{med(ong.duration)} / {(ong.outcome == 1).sum()}")
un = x[x.ev == 0]
say("§5.8", "unrestored ended: n / median follow-up / censored by new episode", f"{len(un)} / {med(un.ttr)} / {(un.stop < 2023).sum()}")
say("§5.8", "competing-risk cumulative incidence of restoration at 10 years", f"{cif(x.ttr.values, x.cause.values, 10):.3f}")

# ---------------------------------------------------------------- Chapter 6
chapter("Chapter 6", "ch06.md")
say("§6.3", "at-risk years from 1997 / restorations among them / restorations before 1997",
    f"{len(r97)} / {r97.event.sum()} / {(rest.restoration < 1997).sum()}")
say("§6.4", "bivariate vs primary: extra country-years / extra restorations", f"{len(dd) - 96} / {dd.event.sum() - 7}  (96 and 7 from results.md)")
say("§6.4", "depth SE ratio, RB2 primary / baseline (6.142 / 1.818, results.md)", f"{6.142 / 1.818:.2f}")
def npar(xs):
    """Coefficients besides the constant: covariates, log_t, decade dummies in the estimation sample."""
    d = r.dropna(subset=xs)
    return len(xs) + 1 + (d.end_year // 10).nunique() - 1


say("§6.5", "events per parameter: primary / secondary / bivariate",
    f"{7 / npar(['dagp'] + ['log_gdp', 'depth', 'breakdown']):.2f} / {9 / npar(['agp', 'log_gdp', 'depth', 'breakdown']):.2f} / {9 / npar(['dagp']):.2f}")
say("§6.5", "odds ratio at primary CI bounds for a 1-SD fall: exp(1.313) / 1 - exp(-2.616)",
    f"{np.exp(1.313):.2f} / {1 - np.exp(-2.616):.3f}")
ar = rest[rest.agp_at_rest.notna()]
say("§6.7; §11.6", "restorations with AGP at restoration / of which relapse observable / relapsed",
    f"{len(ar)} / {int(ar.relapse_observed.sum())} / {int(ar[ar.relapse_observed == True].relapse.sum())}")
nr = ar[(ar.relapse_observed == True) & (ar.relapse == False)]
say("§6.7", "non-relapsed restoration with AGP", ", ".join(f"{a} {int(b)} (AGP {c:.3f})" for a, b, c in nr[["name", "restoration", "agp_at_rest"]].values))

# ---------------------------------------------------------------- Chapter 7
chapter("Chapter 7", "ch07.md")
import models  # noqa: E402  (logit() as in models.py: decade dummies, country-clustered SE)
models.DECADE = True
tv = r.groupby("turnover").event.agg(["sum", "size"])
say("§7.4", "turnover country-years / share of risk set", f"{tv.loc[1, 'size']} / {100 * tv.loc[1, 'size'] / len(r):.0f}%")
say("§7.4", "at-risk years lacking lagged GDP", r.log_gdp.isna().sum())
evr = r[r.event == 1]
say("§7.4", "restorations in the year of the first turnover election", ((evr.turnover == 1) & (evr.turnover_l1 == 0)).sum())
say("§7.5", "odds ratios: exp(1.301) / exp(1.147) / Cox exp(0.94)", f"{np.exp(1.301):.2f} / {np.exp(1.147):.2f} / {np.exp(0.94):.2f}")
for lab, d in [("1950-1989", r[r.end_year < 1990]), ("1990+", r[r.end_year >= 1990])]:
    t = d.groupby("turnover").event.agg(["sum", "size"])
    say("§7.6", f"raw rates per 100, episodes ending {lab}: after / before turnover",
        f"{100 * t.loc[1, 'sum'] / t.loc[1, 'size']:.1f} ({t.loc[1, 'sum']}/{t.loc[1, 'size']}) / "
        f"{100 * t.loc[0, 'sum'] / t.loc[0, 'size']:.1f} ({t.loc[0, 'sum']}/{t.loc[0, 'size']})")
base = ["log_gdp", "depth", "breakdown"]
comb = r.dropna(subset=["turnover", "jucon_end", "party_end", "demmob_l1"] + base)


def coef(m, k):
    ci = m.conf_int().loc[k]
    return f"{m.params[k]:.3f} (CI {ci[0]:.3f} to {ci[1]:.3f}; p = {m.pvalues[k]:.3f})"


m = models.logit(comb, ["turnover"] + base, "turnover alone, combined-model sample")
say("§7.6 (not pre-specified)", f"turnover alone on combined-model sample (N {len(comb)}, events {comb.event.sum()})", coef(m, "turnover"))
say("§7.6", "country-years / restorations lost from 264/27 to combined sample", f"{len(gdp) - len(comb)} / {gdp.event.sum() - comb.event.sum()}")
m = models.logit(r, ["turnover", "jucon_end"] + base, "turnover + jucon")
say("§7.6 (not pre-specified)", "turnover with jucon, full GDP sample: turnover", coef(m, "turnover"))
say("§7.6 (not pre-specified)", "turnover with jucon, full GDP sample: jucon_end", coef(m, "jucon_end"))

# ---------------------------------------------------------------- Chapter 8
chapter("Chapter 8", "ch08.md")
L = {p: x[f"{p}_lost"].astype(bool) for p in PATHS}
R_ = {p: L[p] & x[f"{p}_rest"].notna() for p in PATHS}
rx = x.ev == 1
say("§8.4", "lost and never restored: vertical / horizontal / diagonal (% of lost)",
    " / ".join(f"{(L[p] & ~R_[p]).sum()} ({100 * (L[p] & ~R_[p]).sum() / L[p].sum():.0f}%)" for p in PATHS))
nlost, nrest = sum(L.values()), sum(R_.values())
say("§8.4", "unrestored episodes: n / losing >=1 pathway / with no lost pathway returned",
    f"{(~rx).sum()} / {(nlost[~rx] >= 1).sum()} / {((nrest == 0) & (nlost >= 1) & ~rx).sum()}")
say("§8.4", "unrestored episodes: lost pathways left unrestored, of lost (vertical / horizontal / diagonal)",
    " / ".join(f"{(L[p] & ~R_[p] & ~rx).sum()} of {(L[p] & ~rx).sum()}" for p in PATHS))
say("§8.4", "restored episodes losing >=1 pathway / regaining all lost / with one still below",
    f"{(nlost[rx] >= 1).sum()} / {((nrest == nlost) & (nlost >= 1) & rx).sum()} / {((nrest < nlost) & rx).sum()}")
say("§8.4", "restored episodes: lost pathway still below, of those losing it (vertical / horizontal / diagonal)",
    " / ".join(f"{(L[p] & ~R_[p] & rx).sum()} of {(L[p] & rx).sum()}" for p in PATHS))
seq = []
for _, k in x.iterrows():
    ys = sorted(k[f"{p}_rest"] for p in PATHS if k[f"{p}_lost"] and pd.notna(k[f"{p}_rest"]))
    if len(ys) >= 2:
        first = [p for p in PATHS if k[f"{p}_lost"] and k[f"{p}_rest"] == ys[0]]
        seq.append(dict(name=k["name"], start=k.start, country=k.country, rest=k.restoration, ys=ys,
                        first=first[0] if len(first) == 1 else "tie", gap=ys[1] - ys[0], all_same=ys[0] == ys[-1]))
seq = pd.DataFrame(seq)
say("§8.5", "test set: episodes / restored at regime level / not restored",
    f"{len(seq)} / {seq.rest.notna().sum()} / " + ", ".join(f"{a} ({b})" for a, b in seq[seq.rest.isna()][["name", "start"]].values))
nv, n = (seq["first"] == "vertical").sum(), len(seq)
ci = stats.binomtest(nv, n).proportion_ci(method="exact")
say("§8.5", "exact 95% CI of vertical-first share", f"{ci.low:.3f} to {ci.high:.3f}")
crit = next(k for k in range(n + 1) if stats.binom.sf(k - 1, n, 1 / 3) < 0.05)
say("§8.5", "vertical-first count needed for one-sided p < .05 / power at share 0.5 / 0.6",
    f"{crit} / {stats.binom.sf(crit - 1, n, 0.5):.2f} / {stats.binom.sf(crit - 1, n, 0.6):.2f}")
strict = seq[seq["first"] != "tie"]
bt = stats.binomtest((strict["first"] == "vertical").sum(), len(strict), 1 / 3, alternative="greater")
say("§8.5", "strict orderings: n / vertical first (share) / one-sided p / horizontal first",
    f"{len(strict)} / {(strict['first'] == 'vertical').sum()} ({(strict['first'] == 'vertical').mean():.3f}) / {bt.pvalue:.3f} / {(strict['first'] == 'horizontal').sum()}")
say("§8.6.1", "all restored pathways same year / second within one year of first / sequences (gap range)",
    f"{seq.all_same.sum()} / {(seq.gap <= 1).sum()} / {(seq.gap > 1).sum()} ({seq[seq.gap > 1].gap.min():g}-{seq[seq.gap > 1].gap.max():g})")
say("§8.6.1", "median first-to-second gap among non-ties", med(strict.gap))
sr = seq[seq.rest.notna()]
say("§8.6.1", "restored test-set episodes: first pathway in restoration year / within one year",
    f"{(sr.ys.str[0] == sr.rest).sum()} / {((sr.rest - sr.ys.str[0]).abs() <= 1).sum()} of {len(sr)}")
tvx = P.set_index(["country_text_id", "year"]).v2eltvrexo
for _, k in seq[seq["first"] == "tie"].iterrows():
    y = k.ys[0]
    say("§8.6.2", f"tie: {k['name']} ({k.start}), tie year {y:g}", f"v2eltvrexo max in {y - 1:g} / {y:g}: "
        f"{tvx.get((k.country, int(y) - 1))} / {tvx.get((k.country, int(y)))}")

# ---------------------------------------------------------------- Chapter 9
chapter("Chapter 9", "ch09.md")
say("§9.3.1", "risk-set rows lacking party measure / restorations among them",
    f"{r.party_end.isna().sum()} / {r[r.party_end.isna()].event.sum()}")
pp = P.set_index(["country_text_id", "year"]).v2xps_party
say("§9.3.1", "episodes missing party: n / breakdown / later restored / observed in year before end",
    f"{len(pm)} / {pm.breakdown.sum()} / {pm.restoration.notna().sum()} / "
    f"{sum(pd.notna(pp.get((c, int(y) - 1))) for c, y in zip(pm.country, pm.end))}")
say("§9.3.1", "episodes missing party (list)", ", ".join(f"{a} ({b}-{c})" for a, b, c in pm[["name", "start", "end"]].values))
sdj = r.jucon_end.std()
say("§9.4", "SD of jucon_end across at-risk years / 3.408 x SD / odds ratio", f"{sdj:.3f} / {3.408 * sdj:.2f} / {np.exp(3.408 * sdj):.2f}")
say("§9.4", "median jucon_end: restored / unrestored", f"{rest.jucon_end.median():.3f} / {x[x.ev == 0].jucon_end.median():.3f}")
say("§9.4", "corr(jucon_end, depth), ended episodes", f"{x[['jucon_end', 'depth']].corr().iloc[0, 1]:.3f}")
say("§9.4", "mean jucon_end: breakdown / other", f"{x[x.breakdown].jucon_end.mean():.3f} / {x[~x.breakdown].jucon_end.mean():.3f}")
say("§9.4", "jucon_end range", f"{x.jucon_end.min():.3f} to {x.jucon_end.max():.3f}")
po = x[x.party_end.notna()]
say("§9.5", "party observed: episodes / restored mean (n) / unrestored mean (n)",
    f"{len(po)} / {po[po.ev == 1].party_end.mean():.3f} ({(po.ev == 1).sum()}) / {po[po.ev == 0].party_end.mean():.3f} ({(po.ev == 0).sum()})")
say("§9.5", "RB5b estimated parameters besides the constant", npar(["party_end", "log_gdp", "depth", "breakdown"]))
say("§9.5", "corr(jucon_end, party_end) / episodes", f"{po[['jucon_end', 'party_end']].corr().iloc[0, 1]:.3f} / {len(po)}")

# ---------------------------------------------------------------- Chapter 10
chapter("Chapter 10", "ch10.md")
for col, lab in [("agp", "AGP level"), ("dagp", "dAGP")]:
    d = r.dropna(subset=[col, "demmob_l1"])
    say("§10.3", f"corr({lab}, lagged mobilization): rows / countries / r", f"{len(d)} / {d.country.nunique()} / {d[[col, 'demmob_l1']].corr().iloc[0, 1]:.3f}")
say("§10.4", "lagged mobilization missing rows / restorations among them",
    f"{r.demmob_l1.isna().sum()} / {r[r.demmob_l1.isna()].event.sum()}")
sdm = r.demmob_l1.std()
say("§10.5", "SD of lagged mobilization / odds ratio exp(0.337 x SD)", f"{sdm:.3f} / {np.exp(0.337 * sdm):.2f}")
say("§10.5", "mean lagged mobilization: restoration years / other at-risk years",
    f"{r[r.event == 1].demmob_l1.mean():.2f} / {r[r.event == 0].demmob_l1.mean():.2f}")
mob = P.set_index(["country_text_id", "year"]).v2cademmob
D = pd.DataFrame([(k, kk.ev == 1, mob.get((kk.country, int(kk.end) + k))) for _, kk in x.iterrows() for k in range(-5, 11)],
                 columns=["k", "ev", "v"]).dropna()
G = D.groupby(["ev", "k"]).v.mean().unstack(0)
say("Fig. 10.1", "unrestored mean above restored in every year -5..+10", bool((G[False] > G[True]).all()))
say("§10.6", "pooled mean, 5 years before end: unrestored / restored",
    f"{D[(D.k < 0) & ~D.ev].v.mean():.2f} / {D[(D.k < 0) & D.ev].v.mean():.2f}")
say("§10.6", "pooled mean, 10 years after end: unrestored / restored",
    f"{D[(D.k > 0) & ~D.ev].v.mean():.2f} / {D[(D.k > 0) & D.ev].v.mean():.2f}")
say("§10.6", "year before end: unrestored / restored", f"{G.loc[-1, False]:.2f} / {G.loc[-1, True]:.2f}")
rm = r.dropna(subset=["demmob_l1"]).merge(x[["ep_id", "ev"]], on="ep_id")
em = rm.groupby("ep_id").agg(m=("demmob_l1", "mean"), ev=("ev", "first"))
say("§10.6", "episode-averaged lagged mobilization in at-risk years: restored (n) / unrestored (n)",
    f"{em[em.ev == 1].m.mean():.2f} ({(em.ev == 1).sum()}) / {em[em.ev == 0].m.mean():.2f} ({(em.ev == 0).sum()})")
top = em[em.ev == 0].sort_values("m", ascending=False).head(8).join(x.set_index("ep_id")[["name"]])
say("§10.6", "unrestored episodes by average at-risk mobilization (top 8)", ", ".join(f"{a} ({b}, {m_:.2f})" for b, (m_, _, a) in zip(top.index, top.values)))
rm["n"] = rm.ep_id.map(rm.groupby("ep_id").size())
rm["dev"] = rm.demmob_l1 - rm.groupby("ep_id").demmob_l1.transform("mean")
evm = rm[rm.event == 1]
say("§10.6", "restorations in episodes with >1 at-risk year of mobilization / of which above episode mean",
    f"{(evm.n > 1).sum()} / {((evm.n > 1) & (evm.dev > 0)).sum()}")
say("§10.6", "mean within-episode deviation: restoration years / other at-risk years",
    f"{evm.dev.mean():.2f} / {rm[rm.event == 0].dev.mean():.2f}")
# Exploratory decomposition (results/exploratory_mobilization.md was written by inline code; reproduced here)
for lab, d in [("episodes ending 1950-2022", r), ("extended 1914-2022", r_all)]:
    d = d.dropna(subset=["demmob_l1", "log_gdp", "depth", "breakdown"]).copy()
    d["mob_mean"] = d.groupby("ep_id").demmob_l1.transform("mean")
    d["mob_within"] = d.demmob_l1 - d.mob_mean
    m = models.logit(d, ["mob_within", "mob_mean"] + base, lab)
    say("Table 10.1 (exploratory)", f"{lab}: N / events", f"{len(d)} / {d.event.sum()}")
    for k in ("mob_within", "mob_mean"):
        say("Table 10.1 (exploratory)", f"{lab}: {k}", coef(m, k))

# ---------------------------------------------------------------- Chapter 11
chapter("Chapter 11", "ch11.md")
ob = rest[rest.relapse_observed == True].copy()
say("§11.2", "unobservable restorations", ", ".join(f"{a} ({b}-{c}, restored {int(d)})" for a, b, c, d in
                                                 rest[rest.relapse_observed != True][["name", "start", "end", "restoration"]].values))
say("§11.3", "relapsed / observable (%)", f"{int(ob.relapse.sum())} / {len(ob)} ({100 * ob.relapse.mean():.1f})")
ep_start = P[P.aut_ep == 1].groupby(["country_text_id", "aut_ep_id"]).aut_ep_start_year.min().reset_index()


def next_episode(k):
    n = ep_start[(ep_start.country_text_id == k.country) & (ep_start.aut_ep_start_year > k.restoration)]
    return n.sort_values("aut_ep_start_year").iloc[0] if len(n) else None


rl = ob[ob.relapse == True].copy()
rl["new_start"] = [int(next_episode(k).aut_ep_start_year) for _, k in rl.iterrows()]
rl["new_id"] = [next_episode(k).aut_ep_id for _, k in rl.iterrows()]
rl["gap"] = rl.new_start - rl.restoration
rl["in_pop"] = rl.new_id.isin(e.ep_id) | [((e.country == c) & (e.start == s)).any() for c, s in zip(rl.country, rl.new_start)]
say("§11.3", "relapses within 5 years of restoration", (rl.gap <= 5).sum())
ip = rl[rl.in_pop]
say("§11.3; §11.5", "relapses whose new episode is a population episode: n / gap range / median gap",
    f"{len(ip)} / {ip.gap.min():g}-{ip.gap.max():g} / {med(ip.gap)}")
say("§11.5", "population-episode relapses: name (new episode start, gap; new episode censored?)",
    "; ".join(f"{k['name']} restored {int(k.restoration)} ({k.new_start}, {k.gap:g}; "
              f"{bool(e[(e.country == k.country) & (e.start == k.new_start)].censored.iloc[0])})" for _, k in ip.iterrows()))
say("§11.5", "relapses into non-population episodes", ", ".join(f"{a} restored {int(b)} (new start {c})" for a, b, c in rl[~rl.in_pop][["name", "restoration", "new_start"]].values))
ob["pre90"] = ob.restoration < 1990
for k, g in ob.groupby("pre90"):
    say("§11.3", f"observable restorations {'before 1990' if k else '1990 or later'}: n / relapsed", f"{len(g)} / {int(g.relapse.sum())}")
for k, g in ob.groupby("breakdown"):
    say("§11.3", f"observable restorations after {'breakdown' if k else 'non-breakdown'}: n / relapsed", f"{len(g)} / {int(g.relapse.sum())}")
cc = rl.country.value_counts()
say("§11.3", "relapses: countries / in Fiji, Moldova, Suriname", f"{len(cc)} / {cc[['FJI', 'MDA', 'SUR']].sum()}")
from scipy.stats.contingency import odds_ratio  # noqa: E402
for wnd, (a, n1, c, n0) in {5: (7, 17, 5, 9), 10: (8, 16, 5, 7), 15: (11, 16, 5, 6)}.items():  # counts from results.md / robustness.md
    t = [[a, n1 - a], [c, n0 - c]]
    say("Table 11.1", f"{wnd}-year window: % with horizontal / % without / % overall / one-sided Fisher p",
        f"{100 * a / n1:.1f} / {100 * c / n0:.1f} / {100 * (a + c) / (n1 + n0):.1f} / {stats.fisher_exact(t, alternative='less')[1]:.3f}")
o10 = odds_ratio([[8, 8], [5, 2]], kind="conditional")
ci = o10.confidence_interval(0.95)
say("§11.4.2", "conditional MLE odds ratio (10-year) / exact 95% CI", f"{o10.statistic:.2f} / {ci.low:.2f} to {ci.high:.2f}")


def fisher_power(p1, p0, n1=16, n0=7):
    """Exact power of the one-sided Fisher test (relapse lower with horizontal restored) at group sizes n1, n0."""
    return sum(stats.binom.pmf(a, n1, p1) * stats.binom.pmf(c, n0, p0) for a in range(n1 + 1) for c in range(n0 + 1)
               if stats.fisher_exact([[a, n1 - a], [c, n0 - c]], alternative="less")[1] < 0.05)


say("§11.4.3", "exact power at rates (8/16 vs 5/7), (.30, .60), (.20, .60), (.15, .70), (.10, .80) [text reports 4,000-draw simulations]",
    " / ".join(f"{fisher_power(a, b):.2f}" for a, b in [(0.5, 5 / 7), (0.3, 0.6), (0.2, 0.6), (0.15, 0.7), (0.1, 0.8)]))
hr = rl.horiz_restored_at_rest.astype(str) == "True"
say("§11.5", "relapsed with horizontal restored", f"{hr.sum()}: " + ", ".join(f"{a} ({b})" for a, b in rl[hr][["name", "start"]].values))
say("§11.5", "relapsed without horizontal restored", f"{(~hr).sum()}: " + ", ".join(f"{a} ({b})" for a, b in rl[~hr][["name", "start"]].values))
est = ended_all[(ended_all.country == "EST") & ended_all.relapse.astype(str).eq("True")]
say("§11.5", "extension relapse: Estonia new episode start", ", ".join(f"{a} restored {int(b)}: {next_episode(k).aut_ep_start_year:g}" for (_, k), a, b in zip(est.iterrows(), est.name, est.restoration)))
ao = ob[ob.agp_at_rest.notna()]
say("§11.6", "observable restorations with AGP: relapsed names / distinct AGP values among relapsed",
    f"{', '.join(ao[ao.relapse == True].name)} / {ao[ao.relapse == True].agp_at_rest.round(6).nunique()}")
say("§11.4.2", "extended sample: observable / relapsed (results_extended.md)", f"{int(ended_all[ended_all.ev == 1].relapse_observed.sum())} / "
    f"{int(ended_all[(ended_all.ev == 1) & (ended_all.relapse_observed == True)].relapse.sum())}")

# ---------------------------------------------------------------- Chapter 12
chapter("Chapter 12", "ch12.md")
gx = r_all.dropna(subset=base)
say("§12.2", "extension adds to GDP-controlled models: country-years / restorations", f"{len(gx) - len(gdp)} / {gx.event.sum() - gdp.event.sum()}")
x50 = x[x.end < 2022]  # first-run censoring: episodes ending 2022 treated as censored
say("§12.2", "KM 10-year share before / after the censoring correction", f"{100 * (1 - km(x50.ttr, x50.ev, 10)):.1f} / {100 * (1 - km(x.ttr, x.ev, 10)):.1f}")
say("§12.2", "no-GDP risk set rows gained / events gained by the correction", f"{(r.end_year == 2022).sum()} / {r[r.end_year == 2022].event.sum()}")
z = r.dropna(subset=["dagp"] + base)
say("Table 12.1 note", "SD of dAGP in the 96-year estimation sample / all 118", f"{z.dagp.std():.3f} / {r.dagp.std():.3f}")
for rule in ["rest_tol02", "rest_tol10", "rest_nocred", "rest_half", "uturn"]:
    rr_ = pd.read_csv(ROOT / f"results/riskset_{rule}.csv")
    rr_ = rr_[(rr_.end_year >= 1950) & (rr_.end_year <= 2022)].groupby("ep_id").agg(t=("t_since", "max"), ev=("event", "max"))
    say("§12.4; Table 12.2", f"KM 10-year share from riskset_{rule}.csv (episodes / events)", f"{100 * (1 - km(rr_.t, rr_.ev, 10)):.1f} ({len(rr_)} / {rr_.ev.sum()})")
say("§12.5", "earliest end year among country-years with dAGP", int(r[r.dagp.notna()].end_year.min()))
say("§12.5", "lost to missing lagged GDP: rows / of which 2020+ / restorations (years)",
    f"{len(ng)} / {(ng.year >= 2020).sum()} / {ng.event.sum()} ({sorted(ng[ng.event == 1].year.unique())})")
say("§12.8.4", "censored vs pre-specified ended: median pre-episode EDI / median depth / median start year",
    f"{ong.pre_edi.median():.4f} vs {x.pre_edi.median():.4f} / {ong.depth.median():.3f} vs {x.depth.median():.3f} / {med(ong.start)} vs {med(x.start)}")
say("§12.8.4", "censored episodes beginning 2000 or later", f"{(ong.start >= 2000).sum()} of {len(ong)}")

# ---------------------------------------------------------------- Chapter 13
chapter("Chapter 13", "ch13.md")
k = ep("LKA", 1970)
say("§13.9", "Sri Lanka 1970-89: risk period closed (stop year) / next episode start", f"{k.stop} / {k.stop + 1}")
say("§13.9", "postscript EDI values (Poland, Sri Lanka)", "see results/cases.md Postscript (analysis/cases.py)")

# ---------------------------------------------------------------- Appendix A
chapter("Appendix A", "appA.md")
ea = ended_all[ended_all.ev == 1]
say("intro", "population / ended / censored / pre-specified at risk / restored / relapse observable / relapsed",
    f"{len(e)} / {len(ended_all)} / {int(e.censored.sum())} / {len(x)} / {len(rest)} / {int(rest.relapse_observed.sum())} / {int(rest.relapse.sum())}")
say("intro", "extension: ended before 1950 / restored (all 69) / relapse observable / relapsed",
    f"{len(xp)} / {len(ea)} / {int(ea.relapse_observed.sum())} / {int(ea[ea.relapse_observed == True].relapse.sum())}")
OUTCOME = {1: "Breakdown", 2: "Preempted", 3: "Diminished", 4: "Averted", 6: "Censored"}
OUT.append("\nTable A.1 rows (Country | Start | End | Pre EDI | Trough | Outcome | Restored | Relapse | Status | At risk):")
for _, k in e.sort_values("start", kind="stable").iterrows():
    rel = "Yes" if k.relapse == True else "No" if k.relapse_observed == True else "—"
    OUT.append(f"| {k['name']} | {k.start} | {k.end} | {k.pre_edi:.3f} | {k.trough:.3f} | {OUTCOME[int(k.outcome)]} | "
               f"{int(k.restoration) if pd.notna(k.restoration) else '—'} | {rel} | {'Censored' if k.censored else 'Ended'} | "
               f"{'Yes' if not k.censored and k.end >= 1950 else 'No'} |")

if __name__ == "__main__":
    (ROOT / "results/chapter_numbers.md").write_text(
        "# Chapter numbers not printed by other scripts (generated by analysis/chapter_numbers.py)\n"
        "Format: - location | label: value. Pre-specified sample = ended episodes with final year 1950-2022.\n"
        + "\n".join(OUT) + "\n", encoding="utf8")
    print("\n".join(OUT))
