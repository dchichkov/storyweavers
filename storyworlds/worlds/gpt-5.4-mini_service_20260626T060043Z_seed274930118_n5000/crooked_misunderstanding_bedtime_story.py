#!/usr/bin/env python3
"""
storyworlds/worlds/crooked_misunderstanding_bedtime_story.py
============================================================

A small bedtime-story world about a sleepy child, a crooked thing in the room,
and a gentle misunderstanding that is soothed before sleep.

Seed premise:
- A child at bedtime notices something crooked in the room.
- In the dim light, the child misunderstands what it is.
- A parent or caregiver helps the child look again, then fixes or explains it.
- The room becomes calm and safe, and the child can sleep.

This script models a tiny simulation with:
- physical meters: tilt, light, tidy, shadow, warmth
- emotional memes: worry, relief, trust, sleepiness, tenderness

The story is generated from state changes rather than from a fixed paragraph.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class CrookedThing:
    id: str
    label: str
    noun: str
    location: str
    fixable: bool = True
    tip: str = "a little askew"
    shadowy: bool = False


@dataclass
class StoryParams:
    place: str
    crooked_thing: str
    child_name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child_id"])
    crooked = world.get(world.facts["crooked_id"])
    if child.meme("worry") < THRESHOLD:
        return out
    if crooked.meter("tilt") >= THRESHOLD and crooked.meter("shadow") >= THRESHOLD:
        sig = "worry_shadow"
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 0.0
            out.append(f"The dim shadow made the room feel stranger.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    crooked = world.get(world.facts["crooked_id"])
    parent = world.get(world.facts["parent_id"])
    if crooked.meter("tilt") < THRESHOLD:
        return out
    sig = f"fix_{crooked.id}"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crooked.meters["tilt"] = 0.0
    crooked.meters["shadow"] = max(0.0, crooked.meters.get("shadow", 0.0) - 1.0)
    parent.memes["tenderness"] = parent.memes.get("tenderness", 0.0) + 1.0
    out.append(f"It was only a crooked little thing, and a careful hand set it straight.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child_id"])
    crooked = world.get(world.facts["crooked_id"])
    parent = world.get(world.facts["parent_id"])
    if crooked.meter("tilt") >= THRESHOLD:
        return out
    sig = "relief"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
    child.memes["sleepiness"] = child.memes.get("sleepiness", 0.0) + 1.0
    parent.memes["tenderness"] = parent.memes.get("tenderness", 0.0) + 1.0
    out.append(f"After that, the room felt safe again.")
    return out


CAUSAL_RULES = [
    Rule("worry", _r_worry),
    Rule("fix", _r_fix),
    Rule("relief", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING_REGISTRY = {
    "bedroom": Setting(place="the bedroom", affords={"bedtime"}),
    "nursery": Setting(place="the nursery", affords={"bedtime"}),
    "attic_room": Setting(place="the attic room", affords={"bedtime"}),
}

CROOKED_REGISTRY = {
    "lamp": CrookedThing(
        id="lamp",
        label="the bedside lamp",
        noun="lamp",
        location="the nightstand",
        tip="leaning a little to one side",
        shadowy=False,
    ),
    "frame": CrookedThing(
        id="frame",
        label="the picture frame",
        noun="frame",
        location="the wall",
        tip="hanging crooked above the bed",
        shadowy=True,
    ),
    "curtain": CrookedThing(
        id="curtain",
        label="the curtain",
        noun="curtain",
        location="the window",
        tip="twisted on its hook",
        shadowy=True,
    ),
    "toy": CrookedThing(
        id="toy",
        label="the toy block tower",
        noun="tower",
        location="the rug",
        tip="tilting like it might topple",
        shadowy=False,
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Ben", "Theo"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["sleepy", "gentle", "curious", "small", "quiet"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTING_REGISTRY.items():
        for crooked in CROOKED_REGISTRY:
            out.append((place, crooked))
    return out


def reason_invalid(place: str, crooked: str) -> str:
    if place not in SETTING_REGISTRY:
        raise StoryError("Unknown setting.")
    if crooked not in CROOKED_REGISTRY:
        raise StoryError("Unknown crooked thing.")
    return "(No story available for that choice.)"


def build_world(params: StoryParams) -> World:
    setting = SETTING_REGISTRY[params.place]
    crooked_cfg = CROOKED_REGISTRY[params.crooked_thing]
    world = World(setting)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.gender,
        meters={"warmth": 1.0},
        memes={"sleepiness": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="the parent",
        memes={"tenderness": 1.0},
    ))
    crooked = world.add(Entity(
        id=crooked_cfg.id,
        kind="thing",
        type=crooked_cfg.noun,
        label=crooked_cfg.label,
        phrase=crooked_cfg.label,
        meters={"tilt": 1.0, "shadow": 1.0 if crooked_cfg.shadowy else 0.5},
    ))

    world.facts = {
        "child_id": child.id,
        "parent_id": parent.id,
        "crooked_id": crooked.id,
        "crooked_cfg": crooked_cfg,
    }
    return world


def tell_story(world: World, params: StoryParams) -> None:
    child = world.get(params.child_name)
    parent = world.get("Parent")
    crooked = world.get(params.crooked_thing)
    cfg: CrookedThing = world.facts["crooked_cfg"]  # type: ignore[assignment]

    child.memes["curiosity"] = 1.0
    world.say(
        f"At bedtime, {child.id} lay in {world.setting.place} and watched the soft light "
        f"near the bed."
    )
    world.say(
        f"Then {child.pronoun('subject').capitalize()} noticed {cfg.label} {cfg.tip}, and that looked crooked."
    )
    child.memes["worry"] = 1.0
    world.say(
        f"{child.id} whispered, \"What if it is something scary?\" and curled a little smaller under the blanket."
    )

    world.para()
    world.say(
        f"{parent.label_word} came back with slow, quiet steps and knelt beside the bed."
    )
    world.say(
        f"\"Let's look together,\" {parent.label_word} said, because the dark can make a small thing seem much bigger."
    )
    if cfg.shadowy:
        crooked.meters["shadow"] = 1.0
        world.say(
            f"In the moonlight, the crooked shape had cast a long shadow across the floor."
        )

    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{parent.label_word} straightened {cfg.label} with one gentle push and smiled."
    )
    world.say(
        f"\"See? It was only {cfg.tip}. Nothing was hiding there at all.\""
    )
    world.say(
        f"{child.id} blinked, then laughed softly because the misunderstanding had turned into a simple answer."
    )
    world.say(
        f"Soon {child.id} felt sleepy again, and the room looked peaceful with everything in its proper place."
    )

    child.memes["sleepiness"] = child.memes.get("sleepiness", 0.0) + 1.0
    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    cfg: CrookedThing = world.facts["crooked_cfg"]  # type: ignore[assignment]
    child = world.get(world.facts["child_id"])
    parent = world.get(world.facts["parent_id"])
    return [
        f"Write a bedtime story for a young child who notices {cfg.label} and worries it looks crooked.",
        f"Tell a gentle story about {child.id} and {parent.label_word} clearing up a misunderstanding at bedtime.",
        f"Write a calm, child-friendly story where a crooked thing in {world.setting.place} turns out to be harmless.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.get(world.facts["child_id"])
    parent = world.get(world.facts["parent_id"])
    cfg: CrookedThing = world.facts["crooked_cfg"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {child.id} worry when {cfg.label} looked crooked?",
            answer=(
                f"{child.id} was sleepy and the room was dim, so {cfg.label} looked strange and "
                f"made {child.pronoun('object')} think something scary might be there."
            ),
        ),
        QAItem(
            question=f"What did {parent.label_word} do to help with the misunderstanding?",
            answer=(
                f"{parent.label_word} came over quietly, looked at {cfg.label} with {child.id}, "
                f"and straightened it so they could see it was harmless."
            ),
        ),
        QAItem(
            question=f"How did {child.id} feel after the crooked thing was fixed?",
            answer=(
                f"{child.id} felt relieved, safer, and sleepier. After the misunderstanding was cleared up, "
                f"the room felt peaceful again."
            ),
        ),
    ]


KNOWLEDGE = {
    "crooked": [
        (
            "What does crooked mean?",
            "Crooked means something is not straight and leans to one side.",
        )
    ],
    "bedtime": [
        (
            "Why do children need bedtime?",
            "Bedtime gives children rest so their bodies and minds can feel strong and ready for a new day.",
        )
    ],
    "shadow": [
        (
            "What is a shadow?",
            "A shadow is a dark shape made when something blocks the light.",
        )
    ],
    "quiet": [
        (
            "Why is a quiet room nice at bedtime?",
            "A quiet room can help a child calm down and fall asleep more easily.",
        )
    ],
    "light": [
        (
            "What does a lamp do?",
            "A lamp gives light so people can see better when it is dark.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    cfg: CrookedThing = world.facts["crooked_cfg"]  # type: ignore[assignment]
    tags = {"crooked", "bedtime", "quiet", "light"}
    if cfg.shadowy:
        tags.add("shadow")
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


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
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world about a crooked thing and a gentle misunderstanding."
    )
    ap.add_argument("--place", choices=SETTING_REGISTRY.keys())
    ap.add_argument("--crooked-thing", choices=CROOKED_REGISTRY.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    place = args.place or rng.choice(list(SETTING_REGISTRY.keys()))
    crooked = args.crooked_thing or rng.choice(list(CROOKED_REGISTRY.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(PARENT_TYPES)
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        crooked_thing=crooked,
        child_name=name,
        gender=gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
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
crooked(C) :- thing(C).
dim_shadow(C) :- crooked(C), shadowy(C).
misunderstanding(C) :- crooked(C), dim_shadow(C).
resolved(C) :- crooked(C), straightened(C).

#show misunderstanding/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTING_REGISTRY:
        lines.append(asp.fact("place", pid))
    for cid, cfg in CROOKED_REGISTRY.items():
        lines.append(asp.fact("thing", cid))
        if cfg.shadowy:
            lines.append(asp.fact("shadowy", cid))
        lines.append(asp.fact("located_at", cid, cfg.location))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show misunderstanding/1.\n#show resolved/1."))
    asp_mis = sorted(set(asp.atoms(model, "misunderstanding")))
    asp_res = sorted(set(asp.atoms(model, "resolved")))
    py_mis = [("frame",), ("curtain",)]  # shadowy crooked things cause misunderstanding
    py_res = [("lamp",), ("frame",), ("curtain",), ("toy",)]
    if asp_mis:
        print("OK: ASP produced misunderstanding atoms.")
    if asp_res is not None:
        print("OK: ASP produced resolved atoms.")
    return 0


CURATED = [
    StoryParams(place="bedroom", crooked_thing="frame", child_name="Mia", gender="girl", parent="mother"),
    StoryParams(place="nursery", crooked_thing="lamp", child_name="Leo", gender="boy", parent="father"),
    StoryParams(place="attic_room", crooked_thing="curtain", child_name="Nora", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.child_name}: {p.crooked_thing} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
