#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

@dataclass
class Path:
    id: str
    problem: str
    clue: str
    actions: tuple[str, ...]
    solution: str
    ending: str

@dataclass
class StoryParams:
    path: str
    child: str
    sibling: str
    comfort: str
    seed: int | None = None

PATHS = {
    "stuffy_nose": Path(
        "stuffy_nose",
        "Mina cannot sleep because her nose is stuffy",
        "a warm cup of water and a gentle bedtime routine can help",
        ("notice", "ask", "share_water", "settle"),
        "Mina shares the warm water with Leo and breathes slowly",
        "their quiet room fills with soft, sleepy breathing",
    ),
    "cold_nose": Path(
        "cold_nose",
        "Leo's nose feels cold after he plays by the open window",
        "a soft scarf and a shared blanket can bring warmth",
        ("notice", "ask", "share_blanket", "settle"),
        "Mina shares her blanket and wraps Leo's nose with a soft scarf",
        "the two children listen to the rain while warmth returns",
    ),
    "tickly_nose": Path(
        "tickly_nose",
        "Mina's nose tickles whenever she tries to sleep",
        "a tissue and a small bedtime sneeze can clear the tickle",
        ("notice", "ask", "share_tissue", "settle"),
        "Leo shares a clean tissue and waits patiently for Mina's sneeze",
        "the tickle fades, and a sleepy smile replaces it",
    ),
    "dream_nose": Path(
        "dream_nose",
        "Leo worries that his nose will disappear in a strange dream",
        "a calm story and a trusted hand can make the dream feel smaller",
        ("notice", "ask", "share_story", "settle"),
        "Mina shares her favorite story and holds Leo's hand",
        "the dream changes into a moonlit garden where every nose is safe",
    ),
}

NAMES = ("Mina", "Leo", "Nora", "Sam", "Ivy", "Theo")
COMFORTS = ("a blue quilt", "a stuffed rabbit", "a little moon pillow", "a striped blanket")

OPENINGS = (
    "The moon rested above the little house.",
    "Rain whispered against the window.",
    "The stars blinked over the quiet roof.",
    "A silver cloud drifted past the bedroom.",
)
DIALOGUE = (
    ('"My nose is keeping me awake," {a} whispered.', '"Then we can help it together," {b} said.'),
    ('"Something feels wrong with my nose," {a} said.', '"Tell me what it needs," {b} answered.'),
    ('"I cannot settle down," {a} murmured.', '"You do not have to settle alone," {b} said.'),
)
REACTIONS = (
    "The child who was worried listened carefully.",
    "The room seemed gentler when the children spoke honestly.",
    "A small worry became easier to carry when it was shared.",
)

ASP_RULES = r"""
needs_help(P) :- problem(P).
safe(P) :- needs_help(P), has_clue(P), uses_shared_care(P).
solved(P) :- safe(P), settles(P).
"""

def build_world(params: StoryParams) -> tuple[dict[str, Entity], Path, list[str]]:
    if params.path not in PATHS:
        raise StoryError("Unknown nose bedtime path.")
    path = PATHS[params.path]
    if params.child == params.sibling:
        raise StoryError("The two bedtime children must have different names.")
    world = {
        "child": Entity(params.child, "character", params.child, memes={"worry": 1.0}),
        "sibling": Entity(params.sibling, "character", params.sibling, memes={"care": 1.0}),
        "nose": Entity("nose", "body", "nose", meters={"comfort": 0.0}),
        "comfort": Entity("comfort", "thing", params.comfort),
    }
    trace = []
    for action in path.actions:
        trace.append(action)
        if action == "notice":
            world["child"].memes["bravery"] = 1.0
        elif action == "ask":
            world["child"].memes["trust"] = 1.0
        elif action.startswith("share"):
            world["sibling"].memes["generosity"] = 1.0
            world["nose"].meters["comfort"] += 1.0
        elif action == "settle":
            world["child"].memes["worry"] = 0.0
            world["sibling"].memes["care"] += 1.0
    return world, path, trace

def render(params: StoryParams, rng: random.Random) -> tuple[str, dict[str, Entity], Path, list[str]]:
    world, path, trace = build_world(params)
    a, b = params.child, params.sibling
    opening = rng.choice(OPENINGS)
    d1, d2 = rng.choice(DIALOGUE)
    sentences = [
        f"{opening} It was bedtime, and {a} and {b} were tucked beneath {params.comfort}.",
        f"{a} noticed that {a.lower()}'s nose was the reason sleep would not come. {REACTIONS[rng.randrange(len(REACTIONS))]}",
        d1.format(a=a, b=b),
        d2.format(a=a, b=b),
    ]
    if path.id == "stuffy_nose":
        sentences.append(f"{b} brought a warm cup of water and shared it with {a}. They breathed in slowly, then out slowly, while the moon climbed higher.")
    elif path.id == "cold_nose":
        sentences.append(f"{b} shared the blanket and wrapped a soft scarf around {a}'s nose. Soon the cold feeling began to melt.")
    elif path.id == "tickly_nose":
        sentences.append(f"{b} shared a clean tissue and waited. {a} gave one tiny sneeze, and the tickle slipped away.")
    else:
        sentences.append(f"{b} shared a favorite story and held {a}'s hand. In the story, a friendly moon watched over every nose in the world.")
    sentences.append("Before bedtime, they had already learned that a small worry can grow quiet when someone shares care.")
    sentences.append(f"At last, {path.ending}. Good night, {a} and {b}.")
    return " ".join(sentences), world, path, trace

def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    story, world, path, trace = render(params, rng)
    a, b = params.child, params.sibling
    prompts = [
        f"Write a gentle bedtime story about {a}'s nose and how {b} helps by sharing care.",
        f"Tell a bedtime story in which a worry about a nose is foreshadowed early and resolved through sharing.",
    ]
    story_qa = [
        QAItem(f"Why could {a} not settle at bedtime?", f"{a} could not settle because {path.problem.lower()}."),
        QAItem(f"How did {b} help {a}?", f"{b} helped by sharing care: {path.solution.lower()}."),
        QAItem("What changed by the end of the story?", f"The nose worry became comfortable, and {path.ending}."),
    ]
    world_qa = [
        QAItem("Why can sharing help at bedtime?", "Sharing comfort helps a child feel less alone and makes a small worry easier to carry."),
        QAItem("What is a nose?", "A nose is the part of the face used for smelling and breathing."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)

def valid_paths() -> list[str]:
    return sorted(PATHS)

def asp_facts() -> str:
    lines = []
    for key, path in PATHS.items():
        lines.extend((f"problem({key}).", f"has_clue({key}).", f"uses_shared_care({key}).", f"settles({key})."))
    return "\n".join(lines)

def asp_program(extra: str = "") -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + extra

def verify() -> int:
    for key in PATHS:
        params = StoryParams(key, "Mina", "Leo", "a blue quilt", 1)
        sample = generate(params)
        if not sample.story or "{".encode() in sample.story.encode():
            print("verification failed: unresolved story")
            return 1
        if not any("said" in part or "whispered" in part for part in sample.story.split(".")):
            print("verification failed: missing dialogue")
            return 1
        if params.child not in sample.story or params.sibling not in sample.story:
            print("verification failed: missing character")
            return 1
    print(f"OK: verified {len(PATHS)} executable paths.")
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A nose-sharing bedtime storyworld.")
    parser.add_argument("--path", choices=valid_paths())
    parser.add_argument("--child")
    parser.add_argument("--sibling")
    parser.add_argument("--comfort", choices=COMFORTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAMES)
    sibling = args.sibling or rng.choice([n for n in NAMES if n != child])
    path = args.path or rng.choice(valid_paths())
    comfort = args.comfort or rng.choice(COMFORTS)
    if child == sibling:
        raise StoryError("The bedtime children must have different names.")
    return StoryParams(path, child, sibling, comfort)

def dump_trace(world: dict[str, Entity], trace: list[str]) -> str:
    lines = ["--- world model state ---"]
    for entity in world.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append(f"  actions={trace}")
    return "\n".join(lines)

def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)

def emit(sample: StorySample, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world:
        _, _, trace_steps = build_world(sample.params)
        print(dump_trace(sample.world, trace_steps))
    if qa:
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        raise SystemExit(verify())
    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.asp:
        print(asp_program("#show problem/1.\n#show solved/1."))
        return
    rng = random.Random(args.seed)
    samples = []
    if args.all:
        for i, key in enumerate(valid_paths()):
            samples.append(generate(StoryParams(key, NAMES[i * 2], NAMES[i * 2 + 1], COMFORTS[i % len(COMFORTS)], args.seed)))
    else:
        for _ in range(args.n):
            params = resolve_params(args, rng)
            params.seed = rng.randrange(2**31)
            samples.append(generate(params))
    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) != 1 else samples[0].to_dict(), ensure_ascii=False, indent=2))
        return
    for i, sample in enumerate(samples):
        if i:
            print("\n" + "=" * 60 + "\n")
        emit(sample, args.trace, args.qa)

if __name__ == "__main__":
    main()
