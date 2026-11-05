"""Data processing and statistical aggregation.

Pipeline: load raw .jsonl -> drop warm-up (practice) trials -> apply guardrails
-> aggregate (median, p25/p75, p95, p99, mean/SD, bootstrap 95% CI) -> run the
two pre-specified one-sided tests -> write data/processed/*.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats


# --------------------------------------------------------------------------- #
# Loading and filtering
# --------------------------------------------------------------------------- #
def load_config(path: str = "configs/config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_raw(cfg: dict) -> pd.DataFrame:
    """Read the raw JSON-lines log."""
    return pd.read_json(cfg["data"]["raw_path"], lines=True)


def drop_warmup(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, int]:
    """Discard warm-up (practice) trials: 'cold' first interactions are slower
    and not comparable to evaluation trials."""
    d = cfg["data"]
    is_warm = df[d["phase_column"]] == d["warmup_phase"]
    return df[~is_warm].copy(), int(is_warm.sum())


def apply_guardrails(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Flag invalid evaluation rows and compute the error-rate guardrail per group.

    A row is invalid if status != 'ok', a required value is missing, or the
    decision time lies outside [min_time_sec, max_time_sec].
    """
    d, g = cfg["data"], cfg["guardrails"]
    ok_status = df[d["status_column"]] == "ok"
    has_vals = df[[d["time_column"], d["click_column"]]].notna().all(axis=1)
    in_range = df[d["time_column"]].between(g["min_time_sec"], g["max_time_sec"])
    valid = ok_status & has_vals & in_range

    report = (
        df.assign(invalid=~valid)
        .groupby(d["group_column"])
        .agg(n_total=("invalid", "size"), n_invalid=("invalid", "sum"))
    )
    report["invalid_rate"] = report["n_invalid"] / report["n_total"]
    report["guardrail_ok"] = report["invalid_rate"] <= g["max_invalid_rate"]
    return df[valid].copy(), report


def group_imbalance(df: pd.DataFrame, cfg: dict) -> float:
    counts = df[cfg["data"]["group_column"]].value_counts()
    return float(abs(counts.iloc[0] - counts.iloc[-1]) / counts.max())


# --------------------------------------------------------------------------- #
# Bootstrap helpers (seeded -> reproducible)
# --------------------------------------------------------------------------- #
def bootstrap_ci(x, stat, n_boot: int, level: float, rng: np.random.Generator):
    """Percentile bootstrap CI for a statistic of a 1-D sample."""
    x = np.asarray(x, dtype=float)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    boots = stat(x[idx], axis=1)
    lo, hi = np.percentile(boots, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return float(lo), float(hi)


def describe_times(x, cfg: dict, rng: np.random.Generator) -> dict:
    a = cfg["analysis"]
    x = np.asarray(x, dtype=float)
    lo, hi = bootstrap_ci(x, np.median, a["bootstrap_n"], a["ci_level"], rng)
    return {
        "n": int(len(x)),
        "mean": float(x.mean()), "sd": float(x.std(ddof=1)),
        "median": float(np.median(x)), "median_ci_low": lo, "median_ci_high": hi,
        "p25": float(np.percentile(x, 25)), "p75": float(np.percentile(x, 75)),
        "p95": float(np.percentile(x, 95)), "p99": float(np.percentile(x, 99)),
    }


def click_rate(x, cfg: dict, rng: np.random.Generator) -> dict:
    a = cfg["analysis"]
    x = np.asarray(x, dtype=float)
    lo, hi = bootstrap_ci(x, np.mean, a["bootstrap_n"], a["ci_level"], rng)
    return {"n": int(len(x)), "clicks": int(x.sum()), "rate": float(x.mean()),
            "ci_low": lo, "ci_high": hi}


# --------------------------------------------------------------------------- #
# Hypothesis tests
# --------------------------------------------------------------------------- #
def run_tests(df: pd.DataFrame, cfg: dict, rng: np.random.Generator) -> dict:
    d, a = cfg["data"], cfg["analysis"]
    ctrl = df[df[d["group_column"]] == d["control_group"]]
    trt = df[df[d["group_column"]] == d["treatment_group"]]
    alpha_adj = a["alpha"] / a["n_tests"] if a["multiple_testing"] == "bonferroni" else a["alpha"]

    # H1b (primary): click probability is higher under the urgency trigger
    c_t, c_c = trt[d["click_column"]].astype(int), ctrl[d["click_column"]].astype(int)
    table = [[int(c_t.sum()), int(len(c_t) - c_t.sum())],
             [int(c_c.sum()), int(len(c_c) - c_c.sum())]]
    odds, p_click = stats.fisher_exact(table, alternative=a["click_alternative"])
    # bootstrap CI for the risk difference (treatment - control)
    n_b = a["bootstrap_n"]
    diffs = (rng.choice(c_t.values, (n_b, len(c_t))).mean(axis=1)
             - rng.choice(c_c.values, (n_b, len(c_c))).mean(axis=1))
    rd_lo, rd_hi = np.percentile(diffs, [(1 - a["ci_level"]) / 2 * 100, (1 + a["ci_level"]) / 2 * 100])

    # H1a (secondary): decision time is shorter under the urgency trigger
    t_t, t_c = trt[d["time_column"]].values, ctrl[d["time_column"]].values
    u_stat, p_time = stats.mannwhitneyu(t_t, t_c, alternative=a["time_alternative"])
    cliffs = 2 * u_stat / (len(t_t) * len(t_c)) - 1  # Cliff's delta (negative = treatment faster)
    med_diffs = (np.median(rng.choice(t_t, (n_b, len(t_t))), axis=1)
                 - np.median(rng.choice(t_c, (n_b, len(t_c))), axis=1))
    md_lo, md_hi = np.percentile(med_diffs, [(1 - a["ci_level"]) / 2 * 100, (1 + a["ci_level"]) / 2 * 100])

    return {
        "alpha_nominal": a["alpha"], "alpha_adjusted": alpha_adj,
        "H1b_click_rate": {
            "test": f"Fisher exact ({a['click_alternative']})",
            "risk_difference": float(c_t.mean() - c_c.mean()),
            "risk_difference_ci": [float(rd_lo), float(rd_hi)],
            "odds_ratio": float(odds), "p_value": float(p_click),
            "reject_H0": bool(p_click < alpha_adj),
        },
        "H1a_decision_time": {
            "test": f"Mann-Whitney U ({a['time_alternative']})",
            "median_difference_sec": float(np.median(t_t) - np.median(t_c)),
            "median_difference_ci": [float(md_lo), float(md_hi)],
            "cliffs_delta": float(cliffs), "p_value": float(p_time),
            "reject_H0": bool(p_time < alpha_adj),
        },
    }


# --------------------------------------------------------------------------- #
# Aggregation table and pipeline
# --------------------------------------------------------------------------- #
def anxiety_strata(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Add tercile labels of trait anxiety (used for the interaction figure)."""
    d, a = cfg["data"], cfg["analysis"]
    out = df.copy()
    out["anxiety_stratum"] = pd.qcut(out[d["anxiety_column"]], a["anxiety_strata"],
                                     labels=["Low", "Medium", "High"][: a["anxiety_strata"]])
    return out


def build_summary(df: pd.DataFrame, cfg: dict, rng: np.random.Generator) -> pd.DataFrame:
    """Long-format summary: one row per (group, metric)."""
    d = cfg["data"]
    rows = []
    for grp in (d["control_group"], d["treatment_group"]):
        sub = df[df[d["group_column"]] == grp]
        t = describe_times(sub[d["time_column"]], cfg, rng)
        c = click_rate(sub[d["click_column"]], cfg, rng)
        rows += [
            (grp, "n_valid", t["n"], np.nan, np.nan),
            (grp, "click_rate", c["rate"], c["ci_low"], c["ci_high"]),
            (grp, "time_median_sec", t["median"], t["median_ci_low"], t["median_ci_high"]),
            (grp, "time_p25_sec", t["p25"], np.nan, np.nan),
            (grp, "time_p75_sec", t["p75"], np.nan, np.nan),
            (grp, "time_p95_sec", t["p95"], np.nan, np.nan),
            (grp, "time_p99_sec", t["p99"], np.nan, np.nan),
            (grp, "time_mean_sec", t["mean"], np.nan, np.nan),
            (grp, "time_sd_sec", t["sd"], np.nan, np.nan),
        ]
    return pd.DataFrame(rows, columns=["group", "metric", "value", "ci_low", "ci_high"])


def run_pipeline(cfg: dict) -> dict:
    """Run everything and write data/processed/{clean_trials.csv, metrics_summary.csv, tests_summary.json}."""
    rng = np.random.default_rng(cfg["experiment"]["random_seed"])
    raw = load_raw(cfg)
    evaluation, n_warm = drop_warmup(raw, cfg)
    clean, guard = apply_guardrails(evaluation, cfg)
    clean = anxiety_strata(clean, cfg)

    summary = build_summary(clean, cfg, rng)
    tests = run_tests(clean, cfg, rng)

    out = Path(cfg["data"]["processed_dir"])
    out.mkdir(parents=True, exist_ok=True)
    clean.to_csv(out / "clean_trials.csv", index=False)
    summary.to_csv(out / "metrics_summary.csv", index=False)
    result = {
        "n_raw_rows": int(len(raw)), "n_warmup_dropped": n_warm,
        "n_evaluation_rows": int(len(evaluation)), "n_valid": int(len(clean)),
        "guardrails": guard.reset_index().to_dict(orient="records"),
        "group_imbalance": group_imbalance(clean, cfg),
        "tests": tests,
        "data_source": sorted(raw["source"].unique().tolist()) if "source" in raw else ["unknown"],
    }
    (out / "tests_summary.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return result
