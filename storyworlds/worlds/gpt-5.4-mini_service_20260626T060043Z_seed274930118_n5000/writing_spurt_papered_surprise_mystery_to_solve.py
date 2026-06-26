#!/usr/bin/env python3
"""
Story world: writing, a sudden spurt, and a papered surprise mystery to solve.

A small slice-of-life story domain:
- a child is writing on paper
- something spurts and makes a surprise mess
- the mystery is: who or what made the spurt?
- sharing a careful fix resolves the moment

The world is intentionally small and constraint-checked. The simulated state drives
the prose, QA, and the ASP parity checks.
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


THRESHOLD = 1.0


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    ink_color: str
    spurt_kind: str
    share_kind: str
    can_fix: bool = True


@dataclass
class PaperThing:
    label: str
    phrase: str
    takes: set[str] = field(default_factory=lambda: {"ink"})
    needs: str = "careful hands"


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.mystery_spurt: str = ""

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.mystery_spurt = self.mystery_spurt
        return clone


def _apply_spurt(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("writing", 0) < THRESHOLD:
            continue
        if e.meters.get("spurt", 0) < THRESHOLD:
            continue
        sig = ("spurt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "paper" in world.entities:
            paper = world.get("paper")
            paper.meters["ink"] = paper.meters.get("ink", 0) + 1
            paper.meters["messy"] = paper.meters.get("messy", 0) + 1
        out.append("__spurt__")
    return out


def _apply_surprise(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters.get("surprise", 0) < THRESHOLD:
        return out
    sig = ("surprise", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["surprised"] = hero.memes.get("surprised", 0) + 1
    out.append("__surprise__")
    return out


def _apply_sharing(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    paper = world.get("paper")
    if paper.meters.get("messy", 0) < THRESHOLD:
        return out
    if hero.memes.get("calm", 0) < THRESHOLD:
        return out
    sig = ("share", paper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    paper.meters["fixed"] = 1
    helper.memes["kind"] = helper.memes.get("kind", 0) + 1
    out.append("__share__")
    return out


CAUSAL_RULES = [_apply_spurt, _apply_surprise, _apply_sharing]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__spurt__":
                world.say("A little spurt splashed onto the page.")
            elif bit == "__surprise__":
                world.say("That made the room go very still for a moment.")
            elif bit == "__share__":
                world.say("Then they shared a clean sheet and a careful plan.")
    return produced


def predict_soil(world: World, hero: Entity, tool: Tool) -> bool:
    sim = world.copy()
    sim.get("hero").meters["writing"] = 1
    sim.get("hero").meters["spurt"] = 1
    propagate(sim, narrate=False)
    return sim.get("paper").meters.get("messy", 0) >= THRESHOLD


PLACE = Place(name="the kitchen table", indoor=True, affords={"writing"})
TOOLS = {
    "pen": Tool(id="pen", label="pen", phrase="a blue pen", ink_color="blue", spurt_kind="ink", share_kind="paper"),
    "marker": Tool(id="marker", label="marker", phrase="a green marker", ink_color="green", spurt_kind="ink", share_kind="paper"),
    "brush": Tool(id="brush", label="brush", phrase="a small brush pen", ink_color="brown", spurt_kind="ink", share_kind="paper"),
}
PAPER = PaperThing(label="paper", phrase="a fresh sheet of paper")
NAMES = ["Mina", "Leo", "Nora", "Eli", "Ava", "Theo"]
HELPERS = ["mother", "father", "grandma", "older sister"]
TRAITS = ["quiet", "careful", "curious", "gentle", "thoughtful"]


@dataclass
class StoryParams:
    tool: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    world = World(PLACE)
    hero = world.add(Entity(id="hero", kind="character", type="girl" if params.name in {"Mina", "Nora", "Ava"} else "boy", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    paper = world.add(Entity(id="paper", type="paper", label="paper", phrase=PAPER.phrase))
    tool = TOOLS[params.tool]
    world.facts["tool"] = tool
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["paper"] = paper
    hero.meters["writing"] = 1
    hero.meters["spurt"] = 1
    hero.meters["surprise"] = 1
    hero.memes["careful"] = 1
    world.mystery_spurt = tool.spurt_kind
    world.say(f"{hero.label} was a {params.trait} child who liked writing at {world.place.name}.")
    world.say(f"One afternoon, {hero.label} sat down with {tool.phrase} and a fresh sheet of paper.")
    world.say(f"{hero.label} was writing a small note when something unexpected happened.")
    world.para()
    if predict_soil(world, hero, tool):
        world.say(f"The page was about to get messy, so {helper.label} looked over with a worried face.")
    else:
        world.say(f"The page stayed neat for a moment, but {helper.label} still came closer to help.")
    propagate(world, narrate=True)
    world.para()
    hero.memes["calm"] = 1
    world.say(f"{hero.label} took a breath, and together they shared another sheet of paper.")
    world.say(f"{helper.label} helped hold it steady while {hero.label} started again, slower this time.")
    world.facts.update(tool_id=tool.id)
    return world


def story_text(world: World) -> str:
    hero = world.get("hero")
    helper = world.get("helper")
    paper = world.get("paper")
    tool: Tool = world.facts["tool"]
    return world.render() + f" In the end, {hero.label}'s page was neat again, and {helper.label} smiled beside {hero.label}."


def generation_prompts(world: World) -> list[str]:
    hero = world.get("hero")
    tool: Tool = world.facts["tool"]
    return [
        f'Write a slice-of-life story about {hero.label} writing with {tool.phrase} when a surprise spurt makes a mess on the paper.',
        f'Tell a gentle story where a child named {hero.label} is writing, a mystery spurt happens, and someone shares a clean page.',
        "Write a small everyday story about writing, a sudden spurt, and sharing a fix for the paper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    helper = world.get("helper")
    paper = world.get("paper")
    tool: Tool = world.facts["tool"]
    return [
        QAItem(
            question=f"What was {hero.label} doing at the table?",
            answer=f"{hero.label} was writing on paper with {tool.phrase}.",
        ),
        QAItem(
            question=f"What surprise happened to the paper?",
            answer=f"A little spurt made the paper messy with ink.",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} solve the problem?",
            answer=f"They shared a clean sheet of paper and tried again carefully.",
        ),
        QAItem(
            question=f"What did the ending show had changed?",
            answer=f"The paper was neat again, and {hero.label} was calmer after sharing the fix.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is paper used for?",
        answer="Paper is used for writing, drawing, and making notes.",
    ),
    QAItem(
        question="Why do people share paper sometimes?",
        answer="People share paper when someone needs a fresh sheet or wants to work together.",
    ),
    QAItem(
        question="What is a surprise?",
        answer="A surprise is something unexpected that happens when you do not see it coming.",
    ),
    QAItem(
        question="What is a mystery?",
        answer="A mystery is a question with a hidden answer that people try to figure out.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(tool="pen", name="Mina", helper="mother", trait="careful"),
    StoryParams(tool="marker", name="Leo", helper="father", trait="curious"),
    StoryParams(tool="brush", name="Nora", helper="grandma", trait="thoughtful"),
]


ASP_RULES = r"""
% Facts:
% place(P). tool(T). hero(H). helper(X). paper(Pa).
% writing(H). spurt(T). surprises(H).
% A spurt makes paper messy.
messy_paper(Pa) :- writing(hero), spurt(T), paper(Pa), tool(T).

% A surprise is present when the child's plan changes unexpectedly.
surprise_event(hero) :- surprises(hero).

% Sharing fixes the mess when the child is calm and a helper is present.
shared_fix(Pa) :- messy_paper(Pa), helper(helper), calm(hero), paper(Pa).

#show messy_paper/1.
#show surprise_event/1.
#show shared_fix/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "kitchen_table"))
    lines.append(asp.fact("tool", "pen"))
    lines.append(asp.fact("tool", "marker"))
    lines.append(asp.fact("tool", "brush"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("paper", "paper"))
    lines.append(asp.fact("writing", "hero"))
    lines.append(asp.fact("surprises", "hero"))
    lines.append(asp.fact("calm", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show messy_paper/1.\n#show surprise_event/1.\n#show shared_fix/1."))
    return [(sym.name, tuple(a.string if a.type == a.type.String else a.number for a in sym.arguments)) for sym in model]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show messy_paper/1.\n#show surprise_event/1.\n#show shared_fix/1."))
    asp_atoms = set((sym.name, tuple(getattr(a, "string", getattr(a, "number", a.name)) for a in sym.arguments)) for sym in model)
    # Python parity: we expect the simulated world to have the same three shown facts.
    py = {("messy_paper", ("paper",)), ("surprise_event", ("hero",)), ("shared_fix", ("paper",))}
    if asp_atoms == py:
        print("OK: ASP parity matches Python reasoning.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(asp_atoms))
    print("PY :", sorted(py))
    return 1


def valid_tools() -> list[str]:
    return list(TOOLS.keys())


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    tool = args.tool or rng.choice(valid_tools())
    if tool not in TOOLS:
        raise StoryError("Unknown tool.")
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(tool=tool, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = story_text(world)
    return StorySample(
        params=params,
        story=story,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about writing, a spurt, and a shared fix.")
    ap.add_argument("--tool", choices=valid_tools())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
