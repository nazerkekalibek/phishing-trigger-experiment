# Methodology Passport Card

## 1. Project Information

| Field | Value |
|---|---|
| **Title** | Urgency Triggers and Phishing Susceptibility in Telegram: A Reproducible Experiment Pipeline |
| **Authors** | Nazerke Kalibek (individual work) |
| **GitHub repository** | https://github.com/nazerkekalibek/phishing-trigger-experiment |

## 2. Research Type

**Quantitative (controlled between-subjects experiment).**
The research question concerns the effect of one manipulated factor (trigger intensity) on two numerically measurable outcomes (decision time in seconds and a binary click outcome). Two independent groups are compared with standard statistical tests, which makes a quantitative design the natural fit. Qualitative follow-up (open comments after debriefing) may complement it later, but the hypothesis is tested quantitatively.

## 3. Hypotheses (from Task 1, refined in Week 5)

- **H0:** A high-intensity urgency/fear trigger in a Telegram-style message affects neither the decision time nor the probability of clicking the link, compared with a neutral message.
- **H1:** Under a high-intensity urgency/fear trigger, decision time is shorter and the probability of clicking the link is higher than under a neutral message.

## 4. Variable Matrix

| Type | Variable | Operationalization |
|---|---|---|
| **Independent (IV)** | Trigger intensity | Two levels: `urgent` (e.g., "account will be blocked in 10 minutes") vs. `neutral` (informational text of the same length) |
| **Dependent (DV1)** | Decision time | Seconds from message display to the participant's decision (tap / ignore) |
| **Dependent (DV2)** | Link click | Binary: 1 = would tap the link, 0 = would not |
| **Controlled (CV)** | Device and interface | Mobile screen, identical Telegram mockup layout |
| **Controlled (CV)** | Message structure | Same sender name, same link domain pattern, same message length (±10 %) |
| **Controlled (CV)** | Testing conditions | Fixed time-of-day window, same instructions for all participants |
| **Controlled (CV)** | Software environment | Python 3.12.3; numpy 2.4.4, pandas 3.0.2, scipy 1.17.1, PyYAML 6.0.3; fixed random seed 42 |
| **Covariate (recorded)** | Trait anxiety | Spielberger–Hanin scale, used for subgroup checks |

## 5. Metrics and Baseline

| Item | Description |
|---|---|
| **Primary metric** | Click rate per group (share of participants who clicked). Tested with Fisher's exact test, two-sided, α = 0.05. H0 is rejected for the claim "triggers raise clicks" only if this test is significant. |
| **Secondary metric** | Median decision time (s) per group, tested with Mann–Whitney U (non-parametric because reaction-time data are typically skewed and samples are small). |
| **Guardrail metrics** | (1) Decision time must lie within [1, 120] s, otherwise the row is excluded as accidental or abandoned. (2) No missing values in required columns. (3) Click column strictly binary. (4) Relative group-size imbalance ≤ 30 %. (5) Ethical guardrail: static mockups only, no real links, no credentials collected, informed consent, right to withdraw, debriefing. |
| **Baseline (control group)** | Participants who receive the neutral informational message with identical layout, sender and link pattern. Differences are interpreted only relative to this group. |

## 6. Limitations (stated honestly)

- The sample in `data/sample/` is synthetic (10 rows) and only proves that the pipeline runs; it supports no scientific conclusion.
- Mockup-based clicking measures intention in a safe setting and may differ from real-world behavior.
- Small samples reduce statistical power; planned sample size for Week 7 will be fixed in advance in `configs/config.yaml`.
