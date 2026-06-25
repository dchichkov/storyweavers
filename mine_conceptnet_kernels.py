#!/usr/bin/env python3
"""
mine_conceptnet_kernels.py - mine typed Storyweavers kernel sketches.

This is the executable-shape companion to mine_conceptnet.py. Instead of only
mining ConceptNet-style triples, it asks the model for small typed kernel
templates that can later be reviewed, normalized, and promoted into gen6/gen7.

Output:
    conceptnet/dataXX.kernel_sketches.jsonl

Use the repo venv:
    ./.venv/bin/python mine_conceptnet_kernels.py extract --datasets 3
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import traceback

OUTPUT_DIR = "conceptnet"
RELATIONS = {
    "IsA", "PartOf", "HasA", "MadeOf", "HasProperty", "DefinedAs",
    "UsedFor", "CapableOf", "AtLocation", "LocatedNear", "ReceivesAction",
    "HasPrerequisite", "HasSubevent", "Causes", "CausesDesire", "Desires",
    "MotivatedByGoal", "CharacterRole", "FeelsToward", "ResolvesBy",
}
TYPES = {"Character", "Physical", "Story", "Concept"}

FEWSHOT = {
    "words": ["laugh", "joke", "happy"],
    "features": ["Dialogue"],
    "summary": "Lucy heard a funny joke, laughed, and felt happy.",
    "story": (
        "Lucy was sitting with her friend Ben. Ben told Lucy a silly joke about "
        "a dancing frog. Lucy laughed at the joke, felt happy, and kissed Ben."
    ),
    "kernels": [{
        "name": "Laugh",
        "concept": "laugh",
        "relation": "Causes",
        "target": "happy",
        "evidence": "Lucy laughed at the joke, felt happy",
        "signature": {
            "actor": "Character",
            "stimulus": "Physical",
        },
        "effects": [
            "actor.Joy += 0.4",
            "actor.Love += 0.1",
        ],
        "renders": [
            "{actor} laughed.",
            "{actor} laughed at {stimulus}.",
        ],
        "code": (
            "@REGISTRY.kernel(\"Laugh\")\n"
            "def Laugh(ctx: World, actor: Character, stimulus: Physical = None, **kw) -> str:\n"
            "    actor.Joy += 0.4\n"
            "    actor.Love += 0.1\n"
            "    ctx.actor = actor\n"
            "    if stimulus is not None:\n"
            "        ctx.current_object = stimulus\n"
            "        return f\"{ctx.say(actor)} laughed at {stimulus}.\"\n"
            "    return f\"{ctx.say(actor)} laughed.\"\n"
        ),
    }],
}


def build_prompt(record: dict) -> str:
    return f"""# Typed Story Kernel Mining

Extract a few tiny executable Storyweavers kernel sketches from the story.
Output ONLY a JSON array. No prose outside JSON.

Each kernel object:
  {{
    "name": "PascalCaseKernelName",
    "concept": "short source concept",
    "relation": "ConceptNet relation",
    "target": "short target concept or effect",
    "evidence": "one exact contiguous quote from the story",
    "signature": {{"slot_name": "Character|Physical|Story|Concept"}},
    "effects": ["small state effects, e.g. actor.Joy += 0.4"],
    "renders": ["template sentence(s) using {{slot}} names"],
    "code": "gen6-style Python function sketch"
  }}

Rules:
- `relation` MUST be one of: {", ".join(sorted(RELATIONS))}.
- Slot types MUST be one of: Character, Physical, Story, Concept.
- Prefer executable causal/action concepts over static taxonomy.
  Good: Laugh, Help, Share, Search, Repair, Comfort, Warn, Apologize.
  Avoid making kernels for plain nouns unless they afford an action.
- Keep each kernel small. One kernel should express one reusable move.
- Use ConceptNet-shaped semantics:
  - Causes -> action/state effect, often Joy/Fear/Sadness/Love changes.
  - CausesDesire/Desires -> goal or desire state.
  - UsedFor/CapableOf -> affordance/action.
  - HasPrerequisite -> precondition comment/effect.
  - ResolvesBy -> conflict/tension resolution.
- Evidence must be a contiguous substring of the story. Do not use "...".
- The code should be a sketch, not a whole file. Use gen6 idioms when possible:
  @REGISTRY.kernel, ctx: World, Character, Physical, ctx.say(actor).
- If a Story or Concept slot is needed in code, leave it untyped or use object;
  preserve the stronger type in the JSON `signature`.
- Return 2-6 kernels. If nothing is reusable, return [].

## Example

Words: {", ".join(FEWSHOT["words"])}
Features: {", ".join(FEWSHOT["features"])}
Summary: {FEWSHOT["summary"]}
Story:
{FEWSHOT["story"]}

Kernels:
{json.dumps(FEWSHOT["kernels"], indent=1)}

## Your turn

Words: {", ".join(record.get("instruction", {}).get("words", []))}
Features: {", ".join(record.get("instruction", {}).get("features", []))}
Summary: {record.get("summary", "")}
Story:
{record.get("story", "")}

Kernels:"""


def _parse_json_array(text: str | None) -> list[dict]:
    if not text:
        return []
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []
    try:
        out = json.loads(text[start:end + 1])
        return out if isinstance(out, list) else []
    except json.JSONDecodeError:
        return []


def _log_failure(story_id: str, message: str, content: str | None = None) -> None:
    print(f"[mine_conceptnet_kernels] {story_id}: {message}", file=sys.stderr)
    if content:
        print(content[:2000], file=sys.stderr)
        if len(content) > 2000:
            print("... [truncated diagnostic output]", file=sys.stderr)


def _output_path(name: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, name)


def _clean_kernel(k: dict) -> dict | None:
    if not isinstance(k, dict):
        return None
    if k.get("relation") not in RELATIONS:
        return None
    if not (k.get("name") and k.get("concept") and k.get("evidence")):
        return None
    signature = k.get("signature") or {}
    if not isinstance(signature, dict):
        return None
    signature = {
        str(slot): typ
        for slot, typ in signature.items()
        if isinstance(typ, str) and typ in TYPES
    }
    if not signature:
        return None
    return {
        "name": str(k["name"]),
        "concept": str(k["concept"]),
        "relation": str(k["relation"]),
        "target": str(k.get("target", "")),
        "evidence": str(k["evidence"]),
        "signature": signature,
        "effects": [str(x) for x in k.get("effects", []) if x],
        "renders": [str(x) for x in k.get("renders", []) if x],
        "code": str(k.get("code", "")).strip(),
    }


async def extract_kernels(client, model: str, record: dict, story_id: str) -> list[dict]:
    resp = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": build_prompt(record)}],
        temperature=0.0,
        max_tokens=8000,
    )
    choice = resp.choices[0]
    content = choice.message.content
    finish_reason = getattr(choice, "finish_reason", None)
    if finish_reason == "length":
        _log_failure(story_id, "finish_reason=length; JSON may be truncated", content)
    elif finish_reason not in (None, "stop"):
        _log_failure(story_id, f"finish_reason={finish_reason}", content)

    raw = _parse_json_array(content)
    if not raw and content and content.strip() != "[]":
        _log_failure(story_id, "could not parse a JSON array from model output", content)
    return [k for item in raw if (k := _clean_kernel(item)) is not None]


async def process_dataset(dataset: str, limit: int | None = None) -> None:
    from openai import AsyncOpenAI
    from tqdm.asyncio import tqdm

    base_url = os.environ.get("LOCALHOST_BASE_URL", "http://localhost:8001/v1")
    api_key = os.environ.get("LOCALHOST_API_KEY", "dummy-key")
    model = os.environ.get("MINE_MODEL", "gpt-oss-120b")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    sem = asyncio.Semaphore(int(os.environ.get("MINE_CONCURRENCY", "32")))

    with open(f"TinyStories_all_data/{dataset}.json") as f:
        stories = json.load(f)
    if limit is not None:
        stories = stories[:limit]

    async def limited(idx: int, record: dict) -> dict:
        story_id = f"{dataset}:{idx}"
        async with sem:
            try:
                kernels = await extract_kernels(client, model, record, story_id)
            except Exception as exc:
                _log_failure(story_id, f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}")
                kernels = []
        return {
            "story_id": story_id,
            "words": record.get("instruction", {}).get("words", []),
            "features": record.get("instruction", {}).get("features", []),
            "kernels": kernels,
        }

    async with client:
        tasks = [limited(i, r) for i, r in enumerate(stories)]
        with open(_output_path(f"{dataset}.kernel_sketches.jsonl"), "w") as out:
            for task in tqdm(asyncio.as_completed(tasks), total=len(tasks),
                             desc=f"Mining kernel sketches {dataset}"):
                out.write(json.dumps(await task, ensure_ascii=False) + "\n")
                out.flush()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    pe = sub.add_parser("extract", help="LLM pass: stories -> typed kernel sketches")
    pe.add_argument("--datasets", nargs="+", type=int, default=[3],
                    help="dataXX indices to process (default: 3)")
    pe.add_argument("--limit", type=int, default=None,
                    help="only process the first N stories, useful for prompt testing")

    args = ap.parse_args()
    if args.mode == "extract":
        for i in args.datasets:
            asyncio.run(process_dataset(f"data{i:02d}", args.limit))


if __name__ == "__main__":
    main()
