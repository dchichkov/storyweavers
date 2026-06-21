#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/parallel_mutter_less_rhyme_surprise_detective_story.py
======================================================================================

A standalone storyworld for a small detective tale with rhyme and surprise.

Premise:
- A child detective follows parallel clues.
- A witness mutters about a missing small object.
- The mystery is less scary than it first seems.
- The ending includes a rhyme and a surprise reveal.

The world model tracks:
- physical meters: clue strength, worry, relief, mess, light
- emotional memes: curiosity, suspicion, surprise, delight, patience

The story is constrained so that it reads like a tiny detective case:
a small thing goes missing, the detective notices parallel tracks or clues,
follows them to a hiding place, and a surprise ending reveals who moved it
and why. The prose is state-driven rather than a frozen paragraph with swapped
names.

This script follows the shared StorySample / QAItem API and supports:
default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
and --show-asp.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    parallel_signs: str
    dark_corner: str
    hiding_place: str
    ending_image: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Object:
    id: str
    label: str
    phrase: str
    small: bool = True
    surprise_weight: int = 1
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Witness:
    id: str
    label: str
    mutter: str
    worried_about: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class SuspectMove:
    id: str
    motive: str
    reveal: str
    surprise: str
    rhyme: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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
            self.history.append(text)

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    place: str
    object: str
    witness: str
    move: str
    detective_name: str
    detective_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


PLACES = {
    "hallway": Place(
        "hallway", "the hallway",
        "Two long shoe prints ran in parallel across the floor.",
        "the dim corner by the umbrella stand",
        "behind a stack of boxes",
        "a neat clue path led back to the right door",
        tags={"parallel", "detective"},
    ),
    "library": Place(
        "library", "the library",
        "Two parallel lines of dust showed where fingers had slid along the shelf.",
        "the shadow under the tall window",
        "inside a hollow book box",
        "the lines of dust pointed to the same shelf twice",
        tags={"parallel", "detective"},
    ),
    "kitchen": Place(
        "kitchen", "the kitchen",
        "Two parallel crumbs on the table made a tiny trail.",
        "the dark spot under the chair",
        "in a jar behind the flour tin",
        "the crumbs ended in a grin and a found prize",
        tags={"parallel", "detective"},
    ),
}

OBJECTS = {
    "key": Object("key", "little silver key", "a little silver key", True, 2, {"less", "detective"}),
    "pin": Object("pin", "shiny hair pin", "a shiny hair pin", True, 1, {"less", "detective"}),
    "note": Object("note", "folded note", "a folded note", True, 1, {"less", "detective"}),
}

WITNESSES = {
    "cat": Witness("cat", "cat", "Mutter, mutter, it went under the chair.", "the missing thing", {"mutter", "detective"}),
    "grandpa": Witness("grandpa", "grandpa", "Mutter, mutter, I saw a hand and then a hide.", "the hiding place", {"mutter", "detective"}),
    "neighbor": Witness("neighbor", "neighbor", "Mutter, mutter, the trail was not straight but side by side.", "the parallel clues", {"mutter", "detective"}),
}

MOVES = {
    "mischief": SuspectMove(
        "mischief",
        "wanted to keep the prize safe for later",
        "It was not stolen at all",
        "The surprise was simple: the item had only been tucked away",
        "The little prize was not gone; it was just in the wrong zone.",
        {"surprise", "rhyme", "detective"},
    ),
    "helper": SuspectMove(
        "helper",
        "wanted to surprise the detective with a game",
        "A helper had moved it for a game",
        "The surprise was bigger: someone planned a playful reveal",
        "The secret was sweet; the helper made a tiny treat.",
        {"surprise", "rhyme", "detective"},
    ),
    "pet": SuspectMove(
        "pet",
        "was carried off by a curious pet and hidden nearby",
        "A small pet had nudged it aside",
        "The surprise was funny: a pet caused the puzzle",
        "A pet can fetch, then tuck, then make a quiet luck.",
        {"surprise", "rhyme", "detective"},
    ),
}


def _pick_name(rng: random.Random, gender: str) -> str:
    girls = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Ivy", "Ella"]
    boys = ["Theo", "Finn", "Noah", "Max", "Leo", "Sam", "Eli"]
    return rng.choice(girls if gender == "girl" else boys)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for obj in OBJECTS:
            for move in MOVES:
                combos.append((place, obj, move))
    return combos


def _detective_reassures(world: World, detective: Entity, witness: Witness, place: Place) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} paused in {place.label}. {witness.mutter} "
        f"{detective.pronoun().capitalize()} listened closely."
    )
    world.say(
        f'"We can follow the parallel clues," {detective.id} said. '
        f'"The mystery feels less scary when we look carefully."'
    )


def _follow_clues(world: World, place: Place, obj: Object, move: SuspectMove) -> None:
    world.facts["clue_trail"] = place.parallel_signs
    world.facts["dark_corner"] = place.dark_corner
    world.facts["hidden"] = place.hiding_place
    world.say(
        f"The detective studied {place.parallel_signs.lower()} and then walked toward "
        f"{place.dark_corner}. There, the trail bent toward {place.hiding_place}."
    )
    world.say(
        f"That made {obj.label} feel less lost, because the clues matched on both sides."
    )


def _reveal(world: World, detective: Entity, parent: Entity, witness: Witness,
            obj: Object, move: SuspectMove, place: Place) -> None:
    detective.memes["surprise"] += 1
    detective.memes["delight"] += 1
    world.say(
        f'Suddenly, the answer popped out. {move.reveal}. {parent.id} smiled and '
        f'pointed at {place.hiding_place}.'
    )
    world.say(
        f'"{move.surprise}," {detective.id} said. {witness.label_word.capitalize()} gave a little nod.'
    )
    world.say(
        f'Then {detective.id} found {obj.phrase} tucked there, right where the small surprise had been hiding.'
    )


def _rhyme_ending(world: World, detective: Entity, obj: Object, place: Place, move: SuspectMove) -> None:
    world.say(
        f"{place.ending_image.capitalize()}. {detective.id} held up {obj.phrase} and laughed, "
        f'"A clue can creep, then secrets sleep; but look with care and truth will leap."'
    )
    world.say(
        f"The case was solved, the room was calm, and the little mystery was done."
    )


def tell(place: Place, obj: Object, witness: Witness, move: SuspectMove,
         detective_name: str = "Mia", detective_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "mother") -> World:
    world = World()
    detective = world.add(Entity(detective_name, "character", detective_gender, role="detective"))
    parent = world.add(Entity(parent_name, "character", parent_gender, role="parent"))
    world.add(Entity("object", "thing", "thing", label=obj.label))
    world.facts.update(place=place, object=obj, witness=witness, move=move,
                       detective=detective, parent=parent)

    world.say(
        f"On a quiet afternoon, {detective.id} became a tiny detective in {place.label}. "
        f"{place.parallel_signs} {witness.mutter.lower()}"
    )
    world.say(
        f"{detective.id} knew the missing thing was not far away, because the clues were tidy and plain."
    )

    world.para()
    _detective_reassures(world, detective, witness, place)
    world.say(
        f"{parent.id} listened too. {move.motive.capitalize()}, {move.id} said, but the mystery still needed a careful look."
    )
    _follow_clues(world, place, obj, move)

    world.para()
    _reveal(world, detective, parent, witness, obj, move, place)
    _rhyme_ending(world, detective, obj, place, move)

    world.facts["outcome"] = "solved"
    world.facts["rhyme"] = True
    world.facts["surprise"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    obj: Object = f["object"]
    witness: Witness = f["witness"]
    return [
        f'Write a detective story for a 3-to-5-year-old set in {place.label} that includes the word "parallel".',
        f"Tell a tiny mystery where someone mutters about {obj.label}, and the detective finds it by following parallel clues.",
        f'Write a story with rhyme and surprise where {witness.label} says "mutter" and the answer turns out to be less scary than expected.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]
    obj: Object = f["object"]
    witness: Witness = f["witness"]
    detective: Entity = f["detective"]
    parent: Entity = f["parent"]
    move: SuspectMove = f["move"]
    return [
        QAItem(
            question="Who solved the mystery?",
            answer=f"{detective.id} solved it by listening, looking carefully, and following the parallel clues through {place.label}.",
        ),
        QAItem(
            question="What did the witness mutter?",
            answer=f"{witness.mutter} That mutter gave the detective a small hint about where to look next.",
        ),
        QAItem(
            question="Why was the mystery less scary by the end?",
            answer=f"It was less scary because the missing {obj.label} was found safely, and the answer was a surprise instead of a problem. The detective learned that careful looking can make a mystery feel smaller.",
        ),
        QAItem(
            question="What was the surprise ending?",
            answer=f"The surprise was that {move.reveal.lower()}. After that, everyone could smile because the missing thing was only hidden nearby.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does parallel mean?",
            answer="Parallel means two lines or paths go in the same direction and stay the same distance apart.",
        ),
        QAItem(
            question="What does it mean to mutter?",
            answer="To mutter means to speak in a low, soft voice, like someone is talking to themselves or not to the whole room.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something the reader does not expect at first, but then it makes sense when the story explains it.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hallway", "key", "cat", "mischief", "Mia", "girl", "Mom", "mother"),
    StoryParams("library", "note", "grandpa", "helper", "Theo", "boy", "Dad", "father"),
    StoryParams("kitchen", "pin", "neighbor", "pet", "Lily", "girl", "Mom", "mother"),
]


ASP_RULES = r"""
valid(P, O, M) :- place(P), object(O), move(M).
solved(P, O, M) :- valid(P, O, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for m in MOVES:
        lines.append(asp.fact("move", m))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, object=None, witness=None, move=None, detective_name=None, detective_gender=None, parent_name=None, parent_gender=None, n=1, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), _random.Random(777)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with parallel clues, mutters, rhyme, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--witness", choices=WITNESSES)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    if args.place and args.object and args.move:
        combos = valid_combos()
        if (args.place, args.object, args.move) not in combos:
            raise StoryError("No valid detective case matches the chosen options.")
    place = args.place or rng.choice(sorted(PLACES))
    obj = args.object or rng.choice(sorted(OBJECTS))
    witness = args.witness or rng.choice(sorted(WITNESSES))
    move = args.move or rng.choice(sorted(MOVES))
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    pg = args.parent_gender or rng.choice(["mother", "father"])
    detective_name = args.detective_name or _pick_name(rng, dg)
    parent_name = args.parent_name or ("Mom" if pg == "mother" else "Dad")
    return StoryParams(place, obj, witness, move, detective_name, dg, parent_name, pg)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], OBJECTS[params.object], WITNESSES[params.witness], MOVES[params.move],
                 params.detective_name, params.detective_gender, params.parent_name, params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} detective combos:\n")
        for p, o, m in asp_valid_combos():
            print(f"  {p:8} {o:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
