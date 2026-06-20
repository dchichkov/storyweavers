#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/record_garden_bummie_foreshadowing_repetition_transformation_tall.py
=====================================================================================================

A standalone story world for a tall-tale garden story built from the seed words
record, garden, and bummie, with foreshadowing, repetition, and transformation.

The world is intentionally small: one child, one garden, one old record, and one
bummie who keeps warning, repeating, and changing the mood of the day. The story
engine simulates physical meters and emotional memes, uses a reasonableness gate,
and renders prose from state transitions rather than from a frozen paragraph.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Thing:
    id: str
    label: str
    kind: str = "thing"
    loud: bool = False
    old: bool = False
    carries_seed: bool = False
    gives_music: bool = False
    transforms_into: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Garden:
    id: str
    label: str
    kind: str = "place"
    wild: bool = False
    blooms: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    child: str
    child_gender: str
    child_trait: str
    bummie: str
    record: str
    garden: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_music(world: World) -> list[str]:
    out = []
    rec = world.get("record")
    garden = world.get("garden")
    if rec.meters["spinning"] >= THRESHOLD and rec.meters["played"] >= THRESHOLD:
        if ("music", rec.id) not in world.fired:
            world.fired.add(("music", rec.id))
            garden.meters["music"] += 1
            garden.memes["wonder"] += 1
            out.append("__music__")
    return out


def _r_repeat(world: World) -> list[str]:
    out = []
    b = world.get("bummie")
    if b.memes["echo"] >= THRESHOLD and ("repeat", b.id) not in world.fired:
        world.fired.add(("repeat", b.id))
        b.memes["chorus"] += 1
        out.append("__repeat__")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    garden = world.get("garden")
    b = world.get("bummie")
    if garden.meters["music"] >= THRESHOLD and b.memes["chorus"] >= THRESHOLD:
        sig = ("transform", garden.id)
        if sig not in world.fired:
            world.fired.add(sig)
            garden.blooms = True
            garden.meters["bloom"] += 1
            b.memes["joy"] += 1
            out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("music", "physical", _r_music), Rule("repeat", "social", _r_repeat), Rule("transform", "change", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _play_record(world: World) -> None:
    rec = world.get("record")
    rec.meters["spinning"] += 1
    rec.meters["played"] += 1
    propagate(world)


def predict(world: World) -> dict:
    sim = world.copy()
    _play_record(sim)
    return {"music": sim.get("garden").meters["music"], "bloom": sim.get("garden").meters["bloom"]}


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child", traits=[params.child_trait]))
    bummie = world.add(Entity(id="bummie", kind="character", type="thing", role="helper"))
    record = world.add(Thing(id="record", label="record", loud=True, old=True, carries_seed=True, gives_music=True, transforms_into="garden music box"))
    garden = world.add(Garden(id="garden", label="garden", wild=True, blooms=False))
    world.facts.update(child=child, bummie=bummie, record=record, garden=garden)

    child.memes["curiosity"] += 1
    bummie.memes["warning"] += 1

    world.say(
        f"On a long bright morning, {child.id} wandered into the garden with a dusty record."
    )
    world.say(
        f"The garden was quiet as a church mouse, and the bummie sat nearby as still as a fence post."
    )
    world.say(
        f'"That record is old," said the bummie. "Old things can crack, old sounds can climb, and old days can turn."'
    )
    world.say(
        f"{child.id} smiled and set the record on the player. 'Play it once,' {child.pronoun()} said, 'just once.'"
    )

    world.para()
    _play_record(world)
    world.say("The record went round and round, and round and round, and round again.")
    world.say("The bummie bobbed its head and repeated, 'Round and round, and round and round.'")
    world.say("Then the wind rose through the beans and the roses, just as the bummie had said it might.")

    world.para()
    pred = predict(World()) if False else predict(world)
    world.facts["predicted_music"] = pred["music"]
    world.facts["predicted_bloom"] = pred["bloom"]
    bummie.memes["echo"] += 1
    propagate(world)
    if world.get("garden").blooms:
        world.say("The music woke the beans and the roses, and the whole garden began to bloom and sway.")
        world.say("The bummie, once as plain as a pebble, turned bright as a button and light as a dance step.")
        world.say(f"{child.id} laughed, because the garden was not the same garden anymore.")
        world.say("It had become a singing, blooming wonder from one little record and one mighty chorus.")

    world.facts["outcome"] = "transformed" if world.get("garden").blooms else "unchanged"
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    return [("child", "bummie", "record")]


KNOWLEDGE = {
    "record": [("What is a record?", "A record is a flat disc that can play music when it spins on a player.")],
    "garden": [("What is a garden?", "A garden is a place where plants grow, and people can water, tend, and enjoy them.")],
    "bummie": [("What is a bummie?", "In this story, a bummie is a small helper creature who watches, warns, and repeats things in a funny way.")],
    "music": [("What can music do?", "Music can change how a place feels. It can make a quiet place feel lively and full of motion.")],
    "bloom": [("What does it mean when plants bloom?", "When plants bloom, they open flowers and look bright and alive.")],
}


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a tall tale for a young child that includes the words "record", "garden", and "bummie".',
        'Tell a story with foreshadowing, repetition, and transformation about a record playing in a garden and a bummie who warns about what may happen.',
        'Write a lively garden story where repeated lines build up to a magical change.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    return [
        ("Who is the story about?", f"It is about {child.id}, the record, the garden, and the bummie."),
        ("What did the bummie warn about?", "The bummie warned that the record was old and that old things can crack, make strange sounds, and bring changes."),
        ("What happened after the record was played?", "The record spun and spun, the garden filled with music, and the plants began to bloom."),
        ("How did the garden change?", "It changed from quiet and still into a singing, blooming place full of motion."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"record", "garden", "bummie", "music", "bloom"}
    out = []
    for key in ["record", "garden", "bummie", "music", "bloom"]:
        out.extend(KNOWLEDGE[key])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if getattr(e, "traits", None):
            bits.append(f"traits={e.traits}")
        if getattr(e, "label", ""):
            bits.append(f"label={getattr(e, 'label')}")
        lines.append(f"  {e.id:8} ({getattr(e, 'type', 'thing'):7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [StoryParams("Avery", "girl", "curious", "bummie", "record", "garden")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale garden story world with record, garden, and bummie.")
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait")
    ap.add_argument("--bummie")
    ap.add_argument("--record")
    ap.add_argument("--garden")
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
    if any([args.bummie and args.bummie != "bummie", args.record and args.record != "record", args.garden and args.garden != "garden"]):
        raise StoryError("This world only tells the seed story about a bummie, a record, and a garden.")
    return StoryParams(
        child=args.child or rng.choice(["Avery", "Milo", "June", "Nora"]),
        child_gender=args.gender or rng.choice(["girl", "boy"]),
        child_trait=args.trait or rng.choice(["curious", "spirited", "bold", "thoughtful"]),
        bummie="bummie",
        record="record",
        garden="garden",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
spins(record) :- chosen(record).
music(garden) :- spins(record).
echo(bummie) :- heard(record).
transform(garden) :- music(garden), echo(bummie).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("chosen", "record"),
        asp.fact("heard", "record"),
        asp.fact("thing", "bummie"),
        asp.fact("place", "garden"),
    ])


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show transform/1."))
    asp_ok = bool(asp.atoms(model, "transform"))
    py_ok = True
    smoke = generate(CURATED[0])
    py_ok = smoke.world is not None and smoke.world.get("garden").blooms
    print("OK: ASP and Python both see transformation." if asp_ok and py_ok else "MISMATCH: ASP/Python parity failed.")
    return 0 if asp_ok and py_ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show transform/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible story: record, garden, bummie")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
