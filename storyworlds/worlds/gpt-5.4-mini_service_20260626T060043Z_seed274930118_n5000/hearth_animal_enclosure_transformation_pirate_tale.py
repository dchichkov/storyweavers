#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hearth_animal_enclosure_transformation_pirate_tale.py
=================================================================================

A small classical story world inspired by a pirate tale, set in an animal enclosure
with a hearth at its center. The core tension is a transformation: a timid child or
helper must become brave enough to solve a problem, and the world state tracks the
change.

Seed tale sketch:
---
A young pirate helper enters an animal enclosure to deliver warm oat cakes by the
hearth. The animals are shivering, the fire is low, and a stuck gate keeps the
feeder wagon from reaching the pen. The helper is scared of the loud enclosure,
but the captain teaches a brave pirate trick: wear a lantern charm, speak to the
animals kindly, and use a turning lever to raise the gate. The helper changes from
shaky to brave, lights the hearth again, and leaves with the animals calm and cozy.

World model:
---
- Characters have meters and memes.
- The hearth can go cold, the enclosure can grow dim, and the animals can become
  chilly and restless.
- A transformation helper changes the hero's courage and appearance; the story
  resolves when bravery becomes enough to do the needed task.

The prose should feel like a short pirate story, but grounded in simulated state.
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
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the animal enclosure"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hearth:
    id: str
    label: str
    warmth: float = 0.0
    glow: float = 0.0


@dataclass
class Transform:
    id: str
    from_trait: str
    to_trait: str
    from_meter: str
    to_meter: str
    phrase: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.hearth = Hearth(id="hearth", label="the hearth")
        self.transform = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


def base_name(gender: str, rng: random.Random) -> str:
    return rng.choice(["Pip", "Mara", "Finn", "Sailor", "Nell", "Rowan", "Tamsin", "Jory"])


SETTINGS = {
    "animal_enclosure": Setting(place="the animal enclosure", affords={"feed", "unlock", "light"}),
}

ACTIVITIES = {
    "feed": Activity(
        id="feed",
        verb="feed the animals",
        gerund="feeding the animals",
        rush="hurry to the feeder gate",
        keyword="oat cakes",
        tags={"animals", "hearth"},
    ),
    "light": Activity(
        id="light",
        verb="light the hearth",
        gerund="lighting the hearth",
        rush="fetch the tinder box",
        keyword="hearth",
        tags={"hearth"},
    ),
    "unlock": Activity(
        id="unlock",
        verb="open the stuck gate",
        gerund="opening the stuck gate",
        rush="pull the old lever",
        keyword="gate",
        tags={"gate", "brave"},
    ),
}

TRANSFORMS = {
    "brave": Transform(
        id="brave",
        from_trait="shy",
        to_trait="bold",
        from_meter="fear",
        to_meter="courage",
        phrase="brave as a barnacle on a storm rail",
    ),
    "pirate": Transform(
        id="pirate",
        from_trait="plain",
        to_trait="pirate",
        from_meter="hesitation",
        to_meter="swash",
        phrase="as sharp as a captain's grin",
    ),
}

CURATED = [
    ("Mara", "girl", "captain", "mother", "feed", "brave"),
    ("Finn", "boy", "mate", "father", "unlock", "pirate"),
]


def setup_world(name: str, gender: str, role: str, parent: str, activity_id: str, transform_id: str) -> World:
    world = World(SETTINGS["animal_enclosure"])
    hero = world.add(Entity(
        id=name, kind="character", type=gender, label=name,
        traits=["young", "shy" if transform_id == "brave" else "plain"],
        meters={"fear": 2.0, "courage": 0.0, "hesitation": 1.0, "swash": 0.0},
        memes={"worry": 1.0, "hope": 0.0, "joy": 0.0},
    ))
    captain = world.add(Entity(
        id="Captain", kind="character", type=parent, label=f"the {role}",
        traits=["steady", "kind"],
        meters={"patience": 2.0},
        memes={"care": 2.0},
    ))
    animals = world.add(Entity(
        id="Animals", kind="character", type="creature", label="the animals",
        plural=True, meters={"chill": 2.0, "hunger": 2.0, "restless": 1.0},
        memes={"unease": 1.0},
    ))
    hearth = world.add(Entity(
        id="Hearth", type="thing", label="the hearth", owner="Captain",
        meters={"cold": 2.0, "ash": 1.0}, memes={"glow": 0.0},
    ))
    gate = world.add(Entity(
        id="Gate", type="thing", label="the gate", caretaker="Captain",
        meters={"stuck": 2.0}, memes={"stubborn": 1.0},
    ))
    lantern = world.add(Entity(
        id="LanternCharm", type="thing", label="a lantern charm",
        meters={"shine": 1.0}, memes={"bravery": 1.0},
    ))
    world.transform = TRANSFORMS[transform_id]
    world.facts.update(hero=hero, captain=captain, animals=animals, hearth=hearth, gate=gate,
                       lantern=lantern, activity=ACTIVITIES[activity_id], transform=world.transform)
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    animals: Entity = f["animals"]
    hearth: Entity = f["hearth"]
    world.say(
        f"{hero.id} was a young pirate helper who liked shiny ropes, warm bread, and stories of the sea."
    )
    world.say(
        f"One foggy day, {hero.id} and {captain.label} went into {world.setting.place}, where {animals.label} huddled near {hearth.label}."
    )
    world.say(
        f"The hearth was low and cold, and {animals.label} kept shifting their feet because the pen felt chilly."
    )


def apply_activity(world: World, activity: Activity) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    animals: Entity = f["animals"]
    hearth: Entity = f["hearth"]
    gate: Entity = f["gate"]
    lantern: Entity = f["lantern"]

    if activity.id == "feed":
        if gate.meters.get("stuck", 0) >= THRESHOLD:
            world.say(
                f"{hero.id} wanted to feed the animals, but the feeder cart could not roll through the stuck gate."
            )
        hero.memes["worry"] += 1.0
        return

    if activity.id == "light":
        if hearth.meters.get("cold", 0) >= THRESHOLD:
            world.say(
                f"{hero.id} reached for the tinder, but the dark made the little pirate heart tremble."
            )
        return

    if activity.id == "unlock":
        hero.memes["worry"] += 1.0
        gate.meters["stuck"] = max(0.0, gate.meters.get("stuck", 0) - 2.0)
        world.say(
            f"{hero.id} spotted the old lever beside the gate and tried to pull it, but {hero.pronoun('possessive')} knees shook."
        )


def transform_hero(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    lantern: Entity = f["lantern"]
    tr: Transform = f["transform"]

    if hero.memes.get("worry", 0) < THRESHOLD:
        return

    world.say(
        f"{captain.label} smiled and tied {lantern.label} to {hero.pronoun('possessive')} belt. "
        f'"Hold fast and think of the tide," {captain.pronoun()} said. "That will make you {tr.to_trait}."'
    )
    hero.traits = [t for t in hero.traits if t != tr.from_trait] + [tr.to_trait]
    hero.meters[tr.from_meter] = 0.0
    hero.meters[tr.to_meter] = 2.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 1.0
    world.say(
        f"{hero.id} took a deep breath and changed at once, {tr.phrase}."
    )


def resolve(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    animals: Entity = f["animals"]
    hearth: Entity = f["hearth"]
    gate: Entity = f["gate"]

    gate.meters["stuck"] = 0.0
    hearth.meters["cold"] = 0.0
    hearth.meters["glow"] = 2.0
    animals.meters["chill"] = 0.0
    animals.memes["unease"] = 0.0
    world.say(
        f"Then {hero.id} grabbed the lever, and with {hero.pronoun('possessive')} new brave heart, the gate swung wide."
    )
    world.say(
        f"{hero.id} fed the animals by {hearth.label}, and the warm fire made their noses twitch happily."
    )
    world.say(
        f"By the end, {hero.id} stood tall like a true pirate, while {captain.label} watched the animals settle down in the golden glow."
    )


def tell(name: str, gender: str, role: str, parent: str, activity_id: str, transform_id: str) -> World:
    world = setup_world(name, gender, role, parent, activity_id, transform_id)
    narrate_setup(world)
    world.para()
    apply_activity(world, ACTIVITIES[activity_id])
    transform_hero(world)
    resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    act: Activity = f["activity"]
    tr: Transform = f["transform"]
    return [
        f"Write a short pirate tale for a small child about {hero.id} at the animal enclosure and the hearth.",
        f"Tell a story where {hero.id} is frightened at the animal enclosure, but becomes {tr.to_trait} so {hero.pronoun('subject')} can {act.verb}.",
        f"Write a gentle pirate story with a hearth, a stuck gate, and a brave transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    animals: Entity = f["animals"]
    hearth: Entity = f["hearth"]
    gate: Entity = f["gate"]
    tr: Transform = f["transform"]
    act: Activity = f["activity"]

    return [
        QAItem(
            question=f"Where did {hero.id} go with {captain.label}?",
            answer=f"{hero.id} went to the animal enclosure with {captain.label}, where the animals were waiting near the hearth.",
        ),
        QAItem(
            question=f"Why was {hero.id} worried at first?",
            answer=f"{hero.id} was worried because the gate was stuck, the hearth was cold, and the loud enclosure felt scary.",
        ),
        QAItem(
            question=f"What changed about {hero.id} during the story?",
            answer=f"{hero.id} changed from shy to bold, so {hero.pronoun('subject')} could act like a true pirate helper.",
        ),
        QAItem(
            question=f"What did {hero.id} do after growing brave enough?",
            answer=f"{hero.id} pulled the lever, opened the gate, and then helped {captain.label} feed the animals by the warm hearth.",
        ),
        QAItem(
            question=f"How did the story end for the animals?",
            answer=f"The animals ended calm and cozy, because the hearth glowed again and their chill went away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hearth?",
            answer="A hearth is the place where a fire burns to make warmth and light.",
        ),
        QAItem(
            question="Why can an animal enclosure feel loud?",
            answer="An animal enclosure can feel loud because animals move around, call to each other, and make many different sounds.",
        ),
        QAItem(
            question="What does it mean to be brave?",
            answer="Being brave means doing something scary even when your knees feel shaky.",
        ),
        QAItem(
            question="What can a lantern charm help with in a pirate tale?",
            answer="A lantern charm can help a pirate helper feel safer and notice where to go in the dark.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"hearth: warmth={world.hearth.warmth} glow={world.hearth.glow}")
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}} traits={e.traits}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    name: str
    gender: str
    role: str
    parent: str
    activity: str
    transform: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale storyworld set in an animal enclosure with a hearth and transformation.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=["captain", "mate", "helper"])
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--transform", choices=TRANSFORMS)
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
    activity = args.activity or rng.choice(list(ACTIVITIES))
    transform = args.transform or rng.choice(list(TRANSFORMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or base_name(gender, rng)
    role = args.role or rng.choice(["captain", "mate", "helper"])
    parent = args.parent or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(name=name, gender=gender, role=role, parent=parent, activity=activity, transform=transform)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.role, params.parent, params.activity, params.transform)
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


ASP_RULES = r"""
hearth(h1).
setting(animal_enclosure).
affords(animal_enclosure, feed).
affords(animal_enclosure, unlock).
affords(animal_enclosure, light).

activity(feed).
activity(unlock).
activity(light).

transform(brave).
transform(pirate).

prize_at_risk(light, hearth) :- needs_warmth(hearth).
needs_warmth(hearth).

stuck_gate(unlock).
can_transform(brave).
can_transform(pirate).

valid_story(A, T) :- activity(A), transform(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("setting", "animal_enclosure"))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
        lines.append(asp.fact("affords", "animal_enclosure", a))
    for t in TRANSFORMS:
        lines.append(asp.fact("transform", t))
    lines.append(asp.fact("hearth", "hearth"))
    lines.append(asp.fact("needs_warmth", "hearth"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(a, t) for a in ACTIVITIES for t in TRANSFORMS}
    actual = set(asp_valid())
    if expected == actual:
        print(f"OK: ASP gate matches Python reasoning ({len(actual)} combos).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(actual - expected))
    print("only in Python:", sorted(expected - actual))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(name="Mara", gender="girl", role="captain", parent="mother", activity=a, transform=t)
            for a in ACTIVITIES for t in TRANSFORMS
        ]
        samples = [generate(p) for p in combos]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
