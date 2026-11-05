"""Entry point: raw log -> processed tables -> statistical tests -> figures.

Usage:
    python src/main.py --config configs/config.yaml
"""
import argparse
import json
import logging
import sys

import matplotlib

matplotlib.use("Agg")  # file output only (headless-safe); must be set before importing visualize

import numpy as np  # noqa: E402

from process_data import load_config, run_pipeline
from visualize import run_all  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Urgency-trigger phishing experiment: analysis pipeline")
    parser.add_argument("--config", default="configs/config.yaml", help="Path to YAML config")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    logging.getLogger("fontTools").setLevel(logging.WARNING)  # silence font-subsetting chatter
    log = logging.getLogger("experiment")

    cfg = load_config(args.config)
    np.random.seed(cfg["experiment"]["random_seed"])

    log.info("Running pipeline on %s", cfg["data"]["raw_path"])
    result = run_pipeline(cfg)
    log.info("Rows: raw=%d | warm-up dropped=%d | evaluation=%d | valid=%d",
             result["n_raw_rows"], result["n_warmup_dropped"], result["n_evaluation_rows"], result["n_valid"])
    log.info("Data source label(s): %s", result["data_source"])
    for rec in result["guardrails"]:
        log.info("Guardrail | group=%s invalid_rate=%.3f ok=%s", rec["group"], rec["invalid_rate"], rec["guardrail_ok"])
    log.info("Tests: %s", json.dumps(result["tests"], default=str))

    paths = run_all(cfg)
    log.info("Saved %d figure files to %s", len(paths), cfg["data"]["figures_dir"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
