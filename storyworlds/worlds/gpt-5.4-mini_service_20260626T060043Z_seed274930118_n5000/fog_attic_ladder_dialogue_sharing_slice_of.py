#!/usr/bin/env python3
"""
storyworlds/worlds/fog_attic_ladder_dialogue_sharing_slice_of.py
=================================================================

A small slice-of-life storyworld about a foggy morning, an attic ladder,
gentle dialogue, and a shared task.

Premise
-------
A child wants to climb the attic ladder to look for something special,
but the fog makes the house feel quieter and dimmer than usual. A sibling
or parent notices, starts a conversation, and they share a lamp, a blanket,
and the small job of fetching a keepsake safely.

This world is intentionally modest: the tension is not danger, but hesitation,
wobbliness, and the choice to share instead of rush.

The simulated world tracks:
- physical meters: light, steadiness, warmth, dust, and found items
- emotional memes: worry, curiosity, patience, relief, closeness

It generates:
- a complete child-facing story
- story-grounded QA
- world-knowledge QA
- optional ASP parity verification

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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"light": 0.0, "steady": 0.0, "warmth": 0.0, "dust": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "curiosity": 0.0, "patience": 0.0, "relief": 0.0, "closeness": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    foggy: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    kind: str
    helps: set[str] = field(default_factory=set)
    shares: bool = False
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    object: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PLACES = {
    "attic ladder": Place(id="attic_ladder", label="the attic ladder", foggy=True, affords={"search"}),
}

OBJECTS = {
    "lantern": ObjectDef(id="lantern", label="lantern", phrase="a small brass lantern", kind="light", helps={"light"}, shares=True),
    "blanket": ObjectDef(id="blanket", label="blanket", phrase="a soft blanket", kind="warmth", helps={"warmth"}, shares=True, plural=False),
    "box": ObjectDef(id="box", label="memory box", phrase="a little memory box", kind="keepsake", helps={"found"}, shares=True),
    "ladder_rung": ObjectDef(id="ladder_rung", label="ladder rung", phrase="the old ladder rung", kind="safety", helps={"steady"}),
}

GIRL_NAMES = ["Mina", "Luna", "Nina", "Iris", "Talia", "June"]
BOY_NAMES = ["Eli", "Owen", "Noah", "Finn", "Theo", "Miles"]


ASP_RULES = r"""
place(attic_ladder).
foggy(attic_ladder).
object(lantern).
object(blanket).
object(box).

shares(lantern).
shares(blanket).
shares(box).

help(lantern, light).
help(blanket, warmth).
help(box, found).

compatible(P, O) :- foggy(P), shares(O), help(O, light).
compatible(P, O) :- foggy(P), shares(O), help(O, warmth).
compatible(P, O) :- place(P), object(O), help(O, found).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.foggy:
            lines.append(asp.fact("foggy", pid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.shares:
            lines.append(asp.fact("shares", oid))
        for h in sorted(o.helps):
            lines.append(asp.fact("help", oid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    clingo_set = set(asp.atoms(model, "compatible"))
    python_set = set(valid_choices())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_choices() ({len(python_set)} choices).")
        return 0
    print("MISMATCH between clingo and valid_choices():")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def valid_choices() -> list[tuple]:
    out: list[tuple] = []
    for place_id, place in PLACES.items():
        for obj_id, obj in OBJECTS.items():
            if place.foggy and obj.shares and ("light" in obj.helps or "warmth" in obj.helps):
                out.append((place_id, obj_id))
            if obj.kind == "keepsake":
                out.append((place_id, obj_id))
    return sorted(set(out))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about fog, an attic ladder, dialogue, and sharing.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--object", choices=list(OBJECTS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "sibling"])
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
    if args.place and args.object:
        if (args.place, args.object) not in valid_choices():
            raise StoryError("That object does not make a reasonable shared attic-ladder story for this foggy setting.")
    place = args.place or rng.choice(list(PLACES))
    obj = args.object or rng.choice([o for p, o in valid_choices() if p == place])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "sibling"])
    return StoryParams(place=place, name=name, gender=gender, helper=helper, object=obj)


def _hero_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=_hero_type(params.gender), label=params.name))
    helper_type = {"mother": "mother", "father": "father", "sibling": "sibling"}[params.helper]
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=params.helper))
    obj_def = OBJECTS[params.object]
    item = world.add(Entity(id="item", kind="thing", type=obj_def.kind, label=obj_def.label, phrase=obj_def.phrase, owner=hero.id, caretaker=helper.id))
    lantern = world.add(Entity(id="lantern", kind="thing", type="light", label="lantern", phrase="a small brass lantern", owner=helper.id, caretaker=helper.id, protective=True))
    blanket = world.add(Entity(id="blanket", kind="thing", type="warmth", label="blanket", phrase="a soft blanket", owner=helper.id, caretaker=helper.id, protective=True))
    world.facts.update(hero=hero, helper=helper, item=item, place=place, lantern=lantern, blanket=blanket, obj_def=obj_def)
    return world


def story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    item: Entity = world.facts["item"]
    obj_def: ObjectDef = world.facts["obj_def"]
    place: Place = world.facts["place"]

    world.say(f"On a foggy morning, {hero.label} stood at {place.label} and looked up at the attic ladder.")
    world.say(f"{hero.label.capitalize()} wanted to go up and find {item.phrase}, but the fog made the hallway look pale and quiet.")
    world.say(f'"Can we take the lantern?" {hero.label} asked.')
    world.say(f'"Of course," {helper.label} said, and {helper.pronoun("subject").capitalize()} brought it closer so they could share the light.')

    hero.memes["curiosity"] += 1
    helper.memes["patience"] += 1
    hero.meters["steady"] += 1
    lantern = world.facts["lantern"]
    lantern.worn_by = helper.id
    lantern.meters["light"] += 1

    world.para()
    world.say(f"They climbed one careful rung at a time.")
    world.say(f"The ladder felt a little wobbly, so {helper.label} held the side and {hero.label} held the lantern.")
    hero.memes["worry"] += 1
    helper.memes["closeness"] += 1

    if obj_def.shares:
        world.say(f'"I can carry the blanket," {hero.label} said.')
        world.say(f'"That helps," {helper.label} answered. "We can share it if the attic feels chilly."')
        blanket = world.facts["blanket"]
        blanket.worn_by = hero.id
        blanket.meters["warmth"] += 1
        hero.memes["patience"] += 1
        helper.memes["patience"] += 1

    world.para()
    world.say(f"Up in the attic, they found the little box together.")
    item.meters["found"] += 1
    item.memes["safe"] = item.memes.get("safe", 0.0) + 1
    world.say(f"It was tucked beside an old quilt, and the quilt smelled faintly like dust and sunshine.")

    world.say(f'{hero.label} smiled and said, "I’m glad we came together."')
    world.say(f'{helper.label} smiled back. "Me too," {helper.pronoun("subject")} said. "Sharing the light made the whole job feel easy."')
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["closeness"] += 1
    helper.memes["closeness"] += 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    return [
        f'Write a short slice-of-life story about {hero.label}, a foggy attic ladder, and sharing a lantern.',
        f"Tell a gentle story where {hero.label} and {helper.label} talk together, climb carefully, and find {item.phrase}.",
        f'Write a child-friendly story set at the attic ladder that uses the word "fog" and includes sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    return [
        QAItem(
            question=f"Where did {hero.label} want to go when the morning was foggy?",
            answer=f"{hero.label} wanted to go up the attic ladder because {hero.pronoun('subject')} was looking for {item.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.label} ask to take with {hero.pronoun('object')}?",
            answer=f"{hero.label} asked to take the lantern so they could share the light on the ladder.",
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.label} on the way up?",
            answer=f"{helper.label} held the side of the ladder, and they also shared the blanket and the lantern.",
        ),
        QAItem(
            question=f"What did {hero.label} and {helper.label} find in the attic?",
            answer=f"They found the little memory box tucked beside an old quilt.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fog?",
            answer="Fog is a cloud of tiny water drops that hangs low in the air and makes faraway things look soft and pale.",
        ),
        QAItem(
            question="Why do people use a lantern in a dark place?",
            answer="People use a lantern to make a warm, steady pool of light so they can see better.",
        ),
        QAItem(
            question="What does it mean to share something?",
            answer="To share something means two people use it together or take turns with it kindly.",
        ),
        QAItem(
            question="What is an attic?",
            answer="An attic is a room near the roof of a house where families often keep boxes and old keepsakes.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story(world)
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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible choices:\n")
        for place, obj in combos:
            print(f"  {place:15} {obj}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="attic ladder", name="Mina", gender="girl", helper="mother", object="lantern"),
            StoryParams(place="attic ladder", name="Eli", gender="boy", helper="father", object="blanket"),
            StoryParams(place="attic ladder", name="June", gender="girl", helper="sibling", object="box"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.object} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
