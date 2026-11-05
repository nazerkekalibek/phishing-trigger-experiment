# Methodology Passport Card (revised for Task 3)

## 1. Project Information

| Field | Value |
|---|---|
| **Title** | Urgency Triggers and Phishing Susceptibility in Telegram: A Reproducible Experiment Pipeline |
| **Authors** | Nazerke Kalibek (individual work) |
| **GitHub repository** | https://github.com/nazerkekalibek/phishing-trigger-experiment |

## 2. Research Type

**Quantitative: controlled between-subjects experiment.**
The research question concerns the effect of one manipulated factor (message type: urgency trigger vs. neutral) on two numerically measurable outcomes: decision time in seconds and a binary click outcome. Participants are **randomly assigned** to one of two independent groups, so differences between groups can be attributed to the manipulation rather than to who ended up in which group. Groups are compared with standard statistical tests, which makes a quantitative design the natural fit. Qualitative comments collected at debriefing may complement the results, but the hypotheses are tested quantitatively.

## 3. Hypotheses

The earlier single hypothesis combined two outcomes. It is now split so that each hypothesis has **one outcome, one test and one direction**.

**H1a: decision time (secondary)**
- **H0a:** Decision time under an urgency trigger is not shorter than under a neutral message.
- **H1a:** Decision time under an urgency trigger is shorter than under a neutral message.

**H1b: link click (primary)**
- **H0b:** The probability of clicking the link under an urgency trigger is not higher than under a neutral message.
- **H1b:** The probability of clicking the link under an urgency trigger is higher than under a neutral message.

The hypotheses are directional (grounded in the affect heuristic and prior urgency findings), therefore the tests are **one-sided** in the same direction, so the hypothesis and the test now agree.

## 4. Variable Matrix

| Type | Variable | Operationalization |
|---|---|---|
| **Independent (IV)** | Message type | Two levels: `urgent` (e.g., "account will be blocked in 10 minutes") vs. `neutral` (informational text of the same length) |
| **Dependent (DV1)** | Decision time | Seconds from message display to the participant's decision (tap / ignore) |
| **Dependent (DV2)** | Link click | Binary: 1 = would tap the link, 0 = would not |
| **Controlled (CV)** | Assignment | Random assignment to groups; same instructions for everyone |
| **Controlled (CV)** | Device and interface | Mobile screen, identical Telegram mockup layout |
| **Controlled (CV)** | Message structure | Same sender name, same link domain pattern, same message length (±10 %) |
| **Controlled (CV)** | Warm-up | Every participant first sees one neutral practice message (discarded) |
| **Controlled (CV)** | Software | Python 3.12.3; exact library pins in `requirements.txt`; random seed 42 |
| **Covariate (recorded)** | Trait anxiety | Spielberger–Hanin scale (20–80 points), used for stratified checks |

## 5. Metrics and Baseline

| Item | Description |
|---|---|
| **Primary metric** | Click rate per group (H1b), reported with a bootstrap 95 % CI; tested with a **one-sided Fisher's exact test** (`greater`). |
| **Secondary metrics** | Median decision time per group (H1a) with bootstrap 95 % CI, p25–p75, p95, p99; tested with a **one-sided Mann–Whitney U** (`less`). Effect sizes: risk difference, median difference, Cliff's δ. |
| **Multiple testing** | Two tests are run, so each is compared with the **Bonferroni-adjusted α = 0.05 / 2 = 0.025**. |
| **Guardrail metrics** | (1) **Error rate:** share of invalid evaluation rows per group ≤ 10 % (invalid = status not `ok`, missing value, or time outside [1, 120] s). (2) Relative group-size imbalance ≤ 30 %. (3) Click column strictly binary. (4) Ethics: static mockups only, no real links, no credentials, informed consent, right to withdraw, debriefing. |
| **Baseline (control group)** | Participants receiving the neutral informational message with identical layout, sender and link pattern. |

## 6. Limitations (stated honestly)

- **The repository currently contains simulated data** (`"source": "simulated"` in every record). It validates the pipeline and supports no scientific conclusion about real users.
- Mockup-based clicking measures intention in a safe setting and may differ from real-world behavior.
- One evaluation message per participant limits statistical power; the tail percentiles (p95, p99) are rough estimates at this sample size.
- Exclusion rules (time window) are fixed in advance in `configs/config.yaml`; the number excluded per group is always reported.
