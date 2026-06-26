#!/usr/bin/env python3
"""
A standalone storyworld for a small mystery about a tall place, a moral choice,
and careful problem solving.

The premise is simple: someone finds a puzzling sign that something important
has gone missing. The tension comes from deciding whether to follow a tempting
shortcut or do the honest, careful thing. The turn comes when the characters use
clues, test ideas, and choose the fair solution. The ending proves that the
problem was solved without cheating.

This world is built to stay small, concrete, and state-driven.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    name: str
    tall: bool
    indoors: bool = False
    clue_kind: str = "whisper"
    affordances: set[str] = field(default_factory=set)


@dataclass
class MysteryItem:
    id: str
    label: str
    phrase: str
    type: str
    hidden_by: str
    risk: str
    value: str
    owner_kind: str = "person"


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    solves: set[str]
    requires_honesty: bool = True


@dataclass
class StoryParams:
    place: str
    mystery: str
    item: str
    tool: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.location)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
LOCATIONS = {
    "clocktower": Location(
        name="the tall clocktower",
        tall=True,
        indoors=False,
        clue_kind="tick",
        affordances={"listen", "climb", "search"},
    ),
    "library": Location(
        name="the library",
        tall=False,
        indoors=True,
        clue_kind="note",
        affordances={"read", "search"},
    ),
    "bridge": Location(
        name="the tall bridge",
        tall=True,
        indoors=False,
        clue_kind="wind",
        affordances={"listen", "search"},
    ),
}

MYSTERIES = {
    "missing_key": MysteryItem(
        id="key",
        label="brass key",
        phrase="a tiny brass key",
        type="key",
        hidden_by="drawer",
        risk="lost",
        value="important",
    ),
    "missing_note": MysteryItem(
        id="note",
        label="paper note",
        phrase="a folded paper note",
        type="note",
        hidden_by="book",
        risk="torn",
        value="secret",
    ),
    "missing_lantern": MysteryItem(
        id="lantern",
        label="lantern",
        phrase="a small lantern",
        type="lantern",
        hidden_by="curtain",
        risk="dark",
        value="useful",
    ),
}

TOOLS = {
    "question": Tool(
        id="question",
        label="a careful question",
        phrase="ask the right person",
        method="asking",
        solves={"moral", "clue"},
    ),
    "map": Tool(
        id="map",
        label="a pocket map",
        phrase="trace the path one step at a time",
        method="mapping",
        solves={"clue", "route"},
    ),
    "lamp": Tool(
        id="lamp",
        label="a little lamp",
        phrase="shine light into the dark corners",
        method="lighting",
        solves={"dark", "clue"},
    ),
    "list": Tool(
        id="list",
        label="a list of clues",
        phrase="check each clue in order",
        method="noting",
        solves={"clue", "logic"},
    ),
}

TRAITS = ["kind", "curious", "brave", "patient", "gentle", "careful"]
NAMES = ["Mina", "Toby", "Nia", "Eli", "Pia", "Owen", "Lena", "Noah"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
reachable(P,L) :- place(P), location(L), tall_location(L).
can_solve(T,M) :- tool(T), mystery(M), tool_solves(T, clue).
can_choose(T) :- tool(T), honest(T).

valid_story(P,M,I,T) :- place(P), mystery(M), item(I), tool(T),
                        reachable(P,L), can_solve(T,M), can_choose(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, loc in LOCATIONS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("location", pid))
        if loc.tall:
            lines.append(asp.fact("tall_location", pid))
        if loc.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(loc.affordances):
            lines.append(asp.fact("afford", pid, a))
    for mid, mis in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("item", mis.id))
        lines.append(asp.fact("risk", mis.id, mis.risk))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.requires_honesty:
            lines.append(asp.fact("honest", tid))
        for s in sorted(tool.solves):
            lines.append(asp.fact("tool_solves", tid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Rules / simulation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, loc in LOCATIONS.items():
        for mis_id, mis in MYSTERIES.items():
            if not loc.tall:
                continue
            for tool_id, tool in TOOLS.items():
                if "clue" not in tool.solves:
                    continue
                combos.append((place, mis_id, mis.id, tool_id))
    return combos


def choose_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str, str]:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.item:
        combos = [c for c in combos if c[2] == args.item]
    if args.tool:
        combos = [c for c in combos if c[3] == args.tool]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")
    return rng.choice(sorted(combos))


def predict_solution(world: World, hero: Entity, item: MysteryItem, tool: Tool) -> bool:
    return item.type in tool.solves or "clue" in tool.solves


def make_story(world: World, hero: Entity, helper: Entity, item: MysteryItem, tool: Tool) -> None:
    loc = world.location
    world.say(
        f"{hero.id} lived near {loc.name}, and the place looked extra tall against the sky."
    )
    world.say(
        f"{hero.id} was a {hero.memes['trait']} little {hero.type} who liked to notice small things."
    )
    world.say(
        f"One morning, {hero.id} found that {item.phrase} was missing from its usual spot."
    )
    world.say(
        f"That was strange, because {item.label} was {item.value} and someone would surely need it later."
    )

    world.para()
    world.say(
        f"{hero.id} followed the faint clues: a soft sound, a corner left open, and a careful look up the stairs."
    )
    if loc.tall:
        world.say(
            f"The tall steps made the search harder, so {hero.id} had to go slowly and think clearly."
        )
    world.say(
        f"{helper.id} wanted to help, but {hero.id} first had to decide whether to tell the truth about what {hero.id} had seen."
    )
    world.say(
        f"Instead of guessing or hiding the clue, {hero.id} chose the honest way and used {tool.label}."
    )

    world.para()
    if tool.id == "question":
        world.say(
            f"With {tool.phrase}, {hero.id} asked the right person and learned that the missing item had been set aside safely."
        )
    elif tool.id == "map":
        world.say(
            f"With {tool.phrase}, {hero.id} traced the path step by step and found the item in the right room."
        )
    elif tool.id == "lamp":
        world.say(
            f"With {tool.phrase}, {hero.id} found a dark nook where the missing item had slipped and waited quietly."
        )
    else:
        world.say(
            f"With {tool.phrase}, {hero.id} sorted the clues one by one and solved the mystery without making a mess of things."
        )
    world.say(
        f"{hero.id} returned {item.label} to its proper place, and {helper.id} smiled because the fair choice worked."
    )
    world.say(
        f"In the end, the tall place was no longer puzzling, and {hero.id} felt proud for solving the problem the right way."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(sample: StorySample) -> list[str]:
    p = sample.params
    return [
        f"Write a short mystery story about a child named {p.name} in a tall place.",
        f"Tell a gentle story where {p.name} solves a missing-item mystery by being honest.",
        f"Write a child-friendly mystery with a clear clue, a careful choice, and a happy ending.",
    ]


def story_qa(sample: StorySample) -> list[QAItem]:
    p = sample.params
    return [
        QAItem(
            question=f"Where did {p.name} find the mystery?",
            answer=f"{p.name} found the mystery near {LOCATIONS[p.place].name}, which was a tall place full of clues.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing item was {MYSTERIES[p.mystery].phrase}.",
        ),
        QAItem(
            question=f"How did {p.name} solve the problem?",
            answer=f"{p.name} solved it by using {TOOLS[p.tool].label} and choosing the honest way instead of guessing.",
        ),
        QAItem(
            question=f"Why is the story about moral value as well as problem solving?",
            answer=(
                f"Because {p.name} did not cheat or hide the clue. "
                f"{p.name} told the truth, stayed fair, and used careful thinking to help everyone."
            ),
        ),
    ]


def world_knowledge_qa(sample: StorySample) -> list[QAItem]:
    loc = LOCATIONS[sample.params.place]
    return [
        QAItem(
            question="What does it mean when something is tall?",
            answer="Tall means it reaches a long way upward, like a high tower or a long ladder.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out a mystery.",
        ),
        QAItem(
            question="Why is it good to be honest?",
            answer="It is good to be honest because truth helps people trust each other and solve problems fairly.",
        ),
        QAItem(
            question="How can careful thinking help solve a mystery?",
            answer="Careful thinking helps by letting you compare clues, test ideas, and choose the best answer.",
        ),
        QAItem(
            question="Why are tall places sometimes tricky?",
            answer=(
                f"Tall places can be tricky because clues may be high up, hidden in corners, or hard to reach, "
                f"so you need patience and a good plan."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    loc = LOCATIONS[params.place]
    mis = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    world = World(loc)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.helper == "mother" else "boy",
        memes={"trait": params.trait},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
    ))

    world.facts.update(
        hero=hero.id,
        helper=helper.id,
        place=params.place,
        mystery=params.mystery,
        item=params.item,
        tool=params.tool,
    )
    make_story(world, hero, helper, mis, tool)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(StorySample(params=params, story=story)),
        story_qa=story_qa(StorySample(params=params, story=story)),
        world_qa=world_knowledge_qa(StorySample(params=params, story=story)),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small tall-place mystery storyworld.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--item", choices={v.id for v in MYSTERIES.values()})
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place, mystery, item, tool = choose_combo(args, rng)
    loc = LOCATIONS[place]
    if not loc.tall:
        raise StoryError("This mystery world needs a tall place.")
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        mystery=mystery,
        item=item,
        tool=tool,
        name=name,
        helper=helper,
        trait=trait,
    )


CURATED = [
    StoryParams(place="clocktower", mystery="missing_key", item="key", tool="question", name="Mina", helper="mother", trait="careful"),
    StoryParams(place="bridge", mystery="missing_note", item="note", tool="map", name="Toby", helper="father", trait="curious"),
    StoryParams(place="clocktower", mystery="missing_lantern", item="lantern", tool="lamp", name="Nia", helper="mother", trait="gentle"),
]


def explain_rejection() -> str:
    return "No valid mystery matches the given options."


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
