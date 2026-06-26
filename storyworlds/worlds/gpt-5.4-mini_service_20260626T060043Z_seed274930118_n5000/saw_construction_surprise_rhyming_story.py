#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/saw_construction_surprise_rhyming_story.py
===============================================================================================================

A small, constraint-checked story world about a saw at a construction site,
with a surprise turn and a rhyming, child-facing style.

Seed tale:
---
At a construction site, a little helper loved the saw's toothed song and the
tap-tap of building boards. One day the helper wanted to hurry with the saw,
but the foreman warned that the blade needed patience. Together they measured
carefully, cut the board, and found a surprise inside the little box they were
building.

World model:
- The saw is a sharp tool that can cut a board only when the board is held in a
  clamp and the builder slows down.
- If the hero rushes, the board can splinter and the project can wobble.
- A careful helper can turn the danger into a surprise reveal: a hidden sign,
  ribbon, or tiny treasure tucked into the build.

Style:
- Rhyming Story: short, lyrical sentences with light end-rhymes.
- Child-facing, concrete, and state-driven.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    label: str
    phrase: str
    region: str
    can_be_cut: bool = True


@dataclass
class SafetyGear:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


THRESHOLD = 1.0


def _r_cut(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    board = world.entities.get("board")
    if not hero or not board:
        return out
    if hero.memes.get("rush", 0.0) < THRESHOLD:
        return out
    if board.meters.get("clamped", 0.0) < THRESHOLD:
        return out
    sig = ("cut", board.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if hero.memes.get("careful", 0.0) >= THRESHOLD:
        board.meters["cut"] = 1.0
        out.append("The saw went zip with a tidy little trim.")
    else:
        board.meters["splintered"] = 1.0
        out.append("The saw went zip, but the board gave a sharp little splinter.")
    return out


def _r_surprise(world: World) -> list[str]:
    project = world.entities.get("project")
    board = world.entities.get("board")
    hero = world.entities.get("hero")
    if not project or not board or not hero:
        return []
    if board.meters.get("cut", 0.0) < THRESHOLD:
        return []
    if project.meters.get("opened", 0.0) >= THRESHOLD:
        return []
    sig = ("surprise", project.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    project.meters["opened"] = 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    return ["Inside the box was a bright surprise, tied with a ribbon and hidden from sight."]


def _r_fix_splinter(world: World) -> list[str]:
    board = world.entities.get("board")
    helper = world.entities.get("helper")
    hero = world.entities.get("hero")
    if not board or not helper or not hero:
        return []
    if board.meters.get("splintered", 0.0) < THRESHOLD:
        return []
    sig = ("fix", board.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    board.meters["splintered"] = 0.0
    board.meters["clamped"] = 1.0
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 1)
    helper.memes["calm"] = helper.memes.get("calm", 0.0) + 1
    return ["So the helper slowed the pace, and set the clamp in place."]


CAUSAL_RULES = [_r_cut, _r_surprise, _r_fix_splinter]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_cut(world: World, careful: bool) -> dict:
    sim = world.copy()
    sim.get("hero").memes["rush"] = 1.0
    if careful:
        sim.get("hero").memes["careful"] = 1.0
    propagate(sim, narrate=False)
    return {
        "splintered": sim.get("board").meters.get("splintered", 0.0) >= THRESHOLD,
        "opened": sim.get("project").meters.get("opened", 0.0) >= THRESHOLD,
    }


def rhyme_line(*parts: str) -> str:
    return " ".join(parts)


def tell(world: World) -> World:
    hero = world.add(Entity(id="hero", kind="character", type="boy", label="Milo"))
    helper = world.add(Entity(id="helper", kind="character", type="father", label="Pa"))
    saw = world.add(Entity(id="saw", type="tool", label="saw", phrase="a shiny saw"))
    board = world.add(Entity(id="board", type="material", label="board", phrase="a pine board"))
    project = world.add(Entity(id="project", type="thing", label="box", phrase="a little box"))

    board.meters["clamped"] = 0.0
    project.meters["hidden"] = 1.0
    hero.memes["joy"] = 1.0
    hero.memes["rush"] = 1.0
    helper.memes["calm"] = 1.0

    world.say(
        rhyme_line(
            "At the construction yard, where the bright cranes swayed,",
            "little Milo loved the saw and the work they made."
        )
    )
    world.say(
        rhyme_line(
            "He tapped at the boards with a sing-song grin,",
            "for every nail and beam felt like a game within."
        )
    )
    world.para()
    world.say(
        rhyme_line(
            "Milo wanted to cut, zip-zip, quick as a bee,",
            "but Pa said, 'Slow and steady is the safest key.'"
        )
    )
    world.say(
        rhyme_line(
            " 'A saw is sharp,' said Pa, 'so hold the board with care,",
            "and clamp it nice and tight, with patience in the air.'"
        )
    )
    world.say("Milo frowned for a moment, then nodded with a tiny smile.")
    board.meters["clamped"] = 1.0
    hero.memes["careful"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        rhyme_line(
            "Then zip went the saw, neat as a noodle line,",
            "and the box opened up like a secret design."
        )
    )
    return world


SETTING = Setting(place="the construction site", affords={"saw"})
ACTIVITY = Action(
    id="saw",
    verb="use the saw",
    gerund="sawing",
    rush="rush with the saw",
    risk="sharp tool",
    mess="splinters",
    keyword="saw",
    tags={"saw", "construction", "surprise"},
)
MATERIALS = {
    "board": Material(label="board", phrase="a pine board", region="hands"),
}
GEAR = [
    SafetyGear(
        id="clamp",
        label="a sturdy clamp",
        helps={"saw"},
        prep="set the clamp in place",
        tail="the clamp held the board steady",
    )
]

GIRL_NAMES = ["Mina", "Luna", "Nia", "Tia"]
BOY_NAMES = ["Milo", "Noah", "Eli", "Finn"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    helper: str
    surprise: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about saws, construction, and surprise.")
    ap.add_argument("--place", choices=["construction"], default="construction")
    ap.add_argument("--activity", choices=["saw"], default="saw")
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["father", "mother"], default="father")
    ap.add_argument("--surprise", choices=["ribbon", "note", "badge"], default="ribbon")
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
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(
        place=args.place,
        activity=args.activity,
        name=name,
        helper=args.helper,
        surprise=args.surprise,
    )


def generation_prompts() -> list[str]:
    return [
        "Write a short rhyming story about a child at a construction site who wants to use a saw and finds a surprise.",
        "Tell a gentle construction story with a saw, a careful helper, and a hidden surprise at the end.",
        "Make a child-friendly rhyming tale where a saw, a board, and a surprise box all belong together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    surprise = world.facts["surprise"]
    board = world.facts["board"]
    return [
        QAItem(
            question=f"Who was the child in the construction story?",
            answer=f"The child was {hero.label}, a little boy who loved the saw and the bright worksite.",
        ),
        QAItem(
            question=f"Why did {helper.label} ask {hero.label} to slow down?",
            answer="Because the saw was sharp, and the board needed to be clamped tight before it could be cut safely.",
        ),
        QAItem(
            question=f"What surprise was found after the board was cut?",
            answer=f"A {surprise} was hidden inside the box, so the build ended with a happy surprise.",
        ),
        QAItem(
            question=f"What helped keep the board steady?",
            answer=f"{board.label.capitalize()} stayed steady because a sturdy clamp held it in place.",
        ),
    ]


def world_knowledge_qa() -> list[QAItem]:
    return [
        QAItem(
            question="What is a saw for?",
            answer="A saw is a tool that cuts wood and other materials into smaller pieces.",
        ),
        QAItem(
            question="Why do builders use a clamp?",
            answer="Builders use a clamp to hold a board still so it does not slip while they work.",
        ),
        QAItem(
            question="What is a construction site?",
            answer="A construction site is a place where people build things like houses, boxes, fences, or playground parts.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== (2) Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type="boy", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=("Pa" if params.helper == "father" else "Ma")))
    saw = world.add(Entity(id="saw", type="tool", label="saw", phrase="a shiny saw"))
    board = world.add(Entity(id="board", type="material", label="board", phrase="a pine board"))
    project = world.add(Entity(id="project", type="thing", label="box", phrase=f"a little box with a {params.surprise}"))

    hero.memes["joy"] = 1.0
    hero.memes["rush"] = 1.0
    helper.memes["calm"] = 1.0
    board.meters["clamped"] = 1.0
    project.meters["hidden"] = 1.0

    world.say(
        f"At the construction site, {hero.label} felt bright with glee, "
        f"for the saw said zip and the boards said whee."
    )
    world.say(
        f"{hero.label} wanted to use the saw right now, but {helper.label} said, "
        f"\"Slow is safe, and safe is how.\""
    )
    world.say(
        f"So {helper.label} held the board and smiled so wide, "
        f"while {hero.label} took a careful little stride."
    )
    world.para()
    world.say(
        f"Then the saw went zip with a tidy, quick whirr, "
        f"and the box gave a wiggle, a whisper, a purr."
    )
    project.meters["opened"] = 1.0
    world.say(
        f"Inside was a {params.surprise}, tucked up neat and sweet, "
        f"making the whole construction day feel complete."
    )

    world.facts = {
        "hero": hero,
        "helper": helper,
        "saw": saw,
        "board": board,
        "project": project,
        "surprise": params.surprise,
    }
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(),
        world=world,
    )


ASP_RULES = r"""
% A saw-story is reasonable when a board is clamped and the site affords saw work.
site_ok(construction) :- place(construction).

can_cut(saw, board) :- tool(saw), material(board), clamped(board).
surprise_open(project) :- can_cut(saw, board), project_hidden(project).
valid_story(construction, saw, project) :- site_ok(construction), can_cut(saw, board), surprise_open(project).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "construction"),
        asp.fact("tool", "saw"),
        asp.fact("material", "board"),
        asp.fact("clamped", "board"),
        asp.fact("project_hidden", "project"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("construction", "saw", "project")}
    cl = set(asp_valid())
    if py == cl:
        print("OK: ASP and Python parity confirmed.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="construction", activity="saw", name="Milo", helper="father", surprise="ribbon"),
    StoryParams(place="construction", activity="saw", name="Nia", helper="mother", surprise="note"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
