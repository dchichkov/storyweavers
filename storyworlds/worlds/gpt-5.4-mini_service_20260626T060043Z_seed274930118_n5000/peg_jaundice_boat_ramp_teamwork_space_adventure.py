#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/peg_jaundice_boat_ramp_teamwork_space_adventure.py
============================================================================================================

A tiny, self-contained story world in a space-adventure style.

Seed premise:
- At a boat ramp, a small crew prepares a little space skiff.
- They need teamwork to solve a launch problem.
- The story must include the seed words "peg" and "jaundice".
- The tone stays child-facing and concrete, like a small space adventure.

The world model is intentionally small:
- physical meters track things like stuckness, tide, weight, and readiness
- emotional memes track worry, teamwork, pride, and relief

The story is generated from state changes, not from a frozen template.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "captain"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "captain_boy"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the boat ramp"
    tide: str = "low"
    afford_launch: bool = True


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    consequence: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    helps: set[str]
    prep: str
    tail: str


@dataclass
class StoryParams:
    place: str
    mission: str
    gear: str
    name: str
    role: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "boat_ramp": Setting(place="the boat ramp", tide="low", afford_launch=True),
}

MISSIONS = {
    "launch": Mission(
        id="launch",
        verb="launch the little star skiff",
        gerund="launching the little star skiff",
        rush="push the skiff into the water",
        hazard="stuck on the ramp",
        consequence="stayed stuck and missed the tide",
        keyword="star skiff",
        tags={"space", "water", "teamwork", "ramp"},
    ),
    "tow": Mission(
        id="tow",
        verb="tow the supply pod",
        gerund="towing the supply pod",
        rush="pull the pod down the ramp",
        hazard="too heavy to move alone",
        consequence="did not budge",
        keyword="supply pod",
        tags={"space", "teamwork", "ramp"},
    ),
}

GEAR = {
    "peg": Gear(
        id="peg",
        label="a peg",
        phrase="a little peg for the rope",
        helps={"launch", "tow"},
        prep="set a peg in the dock cleat",
        tail="kept the rope steady",
    ),
    "pull_line": Gear(
        id="pull_line",
        label="a pull line",
        phrase="a strong pull line",
        helps={"tow"},
        prep="loop the pull line around the handle",
        tail="shared the heavy work",
    ),
}

NAMES = ["Peg", "Nova", "Milo", "Aria", "Tess", "Luca", "Zia", "Oren"]
HELPER_NAMES = ["Jaundice", "Comet", "Pip", "Sunny", "Blue"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for mission_id, mission in MISSIONS.items():
            for gear_id, gear in GEAR.items():
                if mission_id in gear.helps:
                    combos.append((place, mission_id, gear_id))
    return combos


def reasonableness_gate(place: str, mission_id: str, gear_id: str) -> bool:
    return (place, mission_id, gear_id) in valid_combos()


def explain_rejection(place: str, mission_id: str, gear_id: str) -> str:
    mission = MISSIONS[mission_id]
    gear = GEAR[gear_id]
    return (
        f"(No story: {gear.label} does not make sense for {mission.gerund} at {place}. "
        f"The teamwork fix has to help with the real problem, not just sound spacey.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small teamwork space adventure at a boat ramp.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mission", choices=MISSIONS.keys())
    ap.add_argument("--gear", choices=GEAR.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--role", choices=["captain", "pilot", "crew"], default=None)
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
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mission is None or c[1] == args.mission)
        and (args.gear is None or c[2] == args.gear)
    ]
    if not combos:
        if args.place and args.mission and args.gear:
            raise StoryError(explain_rejection(args.place, args.mission, args.gear))
        raise StoryError("(No valid combination matches the given options.)")

    place, mission, gear = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != name])
    role = args.role or rng.choice(["captain", "pilot", "crew"])
    return StoryParams(place=place, mission=mission, gear=gear, name=name, role=role, helper_name=helper_name)


def _do_mission(world: World, hero: Entity, helper: Entity, mission: Mission, gear: Gear) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1
    world.say(
        f"At {world.setting.place}, {hero.id} looked at the {mission.keyword} and knew it needed teamwork."
    )
    world.say(
        f"{helper.id} brought out {gear.phrase}, and together they worked by the water."
    )
    if gear.id == "peg":
        world.say(
            f"{hero.id} set {gear.label} into the dock, and {helper.id} tied the rope around it."
        )
    else:
        world.say(
            f"{hero.id} and {helper.id} used {gear.label} to share the load."
        )
    hero.meters["ready"] = hero.meters.get("ready", 0.0) + 1
    helper.meters["ready"] = helper.meters.get("ready", 0.0) + 1
    world.facts["fixed"] = True
    world.facts["gear_label"] = gear.label


def tell(setting: Setting, mission: Mission, gear: Gear, hero_name: str, role: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=role, label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="crew", label=helper_name))
    craft = world.add(Entity(
        id="skiff",
        kind="thing",
        type="craft",
        label=mission.keyword,
        phrase=f"the little {mission.keyword}",
    ))
    peg = world.add(Entity(id="peg", kind="thing", type="tool", label="peg", phrase="a peg"))
    jaundice = world.add(Entity(
        id="jaundice",
        kind="thing",
        type="helper",
        label="Jaundice",
        phrase="Jaundice, the yellow helper light",
    ))

    world.say(
        f"{hero.id} was the {hero.pronoun('subject').capitalize()} in charge of the day, but {helper.id} was ready to help."
    )
    world.say(
        f"Their small space craft, {craft.phrase}, waited beside the boat ramp."
    )
    world.say(
        f"Even {jaundice.label} blinked on the console, bright and jaundice-yellow, as if it wanted to join the teamwork."
    )
    world.para()
    world.say(
        f"{world.setting.place.capitalize()} was calm, but the craft would not move by itself."
    )
    world.say(
        f"{hero.id} wanted to {mission.verb}, yet the skiff felt {mission.hazard}."
    )
    world.say(
        f"If they pushed too hard, the mission would end with the skiff {mission.consequence}."
    )
    world.para()
    _do_mission(world, hero, helper, mission, gear)
    world.say(
        f"With the {gear.label} holding fast, the skiff slid into the water at last."
    )
    world.say(
        f"{hero.id} smiled, {helper.id} laughed, and {jaundice.label} glowed like a tiny sunrise."
    )
    world.facts.update(
        hero=hero,
        helper=helper,
        craft=craft,
        peg=peg,
        jaundice=jaundice,
        mission=mission,
        gear=gear,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    gear = f["gear"]
    return [
        f'Write a short space-adventure story for a young child set at the boat ramp with teamwork and the word "peg".',
        f"Tell a gentle story where {hero.id} and a helper work together to {mission.verb}, using {gear.label} to solve the problem.",
        f'Write a simple story that includes "jaundice" as a bright yellow helper-light and ends with a successful launch.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mission = f["mission"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {helper.id} try to {mission.verb}?",
            answer=f"They worked at {world.setting.place}, right beside the water."
        ),
        QAItem(
            question=f"What made the launch possible for {hero.id} and {helper.id}?",
            answer=f"Teamwork made it possible, and {gear.label} helped hold everything steady."
        ),
        QAItem(
            question=f"Why did {hero.id} need help with the {mission.keyword}?",
            answer=f"The {mission.keyword} was stuck on the ramp, so one child alone could not move it safely."
        ),
        QAItem(
            question=f"What did Jaundice do in the story?",
            answer="Jaundice blinked like a bright yellow helper light and made the scene feel cheerful."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a peg used for?",
            answer="A peg can hold a rope or line in place so something does not drift away."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together."
        ),
        QAItem(
            question="What is a boat ramp?",
            answer="A boat ramp is a slanted path that helps a boat or skiff move into the water."
        ),
        QAItem(
            question="Why do lights help at night?",
            answer="Lights help people see better and know where to go."
        ),
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
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(boat_ramp).
mission(launch).
mission(tow).
gear(peg).
gear(pull_line).

works_for(peg, launch).
works_for(peg, tow).
works_for(pull_line, tow).

valid(P, M, G) :- place(P), mission(M), gear(G), works_for(G, M).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MISSIONS:
        lines.append(asp.fact("mission", m))
    for g in GEAR:
        lines.append(asp.fact("gear", g))
    for gid, gear in GEAR.items():
        for m in gear.helps:
            lines.append(asp.fact("works_for", gid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MISSIONS[params.mission],
        GEAR[params.gear],
        params.name,
        params.role,
        params.helper_name,
    )
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
    StoryParams(place="boat_ramp", mission="launch", gear="peg", name="Peg", role="pilot", helper_name="Jaundice"),
    StoryParams(place="boat_ramp", mission="tow", gear="pull_line", name="Nova", role="captain", helper_name="Jaundice"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mission, gear) combos:\n")
        for p, m, g in combos:
            print(f"  {p:10} {m:8} {g}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mission} at {p.place} (gear: {p.gear})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
