#!/usr/bin/env python3
"""
A small comedy storyworld about bravery, infrastructure, and inner monologue.

Seed tale, used as the premise:
---
A tiny town had a broken streetlamp that kept blinking like a sleepy eye.
Milo the mouse hated heights, but the lamp was the only light on Maple Lane.
He kept thinking, "I am brave, I am brave... but that ladder is also very tall."
When the mayor asked for help, Milo climbed up shaking, tightened the loose bolt,
and the lamp finally glowed. Milo felt proud and a little silly for worrying so much.
---

World model:
- A character has bravery, worry, and pride as meme-like emotional meters.
- Infrastructure objects have brokenness, noise, and safety as physical meters.
- The story turns on a fear-to-action transition: the hero thinks loudly,
  chooses a method, and changes the town by repairing the thing.
- Comedy comes from the inner monologue and the mismatch between tiny courage
  and very large civic equipment.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.meters.setdefault("broken", 0.0)
        self.meters.setdefault("noisy", 0.0)
        self.meters.setdefault("safe", 1.0)
        self.meters.setdefault("tall", 0.0)
        self.meters.setdefault("loose", 0.0)
        self.meters.setdefault("lit", 0.0)
        self.meters.setdefault("fixed", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("bravery", 0.0)
        self.memes.setdefault("pride", 0.0)
        self.memes.setdefault("comic_relief", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "Maple Lane"
    kind: str = "street"
    affords: set[str] = field(default_factory=set)


@dataclass
class Infrastructure:
    id: str
    label: str
    phrase: str
    kind: str
    danger: str
    fix_tool: str
    fix_verb: str
    risk_part: str
    tall: bool = False


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    for infra in [e for e in world.entities.values() if e.kind == "thing" and e.type == "infrastructure"]:
        if infra.meters["broken"] < THRESHOLD:
            continue
        for hero in [e for e in world.entities.values() if e.kind == "character"]:
            if hero.memes["bravery"] < THRESHOLD:
                continue
            if not hero.memes.get("has_tool", 0) >= THRESHOLD:
                continue
            sig = ("repair", infra.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            infra.meters["broken"] = 0.0
            infra.meters["fixed"] = 1.0
            infra.meters["safe"] = 1.0
            out.append(f"{infra.label} finally worked again.")
    return out


def _r_pride(world: World) -> list[str]:
    out: list[str] = []
    for hero in [e for e in world.entities.values() if e.kind == "character"]:
        if hero.memes["bravery"] >= THRESHOLD and hero.memes["worry"] < hero.memes["bravery"]:
            sig = ("pride", hero.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            hero.memes["pride"] += 1
            out.append(f"{hero.id} felt proud and a little amazed.")
    return out


CAUSAL_RULES = [Rule("repair", _r_repair), Rule("pride", _r_pride)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                produced.extend(s)
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_fix(world: World, hero: Entity, infra: Infrastructure, tool: Tool) -> bool:
    sim = world.copy()
    h = sim.get(hero.id)
    i = sim.get(infra.id)
    h.memes["bravery"] += 1
    h.memes["has_tool"] = 1
    i.meters["broken"] = 1
    propagate(sim, narrate=False)
    return i.meters["fixed"] >= THRESHOLD


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "tiny"), "tiny")
    world.say(f"{hero.id} was a {trait} {hero.type} who wanted to help the town.")
    world.say(f"{hero.id} kept a private speech ready for emergencies: \"I can do brave things. Possibly while shaking.\"")


def establish(world: World, hero: Entity, infra: Infrastructure) -> None:
    world.say(
        f"On {world.setting.place}, the {infra.label} kept {infra.danger}, because the {infra.phrase} was {infra.label} and badly {infra.fix_verb}."
    )


def inner_monologue(world: World, hero: Entity, infra: Infrastructure) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} looked up at the {infra.label} and thought, "
        f"\"My legs are brave. My knees are doing jazz.\""
    )
    world.say(
        f"Then {hero.id} thought, \"If I do not fix it, the whole lane will stay grumpy in the dark.\""
    )


def ask_for_help(world: World, hero: Entity, helper: Entity, infra: Infrastructure, tool: Tool) -> None:
    world.say(
        f"{hero.id} asked {helper.id} for the {tool.label}, and {helper.id} handed it over like a tiny hero in a mayor's hat."
    )
    world.say(
        f"\"It is only a ladder,\" {hero.id} told {hero.id}. \"A ladder with opinions.\""
    )
    hero.memes["comic_relief"] += 1
    hero.memes["has_tool"] = 1


def climb_and_fix(world: World, hero: Entity, infra: Infrastructure, tool: Tool) -> None:
    hero.memes["bravery"] += 1
    if not predict_fix(world, hero, infra, tool):
        raise StoryError("The chosen tool does not reasonably fix this infrastructure problem.")
    infra.meters["broken"] = 0.0
    infra.meters["fixed"] = 1.0
    infra.meters["safe"] = 1.0
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} climbed the {tool.label} step by step, fixed the loose part with {tool.phrase}, and let out a tiny victory squeak."
    )
    world.say(
        f"The {infra.label} glowed again, and {world.setting.place} stopped feeling spooky and started feeling friendly."
    )


def resolve(world: World, hero: Entity, infra: Infrastructure) -> None:
    world.say(
        f"{hero.id} climbed down, trying very hard to look casual, which was difficult because {hero.id} was absolutely beaming."
    )
    world.say(
        f"{hero.id} thought, \"I was scared, and I did it anyway. That is a very brave mouse-shaped sentence.\""
    )
    world.say(
        f"That night, the {infra.label} stayed bright, and {world.setting.place} shone like it had remembered how to smile."
    )


def tell(setting: Setting, infra: Infrastructure, tool: Tool,
         hero_name: str = "Milo", hero_type: str = "mouse",
         helper_name: str = "Mayor Dot", helper_type: str = "mouse",
         trait: str = "tiny") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=[trait, "nervous", "kind"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["patient", "helpful"]))
    lamp = world.add(Entity(
        id=infra.id, kind="thing", type="infrastructure", label=infra.label,
        phrase=infra.phrase, meters={"broken": 1.0, "noisy": 1.0, "safe": 0.0, "tall": 1.0, "loose": 1.0, "lit": 0.0, "fixed": 0.0}
    ))
    hero.memes["worry"] = 1.0

    intro(world, hero)
    establish(world, hero, infra)
    world.para()
    inner_monologue(world, hero, infra)
    ask_for_help(world, hero, helper, infra, tool)
    world.para()
    climb_and_fix(world, hero, lamp, tool)
    resolve(world, hero, lamp)

    world.facts.update(hero=hero, helper=helper, infra=lamp, tool=tool, setting=setting)
    return world


SETTINGS = {
    "lane": Setting(place="Maple Lane", kind="street", affords={"streetlamp"}),
    "bridge": Setting(place="Puddle Bridge", kind="bridge", affords={"bridge"}),
}

INFRASTRUCTURE = {
    "streetlamp": Infrastructure(
        id="lamp",
        label="streetlamp",
        phrase="a loose bolt in the lamp arm",
        kind="streetlamp",
        danger="blinking like a sleepy eye",
        fix_tool="ladder",
        fix_verb="loose",
        risk_part="arm",
        tall=True,
    ),
    "bridge": Infrastructure(
        id="bridge",
        label="bridge",
        phrase="a cracked plank near the middle",
        kind="bridge",
        danger="creaking at every step",
        fix_tool="planks",
        fix_verb="cracked",
        risk_part="plank",
        tall=False,
    ),
}

TOOLS = {
    "ladder": Tool(
        id="ladder",
        label="ladder",
        phrase="a brave little wrench twist",
        helps="reach high places",
        covers={"tall"},
    ),
    "planks": Tool(
        id="planks",
        label="planks",
        phrase="careful hammer taps and one determined sniff",
        helps="cover holes",
        covers={"bridge"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Leo"]
TRAITS = ["tiny", "brave-looking", "bouncy", "serious"]


@dataclass
class StoryParams:
    place: str
    infra: str
    tool: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for infra in setting.affords:
            if infra == "streetlamp":
                combos.append((place, infra, "ladder"))
            if infra == "bridge":
                combos.append((place, infra, "planks"))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about bravery and infrastructure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--infra", choices=INFRASTRUCTURE)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.infra is None or c[1] == args.infra)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, infra, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or "Mayor Dot"
    return StoryParams(place=place, infra=infra, tool=tool, name=name, gender=gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    infra = f["infra"]
    return [
        f"Write a short funny story for a young child about {hero.id} being brave enough to fix the {infra.label}.",
        f"Tell a comedy story with an inner monologue where {hero.id} worries about the {infra.label} but helps anyway.",
        f"Write a gentle story about bravery and infrastructure on {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    infra = f["infra"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Why was {hero.id} nervous at first?",
            answer=f"{hero.id} was nervous because the {infra.label} was high or tricky, and the job looked bigger than {hero.id}'s very small paws.",
        ),
        QAItem(
            question=f"What helped {hero.id} be brave?",
            answer=f"{helper.id} gave {hero.id} the {tool.label}, and that made the job feel possible.",
        ),
        QAItem(
            question=f"What changed when {hero.id} finished the repair?",
            answer=f"The {infra.label} worked again, the town became safer and brighter, and {hero.id} felt proud instead of just worried.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something even when you feel scared, especially when it helps someone else.",
        ),
        QAItem(
            question="What is infrastructure?",
            answer="Infrastructure means the useful things people build for everyone, like bridges, roads, and streetlights.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(place,infrastructure,tool) :- place(place), affords(place,infrastructure), needs_tool(infrastructure,tool).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, infra in INFRASTRUCTURE.items():
        lines.append(asp.fact("infrastructure", iid))
        lines.append(asp.fact("needs_tool", iid, infra.fix_tool))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def explain_rejection(place: str, infra: str, tool: str) -> str:
    return f"(No story: the {tool} does not reasonably fix the {infra} at {place}.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], INFRASTRUCTURE[params.infra], TOOLS[params.tool], hero_name=params.name)
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
    StoryParams(place="lane", infra="streetlamp", tool="ladder", name="Milo", gender="boy", helper="Mayor Dot"),
    StoryParams(place="bridge", infra="bridge", tool="planks", name="Mia", gender="girl", helper="Mayor Dot"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.infra} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
