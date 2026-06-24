#!/usr/bin/env python3
"""
A small superhero story world about brave choices, indignation, and a lethal
threat that must be stopped before anyone gets hurt.

Seed tale:
---
Mina was a brave little hero who loved helping people in her city. One evening,
she saw a villain named Dr. Hex aiming a lethal ray at the museum. Mina felt a
hot surge of indignation because the villain was trying to scare everyone. She
put on her cape, raced to the rooftop, and called for the guard to keep the
street clear. Then she used her shield drone to block the ray and made Dr. Hex
drop the remote. The museum stayed safe, and Mina stood tall with bravery
buzzing in her chest.

World idea:
- A hero can feel bravery, fear, and indignation.
- A villain can prepare a lethal device that threatens a building.
- Brave action can protect civilians and stop the device.
- Indignation is the emotional spark that pushes the hero to act, but bravery
  is what carries the action through.
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
    kind: str = "thing"  # "hero" | "villain" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    target: Optional[str] = None
    carried_by: Optional[str] = None
    protects: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "risk": 0.0}
        if not self.memes:
            self.memes = {"bravery": 0.0, "indignation": 0.0, "fear": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "heroine", "mother"}
        male = {"boy", "man", "hero", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class District:
    name: str
    citizen_place: str
    afford: str
    danger_scale: str  # "city" | "building" | "street"


@dataclass
class Threat:
    id: str
    label: str
    phrase: str
    kind: str
    lethal: bool
    charge: str
    counter: str
    place: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    blocks: set[str]
    used_for: str
    plural: bool = False


class World:
    def __init__(self, district: District) -> None:
        self.district = district
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.district)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    district: str
    threat: str
    tool: str
    hero_name: str
    hero_type: str
    villain_name: str
    seed: Optional[int] = None


DISTRICTS = {
    "museum": District(name="the museum", citizen_place="the city square", afford="roof", danger_scale="building"),
    "harbor": District(name="the harbor", citizen_place="the docks", afford="pier", danger_scale="street"),
    "station": District(name="the station", citizen_place="the platform", afford="roof", danger_scale="building"),
}

THREATS = {
    "ray": Threat(
        id="ray",
        label="lethal ray",
        phrase="a lethal ray cannon",
        kind="ray",
        lethal=True,
        charge="glowing red",
        counter="shield",
        place="roof",
    ),
    "gas": Threat(
        id="gas",
        label="lethal gas cloud",
        phrase="a lethal gas canister",
        kind="gas",
        lethal=True,
        charge="hissing",
        counter="mask",
        place="street",
    ),
    "beam": Threat(
        id="beam",
        label="lethal beam",
        phrase="a lethal beam projector",
        kind="beam",
        lethal=True,
        charge="blue-white",
        counter="mirror",
        place="roof",
    ),
}

TOOLS = {
    "shield": Tool(id="shield", label="shield drone", phrase="a shield drone", blocks={"ray", "beam"}, used_for="block"),
    "mask": Tool(id="mask", label="filter mask", phrase="a filter mask", blocks={"gas"}, used_for="filter"),
    "mirror": Tool(id="mirror", label="mirror panel", phrase="a mirror panel", blocks={"beam"}, used_for="bounce"),
}

HERO_NAMES = ["Mina", "Nova", "Riley", "Tess", "Aria", "Zuri"]
VILLAIN_NAMES = ["Dr. Hex", "Night Coil", "Captain Frost", "Mister Rune"]
HERO_TYPES = ["girl", "boy"]


class StoryState:
    def __init__(self, world: World, hero: Entity, villain: Entity, threat: Entity, tool: Entity) -> None:
        self.world = world
        self.hero = hero
        self.villain = villain
        self.threat = threat
        self.tool = tool
        self.alerted = False
        self.stopped = False
        self.civilians_safe = False


def can_use_tool(threat: Threat, tool: Tool) -> bool:
    return threat.kind in tool.blocks


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.threat and args.tool:
        if not can_use_tool(THREATS[args.threat], TOOLS[args.tool]):
            raise StoryError("That tool cannot reasonably stop that lethal threat.")
    if args.tool and args.threat and args.tool == "mask" and args.threat != "gas":
        raise StoryError("A filter mask only fits a gas threat in this story world.")

    threat_id = args.threat or rng.choice(sorted(THREATS))
    tool_options = [k for k, v in TOOLS.items() if can_use_tool(THREATS[threat_id], v)]
    if args.tool:
        if args.tool not in tool_options:
            raise StoryError("No valid combination matches the given options.")
        tool_id = args.tool
    else:
        tool_id = rng.choice(sorted(tool_options))

    district = args.district or rng.choice(sorted(DISTRICTS))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    villain_name = args.villain_name or rng.choice(VILLAIN_NAMES)
    return StoryParams(
        district=district,
        threat=threat_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_type=hero_type,
        villain_name=villain_name,
    )


def setup_world(params: StoryParams) -> StoryState:
    district = DISTRICTS[params.district]
    world = World(district)
    hero = world.add(Entity(id=params.hero_name, kind="hero", type=params.hero_type, label=params.hero_name))
    villain = world.add(Entity(id=params.villain_name, kind="villain", type="man", label=params.villain_name))
    threat_cfg = THREATS[params.threat]
    tool_cfg = TOOLS[params.tool]
    threat = world.add(Entity(
        id="threat",
        kind="thing",
        type=threat_cfg.kind,
        label=threat_cfg.label,
        phrase=threat_cfg.phrase,
        owner=villain.id,
        target=district.name,
        meters={"damage": 0.0, "risk": 1.0},
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
        owner=hero.id,
        protects={threat_cfg.kind},
    ))
    world.facts.update(params=params, district=district, hero=hero, villain=villain, threat=threat, tool=tool, threat_cfg=threat_cfg, tool_cfg=tool_cfg)
    return StoryState(world, hero, villain, threat, tool)


def predict_damage(world: World, threat: Entity, tool: Entity) -> bool:
    threat_cfg: Threat = world.facts["threat_cfg"]
    tool_cfg: Tool = world.facts["tool_cfg"]
    return not can_use_tool(threat_cfg, tool_cfg)


def tell(params: StoryParams) -> World:
    state = setup_world(params)
    world = state.world
    hero, villain, threat, tool = state.hero, state.villain, state.threat, state.tool
    district: District = world.facts["district"]
    threat_cfg: Threat = world.facts["threat_cfg"]
    tool_cfg: Tool = world.facts["tool_cfg"]

    hero.memes["bravery"] += 1
    hero.memes["indignation"] += 1
    villain.memes["fear"] += 0.5

    world.say(f"{hero.label} was a brave young hero who protected {district.name} whenever trouble arrived.")
    world.say(f"One evening, {villain.label} aimed {threat_cfg.phrase} at {district.name}, and the air felt tense and sharp.")

    world.para()
    hero.memes["indignation"] += 1
    hero.memes["fear"] += 0.5
    world.say(f"{hero.label} felt indignation flare up. It was not fair for anyone to threaten {district.name} like that.")
    world.say(f"{hero.label} climbed to the {threat_cfg.place} with {tool_cfg.phrase} ready, even though the beam looked lethal.")

    if predict_damage(world, threat, tool):
        raise StoryError("The selected tool would not stop the threat.")

    world.para()
    hero.memes["bravery"] += 1
    world.say(f"With steady bravery, {hero.label} held up {tool_cfg.phrase} and stood between the threat and the citizens.")
    world.say(f"The {tool_cfg.label} caught the {threat_cfg.kind} and blocked it before it could hurt the museum or the people below.")
    threat.meters["damage"] = 0.0
    threat.meters["risk"] = 0.0
    villain.memes["fear"] += 1

    world.para()
    hero.memes["relief"] += 1
    hero.memes["indignation"] = max(0.0, hero.memes["indignation"] - 0.5)
    world.say(f"{villain.label} dropped the control and backed away, stunned that the plan had failed.")
    world.say(f"{hero.label} stood tall on the rooftop while the city stayed safe, and bravery glowed warmer than fear.")
    state.stopped = True
    state.civilians_safe = True

    world.facts.update(stopped=True, civilians_safe=True, threat_blocked=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    villain = f["villain"]
    threat_cfg: Threat = f["threat_cfg"]
    district: District = f["district"]
    tool_cfg: Tool = f["tool_cfg"]
    return [
        f"Write a short superhero story for a child where {hero.label} shows bravery and indignation to stop {villain.label} from using {threat_cfg.phrase} at {district.name}.",
        f"Tell a concrete, action-filled story about a brave hero, a lethal danger, and a tool like {tool_cfg.label} that protects a city place.",
        f"Write a gentle superhero tale that includes the word 'lethal' and ends with the citizens safe and the hero standing tall.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    villain = f["villain"]
    threat_cfg: Threat = f["threat_cfg"]
    tool_cfg: Tool = f["tool_cfg"]
    district: District = f["district"]

    return [
        QAItem(
            question=f"Who was the brave hero in the story?",
            answer=f"The brave hero was {hero.label}. {hero.label} protected {district.name} from a lethal danger.",
        ),
        QAItem(
            question=f"Why did {hero.label} feel indignation when {villain.label} acted at {district.name}?",
            answer=f"{hero.label} felt indignation because {villain.label} was trying to use {threat_cfg.phrase} on {district.name}, and that was not fair to the people there.",
        ),
        QAItem(
            question=f"What helped {hero.label} stop the lethal threat?",
            answer=f"{tool_cfg.phrase} helped {hero.label} block the {threat_cfg.kind} before it could hurt anyone.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the threat was stopped, the citizens were safe, and {hero.label} stood tall with bravery instead of fear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel scared.",
        ),
        QAItem(
            question="What is indignation?",
            answer="Indignation is a strong feeling that something is unfair or wrong.",
        ),
        QAItem(
            question="What does lethal mean?",
            answer="Lethal means something is so dangerous that it could cause death.",
        ),
        QAItem(
            question="Why do heroes use shields in superhero stories?",
            answer="Heroes use shields to block dangerous attacks and keep people safe.",
        ),
    ]


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
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world about bravery, indignation, and a lethal threat.")
    ap.add_argument("--district", choices=DISTRICTS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--villain-name")
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


def asp_facts() -> str:
    import asp
    lines = []
    for d in DISTRICTS:
        lines.append(asp.fact("district", d))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("kind", tid, t.kind))
        lines.append(asp.fact("lethal", tid))
        lines.append(asp.fact("counter", tid, t.counter))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for b in sorted(u.blocks):
            lines.append(asp.fact("blocks", uid, b))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(D,T,U) :- threat(T), tool(U), kind(T,K), blocks(U,K), district(D).
#show compatible/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = sorted((d, t, u) for d in DISTRICTS for t in THREATS for u in TOOLS if can_use_tool(THREATS[t], TOOLS[u]))
    asv = asp_combos()
    if set(py) == set(asv):
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and python gates.")
    print("python only:", sorted(set(py) - set(asv)))
    print("asp only:", sorted(set(asv) - set(py)))
    return 1


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
    StoryParams(district="museum", threat="ray", tool="shield", hero_name="Mina", hero_type="girl", villain_name="Dr. Hex"),
    StoryParams(district="station", threat="beam", tool="mirror", hero_name="Nova", hero_type="girl", villain_name="Night Coil"),
    StoryParams(district="harbor", threat="gas", tool="mask", hero_name="Riley", hero_type="boy", villain_name="Captain Frost"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.threat and args.tool and not can_use_tool(THREATS[args.threat], TOOLS[args.tool]):
        raise StoryError("That tool cannot reasonably stop that lethal threat.")
    combos = [
        (d, t, u)
        for d in DISTRICTS
        for t in THREATS
        for u in TOOLS
        if can_use_tool(THREATS[t], TOOLS[u])
        and (args.district is None or d == args.district)
        and (args.threat is None or t == args.threat)
        and (args.tool is None or u == args.tool)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    district, threat, tool = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    villain_name = args.villain_name or rng.choice(VILLAIN_NAMES)
    return StoryParams(district=district, threat=threat, tool=tool, hero_name=hero_name, hero_type=hero_type, villain_name=villain_name)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_combos()
        print(f"{len(combos)} compatible combos:\n")
        for d, t, u in combos:
            print(f"  {d:8} {t:6} {u:7}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
