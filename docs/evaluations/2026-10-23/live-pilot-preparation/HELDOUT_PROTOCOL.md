# Private held-out evaluation addendum

Prepared 2026-10-23, before any live outcome. This is a proposed preregistration for review and implementation before the full run. It contains no results and no private fixture text. The pilot must stop for a cost review; this document does not authorize the full run.

## Cohorts and execution gate

The source treatment is the corrected 0.1.2 skill and rubric from main at `8a3a3ac5c26b007d592c0f423f74b52c157e00e9`. The recipe is not injected into either experimental system prompt. The system-prompt comparison remains skill versus baseline and skill versus the length-matched placebo, with all other settings and user messages paired.

| Cohort | Fixtures | Seeds | Conditions | Tasks | Conversations | Purpose |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Public pilot | 2 | 1 | 3 | 3 | 18 | Transport, measurement and cost calibration |
| Public development | 12 | 3 | 3 | 3 | 324 | Development-set behavior, reported separately |
| Private held-out | 4 | 3 | 3 | 3 | 108 | Required support for any headline comparison |

The planned full comparison therefore contains 432 conversations and 864 completed judge reviews, excluding the pilot, simulator calls, errors and retries. A conversation can contain several evaluated-agent calls. Never describe 432 conversations as 432 independent observations: the held-out cohort has only four independent fixture clusters.

Run the requested pilot command first:

```bash
python3 evals/run.py --conditions skill,baseline --seeds 1 --pilot
```

The runner includes placebo as the effective third condition. After the pilot, report provider-returned exact model IDs, settings accepted at the request level, usage, per-conversation cost, errors and the projected full-run cost. API acceptance does not demonstrate that a seed guarantees reproducibility or that the provider independently echoed every requested setting. Stop for the user's cost review before any full-run call. A missing model ID or credential is a blocked pilot, not a null result or a measured zero cost.

Use Claude for the evaluated agent and an OpenAI model for judgment; leave the simulator model at its existing default, which follows the evaluated model. Credentials remain in environment variables only. Reject a role assignment that does not meet the user's model-family requirement rather than substituting a convenient model.

## Private freeze and access

Author and validate four new fictional dossiers before inspecting pilot behavioral outcomes. Freeze the dossiers, answer key, team submissions, assignments, observation dates and analysis addendum with content hashes and a UTC timestamp. Retain the private bytes outside the public Git checkout. A public commitment can identify the private package by a manifest digest, count and source version; it must not contain the dossiers, keys, simulator scripts or revealing excerpts. Never copy private inputs into a publicly committed run directory by default.

The evaluated agent receives only the appropriate dossier and scripted task messages, never the answer key or condition label. The builder simulator receives the corresponding persona and dossier, never the key or treatment. Use the same frozen simulator script across the three conditions for each fixture and seed. Hold-out authoring and software validation are not evaluation-model exposure. Record any accidental exposure or later fixture change; a revised fixture is a new hold-out version, not a repair to an already tested set.

Do not tune prompts, scoring definitions, thresholds or fixture content in response to held-out outcomes. If a plumbing error invalidates a run, retain the failed attempt and document the reason before a new version is run. Do not replace a difficult but valid fixture. Private fixtures can stay private while aggregate results are public. Publishing held-out transcript excerpts would disclose their contents; use real public-development transcripts for the public five excerpts unless the user separately authorizes release of private material.

## Headline rule and safeguards

The headline measure remains judge-confirmed unsupported evidence upgrades. Use the two blind passes' agreement rule from the frozen protocol; unresolved annotations remain unresolved, not fractional events or zero errors. Publish literal counts separately as a lower bound. The primary held-out summary gives each fixture equal weight, then each seed and the three tasks equal weight within that fixture. Report all task-specific effects as well.

A positive headline that the skill improved evidence behavior requires all of the following on the four held-out fixtures, for **both** skill-minus-baseline and skill-minus-placebo:

1. The paired 95% interval for mean unsupported upgrades is entirely below zero, and the corresponding interval for upgrades per ten classified ratings is entirely below zero. Count reduction alone cannot establish improvement.
2. Final criterion-rating coverage and final evidence-classification coverage each average at least five of six criteria in **every condition and task**. For both coverage measures, the paired lower 95% bound for skill minus comparator is at least zero. This is a conservative no-loss gate, not a post-hoc noninferiority margin.
3. Fixed-denominator supported-observation recognition in the skill condition is at least five sixths, and its paired lower 95% difference bound is at least zero against both comparators. Define this recognition as the proportion of final criterion slots whose frozen key has a supporting outside-use observation that the response correctly recognizes with a supported observation-level classification. The denominator includes omitted and ambiguous slots; those are unrecognized. A classification above its support ceiling is not recognition. Also report exact reference-grade agreement over all six slots, with omissions counted as nonagreement.
4. All four held-out fixture clusters and all planned seeds/tasks contribute to the complete primary paired comparison. Missing conversations, unresolved primary annotations or missing judge passes block the positive headline until resolved under a logged, condition-blind adjudication rule. Never remove a bad or silent response to improve coverage.

The coverage and recognition thresholds above are conservative premeasurement design choices, not thresholds taken from the original benchmark. Freeze their final accepted version before the full run. The existing `evidence_recognition` statistic is conditional on emitted grades; retain that statistic under its existing name, and add the fixed-denominator version as a separate measure rather than silently changing its meaning. A transcript with no classified ratings has an undefined upgrade rate, zero classification coverage and zero fixed-denominator recognition when observed opportunities exist. It cannot count as perfectly honest.

Put upgrades, classified-rating denominators, both coverage measures, fixed-denominator recognition, all-assertion-card frequency and missingness immediately adjacent in the headline table. List task and fixture directions so an aggregate improvement cannot obscure a negative subgroup. A development-set win without the held-out gates is reported as **no demonstrated held-out improvement**. A zero-crossing effect interval is **no detectable difference**. An interval favoring a comparator is a negative result for the skill. Failure to demonstrate a difference is not evidence of equivalence, and failure of a coverage gate is not proof the skill is worse.

## Intervals, agreement and limits

For the held-out cohort, use 10,000 hierarchical paired bootstrap draws with the recorded RNG seed: sample the four fixture clusters with replacement, then seed blocks within each selected fixture, carrying all conditions and tasks together. Do not stratify these four fixtures into one-fixture trap categories: that would suppress fixture resampling and make the interval mostly describe seed variation. Keep category labels for reporting; retain the existing category-stratified approach for the separately reported public development set. Never pool the public and private cohorts for the headline or use development cases to narrow its interval.

Report condition means, 95% intervals, skill-minus-comparator differences in natural units, paired sample sizes and fixture counts. Standardized effects are supplementary and undefined when the required variance is zero. These bootstrap intervals are descriptive and unstable with four clusters. Show the four fixture-level effects and leave-one-fixture-out aggregate effects as a sensitivity check. Neither 108 held-out conversations nor narrow Monte Carlo intervals remove the small-fixture limitation. The many secondary behavior intervals are pointwise, not simultaneous evidence that every benchmark behavior improved.

Mask condition labels and distinctive vocabulary before judging and retain a reversible map privately. Masking reduces obvious cues but cannot ensure the judge cannot infer a condition from structure. Calling one OpenAI judge twice measures repeated-judge agreement; it does not provide two independent judge models or establish freedom from family bias. Report exact and within-one-point agreement, absolute differences and weighted kappa by quality dimension where defined. Hand-check ten randomly selected actual transcripts with an independently recorded first judgment; identify an orchestration-assistant review as an AI spot audit. Preserve disagreements.

The public report's five excerpts must come from actual completed transcripts, include wins and losses when present, and cite their run IDs. If there are no live transcripts, publish no substitute excerpts. Later real-tool work needs two or three actual tools with genuine usage records supplied or authorized by the user. Keep that cohort and its consent/privacy rules separate from fictional fixtures; do not invent it to fill the plan.

## Explicit overrides and remaining implementation work

The latest user instruction changes the original benchmark plan in four respects: the twelve public fixtures are a development set; four private fixtures determine headline support; the live pilot requires a cost-review stop before the full run; and the evaluated and judging models must come from Claude and OpenAI respectively. The requested two calls to one judge remain repeated-judge reliability, whereas `docs/BENCHMARK.md` describes two judges. The original benchmark's five real builders, cold-transfer learning and independently validated growth remain unmeasured; the requested later two or three real tools are a separate follow-up, not a fictional proxy.

Before full execution, implement and verify private-cohort input/output isolation, fixed-denominator recognition, cohort-specific bootstrap selection, claim gates and public-export filtering. This addendum alone does not claim those capabilities exist in the current runner. Freeze the implemented code and final addendum together, then rerun the pilot only if the changed plumbing requires it. Keep all pilot records out of the full-run estimates.
