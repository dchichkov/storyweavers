#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/motion_rack_construction_site_teamwork_bad_ending.py
=========================================================================================================

A small storyworld about motion, a rack, teamwork, and a bad ending at a
construction site, told in a ghost-story style.

The premise is simple and intentionally narrow:
- A crew works at a construction site at dusk.
- They move a rack of tools and parts.
- Their teamwork stirs up something cold and unseen.
- The ending turns bad, with the motion and the rack both proving important.

The domain is designed so state changes drive the prose:
- motion affects where the rack is and how visible/safe the site feels
- teamwork increases progress but also can amplify the haunting
- the ghostly disturbance escalates from a small chill to a bad ending

This file is self-contained and follows the storyworld contract.
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
# World tuning
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the construction site"
    dusk: bool = True


@dataclass
class CrewRole:
    id: str
    label: str
    type: str
    traits: list[str] = field(default_factory=list)


@dataclass
class Rack:
    id: str
    label: str
    phrase: str
    weight: str
    contents: list[str]
    fragile: bool = True


@dataclass
class Motion:
    id: str
    verb: str
    gerund: str
    disturbance: str
    speed: str
    kind: str = "motion"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    crew_size: int
    motion: str
    rack: str
    seed: Optional[int] = None


SETTINGS = {
    "construction_site": Setting(place="the construction site", dusk=True),
}

MOTIONS = {
    "rolling": Motion(
        id="rolling",
        verb="roll the rack",
        gerund="rolling the rack",
        disturbance="a low scrape",
        speed="slowly",
    ),
    "dragging": Motion(
        id="dragging",
        verb="drag the rack",
        gerund="dragging the rack",
        disturbance="a rough groan",
        speed="with effort",
    ),
    "tilting": Motion(
        id="tilting",
        verb="tilt the rack",
        gerund="tilting the rack",
        disturbance="a crooked clatter",
        speed="carefully",
    ),
}

RACKS = {
    "tool_rack": Rack(
        id="tool_rack",
        label="tool rack",
        phrase="a tall metal rack full of hammers, ropes, and chalk lines",
        weight="heavy",
        contents=["hammers", "ropes", "chalk lines"],
        fragile=True,
    ),
    "pipe_rack": Rack(
        id="pipe_rack",
        label="pipe rack",
        phrase="a long rack stacked with pipes and bright couplers",
        weight="heavy",
        contents=["pipes", "couplers"],
        fragile=True,
    ),
}

ROLES = [
    CrewRole(id="worker", label="worker", type="man", traits=["tired", "steady"]),
    CrewRole(id="foreman", label="foreman", type="man", traits=["careful", "serious"]),
    CrewRole(id="helper", label="helper", type="girl", traits=["young", "eager"]),
]

NAMES = {
    "man": ["Owen", "Milo", "Frank", "Evan", "Cal", "Jon"],
    "girl": ["Ivy", "Nina", "Rose", "Mara", "Tess", "June"],
}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_crew(world: World, crew_size: int) -> list[Entity]:
    crew: list[Entity] = []
    for i in range(crew_size):
        role = ROLES[i % len(ROLES)]
        name = NAMES[role.type][i % len(NAMES[role.type])]
        ent = world.add(Entity(
            id=name,
            kind="character",
            type=role.type,
            label=role.label,
            traits=list(role.traits),
        ))
        crew.append(ent)
    return crew


def motion_event(world: World, crew: list[Entity], motion: Motion, rack: Rack) -> None:
    for person in crew:
        person.meters["trust"] = person.meters.get("trust", 0.0) + 0.25
    for person in crew:
        person.memes["teamwork"] = person.memes.get("teamwork", 0.0) + 0.5
    rack_state = world.get(rack.id)
    rack_state.meters["motion"] = rack_state.meters.get("motion", 0.0) + 1.0
    rack_state.meters["noise"] = rack_state.meters.get("noise", 0.0) + 1.0
    world.facts["motion_started"] = motion.id
    world.say(
        f"At dusk, the crew began to {motion.verb} at {world.setting.place}, "
        f"and the {rack.label} answered with {motion.disturbance}."
    )


def teamwork_event(world: World, crew: list[Entity], motion: Motion, rack: Rack) -> None:
    for person in crew:
        person.memes["teamwork"] = person.memes.get("teamwork", 0.0) + 1.0
        person.memes["focus"] = person.memes.get("focus", 0.0) + 0.5
    rack_state = world.get(rack.id)
    rack_state.meters["shifted"] = rack_state.meters.get("shifted", 0.0) + 1.0
    world.facts["teamwork"] = True
    world.say(
        f"They leaned together and worked as one, trying to guide the {rack.label} "
        f"{motion.speed} across the dusty ground."
    )


def haunting_event(world: World, crew: list[Entity], motion: Motion, rack: Rack) -> None:
    rack_state = world.get(rack.id)
    rack_state.memes["cold"] = rack_state.memes.get("cold", 0.0) + 1.0
    for person in crew:
        person.memes["fear"] = person.memes.get("fear", 0.0) + 1.0
    world.facts["haunting"] = True
    world.say(
        f"Then the air turned thin and cold, as if something unseen had been waiting "
        f"for the rack to move."
    )


def bad_ending(world: World, crew: list[Entity], motion: Motion, rack: Rack) -> None:
    rack_state = world.get(rack.id)
    rack_state.meters["fall"] = rack_state.meters.get("fall", 0.0) + 1.0
    rack_state.memes["broken"] = rack_state.memes.get("broken", 0.0) + 1.0
    for person in crew:
        person.memes["panic"] = person.memes.get("panic", 0.0) + 1.0
        person.memes["teamwork"] = max(0.0, person.memes.get("teamwork", 0.0) - 0.5)
    world.facts["bad_ending"] = True
    world.say(
        f"Their teamwork came too late. The {rack.label} lurched, crashed hard, and "
        f"sent a cold clang through the site like a door in a haunted house."
    )
    world.say(
        f"When the dust settled, the lantern light shook on bent metal, and nobody "
        f"dared look at the dark corner where the last sound had come from."
    )


def tell(setting: Setting, motion: Motion, rack: Rack, crew_size: int) -> World:
    world = World(setting)
    crew = build_crew(world, crew_size)

    rack_ent = world.add(Entity(
        id=rack.id,
        kind="thing",
        type="rack",
        label=rack.label,
        phrase=rack.phrase,
        plural=False,
    ))
    rack_ent.meters["motion"] = 0.0
    rack_ent.meters["shifted"] = 0.0
    rack_ent.meters["fall"] = 0.0

    motion_event(world, crew, motion, rack)
    world.para()
    teamwork_event(world, crew, motion, rack)
    haunting_event(world, crew, motion, rack)
    world.para()
    bad_ending(world, crew, motion, rack)

    world.facts.update(
        setting=setting,
        motion=motion,
        rack=rack,
        crew=crew,
        crew_size=crew_size,
    )
    return world


# ---------------------------------------------------------------------------
# Registries / content
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for m in MOTIONS:
            for r in RACKS:
                combos.append((s, m, r))
    return combos


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    motion = world.facts["motion"]
    rack = world.facts["rack"]
    return [
        f'Write a short ghost-story for a child about {motion.gerund} and a {rack.label} at a construction site.',
        f'Tell a spooky story where teamwork moves a {rack.label} and the motion makes the ending go bad.',
        f'Write a simple haunted construction story that includes the words "motion" and "rack".',
    ]


def story_qa(world: World) -> list[QAItem]:
    motion = world.facts["motion"]
    rack = world.facts["rack"]
    crew = world.facts["crew"]
    first = crew[0]
    last = crew[-1]
    return [
        QAItem(
            question=f"What were the workers trying to do with the {rack.label}?",
            answer=f"They were trying to {motion.verb} at the construction site.",
        ),
        QAItem(
            question="What made the site feel spooky?",
            answer=f"The {rack.label} moved, and then the air turned cold like something unseen was watching.",
        ),
        QAItem(
            question=f"How did the crew work together before the ending?",
            answer=f"They used teamwork and leaned together to guide the {rack.label} across the ground.",
        ),
        QAItem(
            question=f"Who was in the crew?",
            answer=f"The crew included {first.id} and {last.id}, along with the rest of the workers.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly, with the rack crashing hard and the workers too afraid to keep going.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    rack = world.facts["rack"]
    return [
        QAItem(
            question="What is a rack?",
            answer="A rack is a frame or stand that holds things up or keeps them together.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is a construction site?",
            answer="A construction site is a place where people build or repair things.",
        ),
        QAItem(
            question="Why can motion make something dangerous?",
            answer="Motion can make a heavy object slip, tip, or fall if it is not controlled well.",
        ),
        QAItem(
            question=f"Why would a {rack.label} be hard to move?",
            answer="A rack can be hard to move because it is heavy and awkward to balance.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.kind:7}/{e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts from Python:
% setting(S). motion(M). rack(R). crew(N).
% teamwork(yes). bad_ending(yes).

spooky_story(S, M, R) :- setting(S), motion(M), rack(R).
crew_action(M) :- motion(M).
problem(R) :- rack(R), crew_action(M).
bad_story(S, M, R) :- spooky_story(S, M, R), problem(R), teamwork(yes), bad_ending(yes).

#show spooky_story/3.
#show bad_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MOTIONS:
        lines.append(asp.fact("motion", mid))
    for rid in RACKS:
        lines.append(asp.fact("rack", rid))
    lines.append(asp.fact("teamwork", "yes"))
    lines.append(asp.fact("bad_ending", "yes"))
    return "\n".join(lines)


def asp_program(show: str = "#show spooky_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show bad_story/3."))
    atoms = asp.atoms(model, "bad_story")
    py = [(s, m, r) for (s, m, r) in valid_combos()]
    clingo_set = set(atoms)
    py_set = set(py)
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Parser / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story construction site world about motion, a rack, teamwork, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--motion", choices=MOTIONS)
    ap.add_argument("--rack", choices=RACKS)
    ap.add_argument("--crew-size", type=int, default=3)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    motion = args.motion or rng.choice(list(MOTIONS))
    rack = args.rack or rng.choice(list(RACKS))
    crew_size = args.crew_size
    if crew_size < 2:
        raise StoryError("The crew needs at least two people for teamwork.")
    return StoryParams(setting=setting, crew_size=crew_size, motion=motion, rack=rack)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MOTIONS[params.motion], RACKS[params.rack], params.crew_size)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show bad_story/3."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for s, m, r in valid_combos():
            params = StoryParams(setting=s, crew_size=3, motion=m, rack=r)
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
