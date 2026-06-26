#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/yeller_repetition_flashback_suspense_space_adventure.py
================================================================================================

A small space-adventure storyworld with a loud yeller, repetition, flashback,
and suspense. A child-facing scene on a ship, with a state-driven turn:
someone ignores a repeated warning, remembers an earlier promise in a flashback,
and then uses a careful space fix before anything goes wrong.

The seed image:
- A yeller on a starship keeps shouting about a flashing panel.
- The crew repeats a warning, remembers an earlier lesson, and waits in suspense.
- The ending proves the ship is safe again.
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
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    place: str = "the starship"
    setting: str = "orbit"
    has_window: bool = True


@dataclass
class Hazard:
    id: str
    label: str
    cause: str
    warning: str
    danger: str
    fix: str
    suspense: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    action: str
    effect: str
    protects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.ship)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    ship = world.facts.get("hazard")
    if not ship:
        return out
    crew = world.facts["crew"]
    hazard: Hazard = ship
    if crew.memes.get("ignores_warning", 0) < THRESHOLD:
        return out
    if crew.memes.get("alert", 0) < THRESHOLD:
        return out
    sig = ("suspense", hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crew.meters["risk"] = crew.meters.get("risk", 0.0) + 1
    out.append(f"The flashing panel kept buzzing, and everyone held still.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    hazard: Hazard = world.facts.get("hazard")
    crew = world.facts.get("crew")
    tool: Tool = world.facts.get("tool")
    if not hazard or not crew or not tool:
        return out
    if crew.meters.get("risk", 0) < THRESHOLD:
        return out
    if crew.memes.get("remembered", 0) < THRESHOLD:
        return out
    sig = ("fix", hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crew.meters["risk"] = 0
    crew.meters["safe"] = crew.meters.get("safe", 0) + 1
    out.append(f"{tool.effect}.")
    return out


CAUSAL_RULES = [
    _r_alarm,
    _r_fix,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    ship_name: str
    hero_name: str
    hero_type: str
    yeller_name: str
    yeller_type: str
    hazard: str
    tool: str
    seed: Optional[int] = None


SHIPS = {
    "starship": Ship(place="the starship", setting="orbit", has_window=True),
}

HAZARDS = {
    "panel": Hazard(
        id="panel",
        label="flashing panel",
        cause="a loose wire",
        warning="The panel is flashing",
        danger="it might cut the ship's power",
        fix="The crew tightened the wire and the lights steadied",
        suspense="They waited to see whether the ship would go dark",
        tags={"panel", "light", "suspense"},
    ),
    "hatch": Hazard(
        id="hatch",
        label="stuck hatch",
        cause="space dust in the hinge",
        warning="The hatch is stuck",
        danger="it might trap the crew in one room",
        fix="They brushed out the dust and the hatch slid open",
        suspense="Nobody knew if the door would open in time",
        tags={"hatch", "door", "suspense"},
    ),
    "scanner": Hazard(
        id="scanner",
        label="blank scanner",
        cause="a sleepy battery",
        warning="The scanner is blank",
        danger="it might miss a small moon rock",
        fix="They swapped in a fresh battery and the scanner blinked awake",
        suspense="Everyone watched the screen without blinking",
        tags={"scanner", "battery", "suspense"},
    ),
}

TOOLS = {
    "wrench": Tool(
        id="wrench",
        label="a small wrench",
        action="tighten the wire",
        effect="They used a small wrench, tightened the wire, and the panel stopped flashing",
        protects={"panel"},
        tags={"tool", "wrench"},
    ),
    "brush": Tool(
        id="brush",
        label="a soft brush",
        action="brush out the dust",
        effect="They used a soft brush, brushed out the dust, and the hatch slid open",
        protects={"hatch"},
        tags={"tool", "brush"},
    ),
    "battery": Tool(
        id="battery",
        label="a fresh battery",
        action="swap the battery",
        effect="They popped in a fresh battery, and the scanner blinked bright again",
        protects={"scanner"},
        tags={"tool", "battery"},
    ),
}

GIRL_NAMES = ["Mia", "Lena", "Ivy", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Finn", "Leo", "Max", "Owen", "Eli", "Noah"]


def reasonableness_gate(hazard: Hazard, tool: Tool) -> bool:
    return hazard.id in tool.protects


def select_story_options(rng: random.Random, args: argparse.Namespace) -> StoryParams:
    hazard = args.hazard or rng.choice(list(HAZARDS))
    tool = args.tool or rng.choice([t.id for t in TOOLS.values() if reasonableness_gate(HAZARDS[hazard], t)])
    if not reasonableness_gate(HAZARDS[hazard], TOOLS[tool]):
        raise StoryError("That tool does not genuinely fix that space problem.")
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    yeller_type = args.yeller_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    yeller_name = args.yeller_name or rng.choice(GIRL_NAMES if yeller_type == "girl" else BOY_NAMES)
    return StoryParams(
        ship_name="starship",
        hero_name=hero_name,
        hero_type=hero_type,
        yeller_name=yeller_name,
        yeller_type=yeller_type,
        hazard=hazard,
        tool=tool,
    )


def tell(params: StoryParams) -> World:
    world = World(SHIPS[params.ship_name])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    yeller = world.add(Entity(id=params.yeller_name, kind="character", type=params.yeller_type, label=params.yeller_name, role="yeller"))
    hazard = HAZARDS[params.hazard]
    tool = TOOLS[params.tool]

    world.say(f"On {world.ship.place}, {hero.id} was checking the hallway lights when {yeller.id} started to yell.")
    world.say(f'"{hazard.warning}!" {yeller.id} shouted again and again. "{hazard.warning}!"')
    hero.memes["alert"] = 1
    yeller.memes["loud"] = 1
    world.para()
    world.say(f"The warning made the ship feel very quiet. {hazard.suspense}.")
    world.say(f"{hero.id} stared at {hazard.label}, because {hazard.danger}.")
    world.say(f"Then {hero.id} remembered a flashback: yesterday, the captain had taught {hero.id} to listen for tiny ship sounds before they became big problems.")
    hero.memes["remembered"] = 1
    hero.memes["curious"] = 1
    yeller.memes["ignores_warning"] = 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"{hero.id} repeated the plan aloud, just to be sure: first the tool, then the fix, then the safe trip.")
    world.say(f"{hero.id} picked up {tool.label} and used it to help {tool.action}.")
    propagate(world, narrate=True)
    world.say(f"In the end, {hazard.fix.lower()}, and the ship stayed bright and calm.")
    world.say(f"{yeller.id} stopped yelling and grinned at the now-safe hallway.")
    world.facts.update(hero=hero, yeller=yeller, hazard=hazard, tool=tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    yeller: Entity = f["yeller"]
    hazard: Hazard = f["hazard"]
    tool: Tool = f["tool"]
    return [
        f'Write a short space adventure for a child where a yeller keeps shouting "{hazard.warning}!" and the crew has to stay calm.',
        f"Tell a story about {hero.id} on a starship, with repetition, a flashback, and a careful fix using {tool.label}.",
        f"Write a suspenseful but gentle space story where {yeller.id} warns the crew about the {hazard.label} until the problem is solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    yeller: Entity = f["yeller"]
    hazard: Hazard = f["hazard"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Who kept yelling about the {hazard.label}?",
            answer=f"{yeller.id} kept yelling, and {yeller.pronoun().capitalize()} repeated the warning again and again.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered that the captain had taught {hero.id} to listen for small ship problems before they got big.",
        ),
        QAItem(
            question=f"How did the crew fix the {hazard.label}?",
            answer=f"They used {tool.label} to do the right repair, and that made the ship safe again.",
        ),
        QAItem(
            question=f"What made the middle of the story suspenseful?",
            answer=f"Everyone waited to see if the {hazard.label} would cause trouble, so the ship felt very tense for a moment.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "tool": [("What is a tool?", "A tool is something people use to help fix, build, or open things.")],
    "wrench": [("What does a wrench do?", "A wrench helps tighten or loosen things like bolts and wires.")],
    "brush": [("What does a brush do?", "A brush can sweep dust away from small places.")],
    "battery": [("What is a battery for?", "A battery gives power to machines and toys.")],
    "suspense": [("What is suspense?", "Suspense is the feeling of waiting to see what will happen next.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["hazard"].tags) | set(world.facts["tool"].tags)
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for line in world.trace:
        lines.append(line)
    lines.append("--- entities ---")
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show warning/1.
#show suspense/1.
#show fixed/1.

warning(hazard(panel)).
warning(hazard(hatch)).
warning(hazard(scanner)).

suspense(hazard(panel)) :- warning(hazard(panel)).
suspense(hazard(hatch)) :- warning(hazard(hatch)).
suspense(hazard(scanner)) :- warning(hazard(scanner)).

fixed(hazard(panel)) :- tool(wrench), protects(wrench,panel).
fixed(hazard(hatch)) :- tool(brush), protects(brush,hatch).
fixed(hazard(scanner)) :- tool(battery), protects(battery,scanner).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        for tag in sorted(hazard.tags):
            lines.append(asp.fact("tag", hid, tag))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(tool.protects):
            lines.append(asp.fact("protects", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show fixed/1."))
    fixed = set(asp.atoms(model, "fixed"))
    py = {("hazard", hid) for hid, h in HAZARDS.items() if any(reasonableness_gate(h, t) for t in TOOLS.values())}
    if fixed:
        print("OK: ASP ran.")
        return 0
    print("MISMATCH or empty ASP model.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a yeller, repetition, flashback, and suspense.")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--yeller-name")
    ap.add_argument("--yeller-type", choices=["girl", "boy"])
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
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
    return select_story_options(rng, args)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams("starship", "Mia", "girl", "Bolt", "boy", "panel", "wrench"),
    StoryParams("starship", "Finn", "boy", "Nova", "girl", "hatch", "brush"),
    StoryParams("starship", "Ava", "girl", "Pip", "boy", "scanner", "battery"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show fixed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show warning/1.\n#show suspense/1.\n#show fixed/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
