#!/usr/bin/env python3
"""
storyworlds/worlds/effective_conflict_fable.py
==============================================

A small fable-style story world about a practical conflict and an effective
resolution.

The seed idea is a classical tale shape:
- two small forest creatures both want the same useful thing,
- they quarrel over who should have it first,
- a wise helper suggests a fair and effective plan,
- the plan works, and the story ends with harmony and a clear change.

The world model tracks:
- physical meters: hunger, tiredness, distance, blocked paths, carried goods,
- emotional memes: pride, worry, patience, fairness, relief, friendship.

The prose is generated from state changes, not from a frozen template.
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


# ---------------------------------------------------------------------------
# Typed entities with physical meters and emotional memes.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"hare", "rabbit", "fox", "mouse", "bird", "owl", "deer"}
        male = {"wolf", "boar", "crow", "badger", "bear", "squirrel"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "they" if self.plural else self.pronoun("subject")

    def them(self) -> str:
        return "them" if self.plural else self.pronoun("object")


@dataclass
class Place:
    id: str
    label: str
    feature: str
    afford: str


@dataclass
class Need:
    id: str
    verb: str
    noun: str
    object_label: str
    at_risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    effective_for: set[str]
    requires: str
    prep: str
    tail: str


@dataclass
class StoryParams:
    place: str
    need: str
    tool: str
    hero1: str
    hero2: str
    wise_one: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
PLACES = {
    "brook": Place("brook", "the brook", "a narrow wooden bridge", "cross"),
    "hill": Place("hill", "the hill path", "a steep stone path", "climb"),
    "orchard": Place("orchard", "the orchard gate", "a small gate", "pass through"),
}

NEEDS = {
    "water": Need(
        "water",
        verb="reach the water",
        noun="water",
        object_label="fresh water",
        at_risk="thirst",
        keyword="water",
        tags={"water", "thirst"},
    ),
    "apples": Need(
        "apples",
        verb="carry the apples home",
        noun="apples",
        object_label="sweet apples",
        at_risk="hunger",
        keyword="apples",
        tags={"apples", "hunger"},
    ),
    "path": Need(
        "path",
        verb="go on the path",
        noun="path",
        object_label="the way forward",
        at_risk="delay",
        keyword="path",
        tags={"path", "delay"},
    ),
}

TOOLS = {
    "turns": Tool(
        "turns",
        label="turn-taking pebble",
        phrase="a smooth pebble with a painted leaf on it",
        effective_for={"water", "apples", "path"},
        requires="space",
        prep="set the pebble between them and agree to take turns",
        tail="followed the pebble and took turns",
    ),
    "ladder": Tool(
        "ladder",
        label="short ladder",
        phrase="a short ladder",
        effective_for={"path"},
        requires="height",
        prep="lean the ladder safely against the stone step",
        tail="climbed one at a time",
    ),
    "bucket": Tool(
        "bucket",
        label="small bucket",
        phrase="a small bucket",
        effective_for={"water"},
        requires="water",
        prep="carry the bucket down to the brook",
        tail="used the bucket without bumping shoulders",
    ),
}

HEROES = {
    "hare": {"type": "hare", "kind": "character", "label": "hare"},
    "fox": {"type": "fox", "kind": "character", "label": "fox"},
    "mouse": {"type": "mouse", "kind": "character", "label": "mouse"},
    "crow": {"type": "crow", "kind": "character", "label": "crow"},
    "rabbit": {"type": "hare", "kind": "character", "label": "rabbit"},
    "squirrel": {"type": "squirrel", "kind": "character", "label": "squirrel"},
    "owl": {"type": "owl", "kind": "character", "label": "owl"},
    "beaver": {"type": "beaver", "kind": "character", "label": "beaver"},
    "badger": {"type": "badger", "kind": "character", "label": "badger"},
}

NAMES = {
    "hare": ["Luna", "Mabel", "Pip", "Tilly"],
    "fox": ["Fenn", "Rosie", "Sage", "Mira"],
    "mouse": ["Milo", "Nina", "Dot", "Penny"],
    "crow": ["Cora", "Bran", "Moss", "Ivy"],
    "squirrel": ["Cedar", "Bram", "Wren", "Nub"],
    "owl": ["Orin", "Alta", "Hush", "Sora"],
    "beaver": ["Bess", "Toby", "Rill", "June"],
    "badger": ["Boris", "Nell", "Gus", "Dara"],
}

TRAITS = ["busy", "proud", "hasty", "gentle", "curious", "stubborn", "clever"]


# ---------------------------------------------------------------------------
# Story mechanics.
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for need in NEEDS:
            for tool in TOOLS:
                if need in TOOLS[tool].effective_for:
                    out.append((place, need, tool))
    return out


def reason_rejection(need: Need, tool: Tool) -> str:
    if need.id not in tool.effective_for:
        return (
            f"(No story: {tool.label} would not be an effective fix for {need.noun}. "
            f"Choose a tool that really helps with that need.)"
        )
    return "(No story: the requested choices do not make a usable fable.)"


def actor_name_for_type(kind: str, rng: random.Random) -> str:
    return rng.choice(NAMES[kind])


def choose_distinct_heroes(rng: random.Random) -> tuple[str, str]:
    keys = sorted(k for k in HEROES if k != "owl")
    h1 = rng.choice(keys)
    h2 = rng.choice([k for k in keys if k != h1])
    return h1, h2


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
need_help(P,N,T) :- place(P), need(N), tool(T),
                    tool_fits(T,N), not bad_combo(P,N,T).
bad_combo(P,N,T) :- place(P), need(N), tool(T), not tool_fits(T,N).
valid(P,N,T) :- place(P), need(N), tool(T), tool_fits(T,N).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for need in sorted(tool.effective_for):
            lines.append(asp.fact("tool_fits", tid, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Narrative engine.
# ---------------------------------------------------------------------------
def tell(place: Place, need: Need, tool: Tool, hero1_kind: str, hero2_kind: str, wise_kind: str,
         trait1: str, trait2: str, wise_trait: str) -> World:
    world = World(place)
    h1 = world.add(Entity(
        id=actor_name_for_type(hero1_kind, random.Random(hash((place.id, need.id, tool.id, 1)) & 0xFFFFFFFF)),
        kind="character",
        type=hero1_kind,
        label=hero1_kind,
        memes={"pride": 1.0, "worry": 0.0, "patience": 0.0, "fairness": 0.0, "relief": 0.0},
        meters={"distance": 0.0, "hunger": 0.0, "thirst": 0.0},
    ))
    h2 = world.add(Entity(
        id=actor_name_for_type(hero2_kind, random.Random(hash((place.id, need.id, tool.id, 2)) & 0xFFFFFFFF)),
        kind="character",
        type=hero2_kind,
        label=hero2_kind,
        memes={"pride": 1.0, "worry": 0.0, "patience": 0.0, "fairness": 0.0, "relief": 0.0},
        meters={"distance": 0.0, "hunger": 0.0, "thirst": 0.0},
    ))
    wise = world.add(Entity(
        id=actor_name_for_type(wise_kind, random.Random(hash((place.id, need.id, tool.id, 3)) & 0xFFFFFFFF)),
        kind="character",
        type=wise_kind,
        label=wise_kind,
        memes={"wisdom": 1.0, "calm": 1.0, "fairness": 1.0},
    ))
    obj = world.add(Entity(
        id=need.id,
        type="thing",
        label=need.object_label,
        owner=h1.id,
        caretaker=None,
        meters={"scarcity": 1.0},
    ))
    world.facts.update(
        place=place,
        need=need,
        tool=tool,
        h1=h1,
        h2=h2,
        wise=wise,
        obj=obj,
        trait1=trait1,
        trait2=trait2,
        wise_trait=wise_trait,
    )

    # Act 1
    world.say(
        f"At {place.label}, a {trait1} {h1.type} named {h1.id} and a {trait2} {h2.type} named {h2.id} "
        f"each wanted {need.object_label}."
    )
    world.say(
        f"There was only one useful way to {need.verb}, and that made both of them feel important."
    )

    # Act 2
    world.para()
    h1.memes["pride"] += 1
    h2.memes["pride"] += 1
    h1.memes["worry"] += 1
    h2.memes["worry"] += 1
    h1.meters["distance"] += 1
    h2.meters["distance"] += 1
    world.say(
        f"When {h1.id} reached the place first, {h2.id} frowned. "
        f"Both of them spoke at once, and their voices grew sharp."
    )
    world.say(
        f"Neither could move forward well, because wanting first can block even a short path."
    )
    world.say(
        f"Then {wise.id}, the {wise_trait} {wise.type}, listened quietly and saw the whole trouble."
    )

    # Act 3: effective resolution
    world.para()
    world.say(
        f"{wise.id} pointed to {tool.phrase} and suggested a plan that was effective for {need.noun}."
    )
    world.say(
        f'"{tool.prep}," {wise.id} said, "and the quarrel will not need to last."'
    )
    h1.memes["patience"] += 1
    h2.memes["patience"] += 1
    h1.memes["fairness"] += 1
    h2.memes["fairness"] += 1
    h1.memes["pride"] = max(0.0, h1.memes["pride"] - 0.5)
    h2.memes["pride"] = max(0.0, h2.memes["pride"] - 0.5)
    h1.memes["worry"] = 0.0
    h2.memes["worry"] = 0.0

    world.say(
        f"{h1.id} and {h2.id} tried it, and the plan worked at once."
    )
    world.say(
        f"They {tool.tail}, shared {need.object_label}, and found that a fair plan can be stronger than a loud one."
    )
    world.say(
        f"By the end, {h1.id} and {h2.id} were calm, and {wise.id} looked pleased."
    )

    world.facts["resolved"] = True
    world.facts["ending_image"] = f"{h1.id} and {h2.id} shared {need.object_label} beside {place.label}"
    return world


# ---------------------------------------------------------------------------
# QA generation.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for young children about two animals at {f["place"].label} who both want {f["need"].object_label}.',
        f'Tell a gentle animal story where a quarrel becomes calm because a wise helper suggests an effective plan with "{f["tool"].label}".',
        f"Write a moral-style story in which {f['h1'].id} and {f['h2'].id} learn to share, listen, and solve a conflict fairly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h1, h2, wise, place, need, tool = f["h1"], f["h2"], f["wise"], f["place"], f["need"], f["tool"]
    return [
        QAItem(
            question=f"Who were the two animals that wanted {need.object_label} at {place.label}?",
            answer=f"The two animals were {h1.id} and {h2.id}. They both wanted {need.object_label}, which caused the conflict.",
        ),
        QAItem(
            question=f"Why did {h1.id} and {h2.id} argue?",
            answer=(
                f"They argued because both of them wanted the same helpful thing first. "
                f"Their pride made the disagreement louder before they found a fair way forward."
            ),
        ),
        QAItem(
            question=f"What did {wise.id} suggest to make the conflict better?",
            answer=(
                f"{wise.id} suggested using {tool.label}, which was an effective plan for {need.noun}. "
                f"That plan helped them take turns and share."
            ),
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=(
                f"At the end, {h1.id} and {h2.id} were calm instead of quarrelsome. "
                f"They shared {need.object_label}, and the quarrel ended well."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "water": [
        QAItem(
            question="Why do animals and people need water?",
            answer="Animals and people need water to stay alive, drink when they are thirsty, and keep their bodies working well.",
        )
    ],
    "apples": [
        QAItem(
            question="Why are apples a nice snack?",
            answer="Apples are crunchy, sweet, and easy to carry, so they make a good snack or treat.",
        )
    ],
    "path": [
        QAItem(
            question="Why does a path help in the forest?",
            answer="A path helps travelers move safely and quickly, so they do not have to guess where to go.",
        )
    ],
    "turns": [
        QAItem(
            question="What does it mean to take turns?",
            answer="Taking turns means each person gets a fair chance one after the other.",
        )
    ],
    "ladder": [
        QAItem(
            question="What is a ladder for?",
            answer="A ladder helps someone climb up or reach something that is higher than the ground.",
        )
    ],
    "bucket": [
        QAItem(
            question="What is a bucket for?",
            answer="A bucket is useful for carrying water or other small things from one place to another.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    for tag in f["need"].tags | {f["tool"].id}:
        out.extend(WORLD_KNOWLEDGE.get(tag, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about conflict and an effective plan.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero1", choices=[k for k in HEROES if k != "owl"])
    ap.add_argument("--hero2", choices=[k for k in HEROES if k != "owl"])
    ap.add_argument("--wise-one", dest="wise_one", choices=["owl"])
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
    if args.need and args.tool and args.need not in TOOLS[args.tool].effective_for:
        raise StoryError(reason_rejection(NEEDS[args.need], TOOLS[args.tool]))
    filt = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.need is None or c[1] == args.need)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not filt:
        raise StoryError("(No valid combination matches the given options.)")
    place, need, tool = rng.choice(sorted(filt))
    h1, h2 = choose_distinct_heroes(rng)
    return StoryParams(
        place=place,
        need=need,
        tool=tool,
        hero1=h1,
        hero2=h2,
        wise_one="owl",
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    need = NEEDS[params.need]
    tool = TOOLS[params.tool]
    hero1_kind = params.hero1
    hero2_kind = params.hero2
    wise_kind = params.wise_one

    trait1 = random.Random(hash((params.place, params.need, params.tool, "t1")) & 0xFFFFFFFF).choice(TRAITS)
    trait2 = random.Random(hash((params.place, params.need, params.tool, "t2")) & 0xFFFFFFFF).choice(TRAITS)
    wise_trait = "wise"

    world = tell(place, need, tool, hero1_kind, hero2_kind, wise_kind, trait1, trait2, wise_trait)
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


def asp_verify_wrapper() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify_wrapper())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, need, tool) combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, need, tool in sorted(valid_combos()):
            params = StoryParams(place=place, need=need, tool=tool, hero1="hare", hero2="fox", wise_one="owl")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            rng = random.Random(seed)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
