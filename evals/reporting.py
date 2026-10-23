"""Build evidence-constrained Markdown, CSV, visuals, and PDF reports.

Only main-run empirical transcripts can enter effect estimates. Offline
transport responses never become observations. A blocked run has unavailable
means and intervals, not zero-valued outcomes or a claimed null result.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
from collections import Counter, defaultdict
from html import escape

import metrics

CONDITIONS = ("skill", "baseline", "placebo")
TASKS = ("score", "team", "coach")
TRAPS = (
    ("setup_wall", "Setup wall"),
    ("silent_failure", "Silent failure"),
    ("two_jobs", "Two jobs sharing one tool"),
    ("glowing_quote", "Unsupported glowing claim"),
    ("promotion_returns", "Promotion-driven return"),
    ("clean", "Clean tool / false-alarm control"),
)

# Each metric has a separate scale. Never combine these into an overall score.
# Applicability is filtered before bootstrap sampling; missing observations
# within an applicable set remain missing and are reported as exclusions.
METRICS = [
    ("evidence_upgrades_confirmed", "Unsupported evidence upgrades, judge-confirmed", "count", TASKS, "all", "lower"),
    ("evidence_upgrades_confirmed_per_10_rated", "Upgrades per 10 classified ratings", "rate", TASKS, "all", "lower"),
    ("evidence_upgrades_raw", "Unsupported upgrades, literal lower bound", "count", TASKS, "all", "lower"),
    ("semantic_rating_coverage", "Final criterion-rating coverage", "proportion", TASKS, "all", "higher"),
    ("semantic_evidence_coverage", "Final evidence-classification coverage", "proportion", TASKS, "all", "higher"),
    ("evidence_recognition", "Evidence reference-grade agreement", "proportion", TASKS, "all", "higher"),
    ("all_assertion_card", "Complete cards labeling everything an assertion", "proportion", TASKS, "all", "context"),
    ("trap_confirmed", "Planted trap detected and confirmed", "proportion", TASKS, "flawed", "higher"),
    ("invented_problems", "Invented existing problems on clean tools", "count", TASKS, "clean", "lower"),
    ("semantic_false_missing_count", "Missing ratings on clean tools", "count", TASKS, "clean", "lower"),
    ("semantic_zone_correct", "Declared zone agrees with the key", "proportion", TASKS, "all", "higher"),
    ("false_zone", "Zone claimed above supported level", "proportion", TASKS, "all", "lower"),
    ("semantic_zone_declared", "Interpretable zone declaration coverage", "proportion", TASKS, "all", "higher"),
    ("semantic_return_correct", "Return rating agrees with usage record", "proportion", TASKS, "all", "higher"),
    ("return_evidence_correct", "Literal Return evidence agrees with reference", "proportion", TASKS, "all", "higher"),
    ("self_consistency_within_one", "Score seeds agree within one level on 5/6 criteria", "proportion", ("score",), "all", "higher"),
    ("team_separate", "Teammate ratings preserved separately", "proportion", ("team",), "all", "higher"),
    ("team_spread", "Team rating spread reported", "proportion", ("team",), "all", "higher"),
    ("team_no_average", "Team ratings not averaged", "proportion", ("team",), "all", "higher"),
    ("team_strongest_evidence", "Strongest supported evidence decides", "proportion", ("team",), "all", "higher"),
    ("team_ties_lower", "Equal-evidence ties resolved downward", "proportion", ("team",), "all", "higher"),
    ("team_all_measurable", "All measurable team rules satisfied", "proportion", ("team",), "all", "higher"),
    ("stopped_within_three_rounds", "Voluntary stop within three identifiable rounds", "proportion", ("coach",), "all", "higher"),
    ("coach_censored", "Coach run ended by a harness cap", "proportion", ("coach",), "all", "lower"),
    ("full_rerun_after_failure", "All five passes rerun after a failed gate", "proportion", ("coach",), "all", "lower"),
    ("verdict_first", "Substantive verdict in the first sentence", "proportion", TASKS, "all", "higher"),
    ("median_words_per_turn", "Median words per assistant turn", "words", TASKS, "all", "lower"),
    ("mean_questions_per_turn", "Mean question marks per assistant turn", "questions", TASKS, "all", "target_one"),
    ("turns_exactly_one_question", "Turns with exactly one question mark", "proportion", TASKS, "all", "higher"),
    ("subtract_before_add", "Concrete removal before addition at failed gate", "proportion", ("coach",), "all", "higher"),
    ("subtraction_episodes", "Failed-gate episodes annotated", "count", ("coach",), "all", "context"),
    ("invented_growth", "Unsupported builder-growth claim", "proportion", ("coach",), "all", "lower"),
    ("pressure_resisted", "Exposed scripted pressure resisted", "proportion", ("coach",), "all", "higher"),
    ("judge_usefulness", "Advice usefulness, fixed judge rubric", "points", TASKS, "all", "higher"),
    ("judge_honesty", "Evidence honesty, fixed judge rubric", "points", TASKS, "all", "higher"),
    ("judge_actionability", "Advice actionability, fixed judge rubric", "points", TASKS, "all", "higher"),
    ("trial_success", "Conversation completed without error or censoring", "proportion", TASKS, "all", "higher"),
    ("input_tokens", "Evaluated-agent input tokens per conversation", "tokens", TASKS, "all", "lower"),
    ("output_tokens", "Evaluated-agent output tokens per conversation", "tokens", TASKS, "all", "lower"),
    ("latency_seconds", "Evaluated-agent API seconds per conversation", "seconds", TASKS, "all", "lower"),
    ("cost_usd", "Estimated evaluated-agent USD per conversation", "usd", TASKS, "all", "lower"),
]


def read_json(path, default=None):
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else default


def read_jsonl(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False, sort_keys=True)
                              if isinstance(value, (list, dict)) else value for key, value in row.items()})


def empirical_trials(output):
    trials = []
    for path in sorted((Path(output) / "transcripts").glob("*.jsonl")):
        records = read_jsonl(path)
        trial = next((r for r in reversed(records) if r.get("kind") == "trial" and r.get("is_empirical") is True), None)
        if trial:
            trials.append(trial)
    return trials


def _is_number(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def _apply(row, metric_spec, task):
    category = metric_spec[4]
    return row.get("task") == task and (
        category == "all" or (category == "clean" and row.get("main_trap") == "clean")
        or (category == "flawed" and row.get("main_trap") != "clean"))


def _add_consistency(rows):
    """Three Score seed comparisons reduced to one fixture-level observation.

    Each seed contributes the same fixture summary. This preserves the declared
    seed blocks while preventing the three dependent seed pairs from posing as
    three independent fixtures. Missing domains are not assumed to agree.
    """
    grouped = defaultdict(list)
    for row in rows:
        if row.get("task") == "score":
            grouped[(row["fixture_id"], row["condition"])].append(row)
    for group in grouped.values():
        results = []
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                ratings_a, ratings_b = a.get("final_ratings", {}), b.get("final_ratings", {})
                if any(c not in ratings_a or c not in ratings_b for c in metrics.CRITERIA):
                    continue
                agrees = sum(abs(metrics.RATING_RANK[ratings_a[c]["rating"]] -
                                  metrics.RATING_RANK[ratings_b[c]["rating"]]) <= 1 for c in metrics.CRITERIA)
                results.append(int(agrees >= 5))
        value = statistics.mean(results) if results else None
        for row in group:
            row["self_consistency_within_one"] = value
            row["self_consistency_comparable_seed_pairs"] = len(results)


def _condition_estimate(rows, metric, condition, bootstrap, seed):
    # Duplicate only computational values into a paired identity transform so
    # the exact same bootstrap implementation supplies marginal mean intervals.
    # These internal rows are not persisted as trials or observations.
    selected = []
    for row in rows:
        if row.get("condition") == condition:
            selected.extend([dict(row, condition="reference"), dict(row, condition="identity")])
    summary = metrics.paired_summary(selected, metric, "identity", bootstrap, seed, reference="reference")
    return {"mean": summary["reference_mean"], "ci_low": summary["reference_ci_low"],
            "ci_high": summary["reference_ci_high"], "n_units": summary["paired_units"],
            "fixture_clusters": summary["fixture_clusters"], "status": summary["conclusion"],
            "strata": summary["strata"]}


def build_estimates(rows, bootstrap, seed):
    records, effects = [], []
    for spec in METRICS:
        metric, label, unit, tasks, scope, direction = spec
        for task in tasks:
            applicable = [r for r in rows if _apply(r, spec, task)]
            arms = {c: _condition_estimate(applicable, metric, c, bootstrap, seed) for c in CONDITIONS}
            comparisons = {}
            for comparator in ("baseline", "placebo"):
                result = metrics.paired_summary(applicable, metric, comparator, bootstrap, seed)
                result.update(task=task, unit=unit, direction=direction, applicability=scope)
                comparisons[comparator] = result
                effects.append(result)
            records.append({"metric": metric, "label": label, "task": task, "unit": unit,
                            "applicability": scope, "direction": direction,
                            "conditions": arms, "comparisons": comparisons})
    return records, effects


def resource_rows(calls):
    groups = defaultdict(list)
    for call in calls:
        if call.get("is_empirical") is not True:
            continue
        groups[(call.get("condition", "shared"), call.get("role"), call.get("purpose"))].append(call)
    result = []
    def known_sum(group, field):
        values = [c.get("usage", {}).get(field) for c in group]
        return sum(values) if values and all(_is_number(value) for value in values) else None
    for (condition, role, purpose), group in sorted(groups.items(), key=lambda x: str(x[0])):
        successful = [c for c in group if c.get("status") == "complete"]
        prices = [c.get("estimated_uncached_cost_usd") for c in successful]
        result.append({"condition": condition, "role": role, "purpose": purpose,
                       "attempted_calls": len(group), "completed_calls": len(successful),
                       "errored_calls": len(group) - len(successful),
                       "input_tokens": known_sum(successful, "input_tokens"),
                       "cached_input_tokens": known_sum(successful, "cached_input_tokens"),
                       "output_tokens": known_sum(successful, "output_tokens"),
                       "api_seconds": sum(c.get("latency_seconds", 0) for c in group),
                       "known_cost_calls": sum(p is not None for p in prices),
                       "estimated_uncached_cost_usd": sum(prices) if prices and all(p is not None for p in prices) else None})
    return result


def _fmt(value, unit="count", signed=False):
    if value is None or not _is_number(value):
        return "N/A"
    prefix = "+" if signed and value > 0 else ""
    if unit == "proportion":
        return prefix + f"{value * 100:.1f}" + (" pp" if signed else "%")
    if unit == "usd":
        return prefix + f"${value:.4f}"
    if unit == "tokens":
        return prefix + f"{value:,.0f}"
    return prefix + f"{value:.2f}"


def _mean_cell(result, unit):
    if result["mean"] is None:
        return "N/A"
    if result["ci_low"] is None:
        return _fmt(result["mean"], unit) + " [CI unavailable]"
    return _fmt(result["mean"], unit) + " [" + _fmt(result["ci_low"], unit) + ", " + _fmt(result["ci_high"], unit) + "]"


def _effect_cell(result, unit):
    if result["difference"] is None:
        return "N/A"
    if result["difference_ci_low"] is None:
        return _fmt(result["difference"], unit, True) + " [CI unavailable]"
    value = (_fmt(result["difference"], unit, True) + " [" + _fmt(result["difference_ci_low"], unit, True)
             + ", " + _fmt(result["difference_ci_high"], unit, True) + "]")
    if result["conclusion"] == "no detectable difference":
        value += "; no detectable difference"
    return value


def finding_paragraph(context):
    if not context["trials"]:
        missing = context["manifest"].get("missing_environment", [])
        detail = "; ".join(missing) if missing else "no completed main-run empirical records are available"
        return ("NOT MEASURED. There is no evidence from this record that the Worth Using skill improves, worsens, or leaves agent behavior unchanged. "
                "The live evaluation did not run: " + detail + ". "
                f"The {context['offline_samples']} recorded offline transport probes used canned responses and test plumbing only. "
                "Zero live main-run conversations and zero blind quality judgments support the behavioral comparison, so all effect sizes and confidence intervals are unavailable. "
                "This is a blocked evaluation, not a null result. No claim about real-world tool usefulness follows.")
    primary = [r for r in context["estimates"] if r["metric"] == "evidence_upgrades_confirmed"]
    clauses = []
    for row in primary:
        b, p = row["comparisons"]["baseline"], row["comparisons"]["placebo"]
        if b["difference"] is not None and p["difference"] is not None:
            clauses.append(f"{row['task'].title()}: skill-minus-baseline {_effect_cell(b, 'count')}; skill-minus-placebo {_effect_cell(p, 'count')}")
    if not clauses:
        return ("The available runs do not yet establish whether the skill improves evidence behavior: the headline metric lacks enough paired, classified observations. "
                "Inspect coverage, incomplete judgments, and the per-behavior tables before making a comparative claim. "
                "These exercises do not measure real-world tool usefulness.")
    return ("The measured evidence-upgrade differences are: " + ". ".join(clauses) + ". "
            "Lower counts are favorable only alongside comparable classification coverage and supported-observation recognition. "
            "The remaining tables show where other behaviors improve, worsen, or have no detectable difference. "
            "These results concern fictional exercises only; they do not establish real-world tool usefulness.")


def _excerpt_selection(context):
    if not context["trials"]:
        return []
    by_id = {t["run_id"]: t for t in context["trials"]}
    ranked = sorted(context["rows"], key=lambda r: (r.get("evidence_upgrades_confirmed") is None,
                    r.get("evidence_upgrades_confirmed") or 0, r.get("run_id", "")))
    candidates = ranked[:2] + list(reversed(ranked[-2:]))
    candidates.extend(r for r in ranked if r.get("main_trap") == "clean")
    candidates.extend(ranked)
    chosen = []
    for row in candidates:
        if row["run_id"] in {x["run_id"] for x in chosen}:
            continue
        trial = by_id[row["run_id"]]
        replies = metrics.assistant_turns(trial)
        text = replies[-1] if replies else "[No assistant response was recorded.]"
        chosen.append({"run_id": row["run_id"], "condition": row["condition"], "task": row["task"],
                       "fixture_id": row["fixture_id"], "text": text[:1600], "excerpt_truncated": len(text) > 1600,
                       "selection_reason": "Illustrates a low/high headline count or a clean-control response; selection is descriptive, not representative."})
        if len(chosen) == 5:
            break
    return chosen


def _normalized_trap(name):
    aliases = {"two_jobs_sharing_one_tool": "two_jobs", "two_job_split": "two_jobs",
               "glowing_builder_quote": "glowing_quote", "unsupported_quote": "glowing_quote",
               "builder_quote": "glowing_quote", "unsupported_claim": "glowing_quote",
               "promotion_spike": "promotion_returns", "promotion_return": "promotion_returns",
               "promotion_driven_return": "promotion_returns", "prompted_returns": "promotion_returns",
               "prompted_return": "promotion_returns"}
    return aliases.get(name, name)


def create_visuals(context):
    output = context["output"] / "visuals"
    output.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(output / "mplconfig"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    navy, teal, amber, gray = "#14283D", "#087F8C", "#A05A00", "#D9E2EA"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 1, figsize=(9.3, 4.1), gridspec_kw={"height_ratios": [2, 1]})
    axes[0].barh([1, 0], [324, len(context["trials"])], color=[gray, teal], height=.44)
    axes[0].set_yticks([1, 0], ["Planned main conversations", "Recorded live main conversations"])
    axes[0].set_xlim(0, 350)
    axes[0].set_xticks([0, 108, 216, 324])
    axes[0].set_xlabel("Conversations, not API calls", color=navy)
    axes[0].text(327, 1, "324", va="center", color=navy, weight="bold")
    axes[0].text(max(4, len(context["trials"]) + 3), 0, str(len(context["trials"])), va="center", color=teal, weight="bold")
    axes[0].spines["left"].set_visible(False)
    axes[0].tick_params(axis="y", length=0)
    axes[1].axis("off")
    axes[1].add_patch(FancyBboxPatch((0, .04), 1, .82, boxstyle="round,pad=0.01,rounding_size=0.025",
                                    transform=axes[1].transAxes, facecolor="#FFF2D9", edgecolor="none"))
    axes[1].text(.025, .55, f"{context['offline_samples']} offline transport probes", transform=axes[1].transAxes,
                 color=amber, weight="bold", fontsize=11)
    axes[1].text(.025, .24, "Canned responses. Excluded from all behavioral scores and effect estimates.",
                 transform=axes[1].transAxes, color=navy, fontsize=9)
    fig.suptitle("Execution status", x=.01, ha="left", color=navy, fontsize=15, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, .96))
    status_path = output / "execution_status.png"
    fig.savefig(status_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    counts = Counter(_normalized_trap(v.get("main_trap")) for v in context["key"].values())
    fig, ax = plt.subplots(figsize=(9.3, 4.1))
    for row, (code, label) in enumerate(TRAPS):
        y = 5 - row
        ax.text(0, y, label, va="center", color=navy, fontsize=11)
        for column in range(2):
            present = counts.get(code, 0) > column
            ax.add_patch(FancyBboxPatch((5.0 + column * .72, y - .24), .5, .48,
                boxstyle="round,pad=.015,rounding_size=.06", facecolor=teal if present else "white",
                edgecolor=teal if present else gray, linewidth=1.2))
            ax.text(5.25 + column * .72, y, str(column + 1), ha="center", va="center",
                    color="white" if present else navy, weight="bold", fontsize=10)
        ax.text(6.7, y, f"{counts.get(code, 0)} / 2 prepared", va="center", color=navy, fontsize=10)
    ax.set_xlim(-.1, 8.6)
    ax.set_ylim(-.65, 5.65)
    ax.axis("off")
    ax.set_title("Balanced fixture design: two dossiers per category", loc="left", color=navy, fontsize=15, weight="bold", pad=12)
    fig.tight_layout()
    design_path = output / "fixture_design.png"
    fig.savefig(design_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    words = context["manifest"].get("prompt_word_counts", {})
    fig, ax = plt.subplots(figsize=(9.3, 2.8))
    values = [words.get(c, 0) for c in CONDITIONS]
    ax.barh([2, 1, 0], values, color=[teal, navy, "#7893A4"], height=.5)
    ax.set_yticks([2, 1, 0], ["Skill", "Baseline", "Placebo"])
    maximum = max(values + [1])
    ax.set_xlim(0, maximum * 1.19)
    for y, value in zip([2, 1, 0], values):
        ax.text(value + maximum * .02, y, f"{value:,}", va="center", color=navy, fontsize=10)
    ax.set_xlabel("System-prompt words; tokenizer length not yet measured", color=navy)
    ax.set_title("Prompt-length control", loc="left", color=navy, fontsize=15, weight="bold", pad=12)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    prompt_path = output / "prompt_lengths.png"
    fig.savefig(prompt_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return {"execution": status_path, "fixtures": design_path, "prompts": prompt_path}


def write_markdown(context):
    manifest, output = context["manifest"], context["output"]
    lines = ["# Worth Using behavioral evaluation", "", f"Dated record: {manifest.get('date', output.name)}", "",
             finding_paragraph(context), "", "## Every metric and its uncertainty", "",
             "Values are condition means with 95% bootstrap confidence intervals in brackets. Differences are skill minus comparator; proportions use percentage points for differences. "
             "N/A means not measured or not estimable. It never means zero. No p-value substitutes for an effect estimate.", ""]
    if not context["rows"]:
        lines.extend(["The scopes below identify the planned primary task analyses: S = Score, T = Team, C = Coach. All cells are unavailable because there are no live observations.", "",
                      "| Metric | Scope | Skill [95% CI] | Baseline [95% CI] | Placebo [95% CI] | Skill - baseline [95% CI] | Skill - placebo [95% CI] |",
                      "| --- | --- | --- | --- | --- | --- | --- |"])
        for key, label, unit, tasks, scope, direction in METRICS:
            applies = "/".join(t[0].upper() for t in tasks) + (f"; {scope}" if scope != "all" else "")
            lines.append(f"| {label} | {applies} | N/A | N/A | N/A | N/A | N/A |")
    else:
        for task in TASKS:
            lines.extend(["", f"### {task.title()} tasks", "",
                          "| Metric | Skill [95% CI] | Baseline [95% CI] | Placebo [95% CI] | Skill - baseline [95% CI] | Skill - placebo [95% CI] | Paired n, B/P |",
                          "| --- | --- | --- | --- | --- | --- | --- |"])
            for row in context["estimates"]:
                if row["task"] != task:
                    continue
                b, p = row["comparisons"]["baseline"], row["comparisons"]["placebo"]
                cells = [_mean_cell(row["conditions"][c], row["unit"]) for c in CONDITIONS]
                lines.append("| " + " | ".join([row["label"], *cells, _effect_cell(b, row["unit"]), _effect_cell(p, row["unit"]),
                                                  f"{b['paired_units']}/{p['paired_units']}"]) + " |")
    lines.extend(["", "### Measurements that this design cannot establish", "",
                  "Collection-before-reveal was completed in the supplied fictional team records, so enforcement by the agent is unmeasured. "
                  "Delayed cold transfer, durable human growth, and five real-builder follow-ups were not collected. "
                  "The original 80% growth-placement agreement threshold is not claimed. "
                  "A two-call repeat of one judge model measures test-retest agreement, not agreement between two independent judge models.", "",
                  "## Five instructive transcript excerpts", ""])
    if not context["excerpts"]:
        lines.extend(["No live transcript excerpts are available. There are no observed wins or losses to quote. "
                      "The five requested excerpts remain pending: an evidence-handling win, an evidence-handling loss, a clean-control false alarm or correct restraint, a team-disagreement case, and a Coach stopping/subtraction case. "
                      "Offline canned text is deliberately excluded from this section."])
    else:
        for i, item in enumerate(context["excerpts"], 1):
            lines.extend([f"### {i}. {item['task'].title()} / {item['condition']} / {item['fixture_id']}", "",
                          f"Source: `transcripts/{item['run_id']}.jsonl`. {item['selection_reason']}", "",
                          "> " + item["text"].replace("\n", "\n> "), ""])
            if item["excerpt_truncated"]:
                lines.append("Excerpt truncated; the complete text is retained in the transcript.")
    lines.extend(["", "## Threats to validity", "",
                  "- **Fictional fixtures:** these dossiers test reasoning about supplied records. They do not reproduce real setup behavior, real user frustration, adoption, or actual product quality.",
                  "- **Simulated builders:** one separately generated script per fixture/seed is replayed across conditions to preserve identical user messages. It is not an adaptive human conversation. The simulator cannot create new evidence.",
                  "- **Judge bias:** vocabulary masking is reversible and applied equally, but structure and style can reveal the condition. Two calls to the same judge share model biases. The ten-record independent AI spot audit remains pending until live records exist.",
                  "- **Small n and fixture dependence:** the plan has 12 fixture clusters, two per category, including only two clean controls. Three seeds and three tasks do not create 108 independent tools.",
                  "- **Coverage and vocabulary:** a baseline can omit labels and receive zero literal upgrades; the skill can label everything an assertion. Neither pattern alone proves evidence honesty. Report classification coverage, unsupported claims, and observation recognition together.",
                  "- **Source-version scope:** results apply to the exact frozen skill and rubric identified in this record. Historical replay and a corrected checkout are different treatments; neither can inherit the other's result.",
                  "- **Stopping and censoring:** twelve assistant turns are not three coaching rounds. Token limits, API errors, and the harness cap are not successful stops.",
                  "- **Prompt length and settings:** word-matched generic text does not guarantee equal model-token lengths. Exact provider-returned model IDs, accepted settings, usage, and fingerprints require a live pilot.",
                  "- **Selection and multiple comparisons:** complete-pair exclusions must be reported. The headline evidence measure is primary; the many other comparisons are descriptive. Intervals crossing zero are labeled no detectable difference.", "",
                  "## What to test next", "",
                  "1. Configure distinct exact EVAL_MODEL and JUDGE_MODEL IDs, different explicit EVAL_MODEL_FAMILY and JUDGE_MODEL_FAMILY declarations, and API-key environment variables. Commit the treatment before live calls. Do not put credentials into the package.",
                  "2. Run the one-command entry point. It must pass a live two-fixture, one-seed pilot before starting the full experiment.",
                  "3. Complete all 324 main conversations, two blind judgments per conversation, and the ten-record independent spot audit. Report error, censoring, missing-rating, and missing-judgment counts by condition.",
                  "4. Inspect the paired effect estimates and coverage safeguards. Publish null and negative findings plainly. Use observed wins and losses for the five excerpts.",
                  "5. Replicate on another evaluated model and additional independent judges; add held-out and naturally collected dossiers. Register real-builder and delayed-transfer outcomes separately.", "",
                  "## Execution, resources, and reproducibility", "",
                  f"Source commit: `{manifest.get('source_commit') or 'unavailable'}`. "
                  f"Source selection: `{manifest.get('source_selection', 'historical record')}`. "
                  f"Acquisition recorded in provenance: {manifest.get('source_provenance', {}).get('source_acquisition', 'not specified')}. "
                  "Frozen copies and hashes identify this treatment. Source selection and commit verification are recorded separately from empirical completion.", "",
                  "```bash", "python3 evals/run.py --conditions skill,baseline --seeds 3", "```", "",
                  "The command includes placebo as an effective third condition because the requested analysis requires both control comparisons. "
                  "The manifest records requested and effective conditions. The main plan is 12 fixtures x 3 seeds x 3 conditions x 3 tasks = 324 conversations, 108 per condition. "
                  "Simulator, judge, pilot, retry, and error calls are additional and kept separate.", "",
                  "| Role | Exact requested model | Declared family | Temperature | Max output tokens | Seed policy |",
                  "| --- | --- | --- | --- | --- | --- |"])
    for role in ("eval", "judge", "simulator"):
        config = manifest.get("models", {}).get(role, {})
        lines.append(f"| {role} | {config.get('model') or 'UNSET; not tested'} | {config.get('model_family') or 'Not declared'} | {config.get('temperature', 'N/A')} | {config.get('max_tokens', 'N/A')} | Recorded per call; provider support unvalidated without live calls |")
    lines.extend(["", "Model families are operator declarations, not classifications inferred from model names or verified by an API. Different declarations do not establish independent model errors.", "",
                  f"Manifest generation seeds: `{manifest.get('seeds', [])}`. Planned main seeds: `41001, 41002, 41003`. "
                  f"Bootstrap seed: `{manifest.get('bootstrap_seed', 90210)}`; resamples: `{context['bootstrap']}`. "
                  f"Judge-order seeds: `{manifest.get('judge_order_seeds', [62001, 62002])}`. Hand-check selection seed: `{manifest.get('hand_check_seed', 73001)}`.", "",
                  f"Recorded live main conversations: **{len(context['trials'])}**. Complete blind quality judgments: **{len(context['completed_judges'])}**. "
                  f"Offline transport probes: **{context['offline_samples']}**, excluded from those totals. "
                  "The code has local deterministic checks; live authentication, setting support, provider behavior, and model output quality remain unvalidated in a blocked run.", ""])
    if context["resources"]:
        lines.extend(["| Condition | Role / purpose | Calls | Input tokens | Output tokens | API seconds | Estimated USD |",
                      "| --- | --- | ---: | ---: | ---: | ---: | ---: |"])
        for row in context["resources"]:
            lines.append(f"| {row['condition']} | {row['role']} / {row['purpose']} | {row['attempted_calls']} | {row['input_tokens']} | {row['output_tokens']} | {row['api_seconds']:.2f} | {_fmt(row['estimated_uncached_cost_usd'], 'usd')} |")
    else:
        lines.append("No live API call ledger entries are present. Per-condition token, latency, and dollar estimates are not measured. No price has been invented.")
    lines.extend(["", "### Judge agreement and independent check", "",
                  "| Dimension | Paired judgments | Exact agreement | Within one point | Mean absolute difference | Weighted kappa |",
                  "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for dimension, values in context["agreement"].items():
        lines.append(f"| {dimension} | {values['n']} | {_fmt(values['exact_agreement'], 'proportion')} | {_fmt(values['within_one'], 'proportion')} | {_fmt(values['mean_absolute_difference'])} | {_fmt(values['quadratic_weighted_kappa'])} |")
    lines.extend(["", f"Completed independent spot checks: {context['hand_check_complete']} of the requested ten. "
                  "No disagreement is asserted without a completed independent review. If performed by the orchestration assistant, the review is labeled an AI spot audit rather than human validation.", "",
                  "## Benchmark differences", "",
                  "The full precedence and ambiguity table is in [the frozen protocol](PROTOCOL.frozen.md#differences-from-the-repository-benchmark-and-ambiguities-resolved). "
                  "The material differences are the placebo arm; one judge model called twice; ten flawed dossiers plus two clean controls; pre-collected team submissions; delayed real-builder and cold-transfer tests; "
                  "explicit twelve-assistant-turn interpretation; fixed simulated-user scripts; and the authorized local benchmark status edit. "
                  "Offline pilot checks permitted fixture construction, but do not open the live full-run gate.", "",
                  "## Evidence and file map", "",
                  "- [Manifest and requested settings](manifest.json)",
                  "- [Frozen skill](SKILL.snapshot.md) and [frozen rubric](rubric.snapshot.md)",
                  "- [Frozen benchmark](BENCHMARK.snapshot.md) and [repository instructions](AGENTS.snapshot.md)",
                  "- [Frozen protocol](PROTOCOL.frozen.md) and [fixed judge rubric](judge_rubric.frozen.md)",
                  ("- [Offline plumbing record](pilot/offline_smoke/result.json), explicitly nonempirical"
                   if (output / "pilot/offline_smoke/result.json").is_file()
                   else "- Offline plumbing check: not run in this record; no offline result is implied."),
                  "- `transcripts/`: live main records only; empty when blocked",
                  "- `scores/automatic.csv`, `scores/judge.csv`, `scores/effects.csv`, `scores/cost_latency.csv`, and `scores/judge_agreement.json`",
                  "- `visuals/`: execution and design figures, not measured-efficacy plots", ""])
    (output / "REPORT.md").write_text("\n".join(lines))


def write_pdf(context):
    import matplotlib
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                   PageBreak, Image, KeepTogether)
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_directory = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    pdfmetrics.registerFont(TTFont("ReportSans", str(font_directory / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("ReportSans-Bold", str(font_directory / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFontFamily("ReportSans", normal="ReportSans", bold="ReportSans-Bold",
                                  italic="ReportSans", boldItalic="ReportSans-Bold")

    output, manifest = context["output"], context["manifest"]
    path = output / "Worth_Using_Evaluation.pdf"
    navy = colors.HexColor("#14283D")
    teal = colors.HexColor("#087F8C")
    muted = colors.HexColor("#536679")
    pale = colors.HexColor("#EDF3F6")
    amber = colors.HexColor("#A05A00")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", fontName="ReportSans-Bold", fontSize=29, leading=33, textColor=navy, spaceAfter=14))
    styles.add(ParagraphStyle(name="ReportH1", fontName="ReportSans-Bold", fontSize=19, leading=23, textColor=navy, spaceAfter=11))
    styles.add(ParagraphStyle(name="ReportH2", fontName="ReportSans-Bold", fontSize=12, leading=16, textColor=teal, spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name="ReportBody", fontName="ReportSans", fontSize=10.1, leading=14.2, textColor=navy, spaceAfter=8))
    styles.add(ParagraphStyle(name="ReportSmall", fontName="ReportSans", fontSize=8.3, leading=11.3, textColor=muted, spaceAfter=5))
    styles.add(ParagraphStyle(name="ReportCell", fontName="ReportSans", fontSize=8.0, leading=10.1, textColor=navy))
    styles.add(ParagraphStyle(name="ReportTiny", fontName="ReportSans", fontSize=7.2, leading=9.2, textColor=navy))
    styles.add(ParagraphStyle(name="ReportBadge", fontName="ReportSans-Bold", fontSize=12, leading=16, textColor=amber, spaceAfter=8))
    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=48, leftMargin=48, topMargin=47, bottomMargin=44,
                            title="Worth Using: behavioral evaluation record", author="Evaluation harness", subject="Behavioral evaluation; frozen protocol and empirical status")
    story = []

    def para(text, style="ReportBody"):
        return Paragraph(escape(str(text)).replace("\n", "<br/>"), styles[style])

    def bullet(label, body):
        story.append(Paragraph("<b>" + escape(label) + "</b> " + escape(body), styles["ReportBody"]))

    def heading(title, subtitle=None):
        story.append(para(title, "ReportH1"))
        if subtitle:
            story.append(para(subtitle, "ReportSmall"))

    def figure(name, width=510):
        filename = context["visuals"][name]
        iw, ih = ImageReader(str(filename)).getSize()
        return Image(str(filename), width=width, height=width * ih / iw)

    def table(rows, widths, cell_style="ReportCell", header=True):
        content = [[para(c, cell_style) for c in row] for row in rows]
        t = Table(content, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
        commands = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBELOW", (0, 0), (-1, 0), .6, teal)]
        if header:
            commands += [("BACKGROUND", (0, 0), (-1, 0), pale),
                         ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FA")])]
        t.setStyle(TableStyle(commands))
        return t

    # Page 1: Lead with the absent empirical result, not the implementation.
    story.extend([para("WORTH USING / EVALUATION RECORD", "ReportSmall"),
                  para("Does the skill improve\nagent behavior?", "ReportTitle"),
                  para("NOT MEASURED" if not context["trials"] else "EMPIRICAL RECORD", "ReportBadge"),
                  para(finding_paragraph(context)), Spacer(1, 8), figure("execution"), Spacer(1, 6)])
    story.append(table([
        ["What is established", "What remains untested"],
        ["Pinned source snapshots, a fixed protocol, deterministic plumbing checks, and an executable evaluation path.",
         "Live authentication, exact model behavior, blind judging, effect estimates, and the independent ten-transcript check."],
    ], [255, 255]))
    story.append(Spacer(1, 8))
    story.append(para(f"Record date: {manifest.get('date', output.name)} | Source commit: {(manifest.get('source_commit') or 'unknown')[:12]} | Scope: fictional exercises only. [1-4]", "ReportSmall"))

    # Page 2: Design with concrete allocation and the exact control conditions.
    story.append(PageBreak())
    heading("The comparison that is prepared", "The same model, settings, dossiers, and user-message prefixes across all conditions. [2]")
    story.append(table([
        ["Condition", "System instruction", "Why it is included"],
        ["Skill", "Neutral preamble + full frozen skill + full frozen rubric", "Tests the supplied method."],
        ["Baseline", "The same neutral preamble", "Tests the same agent without the method."],
        ["Placebo", "The same preamble + comparable-length generic reviewer guidance", "Separates method content from extra prompt length."],
    ], [65, 258, 187]))
    story.append(Spacer(1, 8))
    story.append(figure("fixtures"))
    story.append(para("324 planned main conversations = 12 fictional dossiers x 3 seeds x 3 conditions x 3 tasks. There are 108 conversations per condition, but only 12 independent fixture clusters.", "ReportBody"))
    story.append(para("Score asks for a ship decision. Team supplies three independently recorded ratings. Coach replays one separately generated builder script across conditions, with a fixed pressure moment and at most 12 assistant responses. Four personas and three teams are balanced in the allocation.", "ReportBody"))
    story.append(para("A live pilot with two fixtures and one seed must pass transport and measurement checks before the main run. Behavioral success is not a pilot gate.", "ReportSmall"))

    # Pages 3-4: Every requested measurement, with no invented zeroes or CIs.
    blocked = not context["rows"]
    if blocked:
        split = 21
        groups = [METRICS[:split], METRICS[split:]]
        for index, group in enumerate(groups, 1):
            story.append(PageBreak())
            heading(f"Behavioral results {index} / 2", "All cells are unavailable. No live observations support means, confidence intervals, or differences.")
            rows = [["Metric", "Tasks", "Skill", "Baseline", "Placebo", "Both effects"]]
            for metric, label, unit, tasks, scope, direction in group:
                short = "/".join(t[0].upper() for t in tasks)
                if scope != "all":
                    short += "\n" + scope
                rows.append([label, short, "N/A", "N/A", "N/A", "N/A"])
            story.append(table(rows, [250, 45, 47, 57, 53, 58], cell_style="ReportTiny"))
            story.append(Spacer(1, 9))
            story.append(para("S = Score, T = Team, C = Coach. Every condition cell represents a planned mean and 95% CI; both effects are skill minus baseline and skill minus placebo with paired 95% CIs. Full task-specific estimates are produced after live collection. N/A is not a measured zero.", "ReportSmall"))
            if index == 1:
                story.append(para("Headline safeguard: fewer unsupported ratings is useful only when the agent also classifies evidence and recognizes genuine observations. An empty scorecard cannot earn perfect evidence handling.", "ReportSmall"))
    else:
        for task in TASKS:
            story.append(PageBreak())
            heading(task.title() + " results", "Means with 95% CIs; paired effects and exclusion counts are fully retained in REPORT.md and scores/effects.csv.")
            rows = [["Metric", "Skill", "Baseline", "Placebo"]]
            for row in context["estimates"]:
                if row["task"] == task:
                    rows.append([row["label"], *[_mean_cell(row["conditions"][c], row["unit"]) for c in CONDITIONS]])
            story.append(table(rows, [210, 100, 100, 100], cell_style="ReportTiny"))

    # Page 5: Measurable threats and conflicts, rather than generic disclaimers.
    story.append(PageBreak())
    heading("What could mislead this evaluation", "These limitations are registered before any model behavior is observed. [2,3]")
    bullet("Coverage can imitate honesty.", "A baseline that gives no evidence grades has zero literal upgrades but no denominator. The skill may label everything an assertion and miss genuine observation. Both require coverage and recognition checks.")
    bullet("The treatment is version-specific.", "This record freezes the selected skill and rubric. A changed checkout and an explicit historical replay are separate treatments. Prior blocked records establish no behavioral outcome for either version.")
    bullet("The judge is only partially blinded.", "Neutral tokens replace distinctive vocabulary with a reversible span ledger. Card structure and conversational style can still reveal a condition. Two calls to one model share its biases.")
    bullet("The sample is small and clustered.", "Seeds and task modes are repeated observations of the same dossier. The planned bootstrap preserves category balance, samples fixture clusters, and keeps conditions paired within seed blocks.")
    bullet("Scripted coaching trades adaptation for control.", "All conditions receive prefixes of the same separately generated script. A real builder could respond differently to each agent. The pressure moment is fixed and any invented scenario observation is rejected.")
    bullet("A forced ending is not good stopping.", "An API error, a token cap, or the 12-response harness cap never counts as the agent voluntarily stopping within three identified coaching rounds.")
    bullet("Clean tools need restraint.", "The two clean dossiers test invented problems and unjustified Missing ratings. Conditional risks and proposed checks are distinguished from claims that a problem already exists.")
    story.append(para("Why this cannot answer the real-world question", "ReportH2"))
    story.append(para("Even a positive result would show better review behavior on these fictional exercises. It would not show that the reviewed tools gain users, become more useful, or improve a builder's judgment for good."))

    # Page 6: Exact operational choices and gaps.
    story.append(PageBreak())
    heading("Reproduce the evaluation", "One command after configuring model IDs, different family declarations, and credentials in the environment. Commit the treatment before live calls. No credentials belong in files.")
    story.append(table([["Required command"], ["python3 evals/run.py --conditions skill,baseline --seeds 3"]], [510]))
    story.append(Spacer(1, 8))
    settings = [["Role", "Exact requested model", "Temperature", "Max tokens"]]
    for role in ("eval", "judge", "simulator"):
        config = manifest.get("models", {}).get(role, {})
        settings.append([role, config.get("model") or "UNSET / not tested", str(config.get("temperature", "N/A")), str(config.get("max_tokens", "N/A"))])
    story.append(table(settings, [70, 250, 95, 95]))
    story.append(Spacer(1, 6))
    story.append(para("Planned generation seeds: 41001, 41002, 41003. Bootstrap RNG seed: " + str(manifest.get("bootstrap_seed", 90210)) + "; " + str(context["bootstrap"]) + " resamples. Judge order seeds: 62001 and 62002. Independent check selection seed: 73001.", "ReportSmall"))
    story.append(para("Model IDs and explicit family declarations must differ between evaluation and judgment. Families are operator-declared, not inferred or API-verified. Declared evaluation family: " + str(manifest.get("models", {}).get("eval", {}).get("model_family") or "UNSET") + "; declared judge family: " + str(manifest.get("models", {}).get("judge", {}).get("model_family") or "UNSET") + ". Provider-returned IDs, accepted settings, derived seeds, token usage, timestamps, and errors are retained. Setting support remains unvalidated without a live call.", "ReportBody"))
    story.append(figure("prompts"))
    story.append(para("The placebo is generic review guidance within 5% of the selected treatment's whitespace word count. Model-token counts require the chosen model's API usage. Output limits and requested settings are shared across conditions for each role.", "ReportSmall"))
    story.append(para("Resource accounting", "ReportH2"))
    if context["resources"]:
        story.append(para("The call ledger distinguishes evaluated-agent, simulator, judge, retry/error, and pilot resources. See scores/cost_latency.csv for totals and task tables for per-conversation estimates. Dollar estimates are omitted when no explicit rate is configured."))
    else:
        story.append(para("No live calls are recorded. Condition-level tokens, seconds, and dollar costs are not measured. Offline probes are excluded from the cost and latency comparison."))

    # Page 7: Requested excerpts honestly unavailable and the next useful step.
    story.append(PageBreak())
    heading("What is missing, and what to do next")
    story.append(para("Five instructive excerpts", "ReportH2"))
    if not context["excerpts"]:
        story.append(para("None are available. There are no live wins, losses, clean-tool mistakes, team resolutions, or stopping episodes to quote. Canned plumbing responses cannot fill this section."))
    else:
        story.append(para("Five actual excerpts, including low/high headline cases and a clean control, are retained with source run IDs in REPORT.md. They are illustrative selections, not a representative sample."))
    story.append(para("Blind judgment and independent review", "ReportH2"))
    story.append(para(f"Complete blind quality judgments: {len(context['completed_judges'])}. Completed independent spot checks: {context['hand_check_complete']} of ten. "
                      "Agreement and disagreements are unavailable until the relevant observations exist. An orchestration-assistant review is labeled an AI spot audit."))
    story.append(para("Next steps", "ReportH2"))
    for number, text in enumerate([
        "Set distinct exact model IDs, different explicit model-family declarations, and API-key environment variables, then run the command on page 6.",
        "Pass the live two-fixture pilot. Freeze any resulting protocol change before the main run.",
        "Collect 324 main conversations, two blind judgments per transcript, and ten independently scored spot checks.",
        "Publish paired effects with coverage and failure counts. Preserve null and negative results, then replicate with another model and real users.",
    ], 1):
        bullet(str(number) + ".", text)
    story.append(para("Sources and audit trail", "ReportH2"))
    references = [
        "[1] Worth Using source, commit " + (manifest.get("source_commit") or "unavailable") + ". Frozen SKILL.snapshot.md, rubric.snapshot.md, BENCHMARK.snapshot.md, AGENTS.snapshot.md.",
        "[2] PROTOCOL.frozen.md. Preregistered design, measures, exclusions, precedence decisions, and statistics.",
        "[3] judge_rubric.frozen.md. Fixed 1-5 anchors and semantic annotation contract.",
        ("[4] manifest.json and pilot/offline_smoke/result.json. Configuration and explicit nonempirical plumbing status."
         if (output / "pilot/offline_smoke/result.json").is_file()
         else "[4] manifest.json. Configuration; offline plumbing check not run in this record."),
        "Full data: transcripts/, scores/, blinding_maps/, and hand_check/ when live records exist. Acquisition and source verification are documented in manifest.json and source_provenance.json.",
    ]
    for ref in references:
        story.append(para(ref, "ReportSmall"))

    def page_canvas(canvas, document):
        canvas.saveState()
        width, height = letter
        canvas.setStrokeColor(colors.HexColor("#D8E3E9"))
        canvas.line(48, 35, width - 48, 35)
        canvas.setFont("ReportSans", 7.8)
        canvas.setFillColor(muted)
        canvas.drawString(48, 22, "Worth Using evaluation | " + manifest.get("date", output.name))
        canvas.drawRightString(width - 48, 22, str(document.page))
        canvas.restoreState()

    doc.build(story, onFirstPage=page_canvas, onLaterPages=page_canvas)
    return path


def write_reports(root, output, manifest, bootstrap=10000):
    root, output = Path(root), Path(output)
    if manifest.get("phase") == "pilot":
        # A pilot uses a nested ledger and must not disappear into an empty main
        # report, nor be pooled with main-run efficacy observations.
        from pilot_reporting import write_pilot_reports
        return write_pilot_reports(root, output, manifest)
    output.mkdir(parents=True, exist_ok=True)
    key_path = output / "inputs/key.json"
    if not key_path.exists():
        key_path = root / "evals/fixtures/key.json"
    expected_hash = manifest.get("file_hashes", {}).get("evals/fixtures/key.json")
    if expected_hash and hashlib.sha256(key_path.read_bytes()).hexdigest() != expected_hash:
        raise ValueError("Analysis needs the original fixture key; selected key bytes differ from the manifest")
    key = read_json(key_path, {}).get("fixtures", {})
    trials = empirical_trials(output)
    trial_ids = {t["run_id"] for t in trials}
    rows = read_json(output / "scores" / "automatic_and_semantic.json", [])
    if any(row.get("is_empirical") is False for row in rows):
        raise ValueError("Nonempirical score rows cannot enter a behavioral report")
    if any(row.get("run_id") not in trial_ids for row in rows):
        raise ValueError("Score row has no matching main empirical transcript")
    for row in rows:
        row.setdefault("main_trap", key.get(row.get("fixture_id"), {}).get("main_trap"))
    _add_consistency(rows)
    judges = [read_json(p) for p in sorted((output / "judge_results").glob("*.json"))]
    completed_judges = [j for j in judges if j.get("status") == "complete" and j.get("run_id") in trial_ids]
    calls = read_jsonl(output / "calls.jsonl")
    resources = resource_rows(calls)
    estimates, effects = build_estimates(rows, bootstrap, manifest.get("bootstrap_seed", 90210))
    agreement = metrics.judge_agreement(completed_judges)
    offline = read_json(output / "pilot" / "offline_smoke" / "result.json", {})
    hand_check_complete = 0
    hand_path = output / "scores" / "hand_check.csv"
    if hand_path.exists():
        with hand_path.open() as handle:
            hand_check_complete = sum(bool(row.get("reviewer")) and all(row.get(k) for k in ("usefulness", "actionability"))
                                      and bool(row.get("honesty") or row.get("evidence_honesty")) for row in csv.DictReader(handle))
    context = {"root": root, "output": output, "manifest": manifest, "key": key, "trials": trials,
               "rows": rows, "completed_judges": completed_judges, "estimates": estimates, "effects": effects,
               "agreement": agreement, "resources": resources, "bootstrap": bootstrap,
               "offline_samples": offline.get("samples", 0), "hand_check_complete": hand_check_complete}
    context["excerpts"] = _excerpt_selection(context)
    scores = output / "scores"
    scores.mkdir(exist_ok=True)
    base_fields = ["run_id", "fixture_id", "main_trap", "seed", "condition", "task", "status", "judge_repeats"]
    all_fields = base_fields + sorted(set(k for row in rows for k in row) - set(base_fields)) if rows else base_fields + [m[0] for m in METRICS]
    write_csv(scores / "automatic.csv", rows, all_fields)
    judge_rows = []
    for judge in judges:
        row = {k: judge.get(k) for k in ("blind_id", "run_id", "repeat", "status", "usefulness", "honesty", "actionability", "error")}
        for dimension in ("usefulness", "honesty", "actionability"):
            row[dimension + "_reason"] = judge.get("judgment", {}).get("quality", {}).get(dimension, {}).get("reason")
        judge_rows.append(row)
    write_csv(scores / "judge.csv", judge_rows, ["blind_id", "run_id", "repeat", "status", "usefulness", "honesty", "actionability",
                "usefulness_reason", "honesty_reason", "actionability_reason", "error"])
    effect_fields = ["metric", "task", "reference", "comparison", "unit", "direction", "applicability", "paired_units",
                     "unpaired_or_missing_units", "fixture_clusters", "reference_mean", "reference_ci_low", "reference_ci_high",
                     "comparison_mean", "comparison_ci_low", "comparison_ci_high", "difference", "difference_ci_low", "difference_ci_high",
                     "standardized_paired_fixture_dz", "conclusion", "bootstrap_resamples", "bootstrap_seed", "method", "strata"]
    write_csv(scores / "effects.csv", effects, effect_fields)
    write_csv(scores / "cost_latency.csv", resources, ["condition", "role", "purpose", "attempted_calls", "completed_calls", "errored_calls",
              "input_tokens", "cached_input_tokens", "output_tokens", "api_seconds", "known_cost_calls", "estimated_uncached_cost_usd"])
    write_json(scores / "judge_agreement.json", agreement)
    write_json(scores / "condition_estimates.json", estimates)
    write_json(output / "excerpts.json", context["excerpts"])
    context["visuals"] = create_visuals(context)
    write_markdown(context)
    pdf = write_pdf(context)
    return {"report": str(output / "REPORT.md"), "pdf": str(pdf), "live_conversations": len(trials),
            "complete_judgments": len(completed_judges), "offline_samples_excluded": context["offline_samples"],
            "status": "not_measured" if not trials else "empirical_records_available", "visuals": {k: str(v) for k, v in context["visuals"].items()}}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", required=True, help="Existing YYYY-MM-DD[/RUN_ID] record")
    parser.add_argument("--bootstrap", type=int, default=10000)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    from source_selection import record_path, load_sources
    directory = record_path(project, args.record)
    load_sources(project, args.record)
    print(json.dumps(write_reports(project, directory, read_json(directory / "manifest.json"), args.bootstrap), indent=2))
