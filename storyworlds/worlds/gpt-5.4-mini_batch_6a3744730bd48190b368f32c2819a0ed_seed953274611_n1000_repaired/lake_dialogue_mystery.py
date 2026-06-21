#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lake_dialogue_mystery.py
========================================================

A small storyworld for a child-facing mystery by the lake: someone notices a
missing object, asks careful questions, follows clues around the shore, and
finds a quiet answer in the end.

The world uses typed entities with physical meters and emotional memes, drives
the story from simulated state, and supports prompts, grounded QA, JSON, trace,
and an ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
WORRY_STEP = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    detail: str
    waterline: str
    hiding_spot: str
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
class MissingThing:
    id: str
    label: str
    phrase: str
    where_last_seen: str
    clue: str
    owner: str
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
class Clue:
    id: str
    label: str
    text: str
    reveals: str
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
        clone = World()
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, role=v.role,
            traits=list(v.traits), attrs=dict(v.attrs),
            meters=defaultdict(float, dict(v.meters)),
            memes=defaultdict(float, dict(v.memes)),
        ) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    missing: str
    clue1: str
    clue2: str
    sleuth: str
    sleuth_gender: str
    friend: str
    friend_gender: str
    guardian: str
    guardian_gender: str
    mood: str = "curious"
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


LAKES = {
    "calm": Place(
        id="calm",
        label="the lake",
        detail="The lake was smooth and silver, with reeds swaying by the dock.",
        waterline="by the little wooden dock",
        hiding_spot="under the dock",
        tags={"lake", "water"},
    ),
    "foggy": Place(
        id="foggy",
        label="the lake",
        detail="The lake wore a soft fog, and the far bank looked like a quiet shadow.",
        waterline="along the pebbly shore",
        hiding_spot="behind a pile of flat stones",
        tags={"lake", "fog"},
    ),
    "reedy": Place(
        id="reedy",
        label="the lake",
        detail="Tall reeds leaned over the water, whispering when the wind passed through.",
        waterline="near the reeds",
        hiding_spot="in the reeds",
        tags={"lake", "reeds"},
    ),
}

MISSING = {
    "red_kite": MissingThing(
        id="red_kite",
        label="a red kite",
        phrase="a red kite with a wooden tail",
        where_last_seen="by the dock",
        clue="The string was tied in a neat little knot.",
        owner="the child",
        tags={"kite", "string"},
    ),
    "boat_key": MissingThing(
        id="boat_key",
        label="the boat key",
        phrase="the brass key for the rowboat",
        where_last_seen="on the bench",
        clue="A damp footprint pointed toward the water.",
        owner="the guardian",
        tags={"key", "boat"},
    ),
    "jar": MissingThing(
        id="jar",
        label="the jar of minnows",
        phrase="the jar with the minnows",
        where_last_seen="near the bucket",
        clue="A tiny splash mark curved toward the reeds.",
        owner="the friend",
        tags={"jar", "fish"},
    ),
}

CLUES = {
    "knot": Clue("knot", "a knot", "a neat knot", "string", {"string"}),
    "footprint": Clue("footprint", "a footprint", "a damp footprint", "water", {"footprint"}),
    "splash": Clue("splash", "a splash mark", "a tiny splash mark", "reeds", {"splash"}),
    "bench_note": Clue("bench_note", "a note", "a folded note", "bench", {"note"}),
}

SLEUTHS = ["Mina", "Leo", "Nora", "Theo", "Ava", "Eli"]
FRIENDS = ["Ben", "Ivy", "Maya", "Noah", "Luna", "Sam"]
GUARDIANS = ["Mom", "Dad"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid in LAKES:
        for mid in MISSING:
            combos.append((pid, mid))
    return combos


def reasonableness_gate(place: Place, missing: MissingThing) -> bool:
    return "lake" in place.tags and bool(missing.clue)


def clue_chain(place: Place, missing: MissingThing) -> list[Clue]:
    if missing.id == "red_kite":
        return [CLUES["knot"], CLUES["bench_note"]]
    if missing.id == "boat_key":
        return [CLUES["footprint"], CLUES["bench_note"]]
    return [CLUES["splash"], CLUES["knot"]]


def tell(world: World, place: Place, missing: MissingThing, clues: list[Clue],
         sleuth: Entity, friend: Entity, guardian: Entity) -> World:
    world.add(sleuth)
    world.add(friend)
    world.add(guardian)
    world.facts["place"] = place
    world.facts["missing"] = missing
    world.facts["clues"] = clues
    world.facts["sleuth"] = sleuth
    world.facts["friend"] = friend
    world.facts["guardian"] = guardian
    world.facts["found"] = False

    sleuth.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    guardian.memes["care"] += 1

    world.say(
        f"At {place.label}, {place.detail} {sleuth.id} looked around and frowned. "
        f'"{missing.label_word if hasattr(missing, "label_word") else missing.label} is gone," {sleuth.id} said.'
    )
    world.say(f'"Where did you last see it?" {guardian.id} asked.')
    world.say(f'"{missing.where_last_seen}," {friend.id} said. "{missing.clue}"')

    world.para()
    world.say(f"{sleuth.id} knelt by {place.waterline} and studied the shore.")
    world.say(f'"That clue means someone walked this way," {sleuth.id} said.')

    for clue in clues:
        if clue.id == "knot":
            sleuth.meters["evidence"] += 1
            world.say(f'Near the edge, {friend.id} spotted {clue.text}. "{clue.reveals}," {friend.id} whispered.')
        elif clue.id == "footprint":
            sleuth.meters["evidence"] += 1
            world.say(f'By the mud, {guardian.id} found {clue.text}. "{clue.reveals}," {guardian.id} said.')
        elif clue.id == "splash":
            sleuth.meters["evidence"] += 1
            world.say(f'In the reeds, {sleuth.id} noticed {clue.text}. "{clue.reveals}," {sleuth.id} said.')
        elif clue.id == "bench_note":
            sleuth.meters["evidence"] += 1
            world.say(f'On the bench, they found {clue.text}. "{clue.reveals}," {friend.id} said.')

    world.para()
    world.say(f'"It was hidden {place.hiding_spot}," {sleuth.id} said at last.')
    world.say(f'There, tucked away, was {missing.phrase}.')
    world.say(f'"We thought it was lost," {friend.id} said, "but it was only hiding."')
    world.say(f'"Mysteries can look scary," {guardian.id} said, "but careful eyes find answers."')

    sleuth.memes["relief"] += 1
    friend.memes["relief"] += 1
    guardian.memes["relief"] += 1
    world.facts["found"] = True
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small lake mystery storyworld with dialogue.")
    ap.add_argument("--place", choices=LAKES)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--sleuth")
    ap.add_argument("--friend")
    ap.add_argument("--guardian", choices=GUARDIANS)
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
    combos = valid_combos()
    if args.place and args.missing:
        if not reasonableness_gate(LAKES[args.place], MISSING[args.missing]):
            raise StoryError("That lake-and-missing-item pairing does not make a believable mystery.")
    matches = [c for c in combos if (not args.place or c[0] == args.place) and (not args.missing or c[1] == args.missing)]
    if not matches:
        raise StoryError("No valid combination matches the given options.")
    place, missing = rng.choice(sorted(matches))
    sleuth = args.sleuth or rng.choice(SLEUTHS)
    friend = args.friend or rng.choice([n for n in FRIENDS if n != sleuth])
    guardian = args.guardian or rng.choice(GUARDIANS)
    return StoryParams(
        place=place,
        missing=missing,
        clue1=clue_chain(LAKES[place], MISSING[missing])[0].id,
        clue2=clue_chain(LAKES[place], MISSING[missing])[1].id,
        sleuth=sleuth,
        sleuth_gender="girl" if sleuth in {"Mina", "Nora", "Ava"} else "boy",
        friend=friend,
        friend_gender="girl" if friend in {"Ivy", "Maya", "Luna"} else "boy",
        guardian=guardian,
        guardian_gender="girl" if guardian == "Mom" else "boy",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in LAKES or params.missing not in MISSING:
        raise StoryError("Invalid story parameters.")
    place = LAKES[params.place]
    missing = MISSING[params.missing]
    if not reasonableness_gate(place, missing):
        raise StoryError("This mystery is not reasonable enough to tell.")
    clue_ids = [params.clue1, params.clue2]
    clue_lookup = {c.id: c for c in CLUES.values()}
    clues = [clue_lookup[cid] for cid in clue_ids if cid in clue_lookup]
    if len(clues) != 2:
        clues = clue_chain(place, missing)

    world = World()
    sleuth = Entity(id=params.sleuth, kind="character", type=params.sleuth_gender, role="sleuth")
    friend = Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend")
    guardian = Entity(id=params.guardian, kind="character", type=params.guardian_gender, role="guardian")
    world = tell(world, place, missing, clues, sleuth, friend, guardian)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, missing = f["place"], f["missing"]
    return [
        f"Write a short mystery story by {place.label} that includes dialogue and the word 'lake'.",
        f"Tell a child-friendly mystery where {f['sleuth'].id} asks questions, follows clues, and finds {missing.phrase} near {place.label}.",
        f"Write a gentle lake mystery with a missing item, talking, and a quiet solution at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    place, missing = f["place"], f["missing"]
    sleuth, friend, guardian = f["sleuth"], f["friend"], f["guardian"]
    return [
        ("What kind of story is this?", "It is a mystery story with dialogue, set by the lake. The characters ask questions and follow clues until the answer appears."),
        (f"What was missing?", f"{missing.phrase} was missing. The children thought it was lost, but the clues led them to where it had been tucked away."),
        (f"How did {sleuth.id} solve the mystery?", f"{sleuth.id} listened to the clues, noticed the signs on the shore, and followed them to the hiding spot. That is how the missing thing was found without guessing."),
        (f"How did everyone feel at the end?", f"They felt relieved and calm because the missing thing was found. The mystery ended with a quiet answer instead of a worry."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a lake?", "A lake is a large body of water surrounded by land. It can be calm, foggy, or full of reeds and stones."),
        ("What is a clue?", "A clue is a small piece of information that helps solve a mystery. It can be a footprint, a note, or something out of place."),
        ("Why do people ask questions in a mystery?", "People ask questions so they can learn what happened. Questions help them compare clues and understand the answer."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in LAKES:
        lines.append(asp.fact("place", pid))
    for mid in MISSING:
        lines.append(asp.fact("missing", mid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, M) :- place(P), missing(M), lake(P), clue(M).
lake(P) :- place(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, missing=None, sleuth=None, friend=None, guardian=None
        ), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


CURATED = [
    StoryParams(place="calm", missing="red_kite", clue1="knot", clue2="bench_note",
                sleuth="Mina", sleuth_gender="girl", friend="Ben", friend_gender="boy",
                guardian="Mom", guardian_gender="girl", mood="curious"),
    StoryParams(place="foggy", missing="boat_key", clue1="footprint", clue2="bench_note",
                sleuth="Leo", sleuth_gender="boy", friend="Ivy", friend_gender="girl",
                guardian="Dad", guardian_gender="boy", mood="careful"),
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


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser_main().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible lake mysteries:")
        for p, m in asp_valid_combos():
            print(f"  {p} {m}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
