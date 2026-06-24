#!/usr/bin/env python3
"""
storyworlds/worlds/sweep_problem_solving_humor_heartwarming.py
==============================================================

A small story world about a child, a mess, a sweeping problem, and a kind,
humorous fix. The premise is simple: someone makes a mess, someone notices,
they solve it together, and the ending proves the place feels better.
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "clean": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "joy": 0.0, "pride": 0.0, "humor": 0.0}

    def pronoun(self) -> str:
        if self.type in {"girl", "mother", "woman"}:
            return "she"
        if self.type in {"boy", "father", "man"}:
            return "he"
        return "it"

    def possessive(self) -> str:
        return {"girl": "her", "mother": "her", "woman": "her",
                "boy": "his", "father": "his", "man": "his"}.get(self.type, "its")


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    tidy_baseline: float = 1.0
    sweepable: bool = True


@dataclass
class Mess:
    id: str
    label: str
    verb: str
    sound: str
    amount: float
    tiny: bool = False


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    humorous: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace_log: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "kitchen": Place("kitchen", "the kitchen", indoors=True, tidy_baseline=0.7),
    "classroom": Place("classroom", "the classroom", indoors=True, tidy_baseline=0.8),
    "porch": Place("porch", "the porch", indoors=False, tidy_baseline=0.9),
    "workshop": Place("workshop", "the workshop", indoors=True, tidy_baseline=0.6),
}

MESSES = {
    "crumbs": Mess("crumbs", "crumbs", "cracked", "crunch", 1.0, tiny=True),
    "confetti": Mess("confetti", "confetti", "sparkled", "flutter", 1.2, tiny=True),
    "leaves": Mess("leaves", "leaves", "scattered", "rustle", 1.4),
    "beans": Mess("beans", "beans", "rolled", "clatter", 1.5),
}

TOOLS = {
    "broom": Tool("broom", "a broom", "sweep with a broom", helps={"crumbs", "confetti", "leaves"}, humorous="the bristles tickled more than they threatened"),
    "dustpan": Tool("dustpan", "a dustpan", "scoop the pile", helps={"crumbs", "confetti", "beans", "leaves"}, humorous="it looked a little like a tiny black shovel"),
    "mini-vac": Tool("mini-vac", "a little vacuum", "gobble up the mess", helps={"crumbs", "beans"}, humorous="it sounded like a sleepy dinosaur waking up"),
}

HERO_NAMES = ["Mina", "Leo", "Ruby", "Owen", "Pip", "Nora"]
HELPER_NAMES = ["Aunt Jo", "Dad", "Mom", "Grandpa", "Ms. Lee", "Mr. Ben"]

# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mess: str
    tool: str
    name: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
mess_needs_tool(M) :- mess(M), not solved(M).
solved(M) :- helps(T, M).
compatible(P, M, T) :- place(P), mess(M), tool(T), affords(P, M), helps(T, M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        if p.sweepable:
            lines.append(asp.fact("sweepable", pid))
        lines.append(asp.fact("tidy_base", pid, int(p.tidy_baseline * 10)))
    for mid, m in MESSAGES.items():
        lines.append(asp.fact("mess", mid))
        lines.append(asp.fact("affords_mess", "kitchen", mid) if mid in {"crumbs", "beans"} else asp.fact("affords_mess", "classroom", mid) if mid in {"crumbs", "confetti"} else asp.fact("affords_mess", "porch", mid) if mid in {"leaves", "confetti"} else asp.fact("affords_mess", "workshop", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for m in sorted(t.helps):
            lines.append(asp.fact("helps", tid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # Use a simple parity check: every tool that helps a mess makes it compatible.
    model = asp.one_model(asp_program("#show compatible/3."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = set()
    for p in PLACES:
        for m in MESSAGES:
            for t in TOOLS:
                if m in TOOLS[t].helps:
                    py_set.add((p, m, t))
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("only in clingo:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def messy_enough(mess: Mess) -> bool:
    return mess.amount >= 1.0


def compatible(place: Place, mess: Mess, tool: Tool) -> bool:
    return place.sweepable and mess.id in tool.helps


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES.values():
        for m in MESSAGES.values():
            for t in TOOLS.values():
                if compatible(p, m, t):
                    out.append((p.id, m.id, t.id))
    return out


def explain_rejection(place: Place, mess: Mess, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} cannot reasonably help with {mess.label} at {place.label}. "
        f"Choose a mess the tool can actually tidy.)"
    )


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------
def setup(world: World, hero: Entity, helper: Entity, mess: Mess) -> None:
    world.say(f"{hero.id} was a little {hero.type} who liked keeping {world.place.label} neat.")
    world.say(f"{hero.pronoun().capitalize()} also liked a funny little task: {mess.verb} {mess.label} into a neat pile.")
    world.say(f"One day, {hero.id} and {helper.label} were in {world.place.label}, and something messy was waiting there.")


def make_mess(world: World, hero: Entity, mess: Mess) -> None:
    hero.meters["mess"] += mess.amount
    hero.memes["worry"] += 1.0
    world.say(f"There were {mess.label} everywhere, and they went {mess.sound}-{mess.sound} under every careful step.")
    world.say(f"{hero.id} frowned, but then {hero.pronoun()} gave the pile a tiny salute, as if the mess had challenged {hero.possessive()} kindness.")


def problem_solving(world: World, hero: Entity, helper: Entity, tool: Tool, mess: Mess) -> None:
    hero.memes["humor"] += 1.0
    helper.memes["humor"] += 1.0
    world.say(f"{helper.label} peeked in and said, \"Looks like the floor tried to wear {mess.label} as a coat.\"")
    world.say(f"{hero.id} giggled. Then {hero.id} spotted {tool.label}, which looked ready for work.")
    world.say(f"They decided to {tool.phrase}, because sometimes the best fix is the one that makes a small joke and then gets busy.")
    world.say(f"{tool.humorous.capitalize()}.")
    hero.meters["clean"] += 1.0
    hero.meters["mess"] = max(0.0, hero.meters["mess"] - mess.amount)
    hero.memes["joy"] += 1.0
    hero.memes["pride"] += 1.0
    world.place.tidy_baseline += 0.2
    world.say(f"The pile shrank, and the room started to look proud of itself.")


def ending(world: World, hero: Entity, helper: Entity, mess: Mess, tool: Tool) -> None:
    world.para()
    world.say(f"At last, {hero.id} stood back and looked at the floor.")
    world.say(f"The {mess.label} were gone, the air felt lighter, and {world.place.label} was tidy again.")
    world.say(f"{helper.label} smiled and said, \"See? A little sweeping and a little laughter can fix a big day.\"")
    world.say(f"{hero.id} grinned, holding {tool.label} like a tiny trophy, because the clean room was the happiest prize of all.")


def tell(place: Place, mess: Mess, tool: Tool, hero_name: str, helper_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(hero_name, kind="character", type="child"))
    helper = world.add(Entity(helper_name, kind="character", type="adult", label=helper_name))
    world.facts.update(hero=hero, helper=helper, mess=mess, tool=tool, place=place)
    setup(world, hero, helper, mess)
    world.para()
    make_mess(world, hero, mess)
    problem_solving(world, hero, helper, tool, mess)
    ending(world, hero, helper, mess, tool)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child about {f["hero"].id} learning to {f["tool"].phrase} after a mess appears in {f["place"].label}.',
        f'Tell a humorous but gentle story where {f["helper"].label} helps {f["hero"].id} clean {f["mess"].label} with {f["tool"].label}.',
        f'Write a short story with a problem, a clever cleaning plan, and a cozy ending in {f["place"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mess: Mess = f["mess"]
    tool: Tool = f["tool"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"What mess did {hero.id} need to clean in {place.label}?",
            answer=f"{hero.id} needed to clean {mess.label} in {place.label}, and the mess made the floor look very busy."
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{helper.label} helped {hero.id} solve the problem by staying kind, making a joke, and working with {tool.label}."
        ),
        QAItem(
            question=f"How did they fix the mess?",
            answer=f"They fixed it by using {tool.label} to {tool.phrase}, which turned the cleanup into a calm, funny team effort."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {place.label} was tidy again, {hero.id} felt proud, and everyone was smiling."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mess: Mess = f["mess"]
    tool: Tool = f["tool"]
    items = [
        QAItem(
            question="What does a broom do?",
            answer="A broom is used to sweep dust, crumbs, and tiny bits into one place so they can be cleaned up."
        ),
        QAItem(
            question="Why do people sweep a floor?",
            answer="People sweep a floor to gather up messes and make the room safer and nicer to walk in."
        ),
    ]
    if mess.tiny:
        items.append(QAItem(
            question="Why can tiny messes be easy to miss?",
            answer="Tiny messes can be easy to miss because they hide in corners and look harmless until you step on them."
        ))
    if tool.id == "mini-vac":
        items.append(QAItem(
            question="What is a vacuum cleaner for?",
            answer="A vacuum cleaner is for sucking up dirt and crumbs from carpets, floors, and corners."
        ))
    return items


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming sweep-and-fix story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mess", choices=MESSES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = []
    for p in PLACES.values():
        if args.place and p.id != args.place:
            continue
        for m in MESSAGES.values():
            if args.mess and m.id != args.mess:
                continue
            for t in TOOLS.values():
                if args.tool and t.id != args.tool:
                    continue
                if compatible(p, m, t):
                    choices.append((p.id, m.id, t.id))
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, mess, tool = rng.choice(sorted(choices))
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, mess=mess, tool=tool, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MESSAGES[params.mess], TOOLS[params.tool], params.name, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="kitchen", mess="crumbs", tool="broom", name="Mina", helper="Mom"),
    StoryParams(place="classroom", mess="confetti", tool="dustpan", name="Leo", helper="Ms. Lee"),
    StoryParams(place="porch", mess="leaves", tool="broom", name="Ruby", helper="Dad"),
    StoryParams(place="workshop", mess="beans", tool="mini-vac", name="Pip", helper="Grandpa"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        atoms = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(atoms)} compatible combos")
        for row in atoms:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mess} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
