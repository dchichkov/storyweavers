#!/usr/bin/env python3
"""
A small story world: a space adventure with a point of foreshadowing.

Premise:
A child astronaut on a tiny ship sees a mysterious point of light ahead.
A cautious captain notices that the point may mean trouble, and the crew must
decide whether to ignore the hint or follow it.

The world model tracks:
- physical meters: hull charge, distance, fuel, signal strength, dust
- emotional memes: curiosity, worry, pride, trust, relief

Foreshadowing:
The first strange point in the sky is not just decoration; it predicts a later
turn. The story can resolve by approaching the point, finding a helpful beacon,
and using it to safely complete the journey.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    route: str
    sky: str
    feature: str = "foreshadowing"


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    type: str
    risk: str
    fix: str
    clue: str


@dataclass
class StoryParams:
    place: str
    object: str
    name: str
    role: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


SETTINGS = {
    "orbital_lane": Setting(place="the orbital lane", route="space lane", sky="the dark sky"),
    "asteroid_pass": Setting(place="the asteroid pass", route="rocky lane", sky="the glittering dark"),
    "moon_arc": Setting(place="the moon arc", route="lunar lane", sky="the silver sky"),
}

OBJECTS = {
    "point": ObjectCfg(
        label="point beacon",
        phrase="a tiny point beacon with a blinking tip",
        type="beacon",
        risk="it might lead them toward a dead end",
        fix="it can guide them to the safe dock",
        clue="a bright point ahead kept flashing like a wink",
    ),
    "comet": ObjectCfg(
        label="comet shard",
        phrase="a glassy comet shard",
        type="shard",
        risk="it might hide a warning trail in the dust",
        fix="it can shine a warning path",
        clue="a sharp point of light skated across the window",
    ),
    "spark": ObjectCfg(
        label="spark probe",
        phrase="a little spark probe with a pointed nose",
        type="probe",
        risk="it might be the first sign of trouble",
        fix="it can find the safe route",
        clue="a single point blinked where the route bent",
    ),
}

TRAITS = ["curious", "brave", "careful", "hopeful", "steady"]
NAMES = ["Ari", "Mina", "Jett", "Nova", "Sol", "Pip", "Rin", "Tess"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space adventure story world with foreshadowing and a point of light."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["captain", "pilot", "cadet"])
    ap.add_argument("--helper", choices=["robot", "navigator", "mechanic"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    obj = args.object_name or rng.choice(list(OBJECTS))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(["captain", "pilot", "cadet"])
    helper = args.helper or rng.choice(["robot", "navigator", "mechanic"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, object=obj, name=name, role=role, helper=helper, trait=trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.object not in OBJECTS:
        raise StoryError("Unknown foreshadowing object.")
    if not params.name.strip():
        raise StoryError("Name cannot be empty.")


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    setting = SETTINGS[params.place]
    cfg = OBJECTS[params.object]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.role,
        label=params.name,
        traits=["little", params.trait],
        meters={"fuel": 2.0, "distance": 0.0, "dust": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "trust": 0.5, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        meters={"scan": 1.0},
        memes={"trust": 0.5},
    ))
    obj = world.add(Entity(
        id="object",
        kind="thing",
        type=cfg.type,
        label=cfg.label,
        phrase=cfg.phrase,
        meters={"signal": 1.0, "charge": 0.5},
    ))

    world.say(
        f"{hero.label} was a little {params.trait} {params.role} aboard a small ship near {setting.place}."
    )
    world.say(
        f"{hero.label} loved space because every quiet window held a new surprise."
    )
    world.say(
        f"One evening, {cfg.clue} above the hull."
    )
    world.say(
        f"{helper.label.capitalize()} noticed the point too and said, \"Keep watching. Little points can mean big things in space.\""
    )

    world.para()
    hero.memes["curiosity"] += 1.0
    hero.memes["worry"] += 0.5
    hero.meters["distance"] += 1.0
    world.say(
        f"The ship drifted along {setting.route}, and the point stayed ahead like a tiny finger showing the way."
    )
    world.say(
        f"{hero.label} wanted to follow it, but also wondered whether it was a trap."
    )
    if params.place == "asteroid_pass":
        hero.meters["dust"] += 1.0
        hero.memes["worry"] += 0.5
        world.say(
            f"Stone dust tapped the window, which made the point feel even stranger."
        )
    else:
        world.say(
            f"The sky was calm, but the point kept blinking in a way that felt important."
        )

    world.para()
    world.say(
        f"{helper.label.capitalize()} ran a scan and found that the point was a beacon, not a danger."
    )
    world.say(
        f"It pointed toward a hidden safe dock where the ship could refuel."
    )
    hero.memes["trust"] += 0.5
    hero.meters["fuel"] -= 0.5
    world.say(
        f"{hero.label} smiled, because the warning had turned into a promise."
    )

    world.para()
    hero.meters["distance"] += 2.0
    hero.meters["fuel"] += 1.5
    hero.memes["relief"] += 1.0
    world.say(
        f"They followed the point, found the dock, and topped up the tanks just before the ship grew tired."
    )
    world.say(
        f"In the end, {hero.label} looked back at the tiny light and understood the foreshadowing: the first point in the sky had been a clue to safety all along."
    )

    world.facts.update(hero=hero, helper=helper, object=obj, cfg=cfg, params=params, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cfg = f["cfg"]
    return [
        f'Write a short space adventure story for a young child with a mysterious point of light.',
        f"Tell a gentle story about {hero.label}, a {hero.type}, who sees {cfg.clue} and learns what it means.",
        f'Write a story that uses the word "point" and ends with a safe discovery in space.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    cfg = f["cfg"]
    params = f["params"]
    return [
        QAItem(
            question=f"Who saw the first point of light in the sky?",
            answer=f"{hero.label} saw it first while traveling aboard the ship near {world.setting.place}.",
        ),
        QAItem(
            question=f"What did the point turn out to be?",
            answer=f"It turned out to be a {cfg.label}, which was a helpful sign instead of a danger.",
        ),
        QAItem(
            question=f"How did {helper.label} help the crew?",
            answer=f"{helper.label.capitalize()} scanned the point and found that it led to a safe dock for refueling.",
        ),
        QAItem(
            question=f"Why is the point an example of foreshadowing?",
            answer=(
                f"It matters because the tiny point appeared early as a clue, and later the crew learned it was guiding them to safety."
            ),
        ),
        QAItem(
            question=f"How did {params.name} feel at the end?",
            answer=f"{params.name} felt relieved and happier after the ship found fuel and the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beacon in space?",
            answer="A beacon is a light or signal that helps ships know where to go.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is when an early clue hints at something important that will happen later.",
        ),
        QAItem(
            question="Why do spaceships need fuel?",
            answer="Spaceships need fuel so their engines can keep moving through space.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show compatible/1.
compatible(point).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([asp.fact("theme", "space_adventure"), asp.fact("feature", "foreshadowing"), asp.fact("seed_word", "point")])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/1."))
    ok = bool(asp.atoms(model, "compatible"))
    if ok:
        print("OK: ASP gate matches the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
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
    StoryParams(place="orbital_lane", object="point", name="Nova", role="captain", helper="robot", trait="curious"),
    StoryParams(place="asteroid_pass", object="spark", name="Ari", role="pilot", helper="navigator", trait="careful"),
    StoryParams(place="moon_arc", object="comet", name="Tess", role="cadet", helper="mechanic", trait="hopeful"),
]


def resolve_asp() -> None:
    raise StoryError("ASP mode is minimal in this world; use --verify or --show-asp.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        resolve_asp()

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
