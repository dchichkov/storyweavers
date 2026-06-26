#!/usr/bin/env python3
"""
swarm_loft_curiosity_myth.py

A tiny story world about a curious child in a loft who meets a swarm and
learns that wonder can be brave without being reckless.
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the loft"
    detail: str = "under the rafters"
    affords: set[str] = field(default_factory=set)


@dataclass
class Swarm:
    id: str
    name: str
    kind: str
    hum: str
    startle: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    swarm: str
    place: str = "loft"
    name: str = "Mira"
    gender: str = "girl"
    parent: str = "grandmother"
    trait: str = "curious"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.swarm: Optional[Swarm] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "loft": Setting(place="the loft", detail="beneath the dusty rafters", affords={"swarm"}),
}

SWARMS = {
    "moths": Swarm(
        id="moths",
        name="moon moths",
        kind="moths",
        hum="a soft papery hum",
        startle="fluttered up in a bright cloud",
        glow="pale",
        tags={"swarm", "light", "night"},
    ),
    "bees": Swarm(
        id="bees",
        name="honey bees",
        kind="bees",
        hum="a warm golden hum",
        startle="rose in a shining ribbon",
        glow="golden",
        tags={"swarm", "honey", "buzz"},
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Iris", "Nora", "Asha", "Runa"]
BOY_NAMES = ["Eli", "Jon", "Toma", "Soren", "Milo", "Noah"]
TRAITS = ["curious", "brave", "gentle", "wondering", "quietly curious"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    setting = SETTINGS["loft"]
    world = World(setting)
    swarm = SWARMS[params.swarm]
    world.swarm = swarm

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=[params.trait, "little"],
        meters={"footsteps": 0.0},
        memes={"curiosity": 0.0, "fear": 0.0, "wonder": 0.0, "calm": 0.0},
    ))
    parent = world.add(Entity(
        id="Guardian",
        kind="character",
        type=params.parent,
        label=params.parent,
        meters={"steps": 0.0},
        memes={"worry": 0.0, "warmth": 0.0},
    ))
    lantern = world.add(Entity(
        id="Lantern",
        type="thing",
        label="brass lantern",
        phrase="a small brass lantern",
        owner=child.id,
        worn_by=None,
        meters={"glow": 0.0},
    ))
    world.facts.update(child=child, parent=parent, lantern=lantern)
    return world


def close_door(world: World) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, there was a child named "
        f"{world.facts['child'].id} who loved hidden places and old beams."
    )
    world.say(
        f"{world.facts['child'].pronoun('subject').capitalize()} was a "
        f"{world.facts['child'].traits[0]} little {world.facts['child'].type} and liked to ask "
        f"why every shadow had a shape."
    )


def discover_swarm(world: World) -> None:
    c = world.facts["child"]
    s = world.swarm
    c.memes["curiosity"] += 1
    c.memes["wonder"] += 1
    world.say(
        f"One dusk, {c.id} climbed into the loft with a lantern and saw "
        f"{s.startle} near the rafters."
    )
    world.say(
        f"It was {s.hum}, and the little swarm shone {s.glow} in the dust."
    )


def warn_and_reach(world: World) -> None:
    c = world.facts["child"]
    p = world.facts["parent"]
    s = world.swarm
    p.memes["worry"] += 1
    c.memes["curiosity"] += 1
    c.memes["fear"] += 0.5
    world.say(
        f"{p.label.capitalize()} saw {c.id} step closer and said, "
        f'"Careful now. A swarm can be wild when it is startled."'
    )
    world.say(
        f"But {c.id} wanted to know if {s.name} were only frightened, or if it had come "
        f"to guard something old and secret."
    )


def startle_swarm(world: World) -> None:
    c = world.facts["child"]
    s = world.swarm
    if "startled" in world.fired:
        return
    world.fired.add("startled")
    c.meters["footsteps"] += 1
    c.memes["fear"] += 1
    world.say(
        f"When {c.id} lifted the lantern too high, {s.startle}, and the whole loft "
        f"filled with moving gold."
    )


def choose_gentle_way(world: World) -> None:
    c = world.facts["child"]
    p = world.facts["parent"]
    s = world.swarm
    if "gentle_way" in world.fired:
        return
    world.fired.add("gentle_way")
    c.memes["calm"] += 1
    c.memes["wonder"] += 1
    p.memes["warmth"] += 1
    world.say(
        f"Then {c.id} remembered that questions can wait for quiet hands."
    )
    world.say(
        f"{c.id} set the lantern down, backed away, and opened the loft window "
        f"so the swarm could drift out on its own."
    )
    world.say(
        f"The {s.kind} moved into the evening air, and {p.label} smiled at how "
        f"curiosity had become careful instead of careless."
    )


def finish_image(world: World) -> None:
    c = world.facts["child"]
    p = world.facts["parent"]
    s = world.swarm
    world.say(
        f"Afterward, {c.id} stood by the open window and watched the last of the "
        f"{s.kind} go by like tiny stars."
    )
    world.say(
        f"{c.id} still felt curious, but now {c.pronoun('subject')} knew that wonder "
        f"could bow its head and make room."
    )
    world.say(
        f"Below the rafters, {p.label} held the lantern, and the loft stayed peaceful "
        f"and bright."
    )


def build_story(world: World) -> None:
    close_door(world)
    world.para()
    discover_swarm(world)
    warn_and_reach(world)
    startle_swarm(world)
    world.para()
    choose_gentle_way(world)
    finish_image(world)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    s = world.swarm
    return [
        f'Write a short myth-like story for young children about {c.id} in a loft and a {s.kind}.',
        f"Tell a gentle tale where curiosity meets a swarm in the loft and the child learns a careful way to act.",
        f'Write a tiny story with the words "swarm" and "loft" and end with calm wonder.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    p = world.facts["parent"]
    s = world.swarm
    return [
        QAItem(
            question=f"Where did {c.id} find the {s.kind}?",
            answer=f"{c.id} found the {s.kind} in the loft, near the rafters.",
        ),
        QAItem(
            question=f"Why did {p.label} warn {c.id}?",
            answer=f"{p.label} warned {c.id} because a swarm can be wild when it is startled.",
        ),
        QAItem(
            question=f"How did {c.id} solve the problem without hurting the {s.kind}?",
            answer=(
                f"{c.id} set the lantern down, opened the loft window, and let the swarm leave on its own."
            ),
        ),
        QAItem(
            question=f"How did {c.id} feel at the end?",
            answer=f"{c.id} still felt curious, but the curiosity had become calm and careful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a swarm?",
            answer="A swarm is a large group of insects moving together in one place.",
        ),
        QAItem(
            question="What is a loft?",
            answer="A loft is a room near the top of a house, often under the roof.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the wish to know more and to ask questions about things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(C) :- child_name(C).
swarm(S) :- swarm_name(S).
place(loft).

curious_story(C,S) :- child(C), swarm(S).
shown_story(C,S) :- curious_story(C,S).

#show curious_story/2.
#show shown_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("child_name", name))
    for sid in SWARMS:
        lines.append(asp.fact("swarm_name", sid))
    lines.append(asp.fact("place", "loft"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show curious_story/2."))
    return sorted(set(asp.atoms(model, "curious_story")))


def asp_verify() -> int:
    py = {(n, s) for n in GIRL_NAMES + BOY_NAMES for s in SWARMS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in asp:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-like story world about curiosity, a loft, and a swarm.")
    ap.add_argument("--swarm", choices=SWARMS)
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--trait", choices=["curious", "brave", "gentle", "wondering", "quietly curious"])
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
    swarm = args.swarm or rng.choice(list(SWARMS))
    if args.place and args.place != "loft":
        raise StoryError("This world only tells stories in the loft.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(swarm=swarm, place="loft", name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    build_story(world)
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
    StoryParams(swarm="moths", name="Mira", gender="girl", parent="grandmother", trait="curious"),
    StoryParams(swarm="bees", name="Eli", gender="boy", parent="father", trait="wondering"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show curious_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for pair in asp_valid():
            print(pair)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
