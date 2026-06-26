#!/usr/bin/env python3
"""
storyworlds/worlds/refuge_therapy_ist_swimming_pool_humor_sharing.py
=====================================================================

A small comedy storyworld set at a swimming pool, built from the seed words
"refuge" and "therapy-ist" and shaped around humor and sharing.

Premise:
- A child is tense at a busy swimming pool.
- A therapy-ist notices the child hiding at a refuge spot.
- Humor loosens the mood.
- Sharing a pool toy or float becomes the safe bridge back into play.

This world is intentionally narrow: it only generates stories where the tension
is real, the refuge is concrete, and the resolution depends on a believable
shared object plus a light comic turn.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class PoolSetting:
    place: str = "the swimming pool"
    splashy: bool = True
    affords: set[str] = field(default_factory=lambda: {"float", "race", "ring"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    plural: bool = False


@dataclass
class Refuge:
    id: str
    label: str
    phrase: str
    comfort: str


@dataclass
class World:
    setting: PoolSetting

    def __post_init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.water: dict[str, float] = {"splash": 0.0}

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.water = dict(self.water)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    activity: str
    toy: str
    refuge: str
    seed: Optional[int] = None


SETTING = PoolSetting()

ACTIVITIES = {
    "float": Activity(
        id="float",
        verb="float in the water",
        gerund="floating on the water",
        rush="dash toward the deep end",
        mess="splash",
        zone={"feet", "legs", "torso"},
        keyword="float",
        tags={"water", "splash"},
    ),
    "race": Activity(
        id="race",
        verb="race along the pool edge",
        gerund="racing along the edge",
        rush="run to the ladder",
        mess="splash",
        zone={"feet", "legs"},
        keyword="race",
        tags={"water", "splash"},
    ),
    "ring": Activity(
        id="ring",
        verb="spin the pool ring",
        gerund="spinning the pool ring",
        rush="grab the ring first",
        mess="splash",
        zone={"feet", "legs", "torso"},
        keyword="ring",
        tags={"water", "splash"},
    ),
}

TOYS = {
    "duck": Toy(id="duck", label="rubber duck", phrase="a bright rubber duck", plural=False),
    "ball": Toy(id="ball", label="beach ball", phrase="a big beach ball", plural=False),
    "noodle": Toy(id="noodle", label="pool noodle", phrase="a bendy pool noodle", plural=False),
}

REFUGES = {
    "bench": Refuge(
        id="bench",
        label="bench by the showers",
        phrase="the little bench by the showers",
        comfort="dry",
    ),
    "cabana": Refuge(
        id="cabana",
        label="shady cabana",
        phrase="the shady cabana",
        comfort="quiet",
    ),
    "towelfort": Refuge(
        id="towelfort",
        label="towel fort",
        phrase="a towel fort",
        comfort="cozy",
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Zoe", "Nora", "Ivy", "Ada", "Ruby", "Mila"]
BOY_NAMES = ["Theo", "Ben", "Noah", "Finn", "Leo", "Max", "Eli", "Sam"]
TRAITS = ["shy", "curious", "wobbly", "serious", "giggly", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for refuge in REFUGES:
        for activity in ACTIVITIES:
            for toy in TOYS:
                combos.append((refuge, activity, toy))
    return combos


def _is_valid(params: StoryParams) -> bool:
    return (
        params.refuge in REFUGES
        and params.activity in ACTIVITIES
        and params.toy in TOYS
    )


def _predict(world: World, child: Entity, activity: Activity, toy: Entity) -> dict:
    sim = world.copy()
    sim.get(child.id).meters["want"] = 1
    sim.water["splash"] += 1
    ru = toy.meters.get("wet", 0) >= THRESHOLD
    return {"toy_wet": ru, "splash": sim.water["splash"]}


def _do_activity(world: World, child: Entity, activity: Activity) -> None:
    child.meters["splash"] = child.meters.get("splash", 0.0) + 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    world.water["splash"] += 1.0


def build_story(world: World, child: Entity, therapist: Entity, parent: Entity, toy: Entity, refuge: Refuge, activity: Activity) -> None:
    child.memes["nervous"] = 1.0
    world.say(
        f"{child.id} was a little {next(t for t in child.memes.get('trait_list', ['quiet'])) if False else child.type} named {child.id} who felt a little nervous at {world.setting.place}."
    )
    world.say(
        f"{child.id} kept walking to {refuge.phrase}, because it felt like a safe refuge when the pool got loud."
    )
    world.say(
        f"{therapist.id} the therapy-ist noticed {child.id} hiding there and smiled."
    )
    world.say(
        f'"Let me try a joke first," {therapist.pronoun("subject")} said. "Why did the noodle blush? Because it saw the pool in its swimsuit!"'
    )
    child.memes["amused"] = child.memes.get("amused", 0.0) + 1.0
    world.say(f"{child.id} snorted and tried not to laugh.")
    pred = _predict(world, child, activity, toy)
    if pred["toy_wet"]:
        raise StoryError("The chosen toy would not make a good shared bridge for this pool story.")
    world.say(
        f"Then {therapist.id} held up {toy.phrase} and said, \"We can share this first. One turn for you, one turn for me.\""
    )
    toy.owner = therapist.id
    world.say(
        f"{parent.id} nodded from the side of the pool, because sharing made the whole thing feel fair."
    )
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    world.say(
        f"{child.id} climbed out of the refuge, took a turn with {toy.label}, and laughed so hard that {child.pronoun('possessive')} shoulders bounced."
    )
    _do_activity(world, child, activity)
    world.say(
        f"Pretty soon, {child.id} was {activity.gerund}, {toy.it()} passed back and forth, and the pool sounded like a happy comedy show."
    )
    world.say(
        f"At the end, the refuge was only a memory, because {child.id} was smiling right in the middle of the water."
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    therapist = f["therapist"]
    toy = f["toy"]
    refuge = f["refuge"]
    activity = f["activity"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"Why did {child.id} stay near {refuge.phrase} at the swimming pool?",
            answer=f"{child.id} stayed near {refuge.phrase} because it felt like a safe refuge when the pool got loud.",
        ),
        QAItem(
            question=f"How did the therapy-ist help {child.id} feel better?",
            answer=f"{therapist.id} helped by telling a silly joke and then offering {toy.phrase} to share.",
        ),
        QAItem(
            question=f"What happened after {child.id} and {parent.id} started sharing at the pool?",
            answer=f"{child.id} got braver, left the refuge, and ended up {activity.gerund} with everyone smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a refuge?",
            answer="A refuge is a safe place where someone can rest or hide when they feel unsure.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something too, often by taking turns.",
        ),
        QAItem(
            question="Why can humor help?",
            answer="Humor can help because a funny joke can make people relax and feel friendlier.",
        ),
        QAItem(
            question="What is a swimming pool?",
            answer="A swimming pool is a place filled with water where people swim, splash, and play.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    toy = f["toy"]
    refuge = f["refuge"]
    return [
        f"Write a short comedy story set at a swimming pool where {child.id} hides in a refuge and a therapy-ist uses humor and sharing to help.",
        f"Tell a gentle, funny story in which a child learns to leave {refuge.phrase} by sharing {toy.phrase} and joining the pool game.",
        f"Write a TinyStories-style pool story with a worried child, a therapy-ist, a joke, and a happy shared turn doing {activity.verb}.",
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  water={world.water}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("setting", "swimming_pool"),
        asp.fact("feature", "humor"),
        asp.fact("feature", "sharing"),
    ]
    for rid in REFUGES:
        lines.append(asp.fact("refuge", rid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(R, A, T) :- refuge(R), activity(A), toy(T).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy pool storyworld with refuge, humor, and sharing.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--refuge", choices=REFUGES)
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
    if args.gender and args.name:
        if args.gender == "girl" and args.name in BOY_NAMES:
            raise StoryError("The chosen name does not match the requested gender.")
        if args.gender == "boy" and args.name in GIRL_NAMES:
            raise StoryError("The chosen name does not match the requested gender.")
    activity = args.activity or rng.choice(list(ACTIVITIES))
    toy = args.toy or rng.choice(list(TOYS))
    refuge = args.refuge or rng.choice(list(REFUGES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait, activity=activity, toy=toy, refuge=refuge)


def generate(params: StoryParams) -> StorySample:
    if not _is_valid(params):
        raise StoryError("Invalid parameter combination for this storyworld.")

    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    therapist = world.add(Entity(id="TherapyIst", kind="character", type="adult", label="the therapy-ist"))
    toy = world.add(Entity(id=params.toy, kind="thing", type=params.toy, label=TOYS[params.toy].label, phrase=TOYS[params.toy].phrase))
    refuge = REFUGES[params.refuge]
    activity = ACTIVITIES[params.activity]

    world.facts.update(child=child, parent=parent, therapist=therapist, toy=toy, refuge=refuge, activity=activity)

    world.say(f"{child.id} arrived at {world.setting.place} and felt a little wobbly around all the splashy noise.")
    world.para()
    build_story(world, child, therapist, parent, toy, refuge, activity)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", trait="shy", activity="float", toy="duck", refuge="cabana"),
    StoryParams(name="Theo", gender="boy", parent="father", trait="giggly", activity="race", toy="ball", refuge="bench"),
    StoryParams(name="Nora", gender="girl", parent="mother", trait="curious", activity="ring", toy="noodle", refuge="towelfort"),
]


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
