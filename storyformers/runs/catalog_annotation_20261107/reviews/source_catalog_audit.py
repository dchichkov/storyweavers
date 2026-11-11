"""Read-only source/catalog/provenance audit; writes only its adjacent JSON report.

Reproduce from repository root:
  .venv/bin/python storyformers/runs/catalog_annotation_20261107/reviews/source_catalog_audit.py
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

RUN = Path(__file__).resolve().parents[1]
REPO = RUN.parents[2]
SOURCE = REPO / "storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/STORIES.md"
CATALOG = REPO / "storyformers/catalog/attributes.jsonl"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def main():
    mismatches = []
    manifest = read_json(RUN / "manifest.json")
    source_bytes = SOURCE.read_bytes()
    source = source_bytes.decode("utf-8")
    headings = list(re.finditer(r"^## (\d{2}_\w+) \|[^\n]+\n", source, re.M))
    stories = []
    manifest_stories = {r["id"]: r for r in manifest["stories"]}
    for i, heading in enumerate(headings):
        sid = heading.group(1)
        section = source[heading.end():headings[i + 1].start() if i + 1 < len(headings) else len(source)]
        # Remove only LF section separators, never spaces, punctuation or internal whitespace.
        prose = section.strip("\n").encode("utf-8")
        actual = (RUN / "inputs" / sid / "story.txt").read_bytes()
        entry = dict(story_id=sid, heading_line=source.count("\n", 0, heading.start()) + 1,
                     prose_bytes=len(prose), source_prose_sha256=sha(prose), input_sha256=sha(actual),
                     exact_prose_byte_match=prose == actual,
                     manifest_hash_match=sha(actual) == manifest_stories[sid]["sha256"])
        if not entry["exact_prose_byte_match"] or not entry["manifest_hash_match"]:
            mismatches.append({"input": entry})
        stories.append(entry)
    input_ids = sorted(p.parent.name for p in (RUN / "inputs").glob("*/story.txt"))
    if input_ids != sorted(h.group(1) for h in headings) or len(headings) != 20:
        mismatches.append({"source_input_inventory": input_ids})
    if sha(source_bytes) != manifest["source_sha256"]:
        mismatches.append("Original STORIES.md differs from manifest source hash")

    catalog_bytes = CATALOG.read_bytes()
    canonical = [json.loads(line) for line in catalog_bytes.decode().splitlines()]
    by_key = {r["key"]: r for r in canonical}
    feature_files, described = [], []
    for path in sorted((RUN / "prompts").glob("features_*.txt")):
        lines = path.read_text().splitlines()
        local_errors = []
        for number, line in enumerate(lines, 1):
            match = re.fullmatch(r"(A\d{4}) (\S+) \[([^\]]+)\] (.*)", line)
            if not match:
                local_errors.append({"line": number, "issue": "unparsed line"})
                continue
            aid, key, kind, remainder = match.groups()
            described.append((aid, key, kind))
            row = by_key.get(key)
            if row is None:
                local_errors.append({"line": number, "issue": "unknown key", "key": key})
                continue
            prefix = f"{row['description']} Scope: {row['scope']}. Example: "
            exact_description = remainder.startswith(prefix)
            example_equal = exact_description and json.loads(remainder[len(prefix):]) == row["example_value"]
            if (aid, kind) != (row["id"], row["type"]) or not exact_description or not example_equal:
                local_errors.append({"line": number, "key": key, "issue": "canonical metadata differs"})
        feature_files.append(dict(file=path.name, sha256=sha(path.read_bytes()),
                                  described_attributes=len(lines), mismatches=local_errors))
        mismatches.extend({"feature_file": path.name, **error} for error in local_errors)
    expected = [(r["id"], r["key"], r["type"]) for r in canonical]
    exact_inventory = Counter(described) == Counter(expected) and len(described) == len(by_key) == 1024
    if not exact_inventory:
        mismatches.append("Feature description ID/key/type inventory differs from 1024 canonical attributes")
    if sha(catalog_bytes) != manifest["catalog_sha256"]:
        mismatches.append("Canonical catalog differs from manifest catalog hash")

    overrides_path = RUN / "prompts/catalog_overrides.json"
    overrides = read_json(overrides_path)
    override_audit = []
    for override in overrides:
        original = by_key[override["key"]]
        override_audit.append(dict(key=override["key"], canonical_id=original["id"],
                                   original_description=original["description"],
                                   override_description=override["description"],
                                   type_preserved=original["type"] == override["type"],
                                   reason=override["reason"]))
    if {r["key"] for r in overrides} != {"patients", "instruments"} or not all(r["type_preserved"] for r in override_audit):
        mismatches.append("Unexpected participant override inventory/type")

    prompt_hashes = {p.stem.removeprefix("annotate_"): sha(p.read_bytes())
                     for p in sorted((RUN / "prompts").glob("annotate_v*.md"))}
    companion_hashes = {p.name: sha(p.read_bytes()) for p in sorted((RUN / "prompts").glob("*.json"))}
    provenance, incomplete = [], []
    required = ("author.py", "annotations.jsonl", "entities.json", "events.json", "scopes.json",
                "propositions.json", "evidence.json", "new_attributes.json", "feedback.json",
                "metadata.json", "validation.json")
    for sid, spec in manifest_stories.items():
        folder = RUN / "annotations" / sid
        missing = [name for name in required if not (folder / name).is_file()]
        if missing:
            incomplete.append(dict(story_id=sid, manifest_status=spec.get("status", "not_started"), missing=missing))
            continue
        meta = read_json(folder / "metadata.json")
        rows = [json.loads(line) for line in (folder / "annotations.jsonl").read_text().splitlines()]
        entities = read_json(folder / "entities.json")
        events = read_json(folder / "events.json")
        ordinal = int(sid[:2])
        version = "v0" if ordinal <= 2 else "v1" if ordinal <= 8 else "v2" if ordinal <= 14 else "v3"
        checks = dict(expected_phase_prompt=meta["prompt_version"] == version == spec["prompt_version"],
                      current_prompt_hash=meta["prompt_sha256"] == prompt_hashes[version],
                      override_hash=meta["catalog_overrides_sha256"] == sha(overrides_path.read_bytes()),
                      source_hash=meta["source_sha256"] == sha((RUN / "inputs" / sid / "story.txt").read_bytes()),
                      lossless_reconstruction="".join(r["token"] for r in rows).encode() == (RUN / "inputs" / sid / "story.txt").read_bytes(),
                      retrospective_mode=meta["mode"] == "whole_story_retrospective",
                      catalog_count=meta["catalog_attribute_count"] == 1024,
                      saved_validation_clean=read_json(folder / "validation.json")["errors"] == [])
        references = [(field, value) for row in [*rows, *events.values()]
                      for field in ("patients", "instruments") for value in row.get(field, [])]
        checks["participant_arrays_use_registered_entity_ids"] = all(
            isinstance(value, str) and re.fullmatch(r"e[1-9]\d*", value) and value in entities
            for _, value in references)
        entry = dict(story_id=sid, manifest_status=spec["status"], prompt_version=version,
                     prompt_sha256=meta["prompt_sha256"], metadata_sha256=sha((folder / "metadata.json").read_bytes()),
                     participant_reference_count=len(references), checks=checks)
        provenance.append(entry)
        mismatches.extend({"story_id": sid, "provenance_check": key} for key, ok in checks.items() if not ok)
    phase_log = [json.loads(line) for line in (RUN / "reviews/phase_log.jsonl").read_text().splitlines()]
    logged_hash_checks = [{"event": row.get("event", row.get("action")), "prompt": row["prompt"],
                          "matches_current_file": row["prompt_sha256"] == sha((RUN / row["prompt"]).read_bytes())}
                         for row in phase_log if "prompt_sha256" in row]
    if not all(row["matches_current_file"] for row in logged_hash_checks):
        mismatches.append("Logged prompt release hash differs")
    report = dict(
        audit_version=1, audited_at_utc=datetime.now(timezone.utc).isoformat(),
        scope="Direct source prose bytes, full canonical feature definitions, participant erratum and current frozen-version provenance; not a semantic quality verdict.",
        reproduction=".venv/bin/python storyformers/runs/catalog_annotation_20261107/reviews/source_catalog_audit.py",
        method=dict(source_extraction="Match ^## (\\d{2}_\\w+) \\|[^\\n]+\\n headers; slice each body through the next heading; strip only surrounding LF separators; compare remaining UTF-8 bytes directly with input/story.txt. No punctuation, spaces, spelling, Unicode or internal newlines are normalized.",
                    catalog_comparison="Parse every feature line; compare ID/key/type multiset, exact description/scope text and parsed JSON example against canonical rows.",
                    provenance="Audit folders with all twelve required deliverables at snapshot time. Compare expected phase/version, current prompt/override/source hashes, lossless text and saved validation; independently resolve patients/instruments in records and event registry."),
        source=dict(path=str(SOURCE), sha256=sha(source_bytes), section_count=len(headings), stories=stories),
        catalog=dict(path=str(CATALOG), sha256=sha(catalog_bytes), canonical_count=len(canonical),
                     exact_1024_inventory=exact_inventory, feature_files=feature_files),
        participant_override=dict(path=str(overrides_path), sha256=sha(overrides_path.read_bytes()), entries=override_audit,
                                  implementation_evidence="storyformers/annotation.py:111-113 requires unique entity IDs; lines147-149 resolve patients/instruments against registered entities. The trial corrects description/example semantics, retains array types, and leaves archived catalog unchanged."),
        provenance=dict(prompt_hashes=prompt_hashes, companion_file_hashes=companion_hashes,
                        logged_release_hash_checks=logged_hash_checks, completed_artifact_folders=provenance,
                        excluded_incomplete_folders=incomplete,
                        limits=["Matching stored/current hashes proves snapshot consistency, not that no intermediate edit occurred before regeneration.",
                                "Per-annotation metadata stores prompt/source/override hashes and catalog count, but not catalog/example/extension-registry hashes. Catalog provenance is the run manifest; companion current hashes are recorded here.",
                                "Separately logged release hashes are checked when present. Other versions rely on matching per-annotation prompt hashes, phase assignments and release/review records.",
                                "Saved validation reports were inspected rather than reexecuting authors or mutating outputs. In-progress stories are not represented as reviewed."]),
        mismatches=mismatches, result="pass" if not mismatches else "mismatch")
    output = Path(__file__).with_suffix(".json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(result=report["result"], input_stories=len(stories), canonical_attributes=len(canonical),
                          completed_folders=len(provenance), mismatches=mismatches, report=str(output)), indent=2))


if __name__ == "__main__":
    main()
