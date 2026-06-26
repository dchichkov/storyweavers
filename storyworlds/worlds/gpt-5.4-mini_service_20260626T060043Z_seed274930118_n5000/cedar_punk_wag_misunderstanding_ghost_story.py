#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cedar_punk_wag_misunderstanding_ghost_story.py
=================================================================================================

A small simulated story world in the style of a ghost story: a child, a spooky
misunderstanding, and a gentle resolution around a cedar tree, a punk look, and
a wagging pet.

Premise:
- A child who likes punk clothes hears a spooky sound near an old cedar.
- A friendly dog wagging its tail makes the sound, but the child mistakes it
  for a ghost.
- The parent helps the child look again, and the misunderstanding clears.

The world is state-driven: meters track physical motion, sound, and light;
memes track fear, curiosity, relief, and trust. The story only resolves when
the simulated world reaches the right emotional and physical state.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False
    friendly: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cedar grove"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    keyword: str
    weather: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    activity: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.weather: str = ""

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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("sound", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("fear", 0.0) >= THRESHOLD:
            continue
        sig = ("fear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = actor.memes.get("fear", 0.0) + 1
        out.append(f"{actor.id}'s heart thumped hard in the dark.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("dog_wagging") and world.facts.get("hero_fear") and not world.facts.get("understood"):
        sig = ("misunderstanding",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__misunderstanding__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("understood", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("relief", 0.0) >= THRESHOLD:
            continue
        sig = ("relief", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["relief"] = actor.memes.get("relief", 0.0) + 1
        actor.memes["fear"] = 0
        out.append(f"The worry drained away like mist.")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("misunderstanding", _r_misunderstanding), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__misunderstanding__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_catalog() -> dict[str, Activity]:
    return {
        "wag": Activity(
            id="wag",
            verb="watch the wagging tail",
            gerund="watching the tail wag",
            rush="run toward the shadow",
            sound="a soft wag-wag rustle",
            keyword="wag",
            weather="night",
            tags={"dog", "sound", "fear"},
        ),
        "cedar": Activity(
            id="cedar",
            verb="walk under the cedar",
            gerund="walking under cedar boughs",
            rush="peek behind the cedar",
            sound="the cedar needles whispering",
            keyword="cedar",
            weather="night",
            tags={"tree", "sound", "spooky"},
        ),
        "punk": Activity(
            id="punk",
            verb="show off a punk jacket",
            gerund="showing off a punk look",
            rush="clutch the jacket",
            sound="the zipper clinking",
            keyword="punk",
            weather="night",
            tags={"clothes", "identity"},
        ),
    }


def settings() -> dict[str, Setting]:
    return {
        "cedar_grove": Setting(place="the cedar grove", affords={"wag", "cedar", "punk"}),
        "yard": Setting(place="the yard by the cedar", affords={"wag", "cedar", "punk"}),
    }


def explain_rejection(activity: Activity) -> str:
    return f"(No story: the chosen beat '{activity.id}' does not fit the gentle ghost-story misunderstanding pattern.)"


def story_intro(world: World, hero: Entity, parent: Entity, dog: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved a punk jacket and a brave-looking grin."
    )
    world.say(
        f"At {world.setting.place}, an old cedar stood like a tall dark umbrella."
    )
    world.say(
        f"Nearby, {dog.id} kept {activity.gerund}, making {activity.sound} in the leaves."
    )
    world.say(
        f"{hero.id}'s {parent.label or parent.type} said the night was only full of shadows, not trouble."
    )


def build_misunderstanding(world: World, hero: Entity, parent: Entity, dog: Entity, activity: Activity) -> None:
    hero.meters["sound"] = 1
    hero.memes["curiosity"] = 1
    world.para()
    world.say(
        f"When the breeze shook the cedar, {hero.id} heard {activity.sound} and gasped."
    )
    hero.memes["fear"] = 1
    world.facts["hero_fear"] = True
    propagate(world)
    world.say(
        f"{hero.id} whispered, 'I think there is a ghost in the cedar!'"
    )
    world.say(
        f"{parent.id} lifted a lantern and said they should look carefully before believing the dark."
    )
    world.say(
        f"{dog.id} answered with another wag, but the tail was still hidden in shadow."
    )


def resolve_misunderstanding(world: World, hero: Entity, parent: Entity, dog: Entity, activity: Activity) -> None:
    world.para()
    world.say(
        f"{parent.id} knelt beside {hero.id} and pointed at the movement in the grass."
    )
    world.say(
        f"It was only {dog.id}, and its tail was wagging so fast that it looked spooky."
    )
    world.facts["dog_wagging"] = True
    hero.memes["understood"] = 1
    world.facts["understood"] = True
    propagate(world)
    world.say(
        f"{hero.id} let out a shaky laugh and patted {dog.id} on the head."
    )
    world.say(
        f"At the cedar, the dark shape turned into a friendly dog, and the ghost story became a dog story."
    )


def tell(setting: Setting, activity: Activity, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label="punk kid"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    dog = world.add(Entity(id="Moss", kind="character", type="dog", label="dog", friendly=True))

    story_intro(world, hero, parent, dog, activity)
    build_misunderstanding(world, hero, parent, dog, activity)
    resolve_misunderstanding(world, hero, parent, dog, activity)

    world.facts.update(
        hero=hero,
        parent=parent,
        dog=dog,
        activity=activity,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short ghost story for a child about a {f['hero'].type} named {f['hero'].id}, a cedar tree, and a wagging dog.",
        f"Tell a gentle spooky story where {f['hero'].id} thinks the cedar is haunted, but the sound turns out to be {f['dog'].id}'s wagging tail.",
        f"Write a story with a punk jacket, an old cedar, and a misunderstanding that ends in relief.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    dog: Entity = f["dog"]
    activity: Activity = f["activity"]
    return [
        QAItem(
            question=f"Why did {hero.id} think there was a ghost near the cedar?",
            answer=(
                f"{hero.id} heard {activity.sound} in the dark cedar grove and did not know it was just {dog.id}'s tail wagging."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} understand the spooky sound?",
            answer=(
                f"{parent.id} pointed carefully at the grass, and {hero.id} saw that the scary shape was really {dog.id} wagging its tail."
            ),
        ),
        QAItem(
            question=f"What changed for {hero.id} at the end of the story?",
            answer=(
                f"{hero.id} stopped feeling scared, laughed, and turned the ghostly moment into a happy dog discovery."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cedar?",
            answer="A cedar is a kind of tree with needles or scale-like leaves, and it can make a place feel dark and whispery at night.",
        ),
        QAItem(
            question="What does wag mean when a dog wags its tail?",
            answer="When a dog wags its tail, it moves the tail back and forth, which often shows the dog is happy or friendly.",
        ),
        QAItem(
            question="What does punk mean here?",
            answer="Punk here means a bold style of clothes or look, like a jacket with a cool or edgy feeling.",
        ),
        QAItem(
            question="Why do people sometimes get scared by shadows at night?",
            answer="At night, shadows can look like something else for a moment, so people may misunderstand what they are seeing.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost-story misunderstanding around cedar, punk, and wag.")
    ap.add_argument("--place", choices=settings())
    ap.add_argument("--activity", choices=activity_catalog())
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
    combos = []
    for place, setting in settings().items():
        for aid in setting.affords:
            combos.append((place, aid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    acts = activity_catalog()
    if args.activity and args.activity not in acts:
        raise StoryError("Unknown activity.")
    if args.place and args.place not in settings():
        raise StoryError("Unknown place.")
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    hero_name = args.name or rng.choice(["Mina", "Leo", "Pip", "Nora", "Finn", "Milo"])
    return StoryParams(place=place, activity=activity, hero_name=hero_name, hero_type=hero_type, parent_type=parent_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(settings()[params.place], activity_catalog()[params.activity], params.hero_name, params.hero_type, params.parent_type)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- act(A).

valid(Place, Activity) :- affords(Place, Activity).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in settings().items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in activity_catalog():
        lines.append(asp.fact("act", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="cedar_grove", activity="wag", hero_name="Mina", hero_type="girl", parent_type="mother"),
    StoryParams(place="yard", activity="cedar", hero_name="Leo", hero_type="boy", parent_type="father"),
    StoryParams(place="cedar_grove", activity="punk", hero_name="Pip", hero_type="boy", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
