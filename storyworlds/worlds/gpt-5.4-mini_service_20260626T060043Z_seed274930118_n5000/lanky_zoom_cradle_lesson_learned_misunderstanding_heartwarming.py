#!/usr/bin/env python3
"""
A small heartwarming story world about a lanky child, a zooming game, and a
cradle that makes everyone pause and listen.

The seed image:
- A lanky kid loves to zoom around.
- A cradle sits in the home, quiet and important.
- A misunderstanding makes the child think the grown-up is upset.
- In the end, everyone learns a gentle lesson and feels closer.

This world models the story as a tiny simulation with physical meters and
emotional memes. The prose is driven by state, not just by swapping nouns.
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
# Core model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "son", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "daughter", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the sunny hallway"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    type: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hallway": Setting(place="the sunny hallway", affords={"zoom"}),
    "porch": Setting(place="the front porch", affords={"zoom"}),
    "living_room": Setting(place="the cozy living room", affords={"zoom"}),
}

ACTIVITIES = {
    "zoom": Activity(
        id="zoom",
        verb="zoom around",
        gerund="zooming around",
        rush="zip down the hallway",
        sound="whirr-whirr",
        mess="noise",
        tags={"zoom", "sound"},
    )
}

OBJECTS = {
    "cradle": ObjectSpec(
        label="cradle",
        phrase="a small wooden cradle with a soft blanket",
        type="cradle",
        tags={"cradle", "baby"},
    ),
    "blocks": ObjectSpec(
        label="blocks",
        phrase="a basket of colorful blocks",
        type="blocks",
        tags={"toy"},
    ),
}

NAMES = ["Ari", "Milo", "Noah", "Jude", "Theo", "Eli", "Ren", "Finn"]
TRAITS = ["lanky", "gentle", "curious", "cheerful", "thoughtful", "spirited"]


# ---------------------------------------------------------------------------
# Reasoning
# ---------------------------------------------------------------------------
def safe_to_zoom(setting: Setting) -> bool:
    return "zoom" in setting.affords


def predict_noise(world: World, hero: Entity, activity: Activity) -> float:
    sim = world.copy()
    sim.get(hero.id).meters["noise"] += 1.0
    return sim.get(hero.id).meters["noise"]


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a lanky child who loved to move fast, and even the air "
        f"seemed to notice when {hero.id} came into a room."
    )


def set_scene(world: World, hero: Entity, cradle: Entity) -> None:
    world.say(
        f"Inside {world.setting.place}, a cradle stood in a quiet corner with a "
        f"soft blanket tucked neatly inside."
    )
    world.say(
        f"{hero.id} kept glancing at it while {hero.pronoun()} held a little scooter, "
        f"because {hero.pronoun('subject')} loved to zoom."
    )


def start_zooming(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["speed"] = hero.meters.get("speed", 0.0) + 1.0
    hero.meters["noise"] = hero.meters.get("noise", 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    world.say(
        f"{hero.id} gave the scooter a push and went {activity.gerund}, making a "
        f"{activity.sound} sound on the floor."
    )


def misunderstanding(world: World, parent: Entity, hero: Entity, cradle: Entity, activity: Activity) -> None:
    parent.memes["worry"] = parent.memes.get("worry", 0.0) + 1.0
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1.0
    world.say(
        f"{parent.id} looked over at the cradle and raised a hand. "
        f"'{hero.id}, please slow down,' {parent.pronoun()} said."
    )
    world.say(
        f"{hero.id} froze. {hero.pronoun().capitalize()} thought {parent.pronoun('subject')} "
        f"was upset about the fun, not about the noise."
    )


def explain_and_learn(world: World, parent: Entity, hero: Entity, cradle: Entity, activity: Activity) -> None:
    parent.memes["care"] = parent.memes.get("care", 0.0) + 1.0
    hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1.0
    world.say(
        f"{parent.id} knelt down and pointed gently at the cradle. "
        f"'I wasn't trying to spoil your play,' {parent.pronoun()} said. "
        f"'I was protecting the baby resting there.'"
    )
    world.say(
        f"Then {hero.id} understood. The worry was not a scolding; it was a careful kind of love."
    )
    hero.memes["hurt"] = 0.0
    hero.memes["gratitude"] = hero.memes.get("gratitude", 0.0) + 1.0


def resolve(world: World, parent: Entity, hero: Entity, activity: Activity, cradle: Entity) -> None:
    hero.meters["speed"] = max(0.0, hero.meters.get("speed", 0.0) - 1.0)
    hero.meters["noise"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    parent.memes["relief"] = parent.memes.get("relief", 0.0) + 1.0
    world.say(
        f"{hero.id} slowed down, tiptoed beside the cradle, and helped tuck the blanket "
        f"more snugly around it."
    )
    world.say(
        f"After that, {hero.id} zoomed only after moving to a safer spot, and {parent.id} smiled "
        f"because the lesson had landed softly."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    object: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    obj = OBJECTS[params.object]

    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    parent = world.add(Entity(id=params.parent, kind="character", type="adult", label=params.parent))
    cradle = world.add(Entity(id="cradle", type="cradle", label="cradle", phrase=obj.phrase))

    hero.memes["identity"] = 1.0
    parent.memes["care"] = 1.0

    introduce(world, hero)
    world.para()
    set_scene(world, hero, cradle)
    start_zooming(world, hero, activity)
    misunderstanding(world, parent, hero, cradle, activity)
    world.para()
    explain_and_learn(world, parent, hero, cradle, activity)
    resolve(world, parent, hero, activity, cradle)

    world.facts = {
        "hero": hero,
        "parent": parent,
        "cradle": cradle,
        "activity": activity,
        "object": obj,
        "setting": setting,
        "misunderstanding": True,
        "lesson_learned": True,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    activity: Activity = f["activity"]
    obj: ObjectSpec = f["object"]
    return [
        f'Write a heartwarming story about a lanky child named {hero.id} who loves to {activity.verb} near a cradle.',
        f"Tell a gentle story where {hero.id} gets confused after a grown-up asks {hero.pronoun('object')} to slow down.",
        f'Write a simple story that includes the words "{hero.id}", "zoom", and "cradle", and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    activity: Activity = f["activity"]
    obj: ObjectSpec = f["object"]
    cradle: Entity = f["cradle"]
    return [
        QAItem(
            question=f"Why did {parent.id} tell {hero.id} to slow down near the cradle?",
            answer=f"{parent.id} was worried that the {activity.sound} sound from {hero.id}'s zooming could bother the baby resting in the cradle.",
        ),
        QAItem(
            question=f"What did {hero.id} think at first when {parent.id} raised a hand?",
            answer=f"At first, {hero.id} thought {parent.id} was upset about the fun itself, not about the noise.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end of the story?",
            answer=f"{hero.id} learned that a gentle warning can be a sign of care, and that it is kind to slow down when something precious is nearby.",
        ),
        QAItem(
            question=f"What did {hero.id} do after understanding the problem?",
            answer=f"{hero.id} slowed down, helped tuck the blanket around the cradle, and then found a safer place to zoom.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cradle for?",
            answer="A cradle is a small bed for a baby, usually made to rock gently and help the baby rest.",
        ),
        QAItem(
            question="Why can zooming be noisy?",
            answer="Zooming can be noisy because wheels and fast feet make tapping, whirring, or rumbling sounds.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.kind}/{e.type}) " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place, Act, Obj) :- setting(Place), affords(Place, Act), activity(Act), object(Obj).
misunderstanding(Place, Act, Obj) :- valid(Place, Act, Obj), has_cradle(Obj).
heartwarming_story(Place, Act, Obj) :- misunderstanding(Place, Act, Obj).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    lines.append(asp.fact("has_cradle", "cradle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    asp_valid = sorted(set(asp.atoms(model, "valid")))
    py_valid = [(place, act, oid) for place in SETTINGS for act in SETTINGS[place].affords for oid in OBJECTS]
    py_valid = sorted(py_valid)
    if asp_valid == py_valid:
        print(f"OK: clingo gate matches Python ({len(py_valid)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("ASP:", asp_valid)
    print("PY :", py_valid)
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world: lanky zoom, cradle, misunderstanding, lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", choices=OBJECTS, default="cradle")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=["mom", "dad", "mother", "father"], default="mom")
    ap.add_argument("--trait", choices=TRAITS, default="lanky")
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
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "zoom"
    obj = args.object or "cradle"
    if activity not in SETTINGS[place].affords:
        raise StoryError(f"(No story: {activity} does not fit {place}.)")
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mom", "dad"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, object=obj, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_list() -> None:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    combos = sorted(set(asp.atoms(model, "valid")))
    for place, act, obj in combos:
        print(place, act, obj)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                activity="zoom",
                object="cradle",
                name=NAMES[0],
                parent="mom",
                trait="lanky",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
