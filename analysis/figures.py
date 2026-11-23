"""Book figures (grayscale, 6x9 print). -> figures/*.png at 300 dpi."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "savefig.dpi": 300, "savefig.bbox": "tight"})
W = 4.5  # inches, fits a 6x9 text block


def km_curve(d, e):
    d, e = np.asarray(d), np.asarray(e)
    ts, s, out = sorted(set(d[e == 1])), 1.0, [(0, 0.0)]
    for t in ts:
        s *= 1 - ((d == t) & (e == 1)).sum() / (d >= t).sum()
        out.append((t, 1 - s))
    return out


def main():
    e = pd.read_csv(ROOT / "results/episodes.csv")
    r = pd.read_csv(ROOT / "results/riskset.csv")
    p = pd.read_parquet(ROOT / "data/processed/panel.parquet")
    # pre-specified sample (DESIGN.md): episodes ending 1950-2022
    e = e[e.censored | (e.end >= 1950)]
    r = r[(r.end_year >= 1950) & (r.end_year <= 2022)]
    ended = e[~e.censored].copy()
    ended["ttr"] = np.where(ended.restoration.notna(), ended.restoration - ended.end, ended.stop - ended.end)
    ended["ev"] = ended.restoration.notna().astype(int)

    # 5.1 cumulative restoration (KM), all and by breakdown
    fig, ax = plt.subplots(figsize=(W, 3))
    for lab, g, ls in [("All episodes (n = %d)" % len(ended), ended, "-"),
                       ("Breakdown (n = %d)" % ended.breakdown.sum(), ended[ended.breakdown], "--"),
                       ("No breakdown (n = %d)" % (~ended.breakdown).sum(), ended[~ended.breakdown], ":")]:
        c = km_curve(g.ttr, g.ev)
        ax.step([x for x, _ in c], [y for _, y in c], where="post", color="black", ls=ls, label=lab)
    ax.set_xlim(0, 25); ax.set_ylim(0, 1)
    ax.set_xlabel("Years since end of autocratization episode"); ax.set_ylabel("Cumulative share restored")
    ax.legend(frameon=False, loc="lower right")
    fig.savefig(FIG / "fig5_1_km_restoration.png"); plt.close(fig)

    # 5.2 episodes ended and restored, by decade of end
    ended["dec"] = (ended.end // 10) * 10
    t = ended.groupby("dec").agg(n=("ev", "size"), rest=("ev", "sum"))
    fig, ax = plt.subplots(figsize=(W, 2.8))
    ax.bar(t.index, t.n, width=7, color="0.8", label="Episodes ended")
    ax.bar(t.index, t.rest, width=7, color="0.2", label="Restored by 2023")
    ax.set_xlabel("Decade in which episode ended"); ax.set_ylabel("Episodes")
    ax.legend(frameon=False)
    fig.savefig(FIG / "fig5_2_episodes_by_decade.png"); plt.close(fig)

    # 8.1 first pathway restored
    firsts = []
    for _, x in ended.iterrows():
        ys = {k: x[f"{k}_rest"] for k in ("vertical", "horizontal", "diagonal") if x[f"{k}_lost"] and pd.notna(x[f"{k}_rest"])}
        if len(ys) >= 2:
            m = min(ys.values()); w = [k for k, v in ys.items() if v == m]
            firsts.append(w[0].capitalize() if len(w) == 1 else "Tie")
    c = pd.Series(firsts).value_counts().reindex(["Vertical", "Horizontal", "Diagonal", "Tie"]).fillna(0)
    fig, ax = plt.subplots(figsize=(W, 2.5))
    ax.bar(c.index, c.values, color=["0.2", "0.45", "0.65", "0.85"], edgecolor="black", linewidth=.5)
    ax.axhline(len(firsts) / 3, color="black", ls="--", lw=.8)
    ax.text(3.45, len(firsts) / 3 + .3, "n/3", ha="right", fontsize=8)
    ax.set_ylabel("Episodes"); ax.set_xlabel("Pathway restored first (n = %d episodes)" % len(firsts))
    fig.savefig(FIG / "fig8_1_first_pathway.png"); plt.close(fig)

    # 10.1 mobilization around episode end, restored vs not
    rows = []
    for _, x in ended.iterrows():
        g = p[p.country_text_id == x.country].set_index("year").v2cademmob
        for k in range(-5, 11):
            v = g.get(int(x.end) + k)
            if v is not None and not np.isnan(v):
                rows.append((k, "Restored" if x.ev else "Not restored", v))
    m = pd.DataFrame(rows, columns=["k", "grp", "v"]).groupby(["grp", "k"]).v.mean()
    fig, ax = plt.subplots(figsize=(W, 2.8))
    for grp, ls in (("Restored", "-"), ("Not restored", "--")):
        ax.plot(m[grp].index, m[grp].values, color="black", ls=ls, label=grp, marker="o", ms=2.5)
    ax.axvline(0, color="0.5", lw=.6)
    ax.set_xlabel("Years relative to end of episode"); ax.set_ylabel("Mobilization for democracy\n(V-Dem latent, mean)")
    ax.legend(frameon=False)
    fig.savefig(FIG / "fig10_1_mobilization.png"); plt.close(fig)

    # 7.1 annual restoration rate by turnover status
    t = r.groupby("turnover").event.agg(["sum", "size"])
    rate = 100 * t["sum"] / t["size"]
    fig, ax = plt.subplots(figsize=(W, 2.4))
    ax.bar(["No turnover election\nsince episode end", "Turnover election\nsince episode end"], rate.values,
           color=["0.75", "0.25"], edgecolor="black", linewidth=.5)
    for i, (s_, n_) in enumerate(zip(t["sum"], t["size"])):
        ax.text(i, rate.values[i] + .4, f"{int(s_)}/{int(n_)}", ha="center", fontsize=8)
    ax.set_ylabel("Restorations per 100\nat-risk country-years")
    fig.savefig(FIG / "fig7_1_turnover_rate.png"); plt.close(fig)

    # 12.1 coefficient plot across specifications
    rob = (ROOT / "results/robustness.md").read_text(encoding="utf8").splitlines()
    tab = [l for l in rob if l.startswith("| ") and not l.startswith("| Specification") and "Non-breakdown" not in l
           and "no decade control" not in l]
    import re
    specs, est = [], {k: [] for k in ("RB3 turnover", "RB5a jucon", "RB6 demmob")}
    for l in tab:
        cells = [c.strip() for c in l.strip("|").split("|")]
        specs.append(cells[0])
        for k, idx in (("RB3 turnover", 2), ("RB5a jucon", 3), ("RB6 demmob", 5)):
            mm = re.match(r"(-?[\d.]+) \[(-?[\d.]+), (-?[\d.]+)\]", cells[idx])
            est[k].append(tuple(map(float, mm.groups())) if mm else (np.nan,) * 3)
    fig, axs = plt.subplots(1, 3, figsize=(6.0, 3.6), sharey=True)
    y = np.arange(len(specs))[::-1]
    for ax, (k, v) in zip(axs, est.items()):
        v = np.array(v)
        ax.errorbar(v[:, 0], y, xerr=[v[:, 0] - v[:, 1], v[:, 2] - v[:, 0]], fmt="o", color="black", ms=3, lw=.8)
        ax.axvline(0, color="0.5", lw=.6); ax.set_title(k.split(" ", 1)[1].replace("jucon", "judicial constraint")
                                                       .replace("demmob", "mobilization"), fontsize=9)
    axs[0].set_yticks(y); axs[0].set_yticklabels([s.replace("Rule: ", "") for s in specs], fontsize=7)
    fig.savefig(FIG / "fig12_1_robustness.png"); plt.close(fig)
    print("figures written:", sorted(x.name for x in FIG.glob("*.png")))


if __name__ == "__main__":
    main()
