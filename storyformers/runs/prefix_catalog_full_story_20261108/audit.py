"""Read-only provider accounting plus local validation for this full-story run."""

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys

from storyformers.annotation import story_tokens
from storyformers.annotate_prefixes import extract
from storyformers.catalog_prefix_annotation import META, assemble
from storyformers.prefix_annotation import request_prefix

ROOT = Path(__file__).resolve().parent
VERIFY = "--verify" in sys.argv
read = lambda path: json.loads(path.read_text())
manifest = read(ROOT / "manifest.json")[0]
folder = ROOT / manifest["directory"]
story = read(folder / "story.json")["story"]
spans = story_tokens(story)
jobs = sorted((folder / "prefixes").iterdir())
rows = [read(p / "annotation.json") for p in jobs if (p / "annotation.json").exists()]
responses = [read(p) for p in folder.glob("prefixes/**/response.json")]
usage = [r.get("usage") or {} for r in responses]
total_in = sum(u.get("input_tokens", 0) for u in usage)
total_out = sum(u.get("output_tokens", 0) for u in usage)
cached = sum(u.get("input_tokens_details", {}).get("cached_tokens", 0) for u in usage)
writes = sum(u.get("input_tokens_details", {}).get("cache_write_tokens", 0) for u in usage)
reasoning = sum(u.get("output_tokens_details", {}).get("reasoning_tokens", 0) for u in usage)
fields = [{k: v for k, v in r.items() if k not in META | {"index", "token"}} for r in rows]
counts = [len(f) for f in fields]
keys = Counter(k for f in fields for k in f)
bool_keys = Counter(k for f in fields for k, v in f.items() if type(v) is bool)
named_ids = {name: Counter() for name in ("Nia", "Felix", "Leni", "Ivo")}
for row in rows:
    for identifier, entity in row.get("_references", {}).get("entities", {}).items():
        name = entity.get("name")
        if name in {"Ranger", "Ranger Ivo"}:
            name = "Ivo"
        if name in named_ids:
            named_ids[name][identifier] += 1
repairs = [read(p / "metadata.json").get("validation_repairs", 0) for p in jobs if (p / "metadata.json").exists()]
failed = [{"path": str(p.relative_to(ROOT)), **read(p)} for p in folder.glob("prefixes/**/validation.json") if not read(p)["ok"]]
unresolved = [p.name for p in jobs if not (p / "annotation.json").exists() and
              any(not read(v)["ok"] for v in p.glob("**/validation.json"))]
edges, errors = [], Counter()
for dispatch in folder.glob("prefixes/**/attempts/*/dispatch.json"):
    start = read(dispatch)["started_at"]
    result = dispatch.with_name("completed.json")
    if not result.exists():
        result = dispatch.with_name("error.json")
        if result.exists():
            error = read(result)
            errors[f"{error.get('status')}:{error.get('code')}"] += 1
    if result.exists():
        end = start + read(result)["elapsed_seconds"]
        edges += [(start, 1), (end, -1)]
active = peak = 0
for _, change in sorted(edges):
    active += change
    peak = max(peak, active)

# Published Luna/Flex USD per million tokens, checked 2026-11-08.
rates = dict(input=0.05, cached_input=0.005, cache_write_30m=0.0625, output=0.25)
cost_parts = dict(input=(total_in - cached - writes) * rates["input"] / 1e6,
                  cached_input=cached * rates["cached_input"] / 1e6,
                  cache_write_30m=writes * rates["cache_write_30m"] / 1e6,
                  output=total_out * rates["output"] / 1e6)
metrics = dict(source="catalog_annotation_20261107/inputs/18_trail/story.txt",
               words=len(jobs), accepted_words=len(rows), lossless_tokens=len(spans),
               local_records=sum(s["kind"] != "word" for s in spans),
               provider_responses=len(responses), validation_correction_responses=sum(1 for p in folder.glob("prefixes/*/repairs/*/response.json")),
               words_needing_correction=sum(n > 0 for n in repairs), repair_counts=dict(Counter(repairs)),
               input_tokens=total_in, cached_input_tokens=cached, cache_write_tokens=writes,
               ordinary_input_tokens=total_in - cached - writes, output_tokens=total_out,
               reasoning_tokens=reasoning, visible_output_tokens=total_out - reasoning,
               cache_read_fraction=cached / total_in if total_in else None,
               peak_concurrent_requests=peak, dispatch_errors=dict(errors),
               elapsed_seconds_including_pauses=max(t for t, _ in edges)-min(t for t, _ in edges) if edges else 0,
               attributes=dict(mean=statistics.mean(counts) if counts else 0,
                               median=statistics.median(counts) if counts else 0,
                               minimum=min(counts, default=0), maximum=max(counts, default=0),
                               distinct=len(keys), occurrences=sum(counts), frequency=dict(keys.most_common()),
                               boolean_frequency=dict(bool_keys.most_common())),
               named_entity_reference_ids={name: dict(ids.most_common()) for name, ids in named_ids.items()},
               pricing=dict(source="https://developers.openai.com/api/docs/pricing?latest-pricing=flex",
                            usd_per_million=rates, cost_usd_by_category=cost_parts,
                            estimated_cost_usd=sum(cost_parts.values())),
               retained_failed_validation_checks=failed, unresolved_validation_words=unresolved)
if edges:
    metrics["first_dispatch_utc"] = datetime.fromtimestamp(min(t for t, _ in edges), timezone.utc).isoformat()
    metrics["last_completion_utc"] = datetime.fromtimestamp(max(t for t, _ in edges), timezone.utc).isoformat()
if VERIFY:
    assert len(rows) == len(jobs), "missing word annotations"
    for job in jobs:
        body = read(job / "request.json")
        index = int(job.name)
        assert request_prefix(body) == story[:spans[index]["end"]]
        for request in [job / "request.json", *sorted(job.glob("repairs/*/request.json"))]:
            assert request_prefix(read(request)) == request_prefix(body)
        metadata = read(job / "metadata.json")
        accepted = job if not metadata.get("validation_repairs") else job / "repairs" / f"{metadata['validation_repairs']:03d}"
        checked, _ = extract(read(accepted / "request.json"), read(accepted / "response.json"))
        assert checked == read(job / "annotation.json"), "accepted annotation differs from provider response"
    assembled = assemble(story, rows)
    assert assembled == read(folder / "annotations.json")
    assert "".join(r["token"] for r in assembled) == story
    assert all(r["position"]["token"] == r["index"] for r in assembled)
    metrics["checks"] = dict(all_word_records_valid=True, exact_reconstruction=True,
                              exact_prefix_requests=True, corrections_prefix_only=True,
                              accepted_records_unedited=True, positions_aligned=True)
    (ROOT / "measured_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps({k: v for k, v in metrics.items() if k not in {"attributes", "retained_failed_validation_checks", "named_entity_reference_ids"}}, indent=2))
print("Attributes:", {k: v for k, v in metrics["attributes"].items() if k not in {"frequency", "boolean_frequency"}})
print("Unresolved validation words:", unresolved)
