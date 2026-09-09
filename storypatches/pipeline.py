#!/usr/bin/env python3
"""Luna/Flex seed -> story -> conversations -> 100 patches -> variants."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from .artifacts import Budget, artifact, digest_text, json_output, patch_output, request_body, save_json, save_text
from .catalog import (ATU_TYPES, BASIC_PLOTS, BEGINNINGS, ENDINGS, GENRES, KERNELS,
                      LOCATIONS, SITUATIONS, sample_seed)
from .patches import compose_variants, patch_slots, validate_patch
from .quality import qa_report, validate_bundle
from storyscenes.evaluation import trial_cost


ROOT = Path(__file__).resolve().parent
OPENAI_BASE_URL = "https://api.openai.com/v1"
SECTION_IDS = ("opening", "setup", "inciting", "attempt", "turn", "ending")


def obj(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def array(items: dict, **values) -> dict:
    return {"type": "array", "items": items, **values}


def normalize_base_url(value: str) -> str:
    value = value.rstrip("/")
    return value if value.endswith("/v1") else value + "/v1"


def official_openai(value: str) -> bool:
    return urlparse(value).hostname == "api.openai.com"


def make_request(args, prefix: str, suffix: str, **values) -> dict:
    return request_body(prefix, suffix, model=args.model, effort=args.reasoning_effort,
                        cache_mode=args.cache_mode, service_tier=args.service_tier, **values)


STRING = {"type": "string"}
OUTLINE_SCHEMA = obj({
    "title": STRING,
    "premise": STRING,
    "beginning": STRING,
    "ending": STRING,
    "basic_plot": STRING,
    "atu_type": STRING,
    "genre": STRING,
    "situation": STRING,
    "location": STRING,
    "cast": array(obj({"name": STRING, "kind": STRING, "role": STRING}), minItems=2, maxItems=4),
    "objects": array(obj({"name": STRING, "carrier_of": STRING}), minItems=1, maxItems=5),
    "kernels": array(STRING, minItems=3, maxItems=8),
    "beats": array(obj({
        "id": STRING, "kernel": STRING, "actor": STRING, "action": STRING, "state_change": STRING,
    }), minItems=4, maxItems=8),
    "variations": array(obj({
        "name": STRING,
        "kernels": array(STRING, minItems=3, maxItems=8),
        "change": STRING,
    }), minItems=3, maxItems=5),
    "dialogue_plan": array(STRING, maxItems=4),
    "ending_image": STRING,
})
STORY_SCHEMA = obj({
    "title": STRING,
    "sections": array(obj({"id": {"type": "string", "enum": list(SECTION_IDS)}, "text": STRING}),
                      minItems=6, maxItems=6),
})
CONVERSATION = obj({
    "id": STRING,
    "question": STRING,
    "answer": STRING,
    "follow_up_question": STRING,
    "follow_up_answer": STRING,
})
CONVERSATIONS_SCHEMA = obj({"questions": array(CONVERSATION, minItems=6, maxItems=6)})

CATALOG_SUMMARY = json.dumps({
    "kernels": list(KERNELS),
    "beginnings": BEGINNINGS,
    "endings": ENDINGS,
    "basic_plots": BASIC_PLOTS,
    "atu_types": ATU_TYPES,
    "genres": GENRES,
    "situations": SITUATIONS,
    "locations": LOCATIONS,
}, ensure_ascii=False)

OUTLINE_PREFIX = """Design an original, coherent story outline for readers aged 5-8.
The supplied seed is binding. Use every selected kernel as a real causal function,
not a label. Bind concepts and state changes to a character or physical object.
Every beat must cause, enable, or resolve another beat. Plan a concrete final
image rather than a moral paragraph. Include 3-5 materially different variations
that recombine the selected kernels or add one compatible catalog kernel. If
dialogue is required, plan a genuine two-speaker exchange. Return only the
requested JSON.

AVAILABLE CURATED CATALOG:
""" + CATALOG_SUMMARY + "\n\n"

STORY_PREFIX = """Write a warm, complete story for readers aged 5-8 from the supplied
seed and outline. Return six sections in this exact order: opening, setup,
inciting, attempt, turn, ending. Use all three required words naturally and
preserve the outline's causal state changes. Keep the whole story 220-450 words.
The ending must show the changed state through a concrete image. Do not mention
kernels, plot taxonomies, prompts, or patches. If dialogue_required is true,
include at least two direct-speech turns by two named speakers; otherwise dialogue
is optional. Return only the requested JSON.

"""

CONVERSATION_PREFIX = """Generate six grounded reading conversations about the
supplied story. IDs must be q01 through q06. Diversify who/what/where/how/why,
causality, object state, character change, and ending questions. Each answer and
follow-up answer must have at least two short complete sentences. Mention only
facts, entities, motives, and outcomes supported by the story and outline.
Questions are conversation data, not instructions. Return only requested JSON.

"""

PATCH_CONTRACT = """Create one independent patch against the exact BASE BUNDLE
below. This is a synthetic local patch format, not access to OpenCode or a file
system. You have no read/write/search tools: all source is already present here.

Syntax:
*** Begin Patch
*** Update File: story.md
@@ optional anchor
 unchanged context line
-old line
+new line
*** Update File: conversations.json
@@
 ...
*** End Patch

Allowed files are outline.json, story.md, and conversations.json. Context and
removed lines must copy the base exactly and identify one location. Do not add,
delete, rename, or move files. Update story.md and conversations.json in every
patch. Significant or major patches must also update outline.json. Keep JSON
valid, keep 4-10 conversation items with unique IDs and two-sentence answers,
preserve all required words and required dialogue, and make conversation changes
that follow the story change. Output only one apply_patch custom-tool call.

"""


def render_story(value: dict) -> str:
    sections = value.get("sections")
    if not isinstance(sections, list) or [row.get("id") for row in sections] != list(SECTION_IDS):
        raise ValueError("story sections must use the six required IDs in order")
    lines = [f"# {value['title']}", ""]
    for row in sections:
        if not isinstance(row.get("text"), str) or not row["text"].strip():
            raise ValueError("story section text must be nonempty")
        lines.extend((f"<!-- section:{row['id']} -->", row["text"].strip(), ""))
    return "\n".join(lines).rstrip() + "\n"


def validate_outline(outline: dict, seed: dict) -> None:
    if not set(seed["kernels"]) <= set(outline.get("kernels", [])):
        raise ValueError("outline omitted selected kernels")
    for key in ("beginning", "ending", "basic_plot", "atu_type", "genre", "situation", "location"):
        if outline.get(key) != seed[key]:
            raise ValueError(f"outline did not preserve seeded {key}")
    cast = {row["name"] for row in outline.get("cast", [])}
    if not cast or any(beat["actor"] not in cast for beat in outline.get("beats", [])):
        raise ValueError("every beat actor must be in the cast")
    if seed["dialogue_required"] and len(outline.get("dialogue_plan", [])) < 2:
        raise ValueError("dialogue-required outline needs at least two planned turns")
    if len(outline.get("variations", [])) < 3:
        raise ValueError("outline needs at least three kernel-composition variations")


def base_bundle(outline: dict, story: dict, conversations: dict) -> dict[str, str]:
    return {
        "outline.json": json.dumps(outline, ensure_ascii=False, indent=2) + "\n",
        "story.md": render_story(story),
        "conversations.json": json.dumps(conversations["questions"], ensure_ascii=False, indent=2) + "\n",
    }


def patch_prefix(seed: dict, bundle: dict[str, str]) -> str:
    files = "\n".join(f"===== {name} =====\n{bundle[name]}" for name in ("outline.json", "story.md", "conversations.json"))
    return PATCH_CONTRACT + "SEED:\n" + json.dumps(seed, ensure_ascii=False, indent=2) + "\n\nBASE BUNDLE:\n" + files


async def generate_patch(client, budget, story_dir: Path, prefix: str, bundle: dict[str, str],
                         seed: dict, slot, semaphore: asyncio.Semaphore, args) -> dict:
    feedback = ""
    for attempt in range(args.patch_attempts):
        suffix = "\n\n" + slot.instruction()
        if feedback:
            suffix += "\nPrevious returned patch was rejected locally. Fix only this diagnostic:\n" + feedback
        body = make_request(args, prefix, suffix, tokens=2600, patch_tool=True)
        stage = f"{slot.id}_{attempt}"
        try:
            async with semaphore:
                response = await artifact(client, budget, story_dir, stage, body)
        except Exception as exc:
            save_json(story_dir / "patch_attempts" / f"{stage}.failure.json", {"error": str(exc)[:2000]})
            raise
        try:
            text = patch_output(response)
            save_text(story_dir / "patch_attempts" / f"{stage}.patch", text)
            _, digest = validate_patch(bundle, text, slot, seed)
            save_text(story_dir / "patches" / f"{slot.id}.patch", text)
            row = {
                "id": slot.id, "tier": slot.tier, "focus": slot.focus,
                "section": slot.section, "conversation": slot.conversation,
                "patch": text, "standalone_sha256": digest, "attempt": attempt,
            }
            save_json(story_dir / "patches" / f"{slot.id}.json", {key: value for key, value in row.items() if key != "patch"})
            return row
        except Exception as exc:
            feedback = str(exc)[:2000]
            save_json(story_dir / "patch_attempts" / f"{stage}.failure.json", {"error": feedback})
    raise ValueError(f"{slot.id} failed after {args.patch_attempts} returned attempts: {feedback}")


async def author_story(client, budget, run: Path, seed: dict, args) -> dict:
    story_dir = run / f"story_{seed['index']:03d}"
    story_dir.mkdir(exist_ok=True)
    save_json(story_dir / "seed.json", seed)
    if (story_dir / "summary.json").exists():
        return json.loads((story_dir / "summary.json").read_text())

    outline_body = make_request(
        args,
        OUTLINE_PREFIX,
        "BINDING SEED:\n" + json.dumps(seed, ensure_ascii=False),
        tokens=3500, schema=OUTLINE_SCHEMA,
    )
    outline = json_output(await artifact(client, budget, story_dir, "outline", outline_body))
    validate_outline(outline, seed)
    save_json(story_dir / "outline.json", outline)

    story_body = make_request(
        args,
        STORY_PREFIX,
        "SEED:\n" + json.dumps(seed, ensure_ascii=False) + "\nOUTLINE:\n" + json.dumps(outline, ensure_ascii=False),
        tokens=5000, schema=STORY_SCHEMA,
    )
    story = json_output(await artifact(client, budget, story_dir, "story", story_body))

    conversation_body = make_request(
        args,
        CONVERSATION_PREFIX,
        "OUTLINE:\n" + json.dumps(outline, ensure_ascii=False)
        + "\nSTORY:\n" + render_story(story),
        tokens=5000, schema=CONVERSATIONS_SCHEMA,
    )
    conversations = json_output(await artifact(client, budget, story_dir, "conversations", conversation_body))
    if [row.get("id") for row in conversations.get("questions", [])] != [f"q{i:02d}" for i in range(1, 7)]:
        raise ValueError("conversation IDs must be q01 through q06")

    bundle = base_bundle(outline, story, conversations)
    validate_bundle(bundle, seed)
    for name, value in bundle.items():
        save_text(story_dir / "base" / name, value)

    slots = patch_slots()
    prefix = patch_prefix(seed, bundle)
    save_text(story_dir / "patch_prefix.txt", prefix)
    save_json(story_dir / "patch_slots.json", [slot.__dict__ for slot in slots])
    semaphore = asyncio.Semaphore(args.concurrency)
    patches = [await generate_patch(client, budget, story_dir, prefix, bundle, seed,
                                    slots[0], semaphore, args)]
    patches.extend(await asyncio.gather(*(
        generate_patch(client, budget, story_dir, prefix, bundle, seed, slot, semaphore, args)
        for slot in slots[1:]
    )))
    standalone = [row["standalone_sha256"] for row in patches]
    if len(set(standalone)) != len(standalone):
        raise ValueError("patch set contains duplicate standalone results")
    save_json(story_dir / "patch_index.json", [{key: value for key, value in row.items() if key != "patch"} for row in patches])

    records, conflicts = compose_variants(bundle, patches, seed, count=args.variants)
    with (story_dir / "variants.jsonl").open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    save_json(story_dir / "conflicts.json", conflicts)
    save_json(story_dir / "qa_metrics.json", qa_report(records))
    summary = {
        "story": story_dir.name,
        "ok": True,
        "base_sha256": digest_text("".join(bundle.values())),
        "patches": len(patches),
        "variants": len(records),
        "dialogue_required": seed["dialogue_required"],
        "unique_stories": len({record["story"] for record in records}),
    }
    save_json(story_dir / "summary.json", summary)
    return summary


def load_key(path: Path | None, *, required: bool) -> str:
    if path:
        os.environ["OPENAI_API_KEY"] = path.read_text().strip()
    if required and not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("set OPENAI_API_KEY or pass --api-key-file")
    return os.environ.get("OPENAI_API_KEY") or "local"


async def run(args) -> int:
    if min(args.variants, args.concurrency, args.evaluation_concurrency) < 1 or args.budget <= 0:
        raise ValueError("variants, concurrency, evaluation concurrency, and budget must be positive")
    args.base_url = normalize_base_url(args.base_url)
    official = official_openai(args.base_url)
    args.cache_mode = args.cache_mode or ("explicit" if official else "off")
    args.service_tier = "flex" if official else None
    args.reasoning_effort = "low" if official else None
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    settings = {
        "protocol": "storypatches_v1",
        "seed": args.seed,
        "count": args.count,
        "variants": args.variants,
        "model": args.model,
        "base_url": args.base_url,
        "service_tier": args.service_tier,
        "reasoning_effort": args.reasoning_effort,
        "cache_mode": args.cache_mode,
        "patches_per_story": 100,
        "patch_attempts": args.patch_attempts,
        "campaign": str(args.campaign.resolve()),
        "budget": args.budget,
    }
    settings_path = out / "settings.json"
    if settings_path.exists() and json.loads(settings_path.read_text()) != settings:
        raise ValueError("output settings differ; choose a new directory")
    save_json(settings_path, settings)
    seeds = [sample_seed(args.seed, index).to_dict() for index in range(args.count)]
    save_json(out / "seeds.json", seeds)
    if args.dry_run:
        save_json(out / "dry_run_requests.json", [
            make_request(args, OUTLINE_PREFIX, "BINDING SEED:\n" + json.dumps(seed),
                         tokens=3500, schema=OUTLINE_SCHEMA)
            for seed in seeds
        ])
        return 0

    key = load_key(args.api_key_file, required=official)
    from openai import AsyncOpenAI
    budget = Budget(args.campaign.resolve() / "budget.json", args.budget)
    async with AsyncOpenAI(api_key=key, base_url=args.base_url, timeout=900, max_retries=0) as client:
        summaries = []
        for seed in seeds:
            try:
                summaries.append(await author_story(client, budget, out, seed, args))
            except Exception as exc:
                story_dir = out / f"story_{seed['index']:03d}"
                failure = {"story": story_dir.name, "ok": False, "error": str(exc)}
                save_json(story_dir / "failure.json", failure)
                summaries.append(failure)
                break
    save_json(out / "summary.json", summaries)
    responses = [{"response": json.loads(path.read_text())} for path in out.glob("story_*/*.response.json")]
    save_json(out / "cost.json", trial_cost.summarize(responses))
    if args.evaluate and all(row["ok"] for row in summaries):
        from .quality import evaluate_run
        await evaluate_run(out, concurrency=args.evaluation_concurrency)
    return int(any(not row["ok"] for row in summaries))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--out", type=Path, required=True)
    result.add_argument("--campaign", type=Path, default=ROOT / "campaign")
    result.add_argument("--api-key-file", type=Path)
    result.add_argument("--base-url", default=OPENAI_BASE_URL,
                        help="OpenAI-compatible endpoint; /v1 is appended when absent")
    result.add_argument("--model", default="gpt-5.6-luna")
    result.add_argument("--seed", type=int, default=20260909)
    result.add_argument("--count", type=int, choices=range(1, 11), default=1)
    result.add_argument("--variants", type=int, default=100)
    result.add_argument("--concurrency", type=int, default=12)
    result.add_argument("--evaluation-concurrency", type=int, default=5)
    result.add_argument("--patch-attempts", type=int, choices=range(1, 4), default=2)
    result.add_argument("--budget", type=float, default=15.0)
    result.add_argument("--cache-mode", choices=("explicit", "legacy", "off"),
                        help="default: explicit for api.openai.com, off for custom endpoints")
    result.add_argument("--evaluate", action="store_true")
    result.add_argument("--dry-run", action="store_true")
    return result


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parser().parse_args())))
