"""Generate a SYNTHETIC raw log (data/raw/test_run.jsonl) with the same schema
that the real experiment will produce.

!! This file contains simulated numbers, NOT measurements of real people. !!
It exists so the whole pipeline (warm-up filtering, guardrails, statistics,
figures) can be verified end-to-end. Every record carries "source": "simulated".
To analyze real data, replace data/raw/test_run.jsonl with a file of the same
schema and re-run `python src/main.py`.

Design mirrored by the schema:
  - between-subjects, random assignment to `neutral` or `urgent`;
  - every participant first sees one neutral PRACTICE message (warm-up, discarded),
    then one EVALUATION message of their assigned type.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import yaml


def simulate(cfg: dict) -> list[dict]:
    s = cfg["simulation"]
    d = cfg["data"]
    rng = np.random.default_rng(cfg["experiment"]["random_seed"])

    n = s["n_per_group"]
    groups = np.array([d["control_group"]] * n + [d["treatment_group"]] * n)
    rng.shuffle(groups)  # random assignment

    logit0 = np.log(s["neutral_click_prob"] / (1 - s["neutral_click_prob"]))
    b_urgent = np.log(s["urgent_click_odds_ratio"])
    records = []

    for i, grp in enumerate(groups, start=1):
        pid = f"P{i:03d}"
        anxiety = float(np.clip(rng.normal(42, 8), 20, 80).round(0))

        # --- warm-up (practice) trial: neutral message, cold-start slowdown ---
        t_prac = rng.lognormal(np.log(s["neutral_median_time_sec"] * s["warmup_slowdown"]), 0.5)
        p_prac = 1 / (1 + np.exp(-logit0))
        records.append({
            "participant_id": pid, "group": str(grp), "phase": d["warmup_phase"], "trial_index": 0,
            "decision_time_sec": round(float(t_prac), 2),
            "clicked": int(rng.random() < p_prac),
            "trait_anxiety": anxiety, "status": "ok", "source": "simulated",
        })

        # --- evaluation trial ---
        is_urgent = grp == d["treatment_group"]
        logit = logit0 + (b_urgent if is_urgent else 0.0) + 0.03 * (anxiety - 42)
        p_click = 1 / (1 + np.exp(-logit))
        median_t = s["urgent_median_time_sec"] if is_urgent else s["neutral_median_time_sec"]
        t = float(rng.lognormal(np.log(median_t), 0.5 if is_urgent else 0.45))
        clicked, status = int(rng.random() < p_click), "ok"

        if rng.random() < s["invalid_rate"]:  # inject realistic data-quality problems
            status = str(rng.choice(["timeout", "accidental_tap", "app_error"]))
            if status == "timeout":
                t = float(rng.uniform(121, 150))
            elif status == "accidental_tap":
                t = float(rng.uniform(0.2, 0.9))
            else:
                t, clicked = None, None

        records.append({
            "participant_id": pid, "group": str(grp), "phase": "evaluation", "trial_index": 1,
            "decision_time_sec": None if t is None else round(t, 2),
            "clicked": clicked, "trait_anxiety": anxiety, "status": status, "source": "simulated",
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic raw data (pipeline validation only)")
    parser.add_argument("--config", default="configs/config.yaml")
    args = parser.parse_args()
    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))

    records = simulate(cfg)
    out = Path(cfg["data"]["raw_path"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"Wrote {len(records)} simulated records to {out}")


if __name__ == "__main__":
    main()
