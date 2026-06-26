#!/usr/bin/env python3
"""
storyworlds/worlds/hose_train_station_curiosity_suspense_ghost_story.py
========================================================================

A standalone story world for a small ghost-story domain set in a train station.

Premise:
A curious child hears strange hissing in an old train station at night.
The sound leads to a forgotten hose, a leak, and a spooky-looking trick of light.
Suspense comes from the child wanting to investigate, while the ending reveals
the "ghost" is not a ghost at all, but a simple cause hidden in the station.

This world models a tiny simulation with physical meters and emotional memes,
keeps the prose state-driven, and includes a reasonableness gate plus an ASP twin.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    moved_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("wet", 0.0)
        self.meters.setdefault("spooky", 0.0)
        self.meters.setdefault("seen", 0.0)
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("suspense", 0.0)
        self.memes.setdefault("fear", 0.0)
        self.memes.setdefault("relief", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the train station"
    affordance: str = "hiss"


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    location: str
    cause: str


@dataclass
class StoryParams:
    name: str
    gender: str
    companion: str
    place: str = "train_station"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    hose = world.get("hose")
    if hose.meters["wet"] >= THRESHOLD and child.memes["curiosity"] >= THRESHOLD:
        sig = ("spook",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["suspense"] += 1
        hose.meters["spooky"] += 1
        out.append("The dark hose looked like something that should not have been there.")
    return out


def _r_expose_source(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    hose = world.get("hose")
    leak = world.get("leak")
    if child.meters["seen"] >= THRESHOLD and leak.meters["seen"] < THRESHOLD:
        sig = ("source",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        leak.meters["seen"] += 1
        child.memes["relief"] += 1
        out.append("A tiny leak under the platform was making the hiss.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_spook, _r_expose_source):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion, label="the conductor"))
    hose = world.add(Entity(
        id="hose",
        type="hose",
        label="hose",
        phrase="a long black hose",
        location="platform",
    ))
    leak = world.add(Entity(
        id="leak",
        type="leak",
        label="leak",
        phrase="a hidden leak",
        location="under the platform",
    ))
    lantern = world.add(Entity(
        id="lantern",
        type="lantern",
        label="lantern",
        phrase="a small lantern",
        location="ticket hall",
    ))

    world.facts.update(child=child, companion=companion, hose=hose, leak=leak, lantern=lantern)
    return world


def tell(world: World) -> None:
    child = world.get("child")
    companion = world.get("companion")
    hose = world.get("hose")
    leak = world.get("leak")
    lantern = world.get("lantern")

    world.say(
        f"{child.label} was a curious little {child.type} who loved to peek into quiet places."
    )
    world.say(
        f"One late night, {child.label} and {companion.label} were at {world.setting.place}, "
        f"where old tiles glimmered under a sleepy lantern."
    )
    world.say(
        f"{child.label} noticed a strange hiss near the platform. "
        f"It sounded like a whisper, and it came from {hose.phrase}."
    )

    child.memes["curiosity"] += 1
    hose.meters["wet"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{child.label} wanted to look closer, but the station felt bigger and darker now."
    )
    child.memes["suspense"] += 1
    world.say(
        f"{companion.label} held up {lantern.phrase} and said, "
        f"\"Let's be brave and find the sound.\""
    )
    child.meters["seen"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Together they followed the hiss to {leak.phrase} under the platform."
    )
    world.say(
        f"It was only water slipping through a crack, not a ghost at all."
    )
    world.say(
        f"{child.label} smiled, and the spooky feeling melted into relief."
    )
    child.memes["relief"] += 1
    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a short ghost story for a child named {child.label} set in a train station.',
        f"Tell a suspenseful but gentle story about a curious child, a hose, and a strange sound in {world.setting.place}.",
        "Write a small spooky story where the mystery turns out to have an ordinary cause.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    companion = f["companion"]
    return [
        QAItem(
            question=f"Who was the curious child in the train station story?",
            answer=f"The curious child was {child.label}.",
        ),
        QAItem(
            question="What strange thing made the whispering sound?",
            answer="A long hose near the platform made the strange hissing sound.",
        ),
        QAItem(
            question=f"Who helped {child.label} look for the sound?",
            answer=f"{companion.label} helped by holding up a lantern and going with {child.label}.",
        ),
        QAItem(
            question="What was the spooky mystery really about?",
            answer="It was not a ghost. A small leak under the platform was making the hiss.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a train station?",
            answer="A train station is a place where trains stop so people can get on or off.",
        ),
        QAItem(
            question="What is a hose for?",
            answer="A hose is a flexible tube that carries water from one place to another.",
        ),
        QAItem(
            question="Why can a dark station feel spooky?",
            answer="A dark, quiet station can feel spooky because small sounds seem bigger there.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "train_station": Setting(place="the train station", affordance="hiss"),
}

GENDER_NAMES = {
    "girl": ["Maya", "Lina", "Nora", "Ivy", "Tess"],
    "boy": ["Eli", "Noah", "Theo", "Max", "Finn"],
}

COMPLEMENTS = ["conductor", "parent", "older brother", "older sister"]


def valid_combos() -> list[tuple[str, str]]:
    return [("train_station", "girl"), ("train_station", "boy")]


def reasonableness_check(params: StoryParams) -> None:
    if params.place != "train_station":
        raise StoryError("This world only tells stories set in a train station.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("Gender must be girl or boy for this small story world.")


ASP_RULES = r"""
place(train_station).
gender(girl;boy).

valid(P,G) :- place(P), gender(G).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("place", "train_station")]
    for g in ("girl", "boy"):
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python:")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world set in a train station.")
    ap.add_argument("--place", choices=["train_station"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPLEMENTS)
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
    if args.place and args.place != "train_station":
        raise StoryError("Only train_station is supported.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDER_NAMES[gender])
    companion = args.companion or rng.choice(COMPLEMENTS)
    params = StoryParams(name=name, gender=gender, companion=companion, place="train_station")
    reasonableness_check(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(format_qa(sample))


CURATED = [
    StoryParams(name="Maya", gender="girl", companion="conductor", place="train_station"),
    StoryParams(name="Eli", gender="boy", companion="parent", place="train_station"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, g in asp_valid_combos():
            print(f"  {p} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
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
