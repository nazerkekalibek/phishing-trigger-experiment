"""Measurement skeleton for the urgency-trigger phishing experiment.

Reads participant responses, validates them against guardrails, computes the
primary metric (click rate per group) and secondary metric (decision time),
runs the statistical tests defined in the config, and writes a log + JSON summary.

Usage:
    python src/main.py --config configs/config.yaml
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(log_file: str) -> logging.Logger:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger=logging.getLogger("experiment")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt=logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    for handler in (logging.FileHandler(log_file, mode="w", encoding="utf-8"),
                    logging.StreamHandler(sys.stdout)):
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger


def check_guardrails(df: pd.DataFrame, cfg: dict, log: logging.Logger) -> pd.DataFrame:
    """Validate data quality. Returns the cleaned dataframe; raises on fatal problems."""
    d, g=cfg["data"], cfg["guardrails"]

    if g["require_no_missing"] and df[[d["group_column"], d["time_column"], d["click_column"]]].isna().any().any():
        raise ValueError("Guardrail failed: missing values in required columns")

    if not set(df[d["click_column"]].unique()).issubset({0, 1}):
        raise ValueError("Guardrail failed: click column must be binary (0/1)")

    in_range=df[d["time_column"]].between(g["min_time_sec"], g["max_time_sec"])
    n_invalid=int((~in_range).sum())
    if n_invalid:
        log.warning("Guardrail: excluded %d row(s) with decision time outside [%s, %s] s",
                    n_invalid, g["min_time_sec"], g["max_time_sec"])
    df=df[in_range].copy()

    counts=df[d["group_column"]].value_counts()
    for grp in (d["control_group"], d["treatment_group"]):
        if grp not in counts:
            raise ValueError(f"Guardrail failed: group '{grp}' has no valid rows")
    imbalance=abs(counts[d["control_group"]] - counts[d["treatment_group"]]) / counts.max()
    log.info("Group sizes: %s | relative imbalance = %.2f", counts.to_dict(), imbalance)
    if imbalance > g["max_group_imbalance"]:
        log.warning("Guardrail: group imbalance %.2f exceeds limit %.2f", imbalance, g["max_group_imbalance"])
    return df


def run_analysis(df: pd.DataFrame, cfg: dict, log: logging.Logger) -> dict:
    d, a=cfg["data"], cfg["analysis"]
    ctrl=df[df[d["group_column"]] == d["control_group"]]
    trt=df[df[d["group_column"]] == d["treatment_group"]]

    # Primary metric: click rate
    click_ctrl, click_trt = ctrl[d["click_column"]].mean(), trt[d["click_column"]].mean()
    table=[[int(trt[d["click_column"]].sum()), int(len(trt) - trt[d["click_column"]].sum())], [int(ctrl[d["click_column"]].sum()), int(len(ctrl) - ctrl[d["click_column"]].sum())]]
    odds_ratio, p_click = stats.fisher_exact(table, alternative="two-sided")

    # Secondary metric: decision time
    t_ctrl, t_trt=ctrl[d["time_column"]], trt[d["time_column"]]
    u_stat, p_time=stats.mannwhitneyu(t_trt, t_ctrl, alternative="two-sided")

    alpha=a["alpha"]
    result={
        "n_control": int(len(ctrl)),
        "n_treatment": int(len(trt)),
        "primary_metric_click_rate": {
            "control": round(float(click_ctrl), 3),
            "treatment": round(float(click_trt), 3),
            "difference": round(float(click_trt - click_ctrl), 3),
            "test": a["click_test"],
            "p_value": round(float(p_click), 4),
            "reject_H0": bool(p_click < alpha),
        },
        "secondary_metric_decision_time_sec": {
            "control_median": round(float(np.median(t_ctrl)), 2),
            "treatment_median": round(float(np.median(t_trt)), 2),
            "test": a["time_test"],
            "p_value": round(float(p_time), 4),
            "reject_H0": bool(p_time < alpha),
        },
        "alpha": alpha,
        "note": "Sample data is synthetic and used only to verify the pipeline.",
    }
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description="Urgency-trigger phishing experiment: analysis pipeline")
    parser.add_argument("--config", default="configs/config.yaml", help="Path to YAML config")
    args=parser.parse_args()

    cfg=load_config(args.config)
    log=setup_logging(cfg["output"]["log_file"])
    np.random.seed(cfg["experiment"]["random_seed"])

    log.info("Experiment: %s", cfg["experiment"]["name"])
    log.info("Loading data from %s", cfg["data"]["input_path"])
    df=pd.read_csv(cfg["data"]["input_path"])
    log.info("Loaded %d rows", len(df))

    df=check_guardrails(df, cfg, log)
    result=run_analysis(df, cfg, log)

    log.info("Click rate  control=%.3f  treatment=%.3f  p=%.4f",
             result["primary_metric_click_rate"]["control"],
             result["primary_metric_click_rate"]["treatment"],
             result["primary_metric_click_rate"]["p_value"])
    log.info("Median time control=%.2fs  treatment=%.2fs  p=%.4f",
             result["secondary_metric_decision_time_sec"]["control_median"],
             result["secondary_metric_decision_time_sec"]["treatment_median"],
             result["secondary_metric_decision_time_sec"]["p_value"])

    out=Path(cfg["output"]["summary_file"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    log.info("Summary written to %s", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
