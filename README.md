# Urgency Triggers and Phishing Susceptibility in Telegram: A Reproducible Experiment Pipeline

**Author:** Nazerke Kalibek (GitHub: [@nazerkekalibek](https://github.com/nazerkekalibek))
**Course:** Research Methods
**Status:** Week 6 — measurement skeleton tested on a synthetic sample; real data collection planned for Week 7.

## Research Question

> **RQ2.** How do high-intensity emotional triggers (threat of account blocking, urgency) affect decision time and the probability of clicking a phishing link in a Telegram-style message?

| | Statement |
|---|---|
| **H0** | An urgency/fear trigger affects neither decision time nor the probability of clicking the link. |
| **H1** | Under a high-intensity urgency/fear trigger, decision time is shorter and the probability of clicking is higher than under a neutral message. |

## Overview

Participants view screenshot-style mockups of Telegram messages (no real links, no real phishing infrastructure). One group sees a message with a high-intensity urgency/fear trigger (e.g., "your account will be blocked in 10 minutes"), the control group sees a neutral informational message. For each participant we record the decision time and whether they would tap the link.

This repository contains the **analysis pipeline**: it validates incoming data against guardrails, computes the primary and secondary metrics, runs the statistical tests, and writes a log and a JSON summary.

> ⚠️ The file in `data/sample/` is **synthetic** (10 rows) and exists only to verify that the pipeline runs end-to-end. Its results carry no scientific meaning.

## Variables and Metrics

| Role | Variable |
|---|---|
| Independent (IV) | Message type: `urgent` (high-intensity trigger) vs. `neutral` |
| Dependent (DV) | Click on link (0/1); decision time (seconds) |
| Controlled | Mobile device, identical Telegram mockup layout, same sender name/domain pattern, time-of-day window; recorded covariate: trait anxiety (Spielberger–Hanin) |
| **Primary metric** | Click rate per group (Fisher's exact test, two-sided, α = 0.05) |
| Secondary metric | Median decision time per group (Mann–Whitney U, two-sided) |
| Guardrails | Decision time within [1, 120] s; no missing values; binary click column; group-size imbalance ≤ 30 %; mockups only, informed consent, right to withdraw |
| Baseline | Control group receiving the neutral message |

## Planned Benchmarks

| ID | Comparison | Metric | Test | Week |
|---|---|---|---|---|
| B1 | `urgent` vs. `neutral` | Click rate (primary) | Fisher's exact | 7 |
| B2 | `urgent` vs. `neutral` | Median decision time | Mann–Whitney U | 7 |
| B3 | Anxiety-stratified subgroups | Click rate | Stratified comparison | 7–8 |
| B4 | Mixed chat vs. isolated work channel (RQ1) | Recognized indicators | To be defined | Future work |

## System Requirements

- Python 3.12 (or Docker)
- Dependencies pinned in `requirements.txt` (`numpy==2.4.4`, `pandas==3.0.2`, `scipy==1.17.1`, `PyYAML==6.0.3`)

## Quickstart Guide

**Option A — Docker (recommended, 2 commands):**

```bash
docker build -t phishing-trigger-experiment .
docker run --rm phishing-trigger-experiment
```

**Option B — local Python (3 commands):**

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/main.py --config configs/config.yaml
```

Expected output: a log in the console and in `results/run.log`, plus `results/summary.json` with the click rates, median times, p-values and H0 decisions.

## Repository Structure

```
phishing-trigger-experiment/
├── README.md
├── LICENSE
├── Dockerfile
├── requirements.txt          # exact version pins
├── .gitignore
├── configs/
│   └── config.yaml           # all experiment parameters
├── src/
│   └── main.py               # validation + metrics + statistical tests
├── data/
│   └── sample/
│       └── responses_sample.csv   # synthetic 10-row sample
├── notebooks/                # exploratory analysis (Week 7+)
├── docs/
│   └── methodology_card.md   # methodology passport card
└── results/                  # generated logs/summaries (git-ignored)
```

## Ethics

Only static mockups are shown; no real phishing links are used and no credentials are collected. Participants give informed consent, may stop at any time, and are debriefed that all messages were part of a training exercise.

## Citation / License

Released under the [MIT License](LICENSE). If you use this pipeline, please cite:

```
Kalibek, N. (2026). Urgency Triggers and Phishing Susceptibility in Telegram:
A Reproducible Experiment Pipeline. GitHub repository.
https://github.com/nazerkekalibek/phishing-trigger-experiment
```
