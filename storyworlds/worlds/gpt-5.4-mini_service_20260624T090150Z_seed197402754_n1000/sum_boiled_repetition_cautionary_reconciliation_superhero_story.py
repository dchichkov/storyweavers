#!/usr/bin/env python3
"""
A small superhero storyworld about a kid hero, a risky power, a cautionary warning,
a repeated mistake, and a reconciliation that saves the day.

Seed idea:
- A young superhero loves using a number-sum gadget.
- The gadget overheats and boils a pot / overheats a battery?
- A mentor warns them repeatedly.
- The hero ignores the caution, the device boils over, then they reconcile and fix it.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

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
    name: str
    setting: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    label: str
    use_verb: str
    ritual: str
    result: str
    risk: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    ready: str = ""
    tail: str = ""


@dataclass
class StoryParams:
    place: str
    power: str
    tool: str
    name: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
PLACES = {
    "tower": Place(name="the clock tower", setting="city rooftop", affords={"sum"}),
    "lab": Place(name="the little lab", setting="bright workshop", affords={"sum"}),
    "kitchen": Place(name="the kitchen", setting="warm kitchen", affords={"sum"}),
}

POWERS = {
    "sum": Power(
        id="sum",
        label="sum spark",
        use_verb="make a sum",
        ritual="add the numbers again and again",
        result="add up faster than a blink",
        risk="boil the kettle",
        danger="boiled over",
        tags={"sum", "math", "repetition"},
    ),
}

TOOLS = {
    "gloves": Tool(
        id="gloves",
        label="cool gloves",
        phrase="a pair of cool gloves",
        protects={"heat"},
        ready="put on the cool gloves",
        tail="slid the cool gloves back on",
    ),
    "mitts": Tool(
        id="mitts",
        label="oven mitts",
        phrase="thick oven mitts",
        protects={"heat"},
        ready="pull on the oven mitts",
        tail="buckled the oven mitts tight",
    ),
}

NAMES = ["Milo", "Nina", "Ari", "Pia", "Jules", "Tess", "Rae", "Kai"]
SIDEKICKS = ["cat", "robot", "mouse", "sparrow", "dog"]
TRAITS = ["brave", "quick", "kind", "curious", "spirited"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A power is risky in a place when the place allows that power.
risky(P, Pow) :- place(P), power(Pow), affords(P, Pow).

% A tool can calm the risk if it protects heat.
safe_tool(T) :- tool(T), protects(T, heat).

% A valid story needs a risky power and a safe tool.
valid(P, Pow, T) :- risky(P, Pow), safe_tool(T).

% The cautionary beat exists when the hero is warned twice or more.
cautionary(P, Pow) :- valid(P, Pow, _).

% The reconciliation beat exists when the tool is used after the boil.
reconciled(P, Pow, T) :- valid(P, Pow, T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid in POWERS:
        lines.append(asp.fact("power", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.protects):
            lines.append(asp.fact("protects", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
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
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, p in PLACES.items():
        for pow_id in p.affords:
            for tool_id, tool in TOOLS.items():
                if "heat" in tool.protects:
                    combos.append((place, pow_id, tool_id))
    return combos


def explain_rejection() -> str:
    return "(No story: this superhero power needs a heat-safe tool for a real cautionary turn.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_story(world: World, hero: Entity, sidekick: Entity, power: Power, tool: Tool) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1

    world.say(
        f"{hero.id} was a {hero.traits[0]} little superhero who loved a bright {power.label}."
    )
    world.say(
        f"Every morning, {hero.pronoun().capitalize()} would {power.ritual}, and the numbers would {power.result}."
    )
    world.say(
        f"{hero.id} also had a {sidekick.label} who liked to watch from the windowsill."
    )

    world.para()
    world.say(
        f"One day at {world.place.name}, {hero.id} tried to {power.use_verb} beside a warm kettle."
    )
    world.say(
        f"{hero.id}'s mentor called out, 'Careful! {power.danger} if you keep using the {power.label} there.'"
    )
    hero.memes["warned"] = hero.memes.get("warned", 0) + 1
    world.say(
        f"{hero.id} heard the warning, but then {hero.pronoun().subject.capitalize()} tried again."
    )
    world.say(
        f"Again the spark jumped, and again the water got hotter and hotter."
    )
    hero.memes["repetition"] = hero.memes.get("repetition", 0) + 1
    hero.meters["heat"] = hero.meters.get("heat", 0) + 1

    world.say(
        f"At last the kettle {power.danger}, and a tiny cloud puffed into the air."
    )
    hero.memes["oops"] = hero.memes.get("oops", 0) + 1

    world.para()
    world.say(
        f"{hero.id} looked down, took a slow breath, and said sorry."
    )
    world.say(
        f"{hero.id}'s mentor smiled and handed over {tool.phrase}."
    )
    world.say(
        f"'{tool.ready}, and use the {power.label} away from the heat,' said the mentor."
    )
    hero.memes["reconciliation"] = hero.memes.get("reconciliation", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    hero.meters["heat"] = 0

    world.say(
        f"{hero.id} nodded, {tool.tail}, and tried again in a safer spot."
    )
    world.say(
        f"This time the {power.label} made a perfect sum, the kettle stayed calm, and {sidekick.label} clapped from the sill."
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        power=power,
        tool=tool,
        place=world.place,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child that uses the word "sum" and includes a cautionary warning.',
        f"Tell a superhero story where {f['hero'].id} keeps trying to {f['power'].use_verb} until the problem {f['power'].danger}.",
        f"Write a gentle story with repetition, a boiling mishap, and a reconciliation using {f['tool'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    power: Power = f["power"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} love to do over and over with the {power.label}?",
            answer=f"{hero.id} loved to {power.use_verb}, and {hero.pronoun('subject')} kept trying it again and again because the numbers felt exciting.",
        ),
        QAItem(
            question=f"Why did the mentor warn {hero.id} at {world.place.name}?",
            answer=f"The mentor warned {hero.id} because using the {power.label} near the kettle could make it {power.danger}. The warning was cautionary, because it tried to stop the trouble before it got worse.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the problem after the kettle got too hot?",
            answer=f"{hero.id} said sorry, took the {tool.label}, and moved the {power.label} away from the heat. That reconciliation helped everyone calm down and try again safely.",
        ),
        QAItem(
            question=f"Who watched the superhero from the windowsill?",
            answer=f"The {sidekick.label} watched from the windowsill and clapped when the safer plan worked.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sum?",
            answer="A sum is the answer you get when you add numbers together.",
        ),
        QAItem(
            question="What does boiled mean?",
            answer="Boiled means a liquid got so hot that it made bubbles and steam.",
        ),
        QAItem(
            question="What is a cautionary warning?",
            answer="A cautionary warning is a careful warning that tries to stop someone from making a mistake.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace after a problem and start working together again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, power, tool = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(place=place, power=power, tool=tool, name=name, sidekick=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Nina", "Pia", "Tess", "Rae"} else "boy",
        label="hero",
        traits=["brave", "curious"],
    ))
    sidekick = world.add(Entity(
        id="Sidekick",
        kind="character",
        type="animal",
        label=params.sidekick,
    ))
    power = POWERS[params.power]
    tool = TOOLS[params.tool]
    build_story(world, hero, sidekick, power, tool)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="tower", power="sum", tool="gloves", name="Milo", sidekick="cat"),
    StoryParams(place="lab", power="sum", tool="mitts", name="Nina", sidekick="robot"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: sum, boiled, cautionary repetition, reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
