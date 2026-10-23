"""Calendar labels for the FICTIONAL dossiers; these are not real study dates."""
from datetime import date, timedelta
import re


FIRST_WEEK = date(2026, 8, 31)
FOLLOWUP = date(2026, 10, 12)
FIRST_SESSION_OFFSETS = {
    "f01": 0, "f02": 1, "f03": 6, "f04": 2,
    "f05": 4, "f06": 0, "f07": 3, "f08": 0,
    "f09": 1, "f10": 3, "f11": 5, "f12": 2,
}
NEXT_WEEK_RECORDS = {
    "f01": "O07", "f02": "O06", "f06": "O06",
    "f07": "O06", "f08": "O06", "f12": "O06",
}
SUMMARY_RECORDS = {
    "f04": ["O06"], "f05": ["O06", "O07"],
    "f10": ["O06"], "f11": ["O06", "O07"],
}


def calendar_for(fixture_id):
    first = FIRST_WEEK + timedelta(days=FIRST_SESSION_OFFSETS[fixture_id])
    starts = [FIRST_WEEK + timedelta(weeks=n) for n in range(6)]
    ends = [start + timedelta(days=6) for start in starts]
    records = {f"O{n:02d}": first.isoformat() for n in range(1, 8)}
    if fixture_id in NEXT_WEEK_RECORDS:
        records[NEXT_WEEK_RECORDS[fixture_id]] = (first + timedelta(weeks=1)).isoformat()
    for observation_id in SUMMARY_RECORDS.get(fixture_id, []):
        records[observation_id] = FOLLOWUP.isoformat()
    records.update({f"O{n + 8:02d}": end.isoformat() for n, end in enumerate(ends)})
    records["O14"] = FOLLOWUP.isoformat()
    return {
        "note": "All calendar dates are invented for this fictional scenario, not real study dates.",
        "first_session_date": first.isoformat(),
        "usage_week_starts": [start.isoformat() for start in starts],
        "usage_week_ends": [end.isoformat() for end in ends],
        "usage_period_end": ends[-1].isoformat(),
        "followup_record_date": FOLLOWUP.isoformat(),
        "record_dates": records,
    }


def stamp_session(text, fixture_id):
    """Add record dates without changing any event or participant wording."""
    records = calendar_for(fixture_id)["record_dates"]
    # Idempotent so a later explicit authoring pass does not duplicate labels.
    text = re.sub(r"(\[O\d{2}\]) \(Fictional record date: \d{4}-\d{2}-\d{2}\) ", r"\1 ", text)
    return re.sub(r"^\[(O\d{2})\] ", lambda match: "[" + match.group(1) + "] (Fictional record date: " + records[match.group(1)] + ") ", text, flags=re.M)


def stamp_usage(rows):
    """Keep existing log fields and counts; add only an explicit weekly calendar."""
    result = []
    for row in rows:
        start = FIRST_WEEK + timedelta(weeks=int(row["week"]) - 1)
        end = start + timedelta(days=6)
        result.append({**row, "week_start": start.isoformat(),
                       "week_end": end.isoformat(), "record_date": end.isoformat()})
    return result
