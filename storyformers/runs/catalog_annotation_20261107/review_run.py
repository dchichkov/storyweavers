"""Aggregate structural checks and review evidence; never infer semantic labels."""

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from authoring import ROOT, validate, write_json


def review():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    catalog = {row["key"] for row in map(json.loads, (ROOT.parents[1] / "catalog" / "attributes.jsonl").read_text().splitlines())}
    structural = {"token", "index", "start", "end", "kind", "position", "word_index"}
    basic = structural | {"pos", "lemma", "scope_id"}
    summaries, features, proposals, errors = [], Counter(), defaultdict(list), []
    for source in manifest["stories"]:
        sid = source["id"]
        folder = ROOT / "annotations" / sid
        required = ["author.py", "annotations.jsonl", "entities.json", "events.json", "scopes.json",
                    "propositions.json", "evidence.json", "new_attributes.json", "feedback.json",
                    "metadata.json", "validation.json"]
        missing = [name for name in required if not (folder / name).exists()]
        if missing:
            summaries.append(dict(story_id=sid, phase=source["phase"], status="pending", missing=missing))
            continue
        report = validate(sid)
        rows = [json.loads(line) for line in (folder / "annotations.jsonl").read_text().splitlines()]
        words = [row for row in rows if row["kind"] == "word"]
        metadata = json.loads((folder / "metadata.json").read_text())
        feedback = json.loads((folder / "feedback.json").read_text())
        local_errors = list(report["errors"])
        text = "".join(row["token"] for row in rows)
        if hashlib.sha256(text.encode()).hexdigest() != source["sha256"]:
            local_errors.append("lossless reconstruction/source hash mismatch")
        if metadata["source_sha256"] != source["sha256"]:
            local_errors.append("annotation provenance/source hash mismatch")
        prompt = ROOT / "prompts" / f"annotate_{metadata['prompt_version']}.md"
        if not prompt.exists() or hashlib.sha256(prompt.read_bytes()).hexdigest() != metadata["prompt_sha256"]:
            local_errors.append("annotation prompt changed since save")
        overrides = ROOT / "prompts" / "catalog_overrides.json"
        if hashlib.sha256(overrides.read_bytes()).hexdigest() != metadata["catalog_overrides_sha256"]:
            local_errors.append("catalog overrides changed since save")
        if metadata["mode"] != "whole_story_retrospective":
            local_errors.append("wrong annotation mode")
        if feedback.get("reviewed_all_words") is not True:
            local_errors.append("annotator has not confirmed reviewing all words")
        count = Counter(key for row in words for key in row if key not in structural)
        features.update(count)
        for definition in json.loads((folder / "new_attributes.json").read_text()):
            proposals[definition["key"]].append(dict(story_id=sid, definition=definition))
        for error in local_errors:
            errors.append(f"{sid}: {error}")
        summaries.append(dict(story_id=sid, phase=source["phase"], status="structurally_valid" if not local_errors else "invalid",
                              prompt_version=metadata["prompt_version"], words=len(words), tokens=len(rows),
                              entities=report["entities"], events=report["events"],
                              canonical_features=sorted(set(count) & catalog), feature_counts=dict(count.most_common()),
                              words_with_features_beyond_pos_lemma_scope=sum(bool(set(row) - basic) for row in words),
                              pos_unknown_words=[row["word_index"] for row in words if row["pos"] == "unknown"],
                              errors=local_errors, feedback=feedback))
    collisions = []
    for key, uses in proposals.items():
        # Different examples are fine; meaning, scope and type need review.
        signatures = {json.dumps({name: item["definition"][name] for name in ("type", "description", "scope")}, sort_keys=True)
                      for item in uses}
        if len(signatures) > 1:
            collisions.append(dict(key=key, stories=[item["story_id"] for item in uses], definitions=uses))
    complete = [row for row in summaries if row["status"] != "pending"]
    result = dict(mode="whole_story_retrospective", expected_stories=len(summaries), completed_stories=len(complete),
                  valid_stories=sum(row["status"] == "structurally_valid" for row in summaries),
                  total_words=sum(row["words"] for row in complete),
                  distinct_canonical_features=len(set(features) & catalog), canonical_catalog_size=len(catalog),
                  canonical_feature_counts={key: value for key, value in features.most_common() if key in catalog},
                  new_attribute_proposals=dict(proposals), extension_definition_conflicts=collisions,
                  errors=errors, stories=summaries,
                  limits="Checks shape, losslessness, declared types, identity links and provenance. Semantic quality requires the separate phase reviews. Missing features are unknown or unannotated, not false.")
    write_json(ROOT / "reviews" / "progress.json", result)
    print(json.dumps({key: result[key] for key in ("expected_stories", "completed_stories", "valid_stories", "total_words", "distinct_canonical_features", "errors")}))
    return result


if __name__ == "__main__":
    review()
