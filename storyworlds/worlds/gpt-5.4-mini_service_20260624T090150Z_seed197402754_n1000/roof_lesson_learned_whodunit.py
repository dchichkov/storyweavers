#!/usr/bin/env python3
"""
roof_lesson_learned_whodunit.py
===============================

A small whodunit-style story world about a child, a roof, a mystery, and a
lesson learned.

Premise:
- Something important goes missing.
- The clues point to the roof.
- The hero investigates carefully, discovers the truth, and learns a lesson
  about asking for help instead of climbing where it is not safe.

The world is intentionally small and classical:
- one setting
- a handful of typed entities
- physical meters and emotional memes
- a short causal turn and a clear resolution
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    on_roof: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"height": 0.0, "lost": 0.0, "scratched": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    weather: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    object: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

NAMES_GIRL = ["Maya", "Lily", "Nora", "Zoe", "Ella", "Ava"]
NAMES_BOY = ["Leo", "Finn", "Theo", "Max", "Eli", "Ben"]
PARENTS = {"mother": "mom", "father": "dad"}

OBJECTS = {
    "kite": {
        "label": "kite",
        "phrase": "a bright paper kite with a red tail",
        "finding": "stuck on the roof",
        "reason": "the wind had carried it there",
        "lesson": "ask for help before climbing",
    },
    "ball": {
        "label": "ball",
        "phrase": "a blue ball with a yellow stripe",
        "finding": "resting near the roof gutter",
        "reason": "it had bounced up from the yard",
        "lesson": "look carefully and stay where it is safe",
    },
    "toy": {
        "label": "toy car",
        "phrase": "a little toy car with shiny wheels",
        "finding": "wedged beside a roof tile",
        "reason": "it had slipped from a pocket on the porch",
        "lesson": "slow down and tell a grown-up",
    },
}

SETTINGS = {
    "house": {"place": "the house", "weather": "windy"},
    "cottage": {"place": "the cottage", "weather": "rainy"},
    "home": {"place": "home", "weather": "blustery"},
}

CURATED = [
    StoryParams(name="Maya", gender="girl", parent="mother", object="kite"),
    StoryParams(name="Leo", gender="boy", parent="father", object="ball"),
    StoryParams(name="Nora", gender="girl", parent="mother", object="toy"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is reasonable when something is missing, the roof is involved, and
% there is a safe solution that does not require the child to climb alone.
mystery(O) :- object(O), lost(O), clue_to_roof(O), safe_help(O).
valid_story(O) :- mystery(O).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("roof"))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for pname in SETTINGS:
        lines.append(asp.fact("setting", pname))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(oid,) for oid in OBJECTS}
    if asp_set == py_set:
        print(f"OK: ASP and Python agree on {len(py_set)} stories.")
        return 0
    print("MISMATCH between ASP and Python story sets.")
    print("ASP only:", sorted(asp_set - py_set))
    print("PY only:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    setting = SETTINGS["house"]
    world = World(place=setting["place"], weather=setting["weather"])

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"height": 1.0, "lost": 0.0, "scratched": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=PARENTS[params.parent],
        meters={"height": 1.7, "lost": 0.0, "scratched": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    obj_cfg = OBJECTS[params.object]
    thing = world.add(Entity(
        id="Object",
        kind="thing",
        type=params.object,
        label=obj_cfg["label"],
        phrase=obj_cfg["phrase"],
        owner=child.id,
        carried_by=None,
        on_roof=False,
        meters={"height": 0.0, "lost": 0.0, "scratched": 0.0},
        memes={},
    ))

    world.facts.update(child=child, parent=parent, thing=thing, obj_cfg=obj_cfg, params=params)
    return world


def _mystery_turn(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    thing = world.facts["thing"]
    obj_cfg = world.facts["obj_cfg"]

    child.memes["curiosity"] += 1
    world.say(f"{child.id} noticed that {thing.label} was gone from the porch.")

    parent.memes["worry"] += 1
    world.say(f"{parent.label.capitalize()} frowned and said, \"We should look for clues.\"")

    world.para()
    world.say(f"At the back of {world.place}, a small mark on the wall pointed upward.")
    world.say(f"There was {obj_cfg['finding']}, and that made the roof seem important.")

    thing.meters["lost"] += 1
    child.memes["curiosity"] += 1
    world.facts["clue_to_roof"] = True


def _investigate(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    thing = world.facts["thing"]
    obj_cfg = world.facts["obj_cfg"]

    world.para()
    world.say(f"{child.id} wanted to check the roof right away, but {parent.label} stopped {child.pronoun('object')}.")
    world.say(f"\"The wind was busy today,\" {parent.label} said. \"That is not a job for a child alone.\"")

    child.memes["worry"] += 1
    child.memes["curiosity"] += 1

    world.say(f"So they found a long broom and asked the neighbor to help peek up high.")
    thing.on_roof = True
    world.say(f"Sure enough, the {thing.label} was on the roof because {obj_cfg['reason']}.")


def _resolution(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    thing = world.facts["thing"]
    obj_cfg = world.facts["obj_cfg"]

    world.para()
    world.say(f"The neighbor brought the {thing.label} down safely.")
    child.memes["relief"] += 1
    parent.memes["relief"] += 1
    child.memes["pride"] += 1

    world.say(f"{child.id} hugged {parent.pronoun('object')} and said, \"I learned not to climb for clues.\"")
    world.say(f"{parent.label.capitalize()} smiled. \"That is the right lesson,\" {parent.label} said.")
    world.say(f"In the end, the mystery was solved, {thing.label} was back where it belonged, and the roof stayed a roof, not a playground.")

    world.facts["safe_help"] = True
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    world = make_world(params)
    _mystery_turn(world)
    _investigate(world)
    _resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    obj_cfg = world.facts["obj_cfg"]
    return [
        f'Write a short whodunit for a young child about a missing {obj_cfg["label"]} and a roof clue.',
        f"Tell a gentle mystery story where {p.name} looks for {obj_cfg['label']} near a roof and learns a safety lesson.",
        f'Write a child-friendly detective story that includes the word "roof" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    thing = world.facts["thing"]
    obj_cfg = world.facts["obj_cfg"]
    p = world.facts["params"]

    return [
        QAItem(
            question=f"What went missing in the story?",
            answer=f"{child.id}'s {thing.label} went missing from the porch.",
        ),
        QAItem(
            question=f"What clue helped point them toward the roof?",
            answer=f"They found a small mark and saw {obj_cfg['finding']}, which made the roof seem like the place to check.",
        ),
        QAItem(
            question=f"How did they solve the mystery safely?",
            answer=f"They did not climb alone. {parent.label.capitalize()} and the neighbor helped look up high, and the {thing.label} was brought down safely.",
        ),
        QAItem(
            question=f"What lesson did {p.name} learn?",
            answer=f"{p.name} learned to ask for help before climbing and to stay safe when something is high up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a roof?",
            answer="A roof is the top part of a house that helps keep rain, wind, and sun outside.",
        ),
        QAItem(
            question="Why should a child not climb on a roof alone?",
            answer="A roof can be slippery and high, so climbing alone can be dangerous. A grown-up should help.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to figure out what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes} "
            f"owner={e.owner} carried_by={e.carried_by} on_roof={e.on_roof}"
        )
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style roof story world with a lesson learned.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--object", choices=sorted(OBJECTS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    obj = args.object or rng.choice(sorted(OBJECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    if args.gender == "girl" and args.name is None and name in NAMES_BOY:
        raise StoryError("Requested girl story, but the chosen name is a boy name.")
    return StoryParams(name=name, gender=gender, parent=parent, object=obj)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify_mode() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify_mode())
    if args.asp:
        print(asp_program("#show valid_story/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
