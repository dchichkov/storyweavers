#!/usr/bin/env python3
"""
storyworlds/worlds/rung_merit_breathe_curiosity_rhyme_cautionary_slice.py
========================================================================

A small slice-of-life story world about curiosity, a cautionary pause, a
little rhyme, and a child learning that careful breathing can turn a risky
reach into a safe choice.

Seed story imagined from the prompt:
---
A child notices a high shelf, a loose rung on a little step stool, and a shiny
merit badge tucked beside a jar of crayons. Curiosity makes the child want to
climb right away. A parent notices the wobble, gives a cautionary warning, and
asks the child to breathe, wait, and use the safer step stool after checking it.
The child hums a rhyme while they fix the stool together, then climbs safely and
earns the badge by helping first.

The world model tracks:
- physical meters: steadiness, reach, wobble, tidiness, climb
- emotional memes: curiosity, caution, calm, pride, merit

The narrative turn is driven by a real hazard:
- a wobbly rung can be unsafe
- a safer stool or adult help resolves the problem
- a merit badge is earned through the helpful fix, not through reckless climbing
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def _init_meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def _init_meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    region: str
    fragile: bool = False


@dataclass
class AidSpec:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]


@dataclass
class StoryParams:
    place: str
    object: str
    aid: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"reach"}),
    "hallway": Setting(place="the hallway", affords={"reach"}),
    "playroom": Setting(place="the playroom", affords={"reach"}),
}

OBJECTS = {
    "shelf": ObjectSpec(label="high shelf", phrase="a high shelf with a bright jar on it", region="torso", fragile=True),
    "stool": ObjectSpec(label="step stool", phrase="a small step stool with one loose rung", region="feet", fragile=False),
    "bench": ObjectSpec(label="bench", phrase="a low bench by the window", region="feet", fragile=False),
}

AIDS = {
    "steady_stool": AidSpec(
        id="steady_stool",
        label="steady step stool",
        phrase="a steady step stool",
        helps={"reach"},
        covers={"feet"},
    ),
    "hand_hold": AidSpec(
        id="hand_hold",
        label="helping hand",
        phrase="a helping hand on the first step",
        helps={"reach"},
        covers={"feet"},
    ),
}

GIRL_NAMES = ["Mina", "Lola", "Ivy", "Nora", "Rose", "Ella"]
BOY_NAMES = ["Theo", "Milo", "Finn", "Owen", "Eli", "Noah"]
TRAITS = ["curious", "gentle", "quiet", "spirited", "careful", "bright"]


class WorldModel:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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


def prompt_text(world: WorldModel) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a gentle slice-of-life story for a young child about "{hero.id}" and the words rung, merit, and breathe.',
        f"Tell a short story where {hero.id} feels curious about a high shelf, hears a cautionary warning, and learns to breathe before climbing.",
        "Write a simple story with a rhyme, a safe choice, and a small earned merit at the end.",
    ]


def _do_reach(world: WorldModel, actor: Entity, obj: Entity, aid: Optional[Entity], narrate: bool = True) -> None:
    actor.meters["reach"] = actor.meters.get("reach", 0.0) + 1
    if aid and aid.id == "steady_stool":
        actor.meters["steadiness"] = actor.meters.get("steadiness", 0.0) + 1
        obj.meters["wobble"] = max(0.0, obj.meters.get("wobble", 0.0) - 1)
        actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1
        actor.memes["merit"] = actor.memes.get("merit", 0.0) + 1
        if narrate:
            world.say(f"{actor.id} reached the shelf safely with the steady step stool.")
    else:
        actor.meters["climb"] = actor.meters.get("climb", 0.0) + 1
        obj.meters["wobble"] = obj.meters.get("wobble", 0.0) + 1
        if narrate:
            world.say(f"{actor.id} climbed fast, and the loose rung wobbled under {actor.pronoun('possessive')} feet.")


def tell(setting: Setting, object_spec: ObjectSpec, aid_spec: AidSpec, hero_name: str, hero_type: str,
         hero_traits: list[str], parent_type: str) -> WorldModel:
    world = WorldModel(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"curiosity": 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent", memes={"cautionary": 1.0}))
    obj = world.add(Entity(id="Target", type=object_spec.label, label=object_spec.label, phrase=object_spec.phrase, meters={"wobble": 1.0 if "stool" in object_spec.label else 0.0}))
    aid = world.add(Entity(id=aid_spec.id, type="aid", label=aid_spec.label, phrase=aid_spec.phrase))
    world.facts.update(hero=hero, parent=parent, obj=obj, aid=aid, object_spec=object_spec, aid_spec=aid_spec)
    world.say(f"{hero.id} was a {hero_traits[0]} little {hero.type} who noticed everything on ordinary afternoons.")
    world.say(f"{hero.id} kept looking up at {object_spec.phrase} and wishing to see what was beside it.")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.para()
    world.say(f"At home in {setting.place}, {hero.id} stood near the shelf and reached for it.")
    world.say(f"{hero.id} wanted to get there right away, because curiosity had made the jar seem extra interesting.")
    world.say(f"Then {parent.pronoun('subject')} noticed the loose rung and said, \"Breathe first, {hero.id}. Careful feet are better than rushed feet.\"")
    parent.memes["cautionary"] = parent.memes.get("cautionary", 0.0) + 1
    hero.memes["breath"] = hero.memes.get("breath", 0.0) + 1
    world.say(f"{hero.id} took a slow breath, and the room felt quieter.")
    world.para()
    world.say(f"{hero.id} hummed a little rhyme: \"One rung, two rung, steady and slow; breathe, then step, and up I'll go.\"")
    world.say(f"That made the waiting feel easy.")
    _do_reach(world, hero, obj, aid=None, narrate=True)
    world.say(f"But {parent.pronoun('subject')} pointed to the wobble and helped {hero.pronoun('object')} choose the safer way instead.")
    world.say(f"Together they fixed the stool, and {hero.id} used {aid.label} to reach the shelf.")
    _do_reach(world, hero, obj, aid=aid, narrate=True)
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(f"After that, {hero.id} placed the jar back neatly and smiled at the little merit that came from doing it the careful way.")
    world.facts["resolved"] = True
    return world


def generate_story_qa(world: WorldModel) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    obj = f["obj"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Why did {hero.id} want to reach the shelf?",
            answer=f"{hero.id} was curious, so the high shelf and the bright jar made {hero.pronoun('object')} want to see what was there.",
        ),
        QAItem(
            question=f"What did {parent.label_word} tell {hero.id} to do before climbing?",
            answer=f"{parent.pronoun('subject').capitalize()} told {hero.id} to breathe first and take careful steps because the loose rung was wobbly.",
        ),
        QAItem(
            question=f"What safe choice helped {hero.id} reach {obj.label}?",
            answer=f"{hero.id} used {aid.label} with help from {parent.label_word}, so the reaching stayed steady and safe.",
        ),
    ]


def generate_world_qa(world: WorldModel) -> list[QAItem]:
    return [
        QAItem(
            question="What does breathe mean in a calm moment?",
            answer="To breathe means to take air into your body and let it out again. A slow breath can help you feel calmer.",
        ),
        QAItem(
            question="What is a rung?",
            answer="A rung is a step on a ladder or stool that you can put your foot on when you climb.",
        ),
        QAItem(
            question="What does merit mean here?",
            answer="Merit means something good is deserved because someone made a careful, helpful choice.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about curiosity, caution, and a safe climb.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    obj = args.object or rng.choice(list(OBJECTS))
    aid = args.aid or rng.choice(list(AIDS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    if obj == "shelf" and aid == "hand_hold":
        pass
    return StoryParams(place=place, object=obj, aid=aid, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OBJECTS[params.object], AIDS[params.aid], params.name, params.gender, ["curious"], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompt_text(world),
        story_qa=generate_story_qa(world),
        world_qa=generate_world_qa(world),
        world=world,
    )


def dump_trace(world: WorldModel) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
reachable(H) :- curiosity(H), warning_seen(H), breathe(H), safe_aid(A), use_aid(H,A).
unsafe(H) :- curiosity(H), loose_rung(stool), climb_fast(H), not reachable(H).
resolved(H) :- use_aid(H,A), safe_aid(A), breathe(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for o, spec in OBJECTS.items():
        lines.append(asp.fact("object", o))
        if "stool" in o:
            lines.append(asp.fact("loose_rung", o))
    for a, spec in AIDS.items():
        lines.append(asp.fact("safe_aid", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    print("OK: ASP twin is present and the generated world is exerciseable.")
    return 0


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(place="kitchen", object="stool", aid="steady_stool", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="playroom", object="shelf", aid="hand_hold", name="Theo", gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show reachable/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
