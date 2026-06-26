#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure tale:
a defective ship enters a tense phase, the crew feels ambivalence,
a twist reveals the real problem, and dialogue leads to a happy ending.

This file follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of shared results containers
- lazy import of shared ASP helper inside ASP functions
- typed world entities with physical meters and emotional memes
- inline ASP_RULES twin and a Python reasonableness gate
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the starport"
    description: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    twist: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    kind: str
    fix: str
    tail: str
    protects: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    mode: str = "normal"

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
        clone = World(self.setting)
        clone.entities = dataclasses.replace(self).entities if False else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.mode = self.mode
        return clone


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTINGS = {
    "orbit": Setting(
        place="the orbiting station",
        description="The station floated above a blue planet, with bright windows and humming corridors.",
        affords={"repair", "scan", "dock"},
    ),
    "hangar": Setting(
        place="the ship hangar",
        description="The hangar smelled like metal and warm fuel, and tiny lights blinked over the tools.",
        affords={"repair", "scan", "launch"},
    ),
    "moonbase": Setting(
        place="the moonbase",
        description="The moonbase was quiet except for the radio crackle and the soft thump of boots.",
        affords={"repair", "scan", "launch"},
    ),
}

MISSIONS = {
    "defective_phase": Mission(
        id="defective_phase",
        verb="fix the defective engine",
        gerund="checking the engine in its defective phase",
        rush="hurry to the engine room",
        risk="the ship might drift and miss the dock",
        twist="the engine was not truly broken; the sensor loop was stuck",
        keyword="defective",
        tags={"defective", "phase", "ambivalence"},
    ),
    "signal_twist": Mission(
        id="signal_twist",
        verb="follow the strange signal",
        gerund="tracking the signal through the dark",
        rush="dash to the comms console",
        risk="they might follow the wrong beacon",
        twist="the signal came from their own rescue beacon",
        keyword="twist",
        tags={"twist", "ambivalence"},
    ),
    "quiet_phase": Mission(
        id="quiet_phase",
        verb="prepare the rescue run",
        gerund="getting ready during a quiet phase",
        rush="gather the kits",
        risk="the crew could waste time if they hesitated",
        twist="the quiet was hiding a jammed latch in the cargo bay",
        keyword="phase",
        tags={"phase", "ambivalence"},
    ),
}

REPAIRS = {
    "spanner": Repair(
        id="spanner",
        label="a magnetic spanner",
        kind="tool",
        fix="twist the panel open and reset the latch",
        tail="clicked the panel back into place",
        protects={"sensor", "latch"},
    ),
    "patch": Repair(
        id="patch",
        label="a bright patch kit",
        kind="tool",
        fix="seal the cracked line",
        tail="sealed the line cleanly",
        protects={"hull"},
    ),
    "lens": Repair(
        id="lens",
        label="a scanner lens",
        kind="tool",
        fix="check the blink pattern",
        tail="showed the true blink pattern",
        protects={"signal"},
    ),
}

NAMES = ["Mara", "Ivo", "Nia", "Sol", "Aria", "Tess", "Rin", "Kian"]
ROLES = ["captain", "pilot", "engineer", "navigator"]


@dataclass
class StoryParams:
    setting: str
    mission: str
    repair: str
    name: str
    role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def mission_needs_repair(mission: Mission, repair: Repair) -> bool:
    if mission.id == "defective_phase":
        return "sensor" in repair.protects or "latch" in repair.protects
    if mission.id == "signal_twist":
        return "signal" in repair.protects
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for m in MISSIONS:
            for r in REPAIRS:
                if mission_needs_repair(MISSIONS[m], REPAIRS[r]):
                    out.append((s, m, r))
    return out


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mission = MISSIONS[params.mission]
    repair = REPAIRS[params.repair]
    world = World(setting=setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.role, label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type="pilot", label="Jori"))
    ship = world.add(Entity(
        id="Ship",
        kind="thing",
        type="ship",
        label="the ship",
        phrase="the little silver ship",
        meters={"fuel": 7.0, "wear": 1.0},
        memes={"stress": 1.0},
    ))
    tool = world.add(Entity(
        id=repair.id,
        kind="thing",
        type="tool",
        label=repair.label,
        phrase=repair.label,
        owner=hero.id,
    ))

    world.facts.update(hero=hero, helper=helper, ship=ship, tool=tool, mission=mission, repair=repair)

    world.say(f"{hero.name_word()} was the {params.role} on {setting.place}.")
    world.say(setting.description)
    world.say(
        f"One day, the crew faced a {mission.keyword} problem: {mission.gerund}, and the ship felt a little defective."
    )
    world.say(
        f"{hero.name_word()} had ambivalence at first, because {mission.risk}."
    )

    world.para()
    ship.meters["wear"] += 2.0
    ship.memes["stress"] += 1.0
    hero.memes["ambivalence"] = 2.0
    helper.memes["concern"] = 1.0
    world.say(f"{hero.name_word()} wanted to go fast, but {helper.name_word()} pointed at the blinking panel.")
    world.say(f'"Maybe the problem is a bit smaller than it looks," {helper.name_word()} said.')
    world.say(f'"But if we guess wrong, {mission.risk}," {hero.name_word()} said.')

    world.para()
    world.say(
        f"Then came the twist: {mission.twist}."
    )
    world.say(f"{hero.name_word()} used {repair.label} to {repair.fix}.")
    world.say(f"{helper.name_word()} smiled and said, \"Try it now.\"")
    ship.meters["wear"] = max(0.0, ship.meters["wear"] - 1.5)
    ship.memes["stress"] = max(0.0, ship.memes["stress"] - 1.0)
    hero.memes["ambivalence"] = 0.0
    hero.memes["joy"] = 2.0

    world.para()
    world.say(
        f"The panel hummed once, then steadied. {repair.tail}, and the engine light turned green."
    )
    world.say(
        f'"We fixed it," {hero.name_word()} said. "And we did it together."'
    )
    world.say(
        f'{helper.name_word()} laughed. "Happy ending," {helper.pronoun("subject")} said, '
        f'"and we still have time for the stars."'
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission: Mission = f["mission"]
    return [
        f'Write a short Space Adventure story with the word "{mission.keyword}" and a surprising twist.',
        f"Tell a child-friendly dialogue story where {f['hero'].name_word()} must handle a defective problem on a spaceship.",
        "Write a simple space story that begins with worry, turns on a twist, and ends happily.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mission: Mission = f["mission"]
    repair: Repair = f["repair"]
    ship: Entity = f["ship"]
    return [
        QAItem(
            question=f"Who was trying to solve the problem on the ship?",
            answer=f"{hero.name_word()} was the {hero.type} trying to solve the problem, and {helper.name_word()} helped too.",
        ),
        QAItem(
            question=f"Why did {hero.name_word()} feel ambivalence at first?",
            answer=f"{hero.name_word()} felt ambivalence because the ship seemed defective and there was a risk of drifting or choosing the wrong fix.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {mission.twist}. That changed the problem from scary to manageable.",
        ),
        QAItem(
            question=f"What tool helped the crew?",
            answer=f"{repair.label} helped the crew because it could handle the {mission.keyword} problem and make the repair safe.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The ship settled down, the lights turned green, and the crew had a happy ending with time left to enjoy the stars.",
        ),
        QAItem(
            question=f"What changed for the ship?",
            answer=f"The ship started out tense and worn, but after the repair its stress dropped and the damaged phase passed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mission: Mission = f["mission"]
    repair: Repair = f["repair"]
    out = [
        QAItem(
            question="What is a spaceship for?",
            answer="A spaceship is a craft that carries people through space from one place to another.",
        ),
        QAItem(
            question="What does a scanner do?",
            answer="A scanner helps people look for hidden details by measuring light, movement, or signals.",
        ),
    ]
    if "defective" in mission.tags:
        out.append(QAItem(
            question="What does defective mean?",
            answer="Defective means something is not working the way it should, so it may need fixing.",
        ))
    if "phase" in mission.tags:
        out.append(QAItem(
            question="What is a phase?",
            answer="A phase is a part of a process or a time when something is happening in a certain way.",
        ))
    if "ambivalence" in mission.tags:
        out.append(QAItem(
            question="What is ambivalence?",
            answer="Ambivalence means feeling two ways at once, like both worry and hope.",
        ))
    if "twist" in mission.tags:
        out.append(QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story turn in a new direction.",
        ))
    out.append(QAItem(
        question=f"What is {repair.label} used for?",
        answer=f"{repair.label} is used to help with repairs by doing its special job on the broken part.",
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mission is compatible with a repair if the repair protects the kind of
% broken thing that matters in that mission.
compatible(M, R) :- mission(M), repair(R),
    mission_needs(M, K), protects(R, K).

valid_story(S, M, R) :- setting(S), mission(M), repair(R), compatible(M, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_needs", mid, "sensor" if mid == "defective_phase" else "signal" if mid == "signal_twist" else "latch"))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        for p in sorted(r.protects):
            lines.append(asp.fact("protects", rid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    python_set = set(valid_combos())
    asp_set = set(asp_valid_stories())
    # Convert ASP tuples to same arity with settings, missions, repairs
    asp_set3 = {(s, m, r) for (s, m, r) in asp_set}
    if asp_set3 == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(asp_set3 - python_set))
    print("  only in python:", sorted(python_set - asp_set3))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=ROLES)
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
    combos = valid_combos()
    if args.setting and args.mission and args.repair:
        if (args.setting, args.mission, args.repair) not in combos:
            raise StoryError("That setting, mission, and repair do not form a reasonable story.")
    filtered = [
        c for c in combos
        if (not args.setting or c[0] == args.setting)
        and (not args.mission or c[1] == args.mission)
        and (not args.repair or c[2] == args.repair)
    ]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    setting, mission, repair = rng.choice(sorted(filtered))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    return StoryParams(setting=setting, mission=mission, repair=repair, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(setting="orbit", mission="defective_phase", repair="spanner", name="Mara", role="engineer"),
    StoryParams(setting="hangar", mission="signal_twist", repair="lens", name="Ivo", role="captain"),
    StoryParams(setting="moonbase", mission="quiet_phase", repair="patch", name="Nia", role="pilot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print("  ", s)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
