"""Explicit source selection and immutable record identity; no model requests."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from providers import ConfigurationError

SOURCE_FILES = (
    ("skills/worth-using/SKILL.md", "SKILL.snapshot.md"),
    ("skills/worth-using/references/rubric.md", "rubric.snapshot.md"),
    ("docs/BENCHMARK.md", "BENCHMARK.snapshot.md"),
    ("AGENTS.md", "AGENTS.snapshot.md"),
)
TREATMENT_FILES = SOURCE_FILES[:2]
SAFE_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")


def digest(value: bytes | str) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def _git(root: Path, *args: str) -> bytes | None:
    try:
        completed = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    except OSError:
        return None
    return completed.stdout if completed.returncode == 0 else None


def safe_date(value: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ConfigurationError("--date must be an ISO date YYYY-MM-DD") from None
    if parsed.isoformat() != value:
        raise ConfigurationError("--date must be an ISO date YYYY-MM-DD")
    return value


def safe_run_id(value: str) -> str:
    if not SAFE_RUN_ID.fullmatch(value):
        raise ConfigurationError("--run-id must be 1-80 letters, digits, underscores or hyphens, starting with a letter or digit")
    return value


def record_path(root: Path, record: str) -> Path:
    """Only DATE or DATE/RUN_ID, with no symlink escape from records."""
    parts = record.split("/")
    if len(parts) not in {1, 2}:
        raise ConfigurationError("A source record must be YYYY-MM-DD or YYYY-MM-DD/RUN_ID")
    safe_date(parts[0])
    if len(parts) == 2:
        safe_run_id(parts[1])
    base = (root / "docs" / "evaluations").resolve()
    if not base.is_relative_to(root.resolve()):
        raise ConfigurationError("Evaluation records directory escapes the repository")
    path = base.joinpath(*parts)
    if not path.resolve().is_relative_to(base):
        raise ConfigurationError("Evaluation record escapes the records directory")
    return path


def _context_bytes(snapshot: str, value: bytes) -> bytes:
    # The runner updates this one status line after each run. It is metadata,
    # not part of the benchmark plan or either model's treatment prompt.
    if snapshot == "BENCHMARK.snapshot.md":
        return re.sub(rb"(?m)^\*\*Status:.*$", b"**Status: [record pointer]", value)
    return value


@dataclass(frozen=True)
class Sources:
    files: dict[str, bytes]
    provenance: dict
    selection_mode: str
    selected_record: str | None = None

    @property
    def skill(self):
        return self.files["SKILL.snapshot.md"].decode("utf-8")

    @property
    def rubric(self):
        return self.files["rubric.snapshot.md"].decode("utf-8")

    @property
    def version(self):
        return digest(json.dumps({name: digest(self.files[name]) for _, name in TREATMENT_FILES}, sort_keys=True))

    @property
    def identity(self):
        return {"treatment_version": self.version, "commit": self.provenance.get("commit"),
                "selection_mode": self.selection_mode, "selected_record": self.selected_record,
                "context_hashes": {name: digest(_context_bytes(name, data)) for name, data in self.files.items()}}


def load_sources(root: Path, source_record: str | None = None) -> Sources:
    if source_record:
        folder = record_path(root, source_record)
        provenance_path = folder / "source_provenance.json"
        if not provenance_path.is_file():
            raise ConfigurationError("Selected historical record has no source_provenance.json")
        provenance = json.loads(provenance_path.read_text())
        items = {item["snapshot"]: item for item in provenance.get("sources", [])}
        files = {}
        for source_path, snapshot in SOURCE_FILES:
            if snapshot not in items or items[snapshot].get("path") != source_path:
                raise ConfigurationError("Historical provenance does not identify all four expected source files")
            path = folder / snapshot
            if not path.is_file():
                raise ConfigurationError("Selected historical record is missing " + snapshot)
            data = path.read_bytes()
            if git_blob(data) != items[snapshot].get("blob_sha"):
                raise ConfigurationError("Frozen source bytes differ from recorded Git blob: " + snapshot)
            if items[snapshot].get("sha256") and digest(data) != items[snapshot]["sha256"]:
                raise ConfigurationError("Frozen source bytes differ from recorded SHA256: " + snapshot)
            files[snapshot] = data
        return Sources(files, provenance, "historical_record", source_record)
    files = {}
    for source_path, snapshot in SOURCE_FILES:
        path = root / source_path
        if not path.is_file():
            raise ConfigurationError("Checked-out source is missing: " + source_path + "; historical replay requires explicit --source-record")
        files[snapshot] = path.read_bytes()
    head = _git(root, "rev-parse", "--verify", "HEAD")
    commit = head.decode().strip() if head else None
    provenance = {
        "repository": "michaeljabbour/amplifier-skill-worth-using",
        "commit": commit, "source_acquisition": "checked-out source bytes",
        "sources": [{"path": path, "snapshot": snapshot, "blob_sha": git_blob(files[snapshot]),
                     "sha256": digest(files[snapshot])} for path, snapshot in SOURCE_FILES],
    }
    return Sources(files, provenance, "checkout")


def committed_source_errors(root: Path, sources: Sources) -> list[str]:
    """Gate treatment bytes against actual Git objects, not general tree dirt."""
    commit = sources.provenance.get("commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40,64}", commit):
        return ["The selected treatment has no exact Git commit; commit the skill and rubric before live calls"]
    resolved = _git(root, "rev-parse", "--verify", commit + "^{commit}")
    if not resolved or resolved.decode().strip() != commit:
        return ["The selected source commit is unavailable locally; restore its Git history before live calls"]
    errors = []
    for source_path, snapshot in TREATMENT_FILES:
        committed = _git(root, "show", commit + ":" + source_path)
        if committed is None or committed != sources.files[snapshot]:
            errors.append(source_path + " differs from the selected Git commit; commit the corrected treatment before live calls")
        if sources.selection_mode == "checkout" and (root / source_path).read_bytes() != sources.files[snapshot]:
            errors.append(source_path + " changed after source selection; restart with a fresh record")
    return errors


def freeze_sources(output: Path, sources: Sources) -> Sources:
    """Never replace prior snapshots; preserve their original status metadata."""
    for _, snapshot in SOURCE_FILES:
        path = output / snapshot
        if path.exists() and _context_bytes(snapshot, path.read_bytes()) != _context_bytes(snapshot, sources.files[snapshot]):
            raise ConfigurationError("Record contains different frozen sources; select a new --run-id")
    provenance_path = output / "source_provenance.json"
    provenance = sources.provenance
    if provenance_path.exists():
        prior = json.loads(provenance_path.read_text())
        if prior.get("commit") != provenance.get("commit"):
            raise ConfigurationError("Record contains another source commit; select a new --run-id")
        provenance = prior
    output.mkdir(parents=True, exist_ok=True)
    files = {}
    for _, snapshot in SOURCE_FILES:
        path = output / snapshot
        if not path.exists():
            path.write_bytes(sources.files[snapshot])
        files[snapshot] = path.read_bytes()
    if not provenance_path.exists():
        provenance_path.write_text(json.dumps(provenance, indent=2) + "\n")
    return Sources(files, provenance, sources.selection_mode, sources.selected_record)


def model_families() -> tuple[dict, list[str]]:
    """Declarations are operator metadata, never inferred or API-verified."""
    declarations, errors = {}, []
    for role in ("eval", "judge"):
        key = role.upper() + "_MODEL_FAMILY"
        value = " ".join(os.environ.get(key, "").split())
        declarations[role] = {"model_family": value or None,
                              "model_family_basis": "operator_declared_not_api_verified"}
        if not value:
            errors.append(key + " is unset; declare the actual model family explicitly")
    if declarations["eval"]["model_family"] and declarations["eval"]["model_family"].casefold() == (declarations["judge"]["model_family"] or "").casefold():
        errors.append("EVAL_MODEL_FAMILY and JUDGE_MODEL_FAMILY must be different operator-declared families")
    return declarations, errors
