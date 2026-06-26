#!/usr/bin/env python3
"""
storyworlds/worlds/orphan_magic_fairy_tale.py
=============================================

A tiny fairy-tale story world about an orphan, a small magical problem, and a
kind resolution that changes the child's world.

Premise:
- An orphan child lives with a plain life and one precious wish.
- A magical object or helper makes that wish possible, but only if the child
  learns a gentle rule.

The world is intentionally small and constraint-checked:
- physical state is tracked with meters
- emotional state is tracked with memes
- the story is built from simulated causality, not a frozen template
- a Python reasonableness gate is mirrored by inline ASP rules

This world is designed to stay close to fairy-tale style: soft language, a
single clear problem, a magical turn, and an ending image that proves change.
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


# ---------------------------------------------------------------------------
# Small domain model
# ---------------------------------------------------------------------------
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
    magical: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "shine": 0.0, "ruin": 0.0}
        if not self.memes:
            self.memes = {"longing": 0.0, "hope": 0.0, "fear": 0.0, "joy": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter", "princess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son", "prince"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str
    holds_magic: bool = False
    open_sky: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
    danger: str
    requires: str
    gives: str


@dataclass
class StoryParams:
    place: str
    magic: str
    treasure: str
    name: str
    gender: str
    guardian: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "cottage": Place(name="the little cottage", kind="cottage", affords={"seek", "garden"}),
    "forest": Place(name="the moonlit forest", kind="forest", open_sky=True, holds_magic=True, affords={"seek", "glade"}),
    "well": Place(name="the wishing well", kind="well", holds_magic=True, affords={"wish"}),
    "garden": Place(name="the rose garden", kind="garden", open_sky=True, holds_magic=True, affords={"seek"}),
}

MAGICS = {
    "lantern": MagicItem(
        id="lantern",
        label="silver lantern",
        phrase="a silver lantern with a warm pearl inside",
        effect="shone",
        danger="its light could fade if it was used for selfish wishes",
        requires="kindness",
        gives="a safe light",
    ),
    "key": MagicItem(
        id="key",
        label="golden key",
        phrase="a golden key with star teeth",
        effect="opened",
        danger="it would turn cold if it was forced",
        requires="patience",
        gives="a hidden door",
    ),
    "seed": MagicItem(
        id="seed",
        label="magic seed",
        phrase="a tiny magic seed in a blue cloth",
        effect="grew",
        danger="it would wither if it was planted without care",
        requires="gentleness",
        gives="a blossoming tree",
    ),
}

TREASURES = {
    "cloak": {"label": "cloak", "phrase": "a soft blue cloak", "region": "shoulders"},
    "shoes": {"label": "shoes", "phrase": "little red shoes", "region": "feet", "plural": True},
    "crown": {"label": "crown", "phrase": "a tiny glass crown", "region": "head"},
}

GIRL_NAMES = ["Elin", "Mira", "Lena", "Tia", "Nora", "Iris"]
BOY_NAMES = ["Oren", "Pip", "Milo", "Rune", "Evan", "Silas"]
GUARDIANS = ["a kind widow", "a woodcutter", "a baker", "an old gardener"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def treasure_at_risk(place: Place, treasure_id: str, magic_id: str) -> bool:
    if treasure_id == "crown":
        return place.kind in {"forest", "garden", "well"}
    if treasure_id == "cloak":
        return place.holds_magic
    if treasure_id == "shoes":
        return place.open_sky or place.kind == "forest"
    return False


def compatible_fix(place: Place, treasure_id: str, magic_id: str) -> bool:
    if not treasure_at_risk(place, treasure_id, magic_id):
        return False
    item = MAGICS[magic_id]
    if treasure_id == "cloak":
        return magic_id in {"lantern", "seed"}
    if treasure_id == "shoes":
        return magic_id in {"seed", "lantern"}
    if treasure_id == "crown":
        return magic_id in {"key", "lantern"}
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for pid, place in PLACES.items():
        for mid in MAGICS:
            for tid in TREASURES:
                if compatible_fix(place, tid, mid):
                    out.append((pid, mid, tid))
    return out


def explain_rejection(place: Place, treasure_id: str, magic_id: str) -> str:
    treasure = TREASURES[treasure_id]
    magic = MAGICS[magic_id]
    return (
        f"(No story: {magic.label} does not make a fair match for {treasure['label']} "
        f"at {place.name}. The magic must truly protect what is at risk.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(P,T,M) :- place(P), treasure(T), magic(M), risk(P,T,M).
fix(P,T,M) :- at_risk(P,T,M), compatible(M,T).
valid_story(P,T,M) :- fix(P,T,M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.holds_magic:
            lines.append(asp.fact("magic_place", pid))
        if place.open_sky:
            lines.append(asp.fact("open_sky", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for pid, place in PLACES.items():
        for mid in MAGICS:
            for tid in TREASURES:
                if treasure_at_risk(place, tid, mid):
                    lines.append(asp.fact("risk", pid, tid, mid))
                if compatible_fix(place, tid, mid):
                    lines.append(asp.fact("compatible", mid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def make_hero(world: World, name: str, gender: str) -> Entity:
    kind = "girl" if gender == "girl" else "boy"
    hero = world.add(Entity(id=name, kind="character", type=kind))
    hero.memes["longing"] = 1.0
    hero.memes["hope"] = 0.5
    return hero


def simulate(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = make_hero(world, params.name, params.gender)
    guardian = world.add(Entity(id="guardian", kind="character", type="adult"))
    treasure_info = TREASURES[params.treasure]
    treasure = world.add(
        Entity(
            id="treasure",
            type=params.treasure,
            label=treasure_info["label"],
            phrase=treasure_info["phrase"],
            owner=hero.id,
            caretaker=guardian.id,
            plural=bool(treasure_info.get("plural", False)),
        )
    )
    magic = world.add(
        Entity(
            id="magic",
            type=params.magic,
            label=MAGICS[params.magic].label,
            phrase=MAGICS[params.magic].phrase,
            magical=True,
        )
    )
    world.facts.update(hero=hero, guardian=guardian, treasure=treasure, magic=magic, place=place)

    # Act 1
    world.say(
        f"Once upon a time, there was an orphan named {hero.id} who lived near {place.name}."
    )
    world.say(
        f"{hero.id} had no mother or father at home, but {hero.pronoun('possessive')} heart still held one bright wish."
    )
    world.say(
        f"{hero.id} treasured {treasure.phrase}, and {hero.pronoun('possessive')} little life felt less lonely when {treasure.it()} was near."
    )

    # Act 2
    world.para()
    if params.place == "well":
        world.say(
            f"One day, {hero.id} stood beside {place.name} and found {magic.phrase} waiting in the moss."
        )
    else:
        world.say(
            f"One quiet day, {hero.id} went into {place.name} and found {magic.phrase} glimmering in the grass."
        )
    world.say(
        f"The {magic.label} {MAGICS[params.magic].effect} softly, but it could only help if {hero.id} used it with {MAGICS[params.magic].requires}."
    )
    world.say(
        f"{hero.id} wanted to use it at once, because {hero.pronoun('possessive')} wish for {treasure.label} was so strong."
    )
    hero.memes["fear"] += 1.0

    if treasure_at_risk(place, params.treasure, params.magic):
        treasure.meters["ruin"] += 1.0
        hero.memes["fear"] += 0.5
        guardian.memes["concern"] = 1.0
        world.say(
            f"But the old hush of the place warned that {treasure.phrase} could be lost if the magic was rushed."
        )
        world.say(
            f"{hero.id} looked down and began to worry that hope might turn into ruin."
        )

    # Act 3
    world.para()
    if compatible_fix(place, params.treasure, params.magic):
        hero.memes["trust"] += 1.0
        hero.memes["hope"] += 1.0
        hero.memes["joy"] += 1.0
        treasure.meters["shine"] += 1.0
        treasure.meters["ruin"] = 0.0
        world.say(
            f"Then {hero.id}'s guardian came near and said, 'Use it gently, and the magic will keep what you love safe.'"
        )
        world.say(
            f"So {hero.id} listened, and the {magic.label} answered kindly."
        )
        if params.treasure == "cloak":
            world.say(
                f"The blue cloak stayed smooth and bright, and a warm light settled over {hero.id}'s shoulders."
            )
        elif params.treasure == "shoes":
            world.say(
                f"The little red shoes stayed dry and neat, and {hero.id} stepped out as if the path itself were cheering."
            )
        else:
            world.say(
                f"The tiny glass crown remained clear, and {hero.id} walked on as though the stars had chosen {hero.pronoun('object')}."
            )
        world.say(
            f"In the end, {hero.id} was not only an orphan with a wish; {hero.pronoun().capitalize()} was a child with a little magic, a kind guardian, and a brave heart."
        )
    else:
        world.say(
            f"But the magic and the treasure did not fit together kindly, so the tale stopped before harm could be done."
        )

    world.facts.update(
        resolved=compatible_fix(place, params.treasure, params.magic),
        risk=treasure_at_risk(place, params.treasure, params.magic),
        place_id=params.place,
        magic_id=params.magic,
        treasure_id=params.treasure,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    treasure = f["treasure"]
    magic = f["magic"]
    return [
        f'Write a short fairy tale for a child about an orphan named {hero.id}, a {magic.label}, and {treasure.label}.',
        f"Tell a gentle story where {hero.id} finds {magic.phrase} and learns to protect {treasure.phrase}.",
        f"Write a simple story with magic, an orphan, and a happy ending in which {treasure.label} stays safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    treasure: Entity = f["treasure"]
    magic: Entity = f["magic"]
    place: Place = f["place"]
    guardian: Entity = f["guardian"]

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about an orphan named {hero.id} who lives near {place.name}.",
        ),
        QAItem(
            question=f"What did {hero.id} treasure?",
            answer=f"{hero.id} treasured {treasure.phrase} and kept {treasure.it()} close.",
        ),
        QAItem(
            question=f"What magical thing did {hero.id} find?",
            answer=f"{hero.id} found {magic.phrase}. It was a {magic.label} that could help if used with care.",
        ),
        QAItem(
            question=f"Who helped {hero.id} use the magic safely?",
            answer=f"{hero.id}'s guardian helped by reminding {hero.pronoun('object')} to use the magic gently.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    magic: Entity = f["magic"]
    treasure: Entity = f["treasure"]
    items: list[QAItem] = [
        QAItem(
            question="What does an orphan mean?",
            answer="An orphan is a child whose mother and father are gone or not there to care for them at home.",
        ),
        QAItem(
            question=f"What does it mean if something is magical like {magic.label}?",
            answer="Something magical can do unusual or wonder-filled things that ordinary things cannot do.",
        ),
        QAItem(
            question=f"Why should someone care for {treasure.label} carefully?",
            answer=f"{treasure.label.capitalize()} should be cared for carefully because gentle handling helps it stay safe and beautiful.",
        ),
    ]
    return items


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
        if e.magical:
            bits.append("magical=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="forest", magic="lantern", treasure="cloak", name="Elin", gender="girl", guardian="kind widow"),
    StoryParams(place="garden", magic="seed", treasure="shoes", name="Milo", gender="boy", guardian="woodcutter"),
    StoryParams(place="well", magic="key", treasure="crown", name="Nora", gender="girl", guardian="baker"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale world about an orphan and a little magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.magic and args.treasure:
        if not compatible_fix(PLACES[args.place], args.treasure, args.magic):
            raise StoryError(explain_rejection(PLACES[args.place], args.treasure, args.magic))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.magic is None or c[1] == args.magic)
        and (args.treasure is None or c[2] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, magic, treasure = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(GUARDIANS)
    return StoryParams(place=place, magic=magic, treasure=treasure, name=name, gender=gender, guardian=guardian)


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.magic} with {p.treasure} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
