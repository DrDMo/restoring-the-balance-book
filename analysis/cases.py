"""Case-level lists and counts. Writes results/cases.md (all episodes, 1914+) and results/cases_prespec.md
(pre-specified sample: episodes ending 1950-2022). Inputs: results/episodes.csv, results/riskset.csv,
data/processed/panel.parquet, and ERT ($RTB_DATA/raw/vdem_ert/ert.csv) for the 2024-2025 postscript."""
import os
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("RTB_DATA", ROOT / "data"))
COLS = ['name', 'start', 'end', 'pre_edi', 'trough', 'depth', 'outcome', 'censored', 'restoration', 'vertical_lost',
        'vertical_rest', 'horizontal_lost', 'horizontal_rest', 'diagonal_lost', 'diagonal_rest', 'relapse',
        'horiz_restored_at_rest', 'agp_at_rest', 'jucon_end']


def span(x):
    return f"{int(x.start)}" if x.start == x.end else f"{int(x.start)}-{int(x.end)}"


def turnovers(e, p):
    """Per episode: executive-turnover election (v2eltvrexo == 2) in the restoration year; strictly between end and
    restoration; or (unrestored) any year end+1..stop."""
    tv = {c: g.set_index('year').v2eltvrexo for c, g in p.groupby('country_text_id')}
    same, prior, foll = [], [], []
    for _, x in e.iterrows():
        t = tv.get(x.country, pd.Series(dtype=float))
        if pd.notna(x.restoration):
            same.append(t.get(x.restoration) == 2)
            prior.append(any(t.get(u) == 2 for u in range(int(x.end) + 1, int(x.restoration))))
            foll.append(False)
        else:
            same.append(False); prior.append(False)
            foll.append(any(t.get(u) == 2 for u in range(int(x.end) + 1, int(x.stop) + 1)))
    return pd.DataFrame({'same': same, 'prior': prior, 'foll': foll}, index=e.index)


def all_episodes(e, r, p):
    out = ['# Episode case list (ERT v16 prch episodes; EDI from ERT; accountability indices V-Dem v14)\n',
           'outcome: 1 breakdown, 2 preempted breakdown, 4 averted regression, 6 censored\n']
    with pd.option_context('display.width', 300, 'display.max_rows', 200, 'display.max_columns', 30):
        out.append(e[COLS].round(3).sort_values('start', kind='stable').to_string(index=False))
    x, u = e[e.restoration.notna()], e[~e.censored & e.restoration.isna()]
    t = turnovers(e, p)
    out.append(f"\nRestorations ({len(x)}): turnover election in restoration year {t.loc[x.index, 'same'].sum()}; "
               f"turnover election earlier in recovery period {t.loc[x.index, 'prior'].sum()}")
    out.append(f"Unrestored ended episodes ({len(u)}): any turnover election during follow-up {t.loc[u.index, 'foll'].sum()}")
    out.append('\nUnrestored ended episodes: ' + ', '.join(f"{a} ({int(b)}-{int(c)})" for a, b, c in u[['name', 'start', 'end']].values))
    out.append('\nCensored/ongoing: ' + ', '.join(f"{a} ({int(b)}-)" for a, b in e[e.censored][['name', 'start']].values))
    out.append(f"\nRisk set: mean demmob_l1 event years {r[r.event == 1].demmob_l1.mean():.2f} non-event {r[r.event == 0].demmob_l1.mean():.2f}")
    out.append(f"jucon_end restored eps {x.jucon_end.mean():.3f} unrestored ended {u.jucon_end.mean():.3f}")
    # Descriptive only: the at-risk window ends in 2023; ERT v16 runs to 2025.
    ert = pd.read_csv(DATA / "raw/vdem_ert/ert.csv", usecols=['country_text_id', 'year', 'v2x_polyarchy', 'v2x_polyarchy_codehigh', 'v2x_regime'])
    out.append('\n## Postscript (descriptive, outside the pre-specified window): ERT v16 EDI 2024-2025 for ended, unrestored-by-2023 episodes')
    for _, x in u.iterrows():
        g = ert[(ert.country_text_id == x.country) & (ert.year >= 2022)].set_index('year')
        v = {y: round(float(g.v2x_polyarchy.get(y, float('nan'))), 3) for y in (2023, 2024, 2025)}
        thr = round(x.pre_edi - 0.05, 3)
        hit = [y for y in (2024, 2025) if g.v2x_polyarchy.get(y, 0) >= thr and g.v2x_regime.get(y, 0) >= 2]
        hi = float(ert[(ert.country_text_id == x.country) & (ert.year == x.trough_year)].v2x_polyarchy_codehigh.iloc[0])
        full = [y for y in hit if g.v2x_polyarchy[y] > hi]  # credibility: EDI above the trough's upper bound
        out.append(f"- {x['name']} ({x.start}-{x.end}): threshold {thr}; EDI {v}; meets magnitude+regime in {hit or 'neither year'}; "
                   f"trough upper bound {round(hi, 3)}; meets all three conditions in {full or 'neither year'}")
    return out


def prespec(e, r, p):
    e = e[~e.censored & (e.end >= 1950)]
    r = r[(r.end_year >= 1950) & (r.end_year <= 2022)]
    x, u = e[e.restoration.notna()], e[e.restoration.isna()]
    t = turnovers(e, p)
    tx, tu = t.loc[x.index], t.loc[u.index]
    rate = r.groupby('turnover').event.agg(['sum', 'size'])
    y, n = rate.loc[1], rate.loc[0]
    rel = x[x.relapse == True]
    last = u[u.end == 2022].sort_values('name')
    return [
        f"# Case-level counts, PRE-SPECIFIED sample (episodes ending 1950-2022; {len(e)} ended and at risk, {len(x)} restored)\n",
        f"- Restoration rate per 100 at-risk country-years: with a turnover election since episode end {100 * y['sum'] / y['size']:.1f} "
        f"({y['sum']}/{y['size']}); without {100 * n['sum'] / n['size']:.1f} ({n['sum']}/{n['size']}). (Fig. 7.1)",
        f"- Of {len(x)} restorations: turnover election in the restoration year {tx.same.sum()}; turnover election earlier in the "
        f"recovery period {tx.prior.sum()}; either {(tx.same | tx.prior).sum()}.",
        f"- Of {len(u)} unrestored ended episodes: {tu.foll.sum()} had a turnover election during follow-up.",
        f"- Mean judicial constraints at episode end: restored {x.jucon_end.mean():.3f}; unrestored {u.jucon_end.mean():.3f}.",
        f"- Relapsed within 10 years ({len(rel)}): " + ", ".join(f"{a['name']} ({span(a)}, restored {int(a.restoration)})" for _, a in rel.iterrows()) + ".",
        f"- Unrestored ended ({len(u)}): " + ", ".join(f"{a['name']} ({span(a)})" for _, a in u.sort_values('name').iterrows()) +
        f". The {len(last)} ending in 2022 ({', '.join(last['name'])}) have a single at-risk year (2023).",
    ]


if __name__ == "__main__":
    e = pd.read_csv(ROOT / "results/episodes.csv")
    r = pd.read_csv(ROOT / "results/riskset.csv")
    p = pd.read_parquet(ROOT / "data/processed/panel.parquet", columns=['country_text_id', 'year', 'v2eltvrexo'])
    (ROOT / "results/cases.md").write_text("\n".join(all_episodes(e, r, p)) + "\n", encoding="utf8")
    (ROOT / "results/cases_prespec.md").write_text("\n".join(prespec(e, r, p)) + "\n", encoding="utf8")
