#!/usr/bin/env python3
"""
A compact adventure storyworld about a child explorer, a wooden board, and a
transforming solution.

Seed image:
- A little adventurer wants to cross a place the hard way.
- A fragile board is involved.
- A warning against violence pushes the story toward transformation instead.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    form: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Adventure:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    transform_to: str
    help_text: str
    cover: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    adventure: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


PLACES = {
    "dock": Place("dock", "the dock", affords={"cross"}),
    "cove": Place("cove", "the cove", affords={"cross"}),
    "bridgeyard": Place("bridgeyard", "the bridge yard", affords={"cross"}),
}

ADVENTURES = {
    "crossing": Adventure(
        id="crossing",
        verb="cross the creek",
        gerund="crossing the creek",
        rush="dash across the creek",
        risk="broken board",
        zone={"feet"},
        keyword="board",
        tags={"board", "adventure", "transformation"},
    ),
}

TOOLS = {
    "board": Tool(
        id="board",
        label="wooden board",
        phrase="a sturdy wooden board",
        transform_to="bridge",
        help_text="turn the board into a little bridge",
        cover={"feet"},
        guards={"break"},
    ),
}

GIRL_NAMES = ["Mia", "Ava", "Luna", "Nora", "Zoe", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Eli", "Theo", "Ben", "Max"]
TRAITS = ["brave", "curious", "lively", "stubborn", "cheerful"]


def reasonableness_gate(place: str, adventure: str, tool: str) -> bool:
    return place in PLACES and adventure in ADVENTURES and tool in TOOLS


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, t) for p in PLACES for a in ADVENTURES for t in TOOLS if reasonableness_gate(p, a, t)]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ADVENTURES.items():
        lines.append(asp.fact("adventure", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
        lines.append(asp.fact("risk", aid, a.risk))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("transforms_to", tid, t.transform_to))
        for c in sorted(t.cover):
            lines.append(asp.fact("covers", tid, c))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,T) :- place(P), adventure(A), tool(T), affords(P,A).
has_fix(A,T) :- risk(A,_), tool(T), transforms_to(T,_).
valid_story(P,A,T) :- valid(P,A,T), has_fix(A,T).
#show valid/3.
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a transforming board.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.adventure:
        combos = [c for c in combos if c[1] == args.adventure]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, adventure, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, adventure=adventure, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def predict_broken(world: World, hero: Entity, adventure: Adventure) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["strain"] = 1.0
    return True


def tell(place: Place, adventure: Adventure, tool: Tool, name: str, gender: str, helper: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait], meters={"joy": 0.0}, memes={"want": 0.0}))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper, label=f"the {helper}", meters={"care": 0.0}))
    board = world.add(Entity(id="board", type="board", label="board", phrase=tool.phrase, owner=hero.id, caretaker=helper_ent.id, region="feet", meters={"break": 0.0}, form="board"))
    world.facts.update(hero=hero, helper=helper_ent, board=board, adventure=adventure, tool=tool)

    world.say(f"{hero.id} was a little {trait} {gender} who loved adventure and noticed every path near {place.label}.")
    world.say(f"{hero.pronoun().capitalize()} found {board.phrase} and wanted to {adventure.verb}.")
    world.para()
    world.say(f"At {place.label}, the creek looked quick and shiny, and {hero.id} wanted to {adventure.rush}.")
    world.say(f"{hero.id} raised {hero.pronoun('possessive')} hands, but {hero.pronoun('possessive')} {helper} said, \"No violence on the board, and no smashing our way across.\"")
    hero.memes["want"] += 1
    board.meters["stress"] = 1.0
    board.meters["break"] = 1.0
    world.para()
    world.say(f"{hero.id} frowned for a moment, then noticed the board could become something better.")
    world.say(f"{helper_ent.label.capitalize()} smiled and said, \"Let's {tool.help_text}.\"")
    board.form = tool.transform_to
    board.label = "little bridge"
    board.phrase = "a little bridge of wood"
    board.meters["stress"] = 0.0
    board.meters["break"] = 0.0
    hero.meters["joy"] += 1
    hero.memes["want"] = 0.0
    world.say(f"Together they tied it down, and the board changed into {board.phrase}.")
    world.say(f"{hero.id} crossed safely, laughing as the new bridge held steady under {hero.pronoun('object')}.")
    world.say(f"By the end, the board was no longer just a board; it had become a bridge for a brave little adventure.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    ad = f["adventure"]
    return [
        f'Write a short adventure story for a young child that includes the word "board" and the word "violence".',
        f"Tell a gentle adventure about {hero.id}, who wants to {ad.verb}, but learns a safer transformation instead.",
        f"Write a child-friendly story where a board changes into something useful during a creek-crossing adventure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    board = f["board"]
    ad = f["adventure"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do near {world.place.label}?",
            answer=f"{hero.id} wanted to {ad.verb}. The creek looked exciting, but it also needed a careful plan.",
        ),
        QAItem(
            question=f"Why did {helper.label} say no violence on the board?",
            answer=f"{helper.label.capitalize()} wanted {hero.id} to stay safe and not smash the board. The better idea was to change it into a bridge.",
        ),
        QAItem(
            question=f"What did the board become at the end?",
            answer=f"The board became a little bridge, so {hero.id} could cross safely and finish the adventure with a happy laugh.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a board?",
            answer="A board is a flat piece of wood that people can carry, build with, or use to make something sturdier.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new form, like a board turning into a bridge.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.form:
            bits.append(f"form={e.form}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(out)


CURATED = [
    StoryParams(place="dock", adventure="crossing", tool="board", name="Mia", gender="girl", helper="mother", trait="brave"),
    StoryParams(place="cove", adventure="crossing", tool="board", name="Leo", gender="boy", helper="father", trait="curious"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ADVENTURES[params.adventure], TOOLS[params.tool], params.name, params.gender, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, adventure, tool) combos ({len(stories)} with story proof):\n")
        for p, a, t in triples:
            print(f"  {p:10} {a:10} {t:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.adventure} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
