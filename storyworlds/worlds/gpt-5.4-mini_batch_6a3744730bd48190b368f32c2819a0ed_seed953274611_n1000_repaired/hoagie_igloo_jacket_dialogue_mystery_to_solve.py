#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hoagie_igloo_jacket_dialogue_mystery_to_solve.py
=================================================================================

A standalone story world about a snowy adventure: a child, a missing hoagie,
an igloo, a jacket, a misunderstanding, and a mystery that gets solved through
conversation.

The world is intentionally small and classical:
- typed entities with meters and memes
- a forward-chained state model
- a reasonableness gate
- a Python gate mirrored by inline ASP rules
- three QA sets grounded in the simulated world

The seed prompt asks for the words:
- hoagie
- igloo
- jacket

and the narrative instruments:
- Dialogue
- Mystery to Solve
- Misunderstanding

The domain below turns that into a snowy adventure: someone thinks the jacket
hid the hoagie, but the real mystery is a hungry helper who moved it into the
igloo to keep it cold and safe.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    cold: bool = False
    hidden: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    edible: bool = False
    cold_safe: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Misunderstanding:
    id: str
    clue: str
    suspicion: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Resolution:
    id: str
    truth: str
    method: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class StoryParams:
    place: str
    mystery: str
    misunderstanding: str
    resolution: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    jacket_color: str = "blue"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


PLACES = {
    "yard": Place(id="yard", label="the snowy yard", cold=True, hidden=False, tags={"snow", "outdoor"}),
    "igloo": Place(id="igloo", label="the little igloo", cold=True, hidden=True, tags={"igloo", "snow"}),
    "hill": Place(id="hill", label="the icy hill", cold=True, hidden=False, tags={"snow", "adventure"}),
}

ITEMS = {
    "hoagie": Item(id="hoagie", label="hoagie", phrase="a hoagie wrapped in paper", edible=True, cold_safe=True, tags={"hoagie"}),
    "jacket": Item(id="jacket", label="jacket", phrase="a warm jacket", edible=False, cold_safe=True, tags={"jacket"}),
    "map": Item(id="map", label="map", phrase="a folded map", edible=False, cold_safe=False, tags={"mystery"}),
}

MISUNDERSTANDINGS = {
    "blame_jacket": Misunderstanding(
        id="blame_jacket",
        clue="The jacket was sitting beside the empty bench.",
        suspicion="Maybe the jacket hid the hoagie.",
        tags={"misunderstanding", "jacket"},
    ),
    "blame_wind": Misunderstanding(
        id="blame_wind",
        clue="Snow tracks led away from the bench.",
        suspicion="Maybe the wind blew the hoagie away.",
        tags={"misunderstanding", "snow"},
    ),
}

RESOLUTIONS = {
    "helper_move": Resolution(
        id="helper_move",
        truth="A hungry helper moved the hoagie into the igloo to keep it cold.",
        method="They followed the tracks and asked the helper directly.",
        tags={"truth", "igloo", "hoagie"},
    ),
    "lost_in_pack": Resolution(
        id="lost_in_pack",
        truth="The hoagie had slipped into the backpack under the jacket.",
        method="They checked the pack pocket by pocket.",
        tags={"truth", "jacket", "hoagie"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Finn", "Leo", "Theo", "Max", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for mystery in RESOLUTIONS:
            for misunderstanding in MISUNDERSTANDINGS:
                combos.append((place, mystery, misunderstanding))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.mystery not in RESOLUTIONS:
        raise StoryError("Unknown mystery.")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    if params.resolution == "helper_move" and params.place != "igloo":
        return
    if params.resolution == "lost_in_pack" and params.misunderstanding == "blame_wind":
        return


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A snowy mystery storyworld about a hoagie, an igloo, and a jacket.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=RESOLUTIONS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    place = args.place or rng.choice(list(PLACES))
    mystery = args.mystery or rng.choice(list(RESOLUTIONS))
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    resolution = args.resolution or mystery
    if resolution not in RESOLUTIONS:
        raise StoryError("Unknown resolution.")
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        mystery=mystery,
        misunderstanding=misunderstanding,
        resolution=resolution,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        jacket_color=rng.choice(["red", "blue", "green"]),
    )


def _do_search(world: World) -> None:
    for ent in list(world.entities.values()):
        if ent.role == "hoagie_searcher" and ent.memes["curiosity"] >= THRESHOLD:
            ent.memes["determination"] += 1


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    jacket = world.add(Entity(id="jacket", type="thing", label=f"{params.jacket_color} jacket", role="clue"))
    hoagie = world.add(Entity(id="hoagie", type="thing", label="hoagie", role="goal"))
    igloo = world.add(Entity(id="igloo", type="place", label="igloo", role="hideout"))
    hero.memes["curiosity"] = 1.0
    helper.memes["care"] = 1.0

    world.say(f"On a bright winter day, {hero.id} and {helper.id} set out like brave explorers in {PLACES[params.place].label}.")
    world.say(f'{hero.id} pointed at the empty bench. "My hoagie was here," {hero.pronoun()} said, looking worried.')
    world.say(f'{helper.id} found {jacket.label_word if jacket.label_word else "the jacket"} nearby and said, "Maybe the {params.misunderstanding.replace("_", " ")}."')
    world.para()
    world.say(f'That sounded possible, but it was only a misunderstanding. {MISUNDERSTANDINGS[params.misunderstanding].clue}')
    world.say(f'{hero.id} and {helper.id} followed the snowy tracks toward the {params.place}.')
    world.say(f'Inside the cold air, the little {igloo.label_word if hasattr(igloo, "label_word") else "igloo"} looked like a secret fort waiting to speak.')
    world.para()

    truth = RESOLUTIONS[params.resolution]
    if params.resolution == "helper_move":
        world.say(f'{helper.id} knocked on the ice wall. "We need the truth," {helper.pronoun()} said.')
        world.say(f'From inside came a small voice: "I moved it here so it would stay cold!"')
        world.say(truth.truth)
        world.say(f'{hero.id} laughed with relief and tucked the jacket under {hero.pronoun("possessive")} arm before sharing the hoagie with {helper.id}.')
    else:
        world.say(f'{hero.id} and {helper.id} searched the backpack, because the jacket looked as if it had hidden something.')
        world.say(f'{helper.id} said, "Let us check every pocket like careful detectives."')
        world.say(truth.truth)
        world.say(f'At last they found the hoagie, wrapped safe and sound, and the jacket was only a warm jacket after all.')
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.facts.update(
        hero=hero,
        helper=helper,
        jacket=jacket,
        hoagie=hoagie,
        igloo=igloo,
        place=params.place,
        misunderstanding=params.misunderstanding,
        resolution=params.resolution,
    )
    _do_search(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story with dialogue that includes the words "hoagie", "igloo", and "jacket".',
        f"Tell a mystery story where {f['hero'].id} thinks the jacket caused the missing hoagie, but the real answer is hidden near the igloo.",
        f'Write a child-friendly adventure with a misunderstanding that gets solved by asking questions and following clues.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mis = MISUNDERSTANDINGS[f["misunderstanding"]]
    truth = RESOLUTIONS[f["resolution"]]
    return [
        ("What was missing?", "The hoagie was missing. That started the whole mystery and sent them looking for clues."),
        ("What did they think at first?", f"They thought {mis.suspicion.lower()} It turned out to be a misunderstanding."),
        ("How did they solve the mystery?", f"{truth.method} {truth.truth}"),
        ("What role did the jacket play?", "The jacket was only a clue at first. In the end, it was not the thief or the problem."),
        ("Who helped solve it?", f"{helper.id} helped {hero.id} by asking questions, following tracks, and staying calm."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a hoagie?", "A hoagie is a sandwich, often wrapped up for carrying. It is good to eat when you are hungry."),
        ("What is an igloo?", "An igloo is a shelter made from snow or ice. It can be a secret hiding place in a winter adventure."),
        ("What is a jacket for?", "A jacket keeps your body warm when the air is cold. It is useful in snow and wind."),
        ("What is a misunderstanding?", "A misunderstanding happens when someone thinks the wrong thing at first. Then more clues can help them learn the truth."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="igloo", mystery="helper_move", misunderstanding="blame_jacket", resolution="helper_move", hero="Mia", hero_gender="girl", helper="Theo", helper_gender="boy", jacket_color="blue"),
    StoryParams(place="yard", mystery="lost_in_pack", misunderstanding="blame_wind", resolution="lost_in_pack", hero="Finn", hero_gender="boy", helper="Lily", helper_gender="girl", jacket_color="red"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    for r in RESOLUTIONS:
        lines.append(asp.fact("resolution", r))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, M, U) :- place(P), resolution(M), misunderstanding(U).
truthy(helper_move) :- resolution(helper_move).
truthy(lost_in_pack) :- resolution(lost_in_pack).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, misunderstanding=None, resolution=None, name=None, helper=None), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    else:
        print("OK: ASP parity and smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.mystery not in RESOLUTIONS:
        raise StoryError("Unknown mystery.")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    if params.resolution not in RESOLUTIONS:
        raise StoryError("Unknown resolution.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        for i in range(args.n):
            params = resolve_params(args, random.Random((args.seed or 0) + i if args.seed is not None else rng.randrange(2**31)))
            params.seed = args.seed
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
