"""Compare a reviewed story and causal Luna run; replay adjudicated prefixes."""
import argparse
import asyncio
from collections import Counter
import json
import os
from pathlib import Path

from . import catalog_prefix_v3 as contract
from .annotate import freeze, read, save
from .annotate_prefixes import annotate_jobs
from .annotation import story_tokens

ROOT = Path(__file__).resolve().parents[1]
STRUCTURAL = {"index", "token", "start", "end", "kind", "position", "word_index"}


def comparison(manual, generated):
    assert [(r["index"], r["token"]) for r in manual] == [(r["index"], r["token"]) for r in generated]
    def stats(rows):
        keys = Counter(k for row in rows for k in row if k not in STRUCTURAL and not k.startswith("_"))
        families = Counter()
        for key, count in keys.items():
            families[contract.registry().get(key, {}).get("family", "extension")] += count
        return dict(words=len(rows), fields=sum(keys.values()), distinct_fields=len(keys),
                    mean_fields=sum(keys.values()) / len(rows), family_occurrences=dict(families))
    result = dict(manual=stats(manual), luna=stats(generated), caveat="Retrospective labels are a review aid, not causal ground truth. Raw reference IDs use different schemes.")
    for field in ("pos", "lemma"):
        differences = [dict(index=a["index"], token=a["token"], manual=a.get(field), luna=b.get(field))
                       for a, b in zip(manual, generated) if a.get(field) != b.get(field)]
        result[field] = dict(agree=len(manual)-len(differences), total=len(manual), differences=differences)
    return result


def check(row, assertion):
    value = row
    for key in assertion.get("path", "").split("."):
        if key:
            value = value.get(key) if isinstance(value, dict) else None
    kind, expected = assertion["kind"], assertion.get("value")
    if kind == "equals": return value == expected
    if kind == "not_equals": return value != expected
    if kind == "present": return value is not None and value != ""
    if kind == "absent": return value is None
    if kind == "empty": return value is None or value == []
    if kind == "one_of": return value in expected
    scopes, current, seen = row.get("_references", {}).get("scopes", {}), row.get("scope_id"), set()
    while current and current not in seen:
        seen.add(current)
        entry = scopes.get(current, {})
        if kind == "scope_kind" and entry.get("kind") in expected: return True
        if kind == "quote" and current == expected: return True
        current = entry.get("parent")
    if kind in {"scope_kind", "quote"}: return False
    raise ValueError(f"unknown review check: {kind}")


def score(cases, records):
    results = []
    for case in cases:
        row = records.get(case["index"], {})
        checks = [dict(**item, passed=bool(row) and check(row,item)) for item in case["checks"]]
        results.append(dict(index=case["index"], token=case["token"], reason=case["reason"],
                            checks=checks, passed=all(c["passed"] for c in checks), record_available=bool(row)))
    return dict(cases_passed=sum(r["passed"] for r in results), cases_total=len(results),
                checks_passed=sum(c["passed"] for r in results for c in r["checks"]),
                checks_total=sum(len(r["checks"]) for r in results), cases=results)


async def run(options):
    spec = read(options.cases)
    story = (ROOT / spec["story_file"]).read_text()
    spans = story_tokens(story)
    options.out.mkdir(parents=True, exist_ok=True)
    freeze(options.out / "review_spec.json", spec)
    manual = [json.loads(line) for line in (ROOT / spec["manual_annotations"]).read_text().splitlines()]
    baseline = ROOT / spec["baseline_directory"]
    generated = read(baseline / "annotations.json")
    save(options.out / "comparison.json", comparison([r for r in manual if r["kind"] == "word"],
                                                      [r for r in generated if r["kind"] == "word"]))
    prefix, jobs = contract.shared_prefix(), []
    freeze(options.out / "prompt.json", dict(version=contract.VERSION,prefix=prefix))
    for case in spec["cases"]:
        span = spans[case["index"]]
        assert span["token"] == case["token"] and span["kind"] == "word"
        directory = options.out / "prefixes" / f"{span['index']:06d}"
        directory.mkdir(parents=True, exist_ok=True)
        freeze(directory / "request.json", contract.prefix_request(story, span["index"],prefix=prefix))
        jobs.append(dict(directory=directory,prefix_end=span["end"],
                         prefix_words=sum(s["kind"]=="word" for s in spans[:span["index"]+1])))
    if options.live:
        # Provider model/tier, cache layout, journals and correction limits are
        # exactly the production prefix runner; case expectations are never sent.
        from openai import AsyncOpenAI
        key = os.environ.get("OPENAI_API_KEY") or (ROOT / ".API_KEY").read_text().strip()
        async with AsyncOpenAI(api_key=key,base_url="https://api.openai.com/v1",timeout=900,max_retries=0) as client:
            await annotate_jobs(jobs,client,concurrency=8,validation_repairs=3)
    old = {case["index"]:read(baseline / "prefixes" / f"{case['index']:06d}" / "annotation.json") for case in spec["cases"]}
    new = {read(p)["index"]:read(p) for p in options.out.glob("prefixes/*/annotation.json")}
    report = dict(note="Selected regression cases, not a held-out accuracy estimate. Expectations were authored from each prefix; retrospective differences are not automatically errors.",
                  baseline=score(spec["cases"],old), revised=score(spec["cases"],new))
    save(options.out / "evaluation.json",report)
    print(json.dumps({k:{field:v for field,v in value.items() if field != "cases"} for k,value in report.items() if isinstance(value,dict)},indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--live",action="store_true",help="Run Luna/Flex for the selected prefixes")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
