#!/usr/bin/env python3
"""
Space Adventure story world: a small crew, a shivering bridge crossing, a soil
problem, and a brave twist that resolves the conflict.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self):
        if not self.meters:
            self.meters = {"shiver": 0.0, "soil": 0.0, "conflict": 0.0, "bravery": 0.0, "twist": 0.0}
        if not self.memes:
            self.memes = {"shiver": 0.0, "soil": 0.0, "conflict": 0.0, "bravery": 0.0, "twist": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    bridge_name: str
    place_detail: str
    cold: bool = True


@dataclass
class Mission:
    id: str
    goal: str
    verb: str
    rush: str
    twist: str
    risk: str
    keyword: str


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    protects: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.trace_lines: list[str] = []

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


SETTINGS = {
    "orbital_bridge": Setting(
        name="the orbital bridge",
        bridge_name="the bridge",
        place_detail="It stretched between two silver stations above the blue planet.",
        cold=True,
    ),
    "moon_walk": Setting(
        name="the moon walk",
        bridge_name="the glass bridge",
        place_detail="It floated over a quiet crater and glimmered under the stars.",
        cold=True,
    ),
    "dock_ring": Setting(
        name="the dock ring",
        bridge_name="the cargo bridge",
        place_detail="It linked a busy dock to a round hangar full of blinking lights.",
        cold=False,
    ),
}

MISSIONS = {
    "signal": Mission(
        id="signal",
        goal="reach the signal beacon",
        verb="cross the bridge to the beacon",
        rush="dash toward the beacon",
        twist="The beacon had slipped to the far side of the bridge",
        risk="the soil on their boots could make the clear panels slick",
        keyword="bridge",
    ),
    "sample": Mission(
        id="sample",
        goal="bring a soil sample home",
        verb="carry the soil sample across the bridge",
        rush="hurry across with the sample tray",
        twist="The sample tray tipped and the soil drifted loose",
        risk="the loose soil could spill and stain the deck",
        keyword="soil",
    ),
    "rescue": Mission(
        id="rescue",
        goal="help the lost drone",
        verb="guide the drone over the bridge",
        rush="run to the drone",
        twist="The drone bobbed under a loose cable and then shivered",
        risk="the cold wind could shake the tiny drone off course",
        keyword="shiver",
    ),
}

GEAR = [
    Gear(
        id="boots",
        label="warm boots",
        covers={"feet"},
        protects={"soil"},
        prep="put on warm boots first",
        tail="walked back for the warm boots",
        plural=True,
    ),
    Gear(
        id="gloves",
        label="thick gloves",
        covers={"hands"},
        protects={"cold"},
        prep="slip on thick gloves first",
        tail="went back for the thick gloves",
        plural=True,
    ),
    Gear(
        id="cloak",
        label="a star cloak",
        covers={"torso"},
        protects={"cold"},
        prep="wear a star cloak",
        tail="came back in the star cloak",
    ),
]

NAMES = ["Nova", "Milo", "Rin", "Tala", "Juno", "Pax", "Luna", "Ari"]
TYPES = ["girl", "boy", "pilot", "captain"]
ALL_TRIGGERS = ["shiver", "soil", "bridge"]


@dataclass
class StoryParams:
    setting: str
    mission: str
    hero_name: str
    hero_type: str
    partner_name: str
    partner_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with bridge, soil, shiver, twist, bravery, and conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--name")
    ap.add_argument("--partner-name")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--partner-type", choices=TYPES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MISSIONS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.mission:
        if (args.setting, args.mission) not in combos:
            raise StoryError("No valid space adventure matches that setting and mission.")
    setting = args.setting or rng.choice(list(SETTINGS))
    mission = args.mission or rng.choice(list(MISSIONS))
    hero_type = args.hero_type or rng.choice(TYPES)
    partner_type = args.partner_type or rng.choice(TYPES)
    hero_name = args.name or rng.choice(NAMES)
    partner_name = args.partner_name or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(setting=setting, mission=mission, hero_name=hero_name, hero_type=hero_type,
                       partner_name=partner_name, partner_type=partner_type)


def _predict(world: World, hero: Entity, mission: Mission) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["shiver"] += 1
    sim.get(hero.id).meters["soil"] += 1
    return True


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mission = MISSIONS[params.mission]
    w = World(setting)
    hero = w.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, meters={"shiver": 0, "soil": 0, "conflict": 0, "bravery": 0, "twist": 0}, memes={"shiver": 0, "soil": 0, "conflict": 0, "bravery": 0, "twist": 0}))
    partner = w.add(Entity(id=params.partner_name, kind="character", type=params.partner_type))
    sample = w.add(Entity(id="sample", type="thing", label="soil sample", phrase="a jar of glittering soil", owner=hero.id, caretaker=partner.id))
    beacon = w.add(Entity(id="beacon", type="thing", label="beacon"))
    hero.meters["bravery"] += 1
    hero.memes["bravery"] += 1

    w.say(f"{hero.id} and {partner.id} stood at {setting.name}. {setting.place_detail}")
    w.say(f"They had one clear job: {mission.goal}. {hero.id} liked the mission, but the wind made {hero.id} shiver.")

    w.para()
    w.say(f"Then came the twist: {mission.twist}. {mission.risk.capitalize()}.")
    hero.meters["shiver"] += 1
    hero.memes["conflict"] += 1
    partner.memes["conflict"] += 1
    sample.worn_by = hero.id
    w.zone = {"feet", "hands", "torso"}

    w.say(f"{hero.id} wanted to {mission.verb}, but {hero.id} saw {sample.label} on the deck and paused.")
    w.say(f"{partner.id} warned that a bad step could spread the soil. That was the conflict.")

    gear = None
    if mission.id in {"signal", "sample"}:
        gear = GEAR[0]
    else:
        gear = GEAR[1]

    w.para()
    w.say(f"{partner.id} smiled and offered a brave fix: {gear.prep}.")
    w.say(f"{hero.id} listened, took a breath, and chose bravery over rushing.")
    hero.meters["bravery"] += 1
    hero.memes["conflict"] = 0
    if "cold" in gear.protects:
        hero.meters["shiver"] = max(0, hero.meters["shiver"] - 1)
    if "soil" in gear.protects:
        sample.meters["soil"] = max(0, sample.meters["soil"] - 1)

    w.say(f"Together they {gear.tail}. Soon {hero.id} finished the crossing, and the bridge stayed clean enough to shine.")
    w.facts.update(hero=hero, partner=partner, sample=sample, setting=setting, mission=mission, gear=gear, beacon=beacon)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    return [
        f'Write a short space adventure for a young child that includes the words "bridge", "soil", and "shiver".',
        f"Tell a gentle story about {hero.id} who must {mission.goal} but faces a twist and a conflict before showing bravery.",
        f"Write a small spaceship-side story where a bridge crossing is tricky, then ends with a brave choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, partner, mission, gear = f["hero"], f["partner"], f["mission"], f["gear"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, who went on a space mission with {partner.id}.",
        ),
        QAItem(
            question=f"What was the hard part of the mission?",
            answer=f"The hard part was crossing the bridge while dealing with a twist, a conflict, and the cold that made {hero.id} shiver.",
        ),
        QAItem(
            question=f"What brave choice helped at the end?",
            answer=f"{hero.id} accepted {gear.label} and kept going instead of rushing ahead.",
        ),
        QAItem(
            question=f"What happened to the soil?",
            answer=f"The soil stayed under control, so it did not ruin the bridge crossing.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a bridge?", answer="A bridge is a path that helps people cross from one side to another."),
        QAItem(question="What does shiver mean?", answer="To shiver means to shake a little because you are cold or scared."),
        QAItem(question="What is soil?", answer="Soil is the loose earth where plants can grow."),
        QAItem(question="What is bravery?", answer="Bravery means doing something hard or scary even when you feel nervous."),
        QAItem(question="What is a conflict?", answer="A conflict is a problem or disagreement that characters need to solve."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprising change that makes the story turn in a new way."),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MISSIONS:
        lines.append(asp.fact("mission", m))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for p in sorted(g.protects):
            lines.append(asp.fact("protects", g.id, p))
    for trigger in ALL_TRIGGERS:
        lines.append(asp.fact("trigger", trigger))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M) :- setting(S), mission(M).
compatible_story(S,M) :- valid(S,M).
#show valid/2.
#show compatible_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        for title, items in [
            ("Generation prompts", sample.prompts),
            ("Story questions", sample.story_qa),
            ("World questions", sample.world_qa),
        ]:
            print(f"== {title} ==")
            if title == "Generation prompts":
                for p in items:
                    print(p)
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible settings/missions:")
        for s, m in asp_valid_combos():
            print(s, m)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in SETTINGS:
            for m in MISSIONS:
                p = StoryParams(setting=s, mission=m, hero_name="Nova", hero_type="pilot", partner_name="Milo", partner_type="captain")
                samples.append(generate(p))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
