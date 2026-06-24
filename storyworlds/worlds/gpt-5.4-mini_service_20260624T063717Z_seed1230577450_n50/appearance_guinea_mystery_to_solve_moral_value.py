#!/usr/bin/env python3
"""
storyworlds/worlds/appearance_guinea_mystery_to_solve_moral_value.py
===================================================================

A small ghost-story-style world about appearances, a guinea pig, and a mystery
that is solved by choosing a moral value over a spooky first impression.

Premise:
- A child sees a strange "ghost" by appearance alone.
- The ghost turns out to be a guinea pig in disguise-ish circumstances.
- The mystery is solved when the child helps instead of fleeing.

The world model tracks physical meters and emotional memes and lets state drive
the prose. It also includes an inline ASP twin plus a Python reasonableness gate.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Typed entities with physical meters and emotional memes.
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "hiding": 0.0, "help": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "curiosity": 0.0, "kindness": 0.0, "relief": 0.0}


@dataclass
class Location:
    id: str
    label: str
    mood: str
    spooky: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    reveals: str
    appearance: str
    moral: str
    hidden: bool = True


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_clue(self, c: Clue) -> Clue:
        self.clues[c.id] = c
        return c

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
        w = World(self.location)
        w.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        w.clues = dataclasses.deepcopy(self.clues) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.clues)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------

SETTINGS = {
    "attic": Location("attic", "the attic", "dusty and still", spooky=True, tags={"ghost", "dust"}),
    "garden": Location("garden", "the garden", "cool and quiet", spooky=False, tags={"night", "garden"}),
    "hall": Location("hall", "the old hall", "echoing and dim", spooky=True, tags={"ghost", "echo"}),
}

CHARACTERS = {
    "child": {"type": "child", "label": "a brave child"},
    "parent": {"type": "parent", "label": "the parent"},
    "guinea": {"type": "guinea pig", "label": "a small guinea pig"},
    "ghost": {"type": "ghost", "label": "a pale-looking ghost"},
}

CLUES = {
    "white-sheet": Clue(
        id="white-sheet",
        label="a white sheet",
        kind="sheet",
        reveals="It was only a sheet hanging on a line.",
        appearance="a floating white shape",
        moral="appearances can fool you",
    ),
    "guinea-wheels": Clue(
        id="guinea-wheels",
        label="a little wheel toy",
        kind="wheel",
        reveals="The guinea pig had been running under the toy wheel and making it wobble.",
        appearance="a trembling shadow",
        moral="small causes can make big-looking mysteries",
    ),
    "seed-bag": Clue(
        id="seed-bag",
        label="a torn seed bag",
        kind="seed",
        reveals="The bag had spilled seeds, and the guinea pig was only looking for snacks.",
        appearance="a rustling bundle",
        moral="kindness helps more than guessing",
    ),
}

DEFAULT_NAMES = ["Mina", "Theo", "Nia", "Eli", "June", "Owen"]


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate.
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, loc in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            if loc.spooky or clue_id != "seed-bag":
                combos.append((place, clue_id))
    return combos


def explain_rejection(place: str, clue_id: str) -> str:
    if place not in SETTINGS:
        return "(No story: unknown place.)"
    if clue_id not in CLUES:
        return "(No story: unknown clue.)"
    return "(No story: that clue does not fit this place's spooky mystery.)"


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
clue(C) :- clue_def(C).
valid(P,C) :- setting(P), clue_def(C), usable(P,C).
usable(P,"seed-bag") :- setting(P), spooky(P).
usable(P,C) :- setting(P), clue_def(C), C != "seed-bag".
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, loc in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if loc.spooky:
            lines.append(asp.fact("spooky", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue_def", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# World simulation.
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    loc = SETTINGS[params.place]
    w = World(loc)
    child = w.add_entity(Entity(id=params.name, kind="character", type="child", label=params.name))
    parent = w.add_entity(Entity(id="parent", kind="character", type="parent", label="the parent"))
    guinea = w.add_entity(Entity(id="guinea", kind="character", type="guinea pig", label="the guinea pig"))
    clue = w.add_clue(CLUES[params.clue])

    w.facts.update(child=child, parent=parent, guinea=guinea, clue=clue, location=loc)
    return w


def predict_truth(world: World, clue: Clue) -> bool:
    # Mystery solving is justified when the clue truly reveals the appearance.
    return clue.hidden and bool(clue.reveals)


def introduce(world: World) -> None:
    c: Entity = world.facts["child"]
    g: Entity = world.facts["guinea"]
    world.say(f"{c.id} lived near {world.location.label} and loved asking questions.")
    world.say(f"One evening, {c.id} noticed {g.label} and then saw a strange shape in the dark.")
    world.say(f"At first, it looked like {world.facts['clue'].appearance}.")


def mystery(world: World) -> None:
    c: Entity = world.facts["child"]
    clue: Clue = world.facts["clue"]
    c.memes["fear"] += 1
    c.memes["curiosity"] += 1
    world.para()
    world.say(f"{c.id} felt a shiver and whispered, \"Is that a ghost?\"")
    world.say(f"The little mystery mattered because {world.location.mood} made every sound seem bigger.")
    if predict_truth(world, clue):
        world.say("But the child kept looking instead of running away.")


def solve(world: World) -> None:
    c: Entity = world.facts["child"]
    g: Entity = world.facts["guinea"]
    clue: Clue = world.facts["clue"]
    if c.memes["curiosity"] < THRESHOLD:
        raise StoryError("The mystery needs curiosity so it can be solved honestly.")
    clue.hidden = False
    c.memes["kindness"] += 1
    c.memes["fear"] = max(0.0, c.memes["fear"] - 1.0)
    c.memes["relief"] += 1
    world.para()
    world.say(clue.reveals)
    world.say(f"{c.id} saw that the \"ghost\" was really {g.label}, not a haunting at all.")
    world.say(f"{c.id} gently offered a hand, and {g.label} sniffed it and stayed calm.")
    world.say(f"In the end, the answer was simple: the dark shape had only been {clue.kind} and a small animal in motion.")


def moral(world: World) -> None:
    c: Entity = world.facts["child"]
    clue: Clue = world.facts["clue"]
    world.para()
    world.say(f"{c.id} smiled, because {clue.moral}.")
    world.say("The night felt less scary after that, and the little guinea pig looked safe and loved.")


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    c: Entity = world.facts["child"]
    clue: Clue = world.facts["clue"]
    return [
        "Write a short ghost-story-style tale for a young child about a spooky-looking thing that turns out harmless.",
        f"Tell a mystery story where {c.id} thinks a guinea pig is a ghost, then solves the puzzle with kindness.",
        f"Write a gentle story about appearance versus truth, using the clue of {clue.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c: Entity = world.facts["child"]
    g: Entity = world.facts["guinea"]
    clue: Clue = world.facts["clue"]
    loc: Location = world.facts["location"]
    return [
        QAItem(
            question=f"What did {c.id} think the strange shape was at first?",
            answer="At first, the child thought it was a ghost because it only looked spooky in the dark.",
        ),
        QAItem(
            question=f"What was the mystery really about in {loc.label}?",
            answer=f"The mystery was really about {g.label} and {clue.reveals.lower()}",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer="It was solved when the child kept looking closely, listened, and chose kindness instead of fear.",
        ),
        QAItem(
            question="What did the story teach?",
            answer=f"It taught that {clue.moral}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a guinea pig?",
            answer="A guinea pig is a small furry pet that can squeak, sniff, and like gentle handling.",
        ),
        QAItem(
            question="Why can a thing look spooky in the dark?",
            answer="In the dark, shadows and small movements can make ordinary things look much scarier than they are.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find the real answer after noticing clues and thinking carefully.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Generation.
# ---------------------------------------------------------------------------

def valid_story_params() -> list[tuple[str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clue:
        if (args.place, args.clue) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.clue))
    combos = [
        (p, c) for p, c in valid_combos()
        if (args.place is None or p == args.place)
        and (args.clue is None or c == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue = rng.choice(sorted(combos))
    name = args.name or rng.choice(DEFAULT_NAMES)
    return StoryParams(place=place, clue=clue, name=name, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    introduce(world)
    mystery(world)
    solve(world)
    moral(world)
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
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    lines.append(f"location: {world.location.id}")
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} }")
    for c in world.clues.values():
        lines.append(f"clue {c.id}: hidden={c.hidden}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story-style mystery world with a guinea pig and a moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_program_with_show(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_with_show("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, c in combos:
            print(f"  {p:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p, c in sorted(valid_combos()):
            params = StoryParams(place=p, clue=c, name=DEFAULT_NAMES[0], seed=base_seed)
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
