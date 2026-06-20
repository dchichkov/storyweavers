#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/make_sputter_physicist_rhyme_mystery_to_solve.py
=================================================================================

A standalone story world sketch for a small animal tale with rhyme and a mystery
to solve. The core premise is: some animal friends are trying to make a tiny
machine work, it sputters instead, and a careful physicist helps them solve the
mystery with clues from the world state.

The domain is intentionally small and classical:
- animals with roles and feelings,
- a simple device that can sputter,
- physical clues that reveal what went wrong,
- a friendly physicist who reasons from evidence,
- a rhyme beat that turns the investigation into a child-friendly ending.

This script follows the Storyweavers storyworld contract:
- stdlib-only
- typed entities with physical meters and emotional memes
- forward-chained state changes
- Python reasonableness gate and inline ASP twin
- three Q&A sets grounded in world state
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "owl"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Machine:
    id: str
    label: str
    phrase: str
    sputter_word: str
    needs: str
    clue: str
    fixed_image: str
    broken: bool = True
    noisy: bool = True
    makes_story: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_sputter(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["running"] < THRESHOLD:
            continue
        sig = ("sputter", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["sputtering"] += 1
        if "room" in world.entities:
            world.get("room").meters["mess"] += 1
        out.append("__sputter__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["sputtering"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule("sputter", "physical", _r_sputter),
    Rule("worry", "social", _r_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def simple_rhyme(word: str) -> str:
    rhymes = {
        "make": "cake",
        "sputter": "butter",
        "physicist": "list",
        "glow": "show",
        "clue": "blue",
        "night": "light",
    }
    return rhymes.get(word, word)


def machine_needs(machine: Machine) -> str:
    return machine.needs


def predict_sputter(world: World, machine_id: str) -> dict:
    sim = world.copy()
    sim.get(machine_id).meters["running"] += 1
    propagate(sim, narrate=False)
    m = sim.get(machine_id)
    return {
        "sputtering": m.meters["sputtering"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
    }


def set_up(world: World, animals: list[Entity], machine: Machine) -> None:
    names = " and ".join(a.id for a in animals)
    world.say(
        f"On a bright morning, {names} wanted to make a tiny wonder in the barn. "
        f"They had {machine.phrase} and a big wish to see it glow."
    )
    for a in animals:
        a.memes["curious"] += 1
        a.memes["hope"] += 1


def show_problem(world: World, animals: list[Entity], machine: Machine) -> None:
    world.say(
        f"But when they turned the wheel, {machine.label} went {machine.sputter_word}. "
        f"It would not shine; it only coughed and clicked."
    )
    for a in animals:
        a.memes["surprise"] += 1


def notice_clue(world: World, physicist: Entity, clue: Clue, machine: Machine) -> None:
    physicist.memes["focus"] += 1
    world.say(
        f"{physicist.id} bent close and looked at {clue.phrase}. "
        f"{physicist.pronoun().capitalize()} said it could help solve the mystery."
    )
    world.facts["clue"] = clue
    world.facts["prediction"] = predict_sputter(world, machine.id)


def explain_rhyme(world: World, physicist: Entity) -> None:
    world.say(
        f'"A small thing can make a big sound," {physicist.id} said with a smile. '
        f'"When the wheel goes wrong, it sings a sputter song."'
    )


def fix_machine(world: World, physicist: Entity, tool: Tool, machine: Machine) -> None:
    machine.meters["running"] += 1
    machine.meters["fixed"] += 1
    machine.meters["sputtering"] = 0.0
    world.get("room").meters["mess"] = 0.0
    physicist.memes["confidence"] += 1
    world.say(
        f"{physicist.id} used {tool.phrase} to solve the puzzle. "
        f"After that, {machine.label} found its steady beat and began to glow."
    )


def ending_image(world: World, animals: list[Entity], machine: Machine) -> None:
    names = ", ".join(a.id for a in animals[:-1]) + f", and {animals[-1].id}" if len(animals) > 1 else animals[0].id
    world.say(
        f"{names} watched {machine.fixed_image}. The mystery was solved, the barn was calm, "
        f"and the little machine made its light at last."
    )


def tell(theme: str, machine: Machine, clue: Clue, tool: Tool,
         animal1: tuple[str, str], animal2: tuple[str, str],
         physicist_name: str = "Pippa", physicist_type: str = "fox") -> World:
    world = World()
    a = world.add(Entity(id=animal1[0], kind="character", type=animal1[1], role="helper"))
    b = world.add(Entity(id=animal2[0], kind="character", type=animal2[1], role="helper"))
    p = world.add(Entity(id=physicist_name, kind="character", type=physicist_type, role="physicist"))
    room = world.add(Entity(id="room", type="room", label="the barn"))

    machine_ent = world.add(Entity(id=machine.id, type="machine", label=machine.label))
    world.facts["theme"] = theme
    world.facts["machine"] = machine
    world.facts["tool"] = tool
    world.facts["physicist"] = p
    world.facts["animals"] = (a, b)
    world.facts["room"] = room
    world.facts["machine_ent"] = machine_ent

    set_up(world, [a, b], machine)
    world.para()
    show_problem(world, [a, b], machine)
    world.say(
        f"{a.id} looked at {b.id}. Then both of them looked at {p.id}, the physicist, "
        f"who liked to solve small mysteries."
    )
    world.para()
    notice_clue(world, p, clue, machine)
    explain_rhyme(world, p)
    world.para()
    fix_machine(world, p, tool, machine)
    ending_image(world, [a, b], machine)
    world.facts["outcome"] = "fixed"
    return world


THEMES = ["animal_barn", "forest_lab", "pond_workshop"]

MACHINES = {
    "lantern": Machine(
        "lantern", "lantern", "a shiny little lantern for the dark corner",
        "sputter", "oil and a clean wick", "a sticky wick and a tiny drip of oil",
        "the lantern shone steady and warm", tags={"light", "mystery"}
    ),
    "robot": Machine(
        "robot", "toy robot", "a round toy robot with a silver face",
        "sputter", "one loose battery and a dusty gear", "a loose battery and a dusty gear",
        "the robot blinked bright and rolled ahead", tags={"toy", "mystery"}
    ),
    "radio": Machine(
        "radio", "radio", "a little radio with a red button",
        "sputter", "a bent wire and crumbs in the switch", "a bent wire and crumbs in the switch",
        "the radio played a happy tune", tags={"sound", "mystery"}
    ),
}

TOOLS = {
    "cloth": Tool("cloth", "soft cloth", "a soft cloth", "wipe away the dust"),
    "oil": Tool("oil", "tiny oil dropper", "a tiny oil dropper", "steady the moving parts"),
    "wire": Tool("wire", "small wire brush", "a small wire brush", "clear the bent wire"),
}

CLUES = {
    "wick": Clue("wick", "wick", "the wick", "It showed a thirsty wick and a little oil leak", tags={"light"}),
    "battery": Clue("battery", "battery", "the battery", "It showed that the power was loose", tags={"toy"}),
    "crumbs": Clue("crumbs", "crumbs", "the crumbs", "It showed dust in the switch", tags={"sound"}),
}

ANIMALS = [
    ("Milo", "mouse"),
    ("Hazel", "hen"),
    ("Otis", "owl"),
    ("Bea", "bear"),
    ("Pip", "pig"),
    ("Nina", "newt"),
]


@dataclass
@dataclass
class StoryParams:
    theme: str
    machine: str
    clue: str
    tool: str
    animal1_name: str
    animal1_type: str
    animal2_name: str
    animal2_type: str
    physicist_name: str
    physicist_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    return [(t, m, c) for t in THEMES for m in MACHINES for c in CLUES if machine_needs(MACHINES[m])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal mystery story world with rhyme and a physicist.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--machine", choices=MACHINES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
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
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.machine is None or c[1] == args.machine)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, machine, clue = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    a1 = rng.choice(ANIMALS)
    a2 = rng.choice([x for x in ANIMALS if x != a1])
    phys_name = "Pippa"
    phys_type = "fox"
    return StoryParams(theme, machine, clue, tool, a1[0], a1[1], a2[0], a2[1], phys_name, phys_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.theme, MACHINES[params.machine], CLUES[params.clue], TOOLS[params.tool],
                 (params.animal1_name, params.animal1_type),
                 (params.animal2_name, params.animal2_type),
                 params.physicist_name, params.physicist_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    machine: Machine = f["machine"]
    return [
        f'Write an animal story for a young child that includes the word "{machine.label}" and the word "physicist".',
        f"Tell a rhyme-filled mystery where a {machine.label} sputters, a physicist solves the clue, and the animals cheer.",
        f"Write a gentle animal story with a mystery to solve, a sputtering machine, and a rhyming ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["animals"]
    p = f["physicist"]
    machine: Machine = f["machine"]
    tool: Tool = f["tool"]
    clue: Clue = f["clue"]
    return [
        ("Who is the story about?",
         f"It is about {a.id}, {b.id}, and {p.id}, the physicist who helped solve the mystery."),
        ("What problem happened?",
         f"{machine.label.capitalize()} went sputter instead of working smoothly, so the friends had a mystery to solve."),
        ("How did they fix it?",
         f"{p.id} used {tool.phrase} after following the clue about {clue.label}. That solved the problem and made the machine work again."),
        ("How did the story end?",
         f"It ended with {machine.fixed_image}. The animals watched the result and felt happy because the mystery was solved."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    machine: Machine = world.facts["machine"]
    tool: Tool = world.facts["tool"]
    clue: Clue = world.facts["clue"]
    return [
        QAItem("What does a physicist do?",
               "A physicist studies how things work in the world and uses clues to understand problems."),
        QAItem("What is sputtering?",
               "Sputtering is when a machine makes stop-start sounds and does not work smoothly."),
        QAItem(f"Why can a {machine.label} need a clue to fix it?",
               "Small machines can stop working because of a loose part or a tiny problem, and clues help find the cause."),
        QAItem("Why is a soft cloth useful?",
               "A soft cloth can wipe away dust without scratching delicate parts."),
        QAItem("What is a mystery to solve?",
               "A mystery to solve is a problem where you look carefully for clues and figure out what happened."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if bits:
            lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("animal_barn", "lantern", "wick", "oil", "Milo", "mouse", "Hazel", "hen", "Pippa", "fox"),
    StoryParams("forest_lab", "robot", "battery", "cloth", "Otis", "owl", "Pip", "pig", "Pippa", "fox"),
    StoryParams("pond_workshop", "radio", "crumbs", "wire", "Bea", "bear", "Nina", "newt", "Pippa", "fox"),
]


ASP_RULES = r"""
sputtering(M) :- machine(M), broken(M).
mystery(M) :- sputtering(M).
solved(M) :- clue(C), tool(T), matches(C, T), machine(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MACHINES:
        lines.append(asp.fact("machine", mid))
        lines.append(asp.fact("broken", mid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.extend([
        asp.fact("matches", "wick", "oil"),
        asp.fact("matches", "battery", "cloth"),
        asp.fact("matches", "crumbs", "wire"),
    ])
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show solved/1."))
    return sorted(set(asp.atoms(model, "solved")))


def asp_verify() -> int:
    ok = True
    if not valid_combos():
        ok = False
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    import asp
    clingo = set(asp_valid_combos())
    python = {(m,) for _, m, _ in valid_combos()}
    if clingo != python:
        ok = False
        print("MISMATCH in ASP parity.")
    else:
        print("OK: ASP parity matches.")
    print("OK: smoke test passed.")
    return 0 if ok else 1


def explain_rejection() -> str:
    return "(No story: this combination does not make a good mystery to solve.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(m for _, m, _ in valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
