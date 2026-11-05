"""Publication-ready figures.

Rules followed (course "3 core rules of scientific visualization"):
  1. Explicit axis titles with physical units; log scale where values span a wide range.
  2. Uncertainty always shown (bootstrap 95% CI bands / error bars).
  3. Colorblind-safe palette + different markers, line styles and hatches
     so the figures stay readable in monochrome print.
Every figure is exported as vector .pdf and raster .png at 300 DPI.
"""
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter

from process_data import bootstrap_ci

matplotlib.rcParams.update({
    "pdf.fonttype": 42, "ps.fonttype": 42,          # embed TrueType fonts in PDF
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 100, "savefig.dpi": 300,
})

PALETTE = sns.color_palette("colorblind")
STYLE = {  # same group -> same colour/marker/linestyle in every figure
    "neutral": {"color": PALETTE[0], "marker": "o", "ls": "-", "hatch": "", "label": "Neutral (baseline)"},
    "urgent": {"color": PALETTE[3], "marker": "s", "ls": "--", "hatch": "//", "label": "Urgent trigger"},
}


def save(fig, name: str, cfg: dict) -> list[Path]:
    out = Path(cfg["data"]["figures_dir"])
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("pdf", "png"):
        p = out / f"{name}.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight")
        paths.append(p)
    return paths


def fig1_click_rate_vs_anxiety(clean: pd.DataFrame, cfg: dict):
    """Click rate (%) per anxiety tercile and group, with bootstrap 95% CI bands."""
    d, a = cfg["data"], cfg["analysis"]
    rng = np.random.default_rng(cfg["experiment"]["random_seed"])
    strata = list(clean["anxiety_stratum"].cat.categories)
    fig, ax = plt.subplots(figsize=(6.2, 4.2))

    for grp in (d["control_group"], d["treatment_group"]):
        st = STYLE[grp]
        rates, los, his = [], [], []
        for s in strata:
            x = clean[(clean[d["group_column"]] == grp) & (clean["anxiety_stratum"] == s)][d["click_column"]].astype(float)
            lo, hi = bootstrap_ci(x, np.mean, a["bootstrap_n"], a["ci_level"], rng)
            rates.append(x.mean() * 100); los.append(lo * 100); his.append(hi * 100)
        xs = np.arange(len(strata)) + (-0.04 if grp == d["control_group"] else 0.04)  # dodge: avoid overlapping bars
        ax.fill_between(xs, los, his, color=st["color"], alpha=0.18, linewidth=0)
        ax.errorbar(xs, rates, yerr=[np.subtract(rates, los), np.subtract(his, rates)],
                    color=st["color"], marker=st["marker"], linestyle=st["ls"], capsize=3,
                    markersize=6, linewidth=1.8, label=st["label"])

    # tick labels show the actual score range of each tercile
    ticks = []
    for s in strata:
        v = clean.loc[clean["anxiety_stratum"] == s, d["anxiety_column"]]
        ticks.append(f"{s}\n({v.min():.0f}\u2013{v.max():.0f})")
    ax.set_xticks(np.arange(len(strata)), ticks)
    ax.set_xlabel("Trait anxiety tercile (Spielberger\u2013Hanin score, points)")
    ax.set_ylabel("Click rate (% of participants)")
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
    ax.set_title("Link-click rate by anxiety level\n(markers: means; bands and bars: bootstrap 95% CI)")
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def fig2_distribution_boxplot(clean: pd.DataFrame, cfg: dict):
    """Decision-time distribution (s, log scale) by group; diamonds = median with bootstrap 95% CI."""
    d, a = cfg["data"], cfg["analysis"]
    rng = np.random.default_rng(cfg["experiment"]["random_seed"])
    groups = [d["control_group"], d["treatment_group"]]
    data = [clean.loc[clean[d["group_column"]] == g, d["time_column"]].values for g in groups]

    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    bp = ax.boxplot(data, positions=[0, 1], widths=0.5, patch_artist=True, showfliers=False,
                    medianprops={"color": "black", "linewidth": 1.5})
    for patch, g in zip(bp["boxes"], groups):
        patch.set_facecolor(STYLE[g]["color"]); patch.set_alpha(0.35)
        patch.set_hatch(STYLE[g]["hatch"]); patch.set_edgecolor("black")

    for i, (g, x) in enumerate(zip(groups, data)):
        st = STYLE[g]
        jitter = rng.uniform(-0.13, 0.13, len(x))
        ax.scatter(i + jitter, x, s=14, color=st["color"], marker=st["marker"], alpha=0.65, zorder=3)
        lo, hi = bootstrap_ci(x, np.median, a["bootstrap_n"], a["ci_level"], rng)
        med = np.median(x)
        ax.errorbar(i + 0.38, med, yerr=[[med - lo], [hi - med]], fmt="D", color="black",
                    markerfacecolor="white", capsize=4, markersize=6, zorder=4)

    ax.set_yscale("log")
    ticks = [2, 5, 10, 20, 50, 100]
    ax.set_yticks(ticks); ax.set_yticklabels([str(t) for t in ticks])
    ax.set_xticks([0, 1], [STYLE[g]["label"] for g in groups])
    ax.set_xlabel("Message type (experimental group)")
    ax.set_ylabel("Decision time (s, log scale)")
    ax.set_title("Decision-time distribution by message type\n(box: p25\u2013p75; diamond: median with bootstrap 95% CI)")
    ax.grid(axis="y", which="both", alpha=0.25)
    fig.tight_layout()
    return fig


def run_all(cfg: dict) -> list[Path]:
    clean = pd.read_csv(Path(cfg["data"]["processed_dir"]) / "clean_trials.csv")
    labels = ["Low", "Medium", "High"][: cfg["analysis"]["anxiety_strata"]]
    clean["anxiety_stratum"] = pd.Categorical(clean["anxiety_stratum"], categories=labels, ordered=True)
    paths = []
    for name, fn in (("fig1_clickrate_vs_anxiety", fig1_click_rate_vs_anxiety),
                     ("fig2_distribution_boxplot", fig2_distribution_boxplot)):
        fig = fn(clean, cfg)
        paths += save(fig, name, cfg)
        plt.close(fig)
    return paths
