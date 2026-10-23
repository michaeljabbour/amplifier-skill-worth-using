"""Pilot-only resource report. Pilot observations never enter efficacy estimates.

All measurements come from pilot/live. A missing ledger means unmeasured, not
zero usage. Optional pilot/pricing.json may add sourced prices after model IDs
are returned; it must not contain credentials. Its models mapping is keyed by
the exact returned model ID, with input/output_usd_per_million and source_url.
"""
from __future__ import annotations

from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import statistics
from xml.sax.saxutils import escape

CONDITIONS = ("skill", "baseline", "placebo")
TASKS = ("score", "team", "coach")
FIELDS = ("input_tokens", "output_tokens", "latency_seconds", "cost_usd")


def read_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def total(values):
    values = list(values)
    return sum(values) if values and all(number(v) for v in values) else None


def fmt(value, money=False):
    if value is None:
        return "Not measured" if not money else "Unavailable"
    return f"${value:,.4f}" if money else f"{value:,.2f}"


def priced_call(call, manifest, pricing):
    result = dict(call)
    result["cost_usd"] = call.get("estimated_uncached_cost_usd")
    result["pricing_basis"] = "configured input/output rates, uncached estimate" if result["cost_usd"] is not None else None
    rates = pricing.get("models", {}).get(call.get("model_returned"), {})
    if rates and rates.get("source_url"):
        input_rate, output_rate = rates.get("input_usd_per_million"), rates.get("output_usd_per_million")
        usage = call.get("usage", {})
        if all(number(v) and v >= 0 for v in (input_rate, output_rate, usage.get("input_tokens"), usage.get("output_tokens"))):
            result["cost_usd"] = (usage["input_tokens"] * input_rate + usage["output_tokens"] * output_rate) / 1_000_000
            result["pricing_basis"] = "sourced uncached estimate: " + rates["source_url"]
    return result


def aggregate(calls):
    # Errors may have incurred a charge without returning usage. Do not zero-fill.
    return {
        "attempted_calls": len(calls),
        "completed_calls": sum(c.get("status") == "complete" for c in calls),
        "errored_calls": sum(c.get("status") != "complete" for c in calls),
        "input_tokens": total(c.get("usage", {}).get("input_tokens") for c in calls),
        "output_tokens": total(c.get("usage", {}).get("output_tokens") for c in calls),
        "latency_seconds": total(c.get("latency_seconds") for c in calls),
        "cost_usd": total(c.get("cost_usd") for c in calls),
    }


def pilot_data(output, manifest):
    folder = output / "pilot/live"
    pricing = read_json(output / "pilot/pricing.json", {})
    calls = [priced_call(c, manifest, pricing) for c in read_lines(folder / "calls.jsonl") if c.get("is_empirical") is True]
    trials = []
    for path in sorted((folder / "transcripts").glob("*.jsonl")):
        trial = next((r for r in reversed(read_lines(path)) if r.get("kind") == "trial" and r.get("is_empirical") is True), None)
        if trial:
            trials.append(trial)
    conversations = []
    for trial in trials:
        own = [c for c in calls if c.get("run_id") == trial["run_id"]]
        row = {k: trial.get(k) for k in ("run_id", "fixture_id", "seed", "condition", "task", "status")}
        row["agent_turns"] = sum(m.get("role") == "assistant" for m in trial.get("messages", []))
        for role in ("eval", "judge"):
            group = [c for c in own if c.get("role") == role]
            row.update({role + "_" + k: v for k, v in aggregate(group).items()})
            row[role + "_returned_models"] = sorted({c["model_returned"] for c in group if c.get("model_returned")})
        conversations.append(row)
    groups = defaultdict(list)
    for call in calls:
        groups[(call.get("condition", "shared"), call.get("role"), call.get("purpose"))].append(call)
    resources = [dict(condition=c, role=r, purpose=p, **aggregate(group)) for (c, r, p), group in sorted(groups.items(), key=lambda x: str(x[0]))]
    accepted = []
    for role in ("eval", "judge", "simulator"):
        group = [c for c in calls if c.get("role") == role]
        successful = [c for c in group if c.get("status") == "complete"]
        config = manifest.get("models", {}).get(role, {})
        accepted.append({
            "role": role, "requested_model": config.get("model"), "requested_provider": config.get("provider"),
            "returned_models": sorted({c["model_returned"] for c in successful if c.get("model_returned")}),
            "successful_requests": len(successful), "failed_requests": len(group) - len(successful),
            "requested_temperature": config.get("temperature"), "requested_max_tokens": config.get("max_tokens"),
            "accepted_request_temperatures": sorted({c["temperature"] for c in successful if c.get("temperature") is not None}),
            "accepted_request_max_tokens": sorted({c["max_tokens"] for c in successful if c.get("max_tokens") is not None}),
            "seeds_requested": sorted({c["seed"] for c in group if c.get("seed") is not None}),
            "seeds_sent": sorted({c["seed_sent"] for c in successful if c.get("seed_sent") is not None}),
            "seed_support_status": sorted({c["seed_support_status"] for c in successful if c.get("seed_support_status")}),
            "effective_setting_echo": "not returned by these provider responses",
        })
    errors = [{"source": "api", "role": c.get("role"), "run_id": c.get("run_id"), "error": c.get("error")} for c in calls if c.get("status") != "complete"]
    for path in sorted((folder / "judge_results").glob("*.json")):
        judgment = read_json(path, {})
        if judgment.get("status") != "complete":
            errors.append({"source": "judge_validation", "role": "judge", "run_id": judgment.get("run_id"), "error": judgment.get("error")})
    for trial in trials:
        if trial.get("status") not in {"complete", "turn_censored"}:
            errors.append({"source": "conversation", "role": "eval", "run_id": trial["run_id"], "error": trial.get("error", trial.get("status"))})
    for error in manifest.get("missing_environment", []):
        errors.append({"source": "preflight", "role": None, "run_id": None, "error": error})
    if manifest.get("execution_error"):
        errors.append({"source": "execution", "role": None, "run_id": None, "error": manifest["execution_error"]})
    return {"calls": calls, "trials": trials, "conversations": conversations, "resources": resources,
            "accepted_settings": accepted, "errors": errors, "pricing": pricing,
            "gate": read_json(folder / "result.json", {}), "totals": aggregate(calls)}


def projection(data):
    """Balanced condition/task means; two fixture cases do not yield a budget CI."""
    plan = {"development": {"fixtures": 12, "seeds": 3, "conversations": 324},
            "private_heldout": {"fixtures": 4, "seeds": 3, "conversations": 108}}
    result = {"status": "unavailable_until_complete_pilot", "planned_cohorts": plan,
              "total_main_conversations": 432, "main_blind_judgments": 864,
              "main_simulator_generations": 48, "main_script_audits": 48,
              "additional_pilot_allowance": 1,
              "private_fixture_integration": "pending; current runner main path accepts only the 12 development fixtures",
              "method": "Condition-by-task pilot means scaled to 36 development and 12 held-out conversations per cell; shared simulator/audit means scaled from 2 to 48 fixture-seed units. Observed cell minima/maxima are sensitivity bounds, not confidence or prediction intervals.",
              "assumptions": ["Same provider-returned models, settings and prices as the pilot",
                              "Held-out token lengths and Coach turn counts are approximated by the two development pilot cases",
                              "No extra retries or invalid-script repair beyond observed attempts; unexpected charges can exceed this estimate",
                              "One additional pilot is budgeted separately because the current full command reruns its pilot",
                              "Sourced dollar values use uncached token rates and are estimates, not a provider invoice"]}
    if data["gate"].get("status") != "passed" or len(data["conversations"]) != 18:
        return result
    cells = []
    for condition in CONDITIONS:
        for task in TASKS:
            rows = [r for r in data["conversations"] if r["condition"] == condition and r["task"] == task]
            if len(rows) != 2 or any(r["eval_completed_calls"] < 1 or r["judge_completed_calls"] != 2 for r in rows):
                return result
            cell = {"condition": condition, "task": task, "pilot_conversations": 2,
                    "development_conversations": 36, "heldout_conversations": 12}
            for field in FIELDS:
                values = [total((r["eval_" + field], r["judge_" + field])) for r in rows]
                cell[field] = ({"mean": statistics.mean(values), "min": min(values), "max": max(values)}
                               if all(number(v) for v in values) else {"mean": None, "min": None, "max": None})
            cells.append(cell)
    shared = [c for c in data["calls"] if c.get("purpose") in {"paired_builder_script", "script_validation"}]
    if len(shared) != 4:
        return result
    shared_totals = aggregate(shared)
    result["status"] = "pilot_based_planning_estimate"
    result["condition_task_cells"] = cells
    result["shared_pilot_overhead"] = shared_totals
    estimates = {}
    for name, multiplier in (("development_main", 18), ("heldout_main", 6), ("combined_main", 24), ("combined_main_plus_one_additional_pilot", 25)):
        estimates[name] = {field: data["totals"][field] * multiplier if number(data["totals"][field]) else None for field in FIELDS}
    result["estimates"] = estimates
    result["cell_sensitivity_combined_main"] = {}
    for field in FIELDS:
        bounds = {}
        for bound in ("min", "max"):
            direct = total(cell[field][bound] * 48 if number(cell[field][bound]) else None for cell in cells)
            overhead = shared_totals[field] * 24 if number(shared_totals[field]) else None
            bounds[bound] = total((direct, overhead))
        result["cell_sensitivity_combined_main"][field] = bounds
    return result


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items() if k in fields})


def markdown(data, manifest, budget):
    lines = ["# Worth Using: live pilot and full-run budget", ""]
    if not data["calls"]:
        lines += ["**The pilot is blocked before any live call. No skill effect, provider setting support, token usage, latency or dollar cost has been measured.** The requested model configuration is incomplete; there is no pilot-based full-run cost projection. This is an unrun test, not a null result.", ""]
    elif data["gate"].get("status") != "passed":
        lines += ["**The live pilot did not pass its plumbing gate; the full run has not started.** Partial provider measurements below describe attempted calls only. They do not support a skill-effect claim or a reliable full-run budget.", ""]
    else:
        lines += ["**The live pilot passed its plumbing checks; the full run has not started.** These 18 conversations test transport and measurement only. No efficacy conclusion is drawn from this pilot. The budget below is a planning estimate from two development fixtures, not a confidence interval.", ""]
    lines += [f"Source commit: `{manifest.get('source_commit') or 'Unavailable'}`. Record status: `{manifest.get('status')}`.", "",
              "## Provider-returned models and accepted requests", "",
              "Successful requests establish that the provider accepted the submitted payload. Temperature and token limits below are recorded request settings; these APIs do not echo their effective server settings. A seed parameter is best effort where accepted. Anthropic receives no seed parameter.", "",
              "| Role | Requested model | Exact returned model ID(s) | Successful / failed calls | Sent temperature | Sent max output tokens |",
              "| --- | --- | --- | --- | --- | --- |"]
    for row in data["accepted_settings"]:
        models = ", ".join(row["returned_models"]) or "None returned"
        temperature = ", ".join(map(str, row["accepted_request_temperatures"])) or "Unvalidated"
        maximum = ", ".join(map(str, row["accepted_request_max_tokens"])) or "Unvalidated"
        lines.append(f"| {row['role']} | {row['requested_model'] or 'UNSET'} | {models} | {row['successful_requests']} / {row['failed_requests']} | {temperature} | {maximum} |")
    lines += ["", "Requested settings and exact requested/sent seeds are in `scores/pilot_accepted_settings.json`; each successful call retains its exact returned ID in `pilot/live/calls.jsonl`. The simulator keeps its default model selection from EVAL_MODEL.", "",
              "## Token cost per conversation", "",
              "Tokens and seconds are sums of actual returned usage across assistant turns. Judge reviews are shown separately; shared simulator generation and script audits appear in the next table. Empty values mean unavailable. Dollar estimates require configured rates or sourced `pilot/pricing.json` prices for the exact returned models.", "",
              "| Conversation | Agent input / output tokens | Agent seconds | Agent USD | Judge input / output tokens | Judge USD |",
              "| --- | --- | --- | --- | --- | --- |"]
    for row in data["conversations"]:
        lines.append(f"| {row['run_id']} | {fmt(row['eval_input_tokens'])} / {fmt(row['eval_output_tokens'])} | {fmt(row['eval_latency_seconds'])} | {fmt(row['eval_cost_usd'], True)} | {fmt(row['judge_input_tokens'])} / {fmt(row['judge_output_tokens'])} | {fmt(row['judge_cost_usd'], True)} |")
    if not data["conversations"]:
        lines.append("| No live conversations | Not measured | Not measured | Unavailable | Not measured | Unavailable |")
    lines += ["", "## All pilot resource use", "",
              "| Condition | Role / purpose | Calls attempted / complete / error | Input tokens | Output tokens | Seconds | Estimated USD |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for row in data["resources"]:
        lines.append(f"| {row['condition']} | {row['role']} / {row['purpose']} | {row['attempted_calls']} / {row['completed_calls']} / {row['errored_calls']} | {fmt(row['input_tokens'])} | {fmt(row['output_tokens'])} | {fmt(row['latency_seconds'])} | {fmt(row['cost_usd'], True)} |")
    if not data["resources"]:
        lines.append("| No live calls | None | 0 / 0 / 0 | Not measured | Not measured | Not measured | Unavailable |")
    if data["pricing"].get("models"):
        lines += ["", "### Pricing sources", "",
                  "Rates below are per million tokens and are used as uncached estimates. Provider invoices can differ because of caching, request tier or other adjustments.", "",
                  "| Exact returned model | Input USD / million | Output USD / million | Source |",
                  "| --- | --- | --- | --- |"]
        for model, rates in sorted(data["pricing"]["models"].items()):
            lines.append(f"| {model} | {rates.get('input_usd_per_million', 'Unavailable')} | {rates.get('output_usd_per_million', 'Unavailable')} | {rates.get('source_url', 'No source supplied')} |")
    lines += ["", "## Full-run projection and approval stop", "",
              "The planned full evaluation is **324 development conversations plus 108 private held-out conversations = 432**, with 864 blind judgments, 48 simulator scripts and 48 judge script audits. The 18-conversation pilot is separate. Each Coach conversation can require 1–12 evaluated-agent calls, so 432 conversations are not 432 API calls.", "",
              "The current main runner still accepts only the 12 development fixtures. Private input loading and separate held-out analysis must be integrated before the approved full run. Private fixture text, keys, blinded packets and transcripts can reveal the holdout and must stay out of the public PR.", ""]
    if budget["status"] == "pilot_based_planning_estimate":
        lines += ["| Planned scope | Input tokens | Output tokens | API seconds | Estimated USD |", "| --- | --- | --- | --- | --- |"]
        for name, values in budget["estimates"].items():
            lines.append(f"| {name.replace('_', ' ')} | {fmt(values['input_tokens'])} | {fmt(values['output_tokens'])} | {fmt(values['latency_seconds'])} | {fmt(values['cost_usd'], True)} |")
        lines += ["", "The balanced 432-conversation main estimate is 24 times the pilot's measured total. One further pilot allowance raises it to 25 times; the current full command reruns its pilot in a new record. This preserves the skill/baseline/placebo and Score/Team/Coach mixture and includes both judge reviews, simulator calls and script audits. It extrapolates Coach lengths and dossier sizes from only two fixtures. The sensitivity range in `scores/pilot_projection.json` uses observed per-cell minima/maxima with shared overhead held fixed; it is not a statistical interval. Unobserved retries, longer held-out conversations and provider charges can increase the bill.", ""]
    else:
        lines += ["**Projected tokens, seconds and dollars: unavailable until a complete live pilot.** No placeholder price or synthetic usage estimate is substituted.", ""]
    lines += ["The full run remains stopped until the user has reviewed the pilot and cost projection. A passing pilot does not authorize the full run.", "", "## Errors and limitations", ""]
    if data["errors"]:
        lines.extend("- " + str(row["source"]) + ": " + str(row["error"]) for row in data["errors"])
    else:
        lines.append("No recorded API, preflight or schema errors." if data["calls"] else "No provider errors have been observed because no provider call was made.")
    lines += ["", "Coach turn caps, if reached, remain censoring rather than successful stopping. The simulator is an LLM-generated fixed script replayed across conditions, not an adaptive conversation. Repeated reviews by one OpenAI judge measure that judge's consistency, not independent-judge agreement. All pilot dossiers are fictional development cases.", "",
              "## Full-run interpretation safeguards", "",
              "The headline unsupported-evidence-upgrade metric must appear beside final rating coverage, evidence-classification coverage and evidence reference-grade agreement. Omitting ratings cannot count as an honesty win. Public development results and private held-out results will be separate; a headline gain must also hold on the four held-out fixtures. Null or negative comparisons are reported plainly. No real-world tool usefulness claim follows from these exercises.", "",
              "No efficacy effect sizes, confidence intervals or five illustrative efficacy excerpts are supplied for this pilot. The five final excerpts must be selected from real full-run transcripts. Private excerpts require a disclosure decision because they can reveal held-out scenarios. Real tools and real usage logs are a later, separate cohort.", "",
              "## Reproduce this pilot", "", "```bash", "python3 evals/run.py --conditions skill,baseline --seeds 1 --pilot", "```", "",
              "Model IDs and credentials come only from environment variables; do not put API keys in files or transcripts. The placebo is automatically added to the requested two conditions. See the frozen source and protocol files beside this report.", ""]
    return "\n".join(lines)


def write_pdf(path, data, manifest, budget):
    """Compact pilot PDF: a status panel and exact tabular measurements."""
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    import reportlab
    # Embed the fonts bundled with ReportLab so headless renderers and PDF
    # viewers use the same glyph widths rather than platform substitutions.
    font_dir = Path(reportlab.__file__).resolve().parent / "fonts"
    pdfmetrics.registerFont(TTFont("PilotSans", str(font_dir / "Vera.ttf")))
    pdfmetrics.registerFont(TTFont("PilotSans-Bold", str(font_dir / "VeraBd.ttf")))
    styles = getSampleStyleSheet()
    for name, style in styles.byName.items():
        style.fontName = "PilotSans-Bold" if name.startswith("Heading") or name == "Title" else "PilotSans"
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 12
    styles["Heading2"].fontSize = 13
    styles["Heading2"].leading = 17
    styles["Heading2"].keepWithNext = True
    styles.add(ParagraphStyle(name="PilotSmall", parent=styles["BodyText"], fontSize=8, leading=11, spaceAfter=7))
    styles.add(ParagraphStyle(name="PilotTitle", parent=styles["Title"], fontSize=22, leading=26, textColor=colors.HexColor("#143842"), alignment=0))
    def p(text, style="BodyText"):
        return Paragraph(escape(str(text)).replace("\n", "<br/>"), styles[style])
    def table(headers, rows, widths):
        value = Table([[p(x, "PilotSmall") for x in headers]] + [[p(x, "PilotSmall") for x in row] for row in rows], colWidths=widths, repeatRows=1, hAlign="LEFT")
        value.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5eff1")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), .6, colors.HexColor("#55757d")), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        return value
    story = [p("Worth Using", "PilotTitle"), p("Live pilot and full-run budget", "Heading2")]
    status = "BLOCKED BEFORE LIVE CALLS" if not data["calls"] else ("PILOT PASSED · FULL RUN STOPPED" if data["gate"].get("status") == "passed" else "PILOT INCOMPLETE · FULL RUN STOPPED")
    panel = table([status], [["No efficacy conclusion is drawn from this pilot. " + ("Provider usage, accepted settings and cost remain unmeasured." if not data["calls"] else "Resource measurements below come from the actual pilot ledger.")]], [510])
    story += [panel, Spacer(1, 12), p("Source commit: " + str(manifest.get("source_commit")), "PilotSmall")]
    story += [p("Model requests and provider responses", "Heading2"), p("A successful request confirms payload acceptance. Temperature and token limits are request values, not server-echoed effective settings.", "PilotSmall")]
    modelrows = [[r["role"], r["requested_model"] or "UNSET", ", ".join(r["returned_models"]) or "None returned", f"{r['successful_requests']} / {r['failed_requests']}"] for r in data["accepted_settings"]]
    story.append(table(["Role", "Requested model", "Exact returned model", "Success / error"], modelrows, [56, 173, 205, 76]))
    story += [Spacer(1, 10), p("Token cost per conversation", "Heading2")]
    if data["conversations"]:
        rows = [[r["fixture_id"] + " / " + r["task"] + " / " + r["condition"], fmt(r["eval_input_tokens"]) + " / " + fmt(r["eval_output_tokens"]), fmt(r["eval_cost_usd"], True), fmt(r["judge_input_tokens"]) + " / " + fmt(r["judge_output_tokens"]), fmt(r["judge_cost_usd"], True)] for r in data["conversations"]]
        story.append(table(["Conversation", "Agent in / out", "Agent USD", "Judge in / out", "Judge USD"], rows, [150, 103, 67, 123, 67]))
    else:
        story.append(p("No live conversation exists. Token usage, latency and dollar cost are unavailable."))
    story += [Spacer(1, 12), p("The planned full run", "Heading2")]
    story.append(table(["Development", "Private held-out", "Separate pilot"], [["12 fixtures · 3 seeds\n324 conversations", "4 fixtures · 3 seeds\n108 conversations", "2 fixtures · 1 seed\n18 conversations"]], [170, 170, 170]))
    story += [p("Combined main plan: 432 conversations, 864 blind judgments, 48 simulator generations and 48 script audits. Private fixture loading is not yet integrated into the current runner. All private payloads remain outside the public repository.", "PilotSmall")]
    if budget["status"] == "pilot_based_planning_estimate":
        rows = [[name.replace("_", " "), fmt(v["input_tokens"]), fmt(v["output_tokens"]), fmt(v["cost_usd"], True)] for name, v in budget["estimates"].items()]
        story.append(table(["Scope", "Input tokens", "Output tokens", "Estimated USD"], rows, [222, 101, 101, 86]))
        story.append(p("Planning estimate only: the combined main is 24 times measured pilot usage; one further pilot allowance makes 25 times. Coach lengths and held-out dossier sizes may differ. This is not a confidence interval or an invoice. Retry costs can exceed the estimate.", "PilotSmall"))
    else:
        story.append(p("No pilot-based full-run cost projection is available. No model price or token quantity has been invented."))
    story += [p("Errors and next gate", "Heading2")]
    for error in data["errors"]:
        story.append(p(str(error["source"]) + ": " + str(error["error"]), "PilotSmall"))
    story.append(p("Stop before the full run. The user must receive the pilot measurements and projected cost first. Full-run headline comparisons must hold on the private cohort and show rating coverage, evidence coverage and evidence recognition next to unsupported upgrades. Missing ratings cannot masquerade as honesty.", "PilotSmall"))
    story.append(p("No efficacy intervals or illustrative wins/losses are claimed here. Final excerpts must use real full-run transcripts. Fictional fixtures, fixed simulated users, one repeated judge and a small held-out sample limit generalization. Real tools with real usage logs belong to a later separate cohort.", "PilotSmall"))
    story.append(p("Audit files: REPORT.md; scores/pilot_conversations.csv; scores/pilot_cost_latency.csv; scores/pilot_accepted_settings.json; scores/pilot_projection.json. Live requests appear in pilot/live/calls.jsonl only when calls exist.", "PilotSmall"))
    def page(canvas, doc):
        canvas.setFont("PilotSans", 8)
        canvas.setFillColor(colors.HexColor("#55757d"))
        canvas.drawString(42, 25, "Worth Using evaluation · pilot only · " + str(manifest.get("date", "")))
        canvas.drawRightString(552, 25, str(doc.page))
    SimpleDocTemplate(str(path), pagesize=(594, 842), rightMargin=42, leftMargin=42, topMargin=38, bottomMargin=42).build(story, onFirstPage=page, onLaterPages=page)


def write_pilot_reports(root, output, manifest):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    data = pilot_data(output, manifest)
    budget = projection(data)
    scores = output / "scores"
    scores.mkdir(exist_ok=True)
    conversation_fields = ["run_id", "fixture_id", "seed", "condition", "task", "status", "agent_turns"] + [role + "_" + field for role in ("eval", "judge") for field in ("attempted_calls", "completed_calls", "errored_calls", *FIELDS, "returned_models")]
    write_csv(scores / "pilot_conversations.csv", data["conversations"], conversation_fields)
    write_csv(scores / "pilot_cost_latency.csv", data["resources"], ["condition", "role", "purpose", "attempted_calls", "completed_calls", "errored_calls", *FIELDS])
    write_csv(scores / "pilot_errors.csv", data["errors"], ["source", "role", "run_id", "error"])
    for name, value in (("pilot_accepted_settings.json", data["accepted_settings"]), ("pilot_projection.json", budget), ("pilot_resource_totals.json", data["totals"])):
        (scores / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    (output / "REPORT.md").write_text(markdown(data, manifest, budget))
    pdf = output / "Worth_Using_Evaluation.pdf"
    write_pdf(pdf, data, manifest, budget)
    return {"report": str(output / "REPORT.md"), "pdf": str(pdf), "live_conversations": len(data["trials"]),
            "complete_judgments": sum(c.get("role") == "judge" and c.get("purpose") == "blind_judgment" and c.get("status") == "complete" for c in data["calls"]),
            "offline_samples_excluded": 0, "status": "pilot_only" if data["calls"] else "not_measured", "visuals": {}}
