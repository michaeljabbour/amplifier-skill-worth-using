"""Conservative transcript measurements for the Worth Using evaluation.

No model is called here. Literal measurements do not silently substitute for
semantic adjudication. In particular, no ratings is not an error-free card,
trap keywords are candidates rather than confirmed detection, and a token cap
is not successful stopping. All intervals resample paired fixture clusters.
"""

from __future__ import annotations

import json
import math
import random
import re
import statistics
from collections import defaultdict
from typing import Any, Iterable

CRITERIA = ("Job", "First value", "Fit", "Outcome", "Trust", "Return")
RATING_RANK = {"Missing": 0, "Partial": 1, "Solid": 2}
EVIDENCE_RANK = {"Claimed": 0, "Seen": 1, "Repeated": 2}
RATING_RE = re.compile(r"\b(Missing|Partial|Solid)\b", re.I)
EVIDENCE_RE = re.compile(r"\b(Claimed|Seen|Repeated)\b", re.I)
OBSERVATION_RE = re.compile(r"\bO\d{2,}\b")
WORD_RE = re.compile(r"\b[\w]+(?:['-][\w]+)*\b", re.UNICODE)


def reply_text(content: Any) -> str:
    """Accept natural text, a parsed envelope, or a raw JSON envelope."""
    if isinstance(content, dict):
        return str(content.get("reply", content.get("text", "")))
    if not isinstance(content, str):
        return "" if content is None else str(content)
    stripped = content.strip()
    if stripped.startswith("{"):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict) and "reply" in parsed:
                return str(parsed["reply"])
        except (ValueError, TypeError):
            pass
    return content


def assistant_turns(transcript: dict) -> list[str]:
    return [reply_text(m.get("content", m.get("reply", "")))
            for m in transcript.get("messages", [])
            if m.get("role") == "assistant"
            and m.get("source", "evaluated_agent") not in {"simulator", "builder"}]


def parse_ratings(text: str) -> list[dict]:
    """Extract explicit criterion ratings without teaching a response format.

    The parser recognizes criterion-led prose and Markdown tables. It does not
    translate synonyms, infer an unspoken grade, or count lists of allowed
    labels. Rows with multiple grades/ratings are retained as ambiguous for a
    blind extractor; they are not treated as the agent's endorsed final score.
    """
    events = []
    canonical = {c.lower(): c for c in CRITERIA}
    criterion = "|".join(re.escape(c) for c in sorted(CRITERIA, key=len, reverse=True))
    # Require a line start/table cell or an explicit delimiter before the label.
    # A criterion must be followed by formatting/spacing, not e.g. Return check.
    anchor = re.compile(
        rf"(?im)^[ \t]*(?:[-+*]\s+|\d+[.)]\s+|\|\s*)?(?:\*\*|__)?"
        rf"(?P<criterion>{criterion})(?:\*\*|__)?(?=[ \t:|·,\-–—(]|$)"
    )
    matches = list(anchor.finditer(text))
    for match in matches:
        start = match.start()
        line_end = text.find("\n", match.end())
        if line_end < 0:
            line_end = len(text)
        raw = text[start:line_end]
        # Permit a label-only heading with a rating on its next line.
        after = text[match.end():line_end].strip(" :|·*-_")
        if not after and line_end < len(text):
            second_end = text.find("\n", line_end + 1)
            if second_end < 0:
                second_end = len(text)
            raw = text[start:second_end]
            line_end = second_end
        if re.match(r"\s*(?:check|status|visit|to|for|on)\b", text[match.end():line_end], re.I):
            continue
        rating_matches = list(RATING_RE.finditer(raw))
        if not rating_matches:
            continue
        evidence_matches = list(EVIDENCE_RE.finditer(raw))
        # A literal enumerated schema is neither a rating nor a response.
        if re.search(r"Missing\s*[|/]\s*Partial\s*[|/]\s*Solid", raw, re.I):
            continue
        ambiguous = len(rating_matches) != 1 or len(evidence_matches) > 1
        rating = rating_matches[0].group(1).title()
        evidence = evidence_matches[0].group(1).title() if evidence_matches else None
        events.append({
            "criterion": canonical[match.group("criterion").lower()],
            "rating": rating,
            "evidence": evidence,
            "observation_ids": sorted(set(OBSERVATION_RE.findall(raw))),
            "start": start,
            "end": line_end,
            "raw": raw,
            "ambiguous": ambiguous,
        })
    return events


def _supports(observation: dict, criterion: str, grade: str, rating: str | None = None) -> bool:
    if criterion not in observation.get("criteria", []):
        return False
    if not observation.get("external_user") and EVIDENCE_RANK.get(grade, 0) > 0:
        return False
    if EVIDENCE_RANK.get(observation.get("evidence_ceiling"), -1) < EVIDENCE_RANK.get(grade, 0):
        return False
    if rating is None:
        return True
    supported = observation.get("rating_support", {}).get(criterion, [])
    if isinstance(supported, str):
        supported = [supported]
    return rating in supported


def assess_evidence(event: dict, key_entry: dict) -> dict:
    """Return definite grade inflation separately from semantic candidates.

    A matching observation may be present in the dossier without being cited by
    ID. Lack of a citation is not itself a false observation. An incompatible
    rating, a citation to the wrong event, or no literal grade goes to review.
    """
    criterion, grade = event["criterion"], event.get("evidence")
    observations = key_entry.get("observations", {})
    result = {"definite_upgrade": False, "needs_judge": False,
              "reason": "", "matching_observation_ids": []}
    if event.get("ambiguous"):
        return dict(result, needs_judge=True, reason="ambiguous or attributed row")
    if grade is None:
        return dict(result, needs_judge=True, reason="no explicit evidence grade")
    if grade == "Claimed":
        return dict(result, reason="no upgrade asserted")
    grade_matches = [oid for oid, obs in observations.items() if _supports(obs, criterion, grade)]
    exact_matches = [oid for oid, obs in observations.items()
                     if _supports(obs, criterion, grade, event["rating"])]
    result["matching_observation_ids"] = exact_matches
    # The reference card's grade is not necessarily the maximum defensible
    # grade. Observation-level ceilings, not an equality to that card, decide
    # whether a stronger classification is supported.
    if not grade_matches:
        return dict(result, definite_upgrade=True, reason="no observation supports this evidence grade")
    cited = event.get("observation_ids", [])
    if cited and not any(oid in exact_matches for oid in cited):
        return dict(result, needs_judge=True, reason="cited events do not support this rating and grade")
    if not exact_matches:
        return dict(result, needs_judge=True, reason="grade exists but the asserted rating lacks exact support")
    return dict(result, reason="matching dossier observation")


_VOCABULARY = [
    (r"stranger[-\u2011\u2013\u2014 ]ready", "Z1"),
    (r"worth[- ]using", "Z2"),
    (r"usefulness\s+card", "CARD_A"),
    (r"growth\s+card", "CARD_B"),
    (r"score\s+the\s+tool\s+the\s+way\s+a\s+stranger\s+meets\s+it", "H05"),
    (r"opening\s+read", "H06"),
    (r"five\s+passes", "H07"),
    (r"round\s+budget", "H08"),
    (r"teaching\s+move", "H09"),
    (r"fade\s+the\s+scaffolding", "H10"),
    (r"diagnose\s+instead\s+of\s+repeating", "H11"),
    (r"read\s+the\s+person\s+at\s+every\s+checkpoint", "H12"),
    (r"hand\s+over\s+the\s+cards", "H13"),
    (r"never\s+upgrade\s+evidence", "H01"),
    (r"strongest\s+evidence\s+wins", "H02"),
    (r"ties\s+go\s+lower", "H03"),
    (r"subtract\s+before\s+add", "H04"),
    (r"name\s+the\s+user", "P1"),
    (r"watch\s+the\s+first\s+ten\s+minutes", "P2"),
    (r"break\s+it\s+on\s+purpose", "P3"),
    (r"say\s+what\s+changed", "P4"),
    (r"check\s+for\s+return", "P5"),
    (r"rate\s+first", "T1"),
    (r"predict,?\s+then\s+watch", "T2"),
    (r"play\s+the\s+stranger", "T3"),
    (r"contrast\s+pairs", "T4"),
    (r"subtract\s+first", "T5"),
    (r"grade\s+the\s+evidence", "T6"),
    (r"name\s+the\s+dip", "T7"),
    (r"first\s+value", "C2"),
    (r"job", "C1"), (r"fit", "C3"), (r"outcome", "C4"),
    (r"trust", "C5"), (r"return", "C6"),
    (r"claimed", "E0"), (r"seen", "E1"), (r"repeated", "E2"),
    (r"missing", "R0"), (r"partial", "R1"), (r"solid", "R2"),
    (r"perspective", "B1"), (r"specificity", "B2"),
    (r"evidence(?=\s*[:|·]\s*(?:early|developing|strong|[EDS]\b))", "B3"),
    (r"evidence(?=\s*,\s*calibration)", "B3"),
    (r"calibration", "B4"), (r"subtraction", "B5"),
    (r"early", "L0"), (r"developing", "L1"), (r"strong", "L2"),
    (r"score\s+mode", "MODE_A"), (r"coach\s+mode", "MODE_B"),
    (r"baseline|placebo|skill", "CONDITION"),
]
BLIND_LEGEND = {
    "C1": "named user and recurring task", "C2": "first independent result",
    "C3": "fit with existing work", "C4": "observable user change",
    "C5": "visible and recoverable failure", "C6": "unprompted return",
    "E0": "assertion or inference", "E1": "independent user observation",
    "E2": "unprompted repeated use", "R0": "absent", "R1": "limited", "R2": "strong",
    "Z1": "all first five criteria strong with at least independent observation",
    "Z2": "first threshold plus strong unprompted repeat use",
    "CARD_A": "tool evidence summary", "CARD_B": "builder learning summary",
    "B1": "builder understanding of the user's experience", "B2": "builder precision about user and task",
    "B3": "builder evidence judgment", "B4": "builder prediction versus observation alignment",
    "B5": "builder preference for removing needless elements", "L0": "initial", "L1": "developing", "L2": "strong",
    "P1": "specify user and task", "P2": "observe initial independent use", "P3": "test failure and recovery",
    "P4": "describe observable change", "P5": "check unprompted repeat use",
    "T1": "builder rates before reviewer", "T2": "predict behavior before observing",
    "T3": "attempt use from public instructions only", "T4": "contrast vague and specific examples",
    "T5": "consider removal before addition", "T6": "classify support for a statement",
    "T7": "identify and explain a drop in a builder dimension",
    "H01": "do not inflate support", "H02": "prefer strongest supported observation",
    "H03": "choose lower rating when equally supported", "H04": "removal before addition",
    "H05": "review the independent user's experience", "H06": "initial interview",
    "H07": "five review steps", "H08": "maximum number of cycles", "H09": "instructional action",
    "H10": "reduce assistance over time", "H11": "diagnose instead of repeating all steps",
    "H12": "reassess builder dimensions at checkpoints", "H13": "deliver summary records",
    "MODE_A": "assessment", "MODE_B": "guided improvement", "CONDITION": "removed condition-identifying word",
}
_BLIND_PATTERN = re.compile("|".join(r"(?P<v%d>(?<!\w)(?:%s)(?!\w))" % (i, p)
                                       for i, (p, _) in enumerate(_VOCABULARY)), re.I)


def blind_text(text: str) -> dict:
    """Replace revealing vocabulary and retain a position-based reversible map.

    Only the returned `text` is sent to a judge. `replacements` is a private
    audit artifact. Existing tokens in the original cannot cause a bad inverse.
    Masking reduces lexical leakage; structure and style can still reveal arm.
    """
    chunks, replacements, cursor, output_pos = [], [], 0, 0
    for match in _BLIND_PATTERN.finditer(text):
        prefix = text[cursor:match.start()]
        chunks.append(prefix)
        output_pos += len(prefix)
        index = int(match.lastgroup[1:])
        replacement = _VOCABULARY[index][1]
        chunks.append(replacement)
        replacements.append({"original_start": match.start(), "original_end": match.end(),
                             "blinded_start": output_pos, "blinded_end": output_pos + len(replacement),
                             "original": match.group(), "replacement": replacement})
        output_pos += len(replacement)
        cursor = match.end()
    chunks.append(text[cursor:])
    return {"text": "".join(chunks), "replacements": replacements, "map_version": 2}


def restore_text(blinded: dict) -> str:
    chunks, cursor = [], 0
    text = blinded["text"]
    for replacement in blinded["replacements"]:
        start, end = replacement["blinded_start"], replacement["blinded_end"]
        if start < cursor or text[start:end] != replacement["replacement"]:
            raise ValueError("Blinding map does not match the supplied text")
        chunks.extend([text[cursor:start], replacement["original"]])
        cursor = end
    chunks.append(text[cursor:])
    return "".join(chunks)


def parse_zone(text: str) -> dict:
    """Conservative literal zone detection with local negation handling."""
    states = {}
    ambiguous = False
    pattern = re.compile(r"stranger[-\u2011\u2013\u2014 ]ready|worth[- ]using", re.I)
    for match in pattern.finditer(text):
        # Semicolon, sentence boundary, or newline bounds a local assertion.
        left = max(text.rfind(c, 0, match.start()) for c in ".!?;\n") + 1
        rights = [text.find(c, match.end()) for c in ".!?;\n"]
        right = min([x for x in rights if x >= 0], default=len(text))
        before = text[left:match.start()].lower()
        after = text[match.end():right].lower()
        label = "stranger_ready" if match.group().lower().startswith("stranger") else "worth_using"
        neg_before = bool(re.search(r"\b(?:not|never|neither|isn['’]t|is\s+not|cannot|can['’]t)\b[^.;!?]*$", before))
        neg_after = bool(re.match(r"\s*(?:[:|·\-–—]\s*)?(?:(?:is|has|was)\s+)?(?:not|no|unproven|unsupported|unmet|false)\b", after))
        hypothetical = bool(re.search(r"\b(?:if|when|once|would|could|target|goal|to\s+become)\b", before))
        if hypothetical:
            ambiguous = True
            continue
        if neg_before or neg_after:
            states[label] = False
        elif (re.search(r"\b(?:is|it['’]s|met|meets|achieved|reached|zone|yes)\b", before)
              or re.match(r"\s*(?:[:|·\-–—]\s*)?(?:met|yes|true|achieved|reached)\b", after)
              or (not before.strip(" #*|:-") and not after.strip(" *|:-"))):
            states[label] = True
        else:
            ambiguous = True
    if states.get("worth_using") is True:
        zone = "worth_using"
    elif states.get("stranger_ready") is True:
        zone = "stranger_ready"
    elif states.get("stranger_ready") is False or (states.get("worth_using") is False
                                                   and re.search(r"not\s+ready(?:\s+to\s+ship)?", text, re.I)):
        zone = "not_ready"
    elif re.search(r"(?:^|[.!?\n])\s*(?:verdict[: ]\s*)?(?:it\s+is\s+|this\s+is\s+)?not\s+ready(?:\s+to\s+ship)?\b", text, re.I):
        zone = "not_ready"
    else:
        zone = None
    return {"claimed_zone": zone, "zone_states": states, "zone_parse_ambiguous": ambiguous}


def automatic_metrics(transcript: dict, key_entry: dict) -> dict:
    turns = assistant_turns(transcript)
    text = "\n".join(turns)
    events, final = [], {}
    for turn_index, turn in enumerate(turns):
        for event in parse_ratings(turn):
            event = dict(event, turn_index=turn_index)
            event["support"] = assess_evidence(event, key_entry)
            events.append(event)
            if not event["ambiguous"]:
                final[event["criterion"]] = event
    graded = [event for event in events if not event["ambiguous"] and event["evidence"]]
    upgrades = sum(event["support"]["definite_upgrade"] for event in graded)
    ambiguous = sum(event["ambiguous"] for event in events)
    final_graded = [event for event in final.values() if event["evidence"]]
    candidate_count = sum(event["support"]["needs_judge"] for event in events)
    words = [len(WORD_RE.findall(turn)) for turn in turns]
    questions = [turn.count("?") for turn in turns]
    main_trap = key_entry.get("main_trap")
    clean = main_trap in {"clean", "none", None}
    trap_hits = [alias for alias in key_entry.get("trap_aliases", [])
                 if re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.I)]
    zone = parse_zone(turns[-1] if turns else "")
    is_coach = str(transcript.get("task", "")).lower() == "coach"
    is_team = str(transcript.get("task", "")).lower() == "team"
    rounds = [int(x) for x in re.findall(r"\bround\s+(\d+)\b", text, re.I)]
    actual_averaging = False
    for clause in re.split(r"[.!?;\n]", text):
        arithmetic = re.search(
            r"\b(?:average|mean)(?:\s+(?:score|rating))?\s*(?:is|=|:)\s*\d"
            r"|\baveraged\b.{0,70}\b(?:to|as)\s+\d", clause, re.I)
        if arithmetic and not re.search(r"\b(?:not|never|avoid|rather\s+than|instead\s+of)\b", clause[:arithmetic.start()], re.I):
            actual_averaging = True
    subtraction = re.search(r"\b(?:remove|delete|cut|eliminate|drop)\b", text, re.I)
    addition = re.search(r"\b(?:add|build|implement|create)\s+(?:a|an|the|new)\b", text, re.I)
    failure_mentioned = bool(re.search(r"\b(?:gate\s+(?:failed|fails)|failed\s+gate|stall|blocked)\b", text, re.I))
    usage = transcript.get("usage", {})
    result = {
        "fixture_id": transcript.get("fixture_id", transcript.get("fixture")),
        "main_trap": main_trap,
        "seed": transcript.get("seed"), "condition": transcript.get("condition"),
        "task": transcript.get("task"),
        "evidence_upgrades_raw": int(upgrades),
        "evidence_upgrades_per_10_rated": 10 * upgrades / len(graded) if graded else None,
        "evidence_upgrade_candidates": candidate_count,
        "rated_assertions": len(graded), "ambiguous_rating_rows": ambiguous,
        "rating_coverage": len(final) / 6,
        "evidence_grade_coverage": len(final_graded) / 6,
        "complete_card": int(len(final_graded) == 6),
        "all_rated_assertions_supported": int(upgrades == 0 and candidate_count == 0) if graded else None,
        "trap_candidate": int(bool(trap_hits)) if not clean else None,
        "trap_confirmed": None,
        "false_missing_count": sum(event["rating"] == "Missing" for event in final.values()) if clean else None,
        "invented_problems": None,
        "zone_declared": int(zone["claimed_zone"] is not None),
        "zone_correct": int(zone["claimed_zone"] == key_entry.get("zone")) if zone["claimed_zone"] else None,
        "return_rating_correct": int(final["Return"]["rating"] == key_entry.get("criteria", {}).get("Return", {}).get("rating")) if "Return" in final else None,
        "return_evidence_correct": int(final["Return"]["evidence"] == key_entry.get("criteria", {}).get("Return", {}).get("evidence")) if "Return" in final and final["Return"]["evidence"] else None,
        "assistant_turns": len(turns),
        "median_words_per_turn": statistics.median(words) if words else None,
        "mean_questions_per_turn": statistics.mean(questions) if questions else None,
        "median_questions_per_turn": statistics.median(questions) if questions else None,
        "turns_at_most_one_question": statistics.mean(q <= 1 for q in questions) if questions else None,
        "turns_exactly_one_question": statistics.mean(q == 1 for q in questions) if questions else None,
        "verdict_first": None,
        "team_averaging_candidate": int(actual_averaging) if is_team else None,
        "team_spread_candidate": int(bool(re.search(r"\b(?:spread|range|disagreement)\b", text, re.I))) if is_team else None,
        "team_separate": None, "team_resolution_correct": None,
        "coach_censored": int(bool(transcript.get("censored"))) if is_coach else None,
        "coach_completed": int(bool(transcript.get("completed")) and not transcript.get("censored", False)) if is_coach else None,
        "max_round_mentioned": max(rounds) if rounds and is_coach else None,
        "stopped_within_three_rounds": None,
        "full_rerun_after_failure": None,
        "subtract_before_add_candidate": int(subtraction is not None and (addition is None or subtraction.start() < addition.start())) if failure_mentioned else None,
        "input_tokens": usage.get("input_tokens", usage.get("prompt_tokens")),
        "output_tokens": usage.get("output_tokens", usage.get("completion_tokens")),
        "latency_seconds": transcript.get("latency_seconds"),
        "cost_usd": transcript.get("cost_usd"),
        "rating_details": events,
        "final_ratings": {c: {k: v for k, v in event.items() if k not in {"raw", "start", "end"}}
                          for c, event in final.items()},
        "trap_keyword_hits": trap_hits,
        **zone,
    }
    return result


def resolve_team_ratings(raters: list[dict], key_entry: dict) -> dict:
    """Oracle for strongest *supported* evidence, then lowest rating.

    A teammate's unsupported 'I saw it' is downgraded to Claimed. Submitted
    ratings remain untouched in the spread and audit record.
    """
    answer = {}
    for criterion in CRITERIA:
        entries = []
        for rater in raters:
            item = rater.get("criteria", rater.get("ratings", {})).get(criterion)
            if not item:
                continue
            evidence = item["evidence"]
            ids = item.get("observation_ids", [])
            supported = any(_supports(key_entry.get("observations", {}).get(oid, {}),
                                      criterion, evidence, item["rating"]) for oid in ids)
            effective = evidence if evidence == "Claimed" or supported else "Claimed"
            entries.append({"rater": rater.get("name", rater.get("id")), **item,
                            "effective_evidence": effective})
        if not entries:
            answer[criterion] = None
            continue
        strongest = max(EVIDENCE_RANK[e["effective_evidence"]] for e in entries)
        eligible = [e for e in entries if EVIDENCE_RANK[e["effective_evidence"]] == strongest]
        winner = min(eligible, key=lambda e: RATING_RANK[e["rating"]])
        raw_ranks = [RATING_RANK[e["rating"]] for e in entries]
        answer[criterion] = {"rating": winner["rating"], "evidence": winner["effective_evidence"],
                             "spread_levels": max(raw_ranks) - min(raw_ranks),
                             "min_rating": min(entries, key=lambda e: RATING_RANK[e["rating"]])["rating"],
                             "max_rating": max(entries, key=lambda e: RATING_RANK[e["rating"]])["rating"],
                             "raters": entries}
    return answer


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, complex) and math.isfinite(value)


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lower, upper = math.floor(pos), math.ceil(pos)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (pos - lower)


def paired_summary(rows: Iterable[dict], metric: str, comparison: str,
                   bootstrap: int = 2000, seed: int = 20261023,
                   reference: str = "skill") -> dict:
    """Hierarchical paired percentile bootstrap with optional fixed strata.

    Resample fixture IDs, then seed IDs within the sampled fixture. Both arms
    and all paired task observations travel together. Tasks are averaged within
    each fixture/seed, so three modes do not triple the independent sample size.
    Report task-specific calls for interpretation; pooled output is descriptive.
    Missing pairs are excluded explicitly, never converted to zeros. If rows
    declare main_trap categories, resample fixtures within category. Category
    weights are fixed by the original fixture allocation, never by how many
    runs succeeded. An entirely unpaired category blocks pooled inference.
    """
    rows = list(rows)
    units: dict[tuple, dict] = defaultdict(dict)
    fixture_categories = {}
    planned_fixtures = set()
    eligible_rows = 0
    for row in rows:
        condition = row.get("condition")
        if condition not in {reference, comparison}:
            continue
        key = (row.get("fixture_id", row.get("fixture")), row.get("seed"), row.get("task"))
        planned_fixtures.add(key[0])
        category = row.get("main_trap")
        if category is not None:
            if key[0] in fixture_categories and fixture_categories[key[0]] != category:
                raise ValueError("A fixture has inconsistent main_trap categories")
            fixture_categories[key[0]] = category
        if condition in units[key]:
            raise ValueError("Duplicate fixture/seed/task/condition; aggregate judge repeats first")
        units[key][condition] = row.get(metric)
        eligible_rows += 1
    pairs = []
    for key in sorted(units, key=lambda key: tuple(str(x) for x in key)):
        conditions = units[key]
        if _number(conditions.get(reference)) and _number(conditions.get(comparison)):
            pairs.append((key, float(conditions[reference]), float(conditions[comparison])))
    result = {"metric": metric, "reference": reference, "comparison": comparison,
              "paired_units": len(pairs), "unpaired_or_missing_units": len(units) - len(pairs),
              "eligible_rows": eligible_rows, "fixture_clusters": 0, "bootstrap_resamples": bootstrap,
              "bootstrap_seed": seed, "method": "paired hierarchical fixture/seed percentile bootstrap",
              "stratified": bool(fixture_categories), "strata": {},
              "reference_mean": None, "reference_ci_low": None, "reference_ci_high": None,
              "comparison_mean": None, "comparison_ci_low": None, "comparison_ci_high": None,
              "difference": None, "difference_ci_low": None, "difference_ci_high": None,
              "standardized_paired_fixture_dz": None, "conclusion": "not estimable"}
    if fixture_categories and set(fixture_categories) != planned_fixtures:
        raise ValueError("main_trap must be supplied for every fixture when stratification is enabled")
    if not fixture_categories:
        fixture_categories = {fixture: "all" for fixture in planned_fixtures}
    planned_by_category = defaultdict(list)
    for fixture in sorted(planned_fixtures, key=str):
        planned_by_category[fixture_categories[fixture]].append(fixture)
    paired_fixtures = {key[0] for key, a, b in pairs}
    categories = sorted(planned_by_category, key=str)
    strata = {category: {
        "weight": len(planned_by_category[category]) / len(planned_fixtures),
        "planned_fixture_clusters": len(planned_by_category[category]),
        "paired_fixture_clusters": sum(f in paired_fixtures for f in planned_by_category[category]),
    } for category in categories}
    result["strata"] = strata
    result["fixture_clusters"] = len(paired_fixtures)
    if result["stratified"]:
        result["method"] = "fixed-category stratified paired hierarchical fixture/seed percentile bootstrap"
    if not pairs:
        return result
    missing_categories = [str(category) for category in categories if not strata[category]["paired_fixture_clusters"]]
    if missing_categories:
        result["conclusion"] = "not estimable: no complete pairs in category " + ", ".join(missing_categories)
        return result
    grouped: dict[Any, dict[Any, list[tuple[float, float]]]] = defaultdict(lambda: defaultdict(list))
    for (fixture, trial_seed, task), a, b in pairs:
        grouped[fixture][trial_seed].append((a, b))
    seeds_by_fixture = {}
    for fixture, seeds in grouped.items():
        seeds_by_fixture[fixture] = {s: (statistics.mean(x[0] for x in values),
                                          statistics.mean(x[1] for x in values))
                                     for s, values in seeds.items()}
    fixture_means = {f: (statistics.mean(x[0] for x in seeds.values()),
                         statistics.mean(x[1] for x in seeds.values()))
                     for f, seeds in seeds_by_fixture.items()}
    fixtures_by_category = {category: [f for f in planned_by_category[category] if f in grouped]
                            for category in categories}
    category_means = {category: (statistics.mean(fixture_means[f][0] for f in fixtures),
                                  statistics.mean(fixture_means[f][1] for f in fixtures))
                      for category, fixtures in fixtures_by_category.items()}
    reference_mean = sum(strata[c]["weight"] * category_means[c][0] for c in categories)
    comparison_mean = sum(strata[c]["weight"] * category_means[c][1] for c in categories)
    result.update(reference_mean=reference_mean,
                  comparison_mean=comparison_mean, difference=reference_mean - comparison_mean)
    if len(grouped) < 2:
        result["conclusion"] = "not estimable: fewer than two fixture clusters"
        return result
    # Optional standardized supplement uses the same fixed category weights as
    # the raw contrast. Effective weights are equal among paired fixtures in a
    # category. The weighted sample correction is undefined for one fixture.
    weighted_differences = [(strata[fixture_categories[f]]["weight"] /
                             len(fixtures_by_category[fixture_categories[f]]), a - b)
                            for f, (a, b) in fixture_means.items()]
    difference_mean = reference_mean - comparison_mean
    correction = 1 - sum(weight ** 2 for weight, difference in weighted_differences)
    variance = sum(weight * (difference - difference_mean) ** 2
                   for weight, difference in weighted_differences) / correction if correction > 0 else 0
    if variance > 0:
        result["standardized_paired_fixture_dz"] = difference_mean / math.sqrt(variance)
    if bootstrap < 100:
        raise ValueError("At least 100 bootstrap resamples are required")
    rng = random.Random(seed)
    draws_a, draws_b, draws_d = [], [], []
    for _ in range(bootstrap):
        a = b = 0.0
        for category in categories:
            fixtures = fixtures_by_category[category]
            sample_a, sample_b = [], []
            for fixture in rng.choices(fixtures, k=len(fixtures)):
                seeds = seeds_by_fixture[fixture]
                chosen = rng.choices(sorted(seeds, key=str), k=len(seeds))
                sample_a.append(statistics.mean(seeds[s][0] for s in chosen))
                sample_b.append(statistics.mean(seeds[s][1] for s in chosen))
            a += strata[category]["weight"] * statistics.mean(sample_a)
            b += strata[category]["weight"] * statistics.mean(sample_b)
        draws_a.append(a)
        draws_b.append(b)
        draws_d.append(a - b)
    lo, hi = _quantile(draws_d, 0.025), _quantile(draws_d, 0.975)
    result.update(reference_ci_low=_quantile(draws_a, 0.025), reference_ci_high=_quantile(draws_a, 0.975),
                  comparison_ci_low=_quantile(draws_b, 0.025), comparison_ci_high=_quantile(draws_b, 0.975),
                  difference_ci_low=lo, difference_ci_high=hi,
                  conclusion="no detectable difference" if lo <= 0 <= hi else "detectable difference")
    return result


def judge_agreement(rows: Iterable[dict], dimensions: tuple = ("usefulness", "honesty", "actionability")) -> dict:
    """Test-retest agreement for one judge called twice, not interjudge validity."""
    grouped = defaultdict(dict)
    for row in rows:
        grouped[row["transcript_id"]][row.get("repeat", row.get("judge_repeat"))] = row
    output = {}
    for dimension in dimensions:
        pairs = []
        for repeats in grouped.values():
            if len(repeats) != 2:
                continue
            ordered = [repeats[k] for k in sorted(repeats, key=str)]
            values = [r.get(dimension) for r in ordered]
            if all(_number(v) for v in values):
                pairs.append(values)
        if not pairs:
            output[dimension] = {"n": 0, "exact_agreement": None, "within_one": None,
                                  "mean_absolute_difference": None, "quadratic_weighted_kappa": None}
            continue
        n = len(pairs)
        observed = sum(((a - b) / 4) ** 2 for a, b in pairs) / n
        marg_a = {x: sum(a == x for a, b in pairs) / n for x in range(1, 6)}
        marg_b = {x: sum(b == x for a, b in pairs) / n for x in range(1, 6)}
        expected = sum(marg_a[a] * marg_b[b] * ((a - b) / 4) ** 2
                       for a in range(1, 6) for b in range(1, 6))
        output[dimension] = {"n": n, "exact_agreement": sum(a == b for a, b in pairs) / n,
                             "within_one": sum(abs(a - b) <= 1 for a, b in pairs) / n,
                             "mean_absolute_difference": statistics.mean(abs(a - b) for a, b in pairs),
                             "quadratic_weighted_kappa": 1 - observed / expected if expected else None}
    return output
