#!/usr/bin/env python3
"""
A small detective-style storyworld about a child solving a mystery, learning a lesson,
and hearing a tiny SOS that turns out to matter.

Premise:
- A curious child detective notices a missing item or confusing clue.
- A simple search reveals the truth through cause and effect.
- The story ends with a clear lesson learned: looking carefully and asking for help
  solves problems better than rushing.

The world is intentionally small and classical:
- one setting
- one mystery
- one helper or culprit
- one resolution that proves what changed

The prose engine drives off a mutable world model with meters and memes.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool
    hides: set[str] = field(default_factory=set)
    allows: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    found_by: str
    reveals: str
    detail: str


@dataclass
class Mystery:
    id: str
    missing: str
    culprit: str
    clue_chain: list[str]
    lesson: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        clone = World(self.place)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "plural": v.plural, "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _set_meter(e: Entity, key: str, value: float) -> None:
    e.meters[key] = value


def _set_meme(e: Entity, key: str, value: float) -> None:
    e.memes[key] = value


def _add_meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _add_meme(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def _clue_found(world: World, hero: Entity, clue: Clue, mystery: Mystery) -> None:
    sig = ("found", clue.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    _add_meme(hero, "curiosity", 1)
    world.say(
        f"{hero.id} noticed {clue.label}. "
        f"It was a clue that pointed toward {clue.reveals}."
    )
    world.trace.append(f"clue:{clue.id}")


def _solve(world: World, hero: Entity, mystery: Mystery, helper: Entity) -> None:
    sig = ("solve", mystery.id)
    if sig in world.fired:
        return
    if _meter(hero, "clues") < THRESHOLD:
        return
    world.fired.add(sig)
    _set_meme(hero, "relief", _meme(hero, "relief") + 1)
    _set_meme(hero, "lesson", 1)
    world.say(
        f"Then {hero.id} understood the mystery. "
        f"{helper.id} had not stolen anything at all; {mystery.culprit} had simply been "
        f"hidden by a small mix-up."
    )
    world.say(
        f"{hero.id} learned a lesson: when something seems missing, it helps to look carefully, "
        f"follow the clues, and ask for help."
    )


def _sos(world: World, hero: Entity, helper: Entity) -> None:
    sig = ("sos",)
    if sig in world.fired:
        return
    if _meter(helper, "trapped") < THRESHOLD:
        return
    world.fired.add(sig)
    world.say(
        f"Far away, {hero.id} heard a tiny SOS from behind the old box. "
        f"{hero.id} hurried over and called for {helper.id}."
    )
    _add_meme(hero, "helpfulness", 1)


def tell(place: Place, mystery: Mystery, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(place)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        label=hero_name, phrase=f"young detective {hero_name}",
    ))
    helper = world.add(Entity(
        id="Helper", kind="character", type=helper_type, label="the helper",
    ))
    missing = world.add(Entity(
        id="Missing", kind="thing", type="thing", label=mystery.missing,
        phrase=mystery.missing, owner=hero.id,
    ))
    culprit = world.add(Entity(
        id="Culprit", kind="thing", type="thing", label=mystery.culprit,
        phrase=mystery.culprit, caretaker=helper.id,
    ))
    clue1 = Clue(
        id="clue1",
        label="a muddy footprint",
        found_by=hero.id,
        reveals="the space behind the box",
        detail="mud on the floor",
    )
    clue2 = Clue(
        id="clue2",
        label="a bent ribbon",
        found_by=hero.id,
        reveals="the helper's basket",
        detail="a ribbon caught on the basket handle",
    )

    hero.meters["clues"] = 0.0
    helper.meters["trapped"] = 1.0
    helper.meters["worry"] = 0.0
    hero.memes["curiosity"] = 1.0

    world.say(
        f"One day in {place.name}, {hero.id} was a small detective who loved solving puzzles."
    )
    world.say(
        f"{hero.id} noticed that {missing.label} was missing, and that made {hero.pronoun('object')} frown."
    )

    world.para()
    world.say(
        f"{hero.id} searched the room carefully, because detectives do not guess before they look."
    )
    _clue_found(world, hero, clue1, mystery)
    _add_meter(hero, "clues", 1)
    world.say(
        f"The first clue led {hero.id} near the old box, where something seemed stuck."
    )
    _sos(world, hero, helper)

    world.para()
    world.say(
        f"Inside the helper's basket, {hero.id} found {clue2.label}."
    )
    _clue_found(world, hero, clue2, mystery)
    _add_meter(hero, "clues", 1)
    _set_meter(helper, "trapped", 0.0)
    world.say(
        f"After {hero.id} moved the basket aside, {helper.id} could finally stand up."
    )
    _solve(world, hero, mystery, helper)

    world.facts.update(
        hero=hero,
        helper=helper,
        missing=missing,
        culprit=culprit,
        mystery=mystery,
        clues=[clue1, clue2],
    )
    return world


PLACES = {
    "library": Place(
        name="the library",
        indoors=True,
        hides={"behind shelves", "under tables", "inside baskets"},
        allows={"search", "whisper", "read"},
    ),
    "classroom": Place(
        name="the classroom",
        indoors=True,
        hides={"behind a box", "under a desk", "inside a bin"},
        allows={"search", "whisper", "look"},
    ),
    "kitchen": Place(
        name="the kitchen",
        indoors=True,
        hides={"inside a basket", "behind jars", "under the table"},
        allows={"search", "open", "ask"},
    ),
}

MYSTERIES = {
    "missing_cookie": Mystery(
        id="missing_cookie",
        missing="the cookie tin",
        culprit="the cookie tin lid",
        clue_chain=["muddy footprint", "bent ribbon"],
        lesson="look carefully before accusing",
    ),
    "lost_bell": Mystery(
        id="lost_bell",
        missing="the little bell",
        culprit="the bell under the cushion",
        clue_chain=["muddy footprint", "bent ribbon"],
        lesson="follow clues one by one",
    ),
    "hidden_key": Mystery(
        id="hidden_key",
        missing="the tiny key",
        culprit="the key under the basket",
        clue_chain=["muddy footprint", "bent ribbon"],
        lesson="ask for help when the search feels stuck",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Sam", "Finn"]
HELPERS = ["mother", "father", "teacher", "brother", "sister"]
TRAITS = ["careful", "brave", "curious", "quiet", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in PLACES for m in MYSTERIES]


@dataclass
class _AspKey:
    place: str
    mystery: str


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style storyworld with a tiny mystery and lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.place and args.mystery:
        if (args.place, args.mystery) not in valid_combos():
            raise StoryError("No reasonable detective story matches that combination.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f"Write a short detective story about {hero.id} solving a small mystery in {world.place.name}.",
        f"Tell a child-friendly story where a tiny SOS leads {hero.id} to a hidden clue and a lesson learned.",
        f"Create a mystery to solve story with {hero.id}, {mystery.missing}, and a careful search.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    qas = [
        QAItem(
            question=f"What kind of story is this about {hero.id} in {world.place.name}?",
            answer=f"It is a detective story about {hero.id} solving a small mystery in {world.place.name}.",
        ),
        QAItem(
            question=f"What was missing at the start of the story?",
            answer=f"{mystery.missing.capitalize()} was missing, and that is why {hero.id} began searching.",
        ),
        QAItem(
            question=f"What did the tiny SOS help {hero.id} do?",
            answer=f"The tiny SOS helped {hero.id} find {helper.id} and discover that the clue was hidden near the old box.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned to look carefully, follow clues one by one, and ask for help instead of guessing.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues to solve a mystery.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does SOS mean?",
            answer="SOS is a simple distress signal that means someone needs help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  trace: {world.trace}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- case(M).

valid(P, M) :- setting(P), case(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("case", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - asps:
        print("only python:", sorted(py - asps))
    if asps - py:
        print("only asp:", sorted(asps - py))
    return 1


CURATED = [
    StoryParams(place="library", mystery="missing_cookie", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="classroom", mystery="lost_bell", name="Leo", gender="boy", helper="teacher"),
    StoryParams(place="kitchen", mystery="hidden_key", name="Ava", gender="girl", helper="father"),
]


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = tell(place, mystery, params.name, "girl" if params.gender == "girl" else "boy", params.helper)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
