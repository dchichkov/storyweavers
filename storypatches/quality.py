"""Deterministic gates and adapters to the repository's existing quality tools."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re
import sys


SECTION_RE = re.compile(r"^<!-- section:([a-z][a-z0-9_-]*) -->$")


def sentence_count(text: str) -> int:
    return len([part for part in re.split(r"[.!?]+(?:\s+|$)", text.strip()) if part.strip()])


def story_text(markdown: str) -> str:
    paragraphs = []
    for line in markdown.splitlines():
        line = line.strip()
        if line and not line.startswith("# ") and not SECTION_RE.fullmatch(line):
            paragraphs.append(line)
    return "\n\n".join(paragraphs)


def has_dialogue(story: str) -> bool:
    quotes = re.findall(r'["“]([^"”]{2,})["”]', story)
    speakers = set(re.findall(r"\b([A-Z][a-z]+)\s+(?:said|asked|called|whispered|replied|answered)\b", story))
    return len(quotes) >= 2 and len(speakers) >= 2


def load_bundle(bundle: dict[str, str]) -> tuple[dict, str, list[dict]]:
    try:
        outline = json.loads(bundle["outline.json"])
        conversations = json.loads(bundle["conversations.json"])
    except (KeyError, json.JSONDecodeError) as exc:
        raise ValueError(f"bundle JSON is invalid: {exc}") from exc
    if not isinstance(conversations, list):
        raise ValueError("conversations.json must be an array")
    return outline, story_text(bundle["story.md"]), conversations


def validate_bundle(bundle: dict[str, str], seed: dict) -> None:
    outline, story, conversations = load_bundle(bundle)
    if not story or not isinstance(outline.get("title"), str):
        raise ValueError("bundle needs a title and story text")
    heading = bundle["story.md"].splitlines()[0] if bundle["story.md"].splitlines() else ""
    if heading != f"# {outline['title']}":
        raise ValueError("story heading and outline title differ")
    words = story.split()
    if not 150 <= len(words) <= 650:
        raise ValueError(f"story length {len(words)} is outside 150-650 words")
    sections = [match.group(1) for line in bundle["story.md"].splitlines()
                if (match := SECTION_RE.fullmatch(line))]
    if len(sections) < 5 or len(sections) != len(set(sections)):
        raise ValueError("story.md needs at least five unique section anchors")
    missing = [word for word in seed["words"]
               if not re.search(rf"\b{re.escape(word)}\b", story, re.IGNORECASE)]
    if missing:
        raise ValueError("story omitted required words: " + ", ".join(missing))
    if seed["dialogue_required"] and not has_dialogue(story):
        raise ValueError("dialogue-required story lacks a two-speaker exchange")
    kernels = outline.get("kernels")
    if not isinstance(kernels, list) or not 3 <= len(kernels) <= 8 or any(not isinstance(x, str) for x in kernels):
        raise ValueError("outline must contain 3-8 kernel names")
    beats = outline.get("beats")
    if not isinstance(beats, list) or len(beats) < 4:
        raise ValueError("outline needs at least four causal beats")
    cast = {row.get("name") for row in outline.get("cast", []) if isinstance(row, dict)}
    if len(cast) < 2 or any(beat.get("actor") not in cast or beat.get("kernel") not in kernels
                          for beat in beats if isinstance(beat, dict)):
        raise ValueError("outline beats must use declared actors and kernels")
    if any(not isinstance(beat, dict) for beat in beats) or not outline.get("objects"):
        raise ValueError("outline needs structured beats and physical objects")
    variations = outline.get("variations")
    if not isinstance(variations, list) or len(variations) < 3 or any(
            not isinstance(row, dict) or not 3 <= len(row.get("kernels", [])) <= 8 for row in variations):
        raise ValueError("outline needs at least three kernel-composition variations")
    if not 4 <= len(conversations) <= 10:
        raise ValueError("conversations must contain 4-10 items")
    ids = []
    for item in conversations:
        required = {"id", "question", "answer", "follow_up_question", "follow_up_answer"}
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError("conversation item has unexpected fields")
        ids.append(item["id"])
        if any(not isinstance(item[key], str) or not item[key].strip() for key in required):
            raise ValueError("conversation fields must be nonempty strings")
        if sentence_count(item["answer"]) < 2 or sentence_count(item["follow_up_answer"]) < 2:
            raise ValueError("conversation answers must contain at least two sentences")
    if len(ids) != len(set(ids)):
        raise ValueError("conversation IDs must be unique")


def conversation_records(conversations: list[dict]) -> list[dict]:
    return [{
        **item,
        "turns": [
            {"role": "user", "content": item["question"]},
            {"role": "assistant", "content": item["answer"]},
            {"role": "user", "content": item["follow_up_question"]},
            {"role": "assistant", "content": item["follow_up_answer"]},
        ],
    } for item in conversations]


def record_from_bundle(bundle: dict[str, str], *, patch_ids: list[str], seed: int) -> dict:
    outline, story, conversations = load_bundle(bundle)
    return {
        "seed": seed,
        "title": outline["title"],
        "story": story,
        "questions": conversation_records(conversations),
        "patch_ids": patch_ids,
        "outline": outline,
    }


def qa_report(records: list[dict]) -> dict:
    from storyscripts.qa_quality import measure
    report = asdict(measure(records))
    return {key: dict(value) if hasattr(value, "items") else value for key, value in report.items()}


async def evaluate_run(run: Path, *, concurrency=5, selection_seed=777) -> list[dict]:
    """Run the unchanged storyscenes ten-of-100 Terra set-judge protocol."""
    evaluation_dir = Path(__file__).resolve().parents[1] / "storyscenes/evaluation"
    sys.path.insert(0, str(evaluation_dir))
    import openai_world_set_quality as judge

    destination = run / "quality"
    if destination.exists():
        summary = destination / "summary.json"
        if summary.exists():
            return json.loads((destination / "results.json").read_text()) if (destination / "results.json").exists() else []
        raise ValueError("quality directory is incomplete; inspect before retrying paid calls")
    inputs = []
    for story_dir in sorted(run.glob("story_*")):
        path = story_dir / "variants.jsonl"
        if not path.exists():
            continue
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        item = judge.select_set(str(path.resolve()), rows, selection_seed)
        item["sample_file"] = str(path.resolve())
        inputs.append(item)
    results = await judge.run_sets(inputs, destination, concurrency=concurrency)
    (destination / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    return results
