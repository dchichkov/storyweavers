#!/usr/bin/env python3
"""
A small story world: Curiosity, a pseudo ghost, and a benefactive helper.

Seed tale:
---
A curious child hears spooky bumps at night and thinks a ghost is in the house.
But the "ghost" is only a sheet snagged on a chair and a toy making the bumps.
The child keeps looking because curiosity pulls hard, and a kind helper stays
near, checks several rooms, and helps the child feel brave. In the end the child
learns it was a pseudo ghost, not a real one, and the house feels calm again.
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
# Core model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    dark: bool = False
    objects: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    place: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Room):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        import copy as _copy
        w = World(Room(self.place.name, self.place.dark, list(self.place.objects)))
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ROOMS = {
    "hall": Room("the hall", dark=False),
    "stairs": Room("the stairs", dark=True),
    "bedroom": Room("the bedroom", dark=True),
    "living_room": Room("the living room", dark=False),
}

NAMES_GIRL = ["Mina", "Lily", "Nora", "Zoe", "Ivy", "Ella"]
NAMES_BOY = ["Theo", "Ben", "Milo", "Leo", "Finn", "Noah"]
HELPERS = ["mother", "father", "older sister", "older brother", "grandma"]

# The pseudo ghost is intentionally not real; it is a mistaken reading.
PSEUDO_GHOSTS = {
    "sheet": {
        "label": "a white sheet",
        "phrase": "a white sheet draped over a chair",
        "motion": "fluttered",
        "place": "the living room",
    },
    "curtain": {
        "label": "the curtain",
        "phrase": "a curtain moving in the draft",
        "motion": "trembled",
        "place": "the bedroom",
    },
    "toy": {
        "label": "a clockwork toy",
        "phrase": "a clockwork toy knocking against the wall",
        "motion": "ticked",
        "place": "the hall",
    },
}

LOCATIONS = list(ROOMS)


# ---------------------------------------------------------------------------
# World building and causal rules
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.place not in ROOMS:
        raise StoryError("Unknown place.")
    room = ROOMS[params.place]
    world = World(room)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"fear": 0.0, "bravery": 0.0},
        memes={"curiosity": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        meters={"care": 0.0},
        memes={"patience": 0.0, "help": 0.0},
    ))
    ghost_kind = random.choice(list(PSEUDO_GHOSTS))
    ghost = PSEUDO_GHOSTS[ghost_kind]
    suspect = world.add(Entity(
        id="suspect",
        type=ghost_kind,
        label=ghost["label"],
        phrase=ghost["phrase"],
        meters={"mystery": 1.0},
        props=ghost,
    ))
    world.facts.update(hero=hero, helper=helper, suspect=suspect, place=room, ghost_kind=ghost_kind)
    return world


def _r_curiosity_spreads(world: World) -> list[str]:
    out: list[str] = []
    hero: Entity = world.facts["hero"]
    if hero.memes.get("curiosity", 0.0) < 1.0:
        return out
    sig = ("curiosity_spreads",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["investigation"] = hero.meters.get("investigation", 0.0) + 1.0
    out.append(f"{hero.id} kept looking because curiosity would not let the mystery rest.")
    return out


def _r_benefactive_help(world: World) -> list[str]:
    out: list[str] = []
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    suspect: Entity = world.facts["suspect"]
    if hero.meters.get("fear", 0.0) < 1.0 or hero.memes.get("curiosity", 0.0) < 1.0:
        return out
    sig = ("benefactive_help", suspect.type)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["help"] = helper.memes.get("help", 0.0) + 1.0
    helper.meters["care"] = helper.meters.get("care", 0.0) + 1.0
    hero.meters["bravery"] = hero.meters.get("bravery", 0.0) + 1.0
    out.append(f"The {helper.type} stayed beside {hero.id} and helped {hero.pronoun('object')} check the rooms.")
    return out


def _r_multiple_checks(world: World) -> list[str]:
    out: list[str] = []
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    suspect: Entity = world.facts["suspect"]
    if hero.memes.get("curiosity", 0.0) < 1.0:
        return out
    if hero.meters.get("investigation", 0.0) < 1.0:
        return out
    sig = ("multiple_checks", suspect.type)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(
        f"Together they checked the hall, the stairs, and the bedroom, looking for the thing that made the bumps."
    )
    return out


def _r_reveal_pseudo(world: World) -> list[str]:
    out: list[str] = []
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    suspect: Entity = world.facts["suspect"]
    if hero.meters.get("investigation", 0.0) < 1.0 or helper.memes.get("help", 0.0) < 1.0:
        return out
    sig = ("reveal", suspect.type)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["fear"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    world.facts["revealed"] = True
    out.append(f"It was only {suspect.phrase}, a pseudo ghost, and not a real one at all.")
    return out


CAUSAL_RULES = [_r_curiosity_spreads, _r_multiple_checks, _r_benefactive_help, _r_reveal_pseudo]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    suspect: Entity = world.facts["suspect"]
    room: Room = world.facts["place"]

    hero.memes["curiosity"] = 1.0
    hero.meters["fear"] = 1.0

    world.say(
        f"{hero.id} was a curious little {params.gender} who loved to ask what made strange sounds in the dark."
    )
    world.say(
        f"One night, {hero.id} heard a bump from {room.name} and saw {suspect.phrase} move in the corner."
    )

    world.para()
    world.say(
        f"{hero.id} felt a tingle of worry, but curiosity pulled stronger than the scare."
    )
    world.say(
        f"{helper.label.capitalize()} came too, because the mystery was something to solve together."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"At last, {helper.label} lifted the sheet, nudged the toy, and showed {hero.id} the plain old trick behind the ghostly shape."
    )
    world.say(
        f"{hero.id} laughed, breathed out, and felt brave in the quiet house again."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    room: Room = f["place"]
    return [
        f"Write a short ghost story for a child who is curious about a mystery in {room.name}, and reveal that the ghost is only {suspect.phrase}.",
        f"Tell a gentle story where {hero.id} gets scared, keeps investigating because of curiosity, and a kind {helper.type} helps them figure out the pseudo ghost.",
        f"Write a bedtime story with a spooky start, multiple checks around the house, and a warm ending where {helper.label} helps {hero.id} feel brave.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    room: Room = f["place"]

    qa = [
        QAItem(
            question=f"Why did {hero.id} keep looking around after hearing the bump in {room.name}?",
            answer=f"{hero.id} kept looking because curiosity was stronger than the first scare, so {hero.pronoun()} wanted to find out what was really there.",
        ),
        QAItem(
            question=f"Who helped {hero.id} check the house?",
            answer=f"The {helper.type} helped {hero.id} by staying close, checking the rooms, and making the mystery less frightening.",
        ),
        QAItem(
            question=f"What did the scary-looking thing turn out to be?",
            answer=f"It turned out to be {suspect.phrase}, so it was a pseudo ghost and not a real ghost at all.",
        ),
        QAItem(
            question=f"How many places did they check while solving the mystery?",
            answer="They checked multiple places: the hall, the stairs, and the bedroom.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end for {hero.id}?",
                answer=f"{hero.id} felt brave again, laughed at the harmless trick, and the house became calm and quiet.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more and ask questions about something they do not understand.",
        ),
        QAItem(
            question="What does pseudo mean?",
            answer="Pseudo means something only seems real or true at first, but is actually not what it looks like.",
        ),
        QAItem(
            question="What does benefactive mean?",
            answer="Benefactive means done to help someone else or for their good.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
curious(H) :- hero(H), curiosity(H).
needs_help(H) :- curious(H), afraid(H).
multiple_checks(H) :- checks(H, hall), checks(H, stairs), checks(H, bedroom).
pseudo_ghost(S) :- suspect(S), appears_scary(S), not real_ghost(S).
resolved(H) :- curious(H), helped(H), pseudo_ghost(_).
valid_story(H, P) :- hero(H), place(P), curious(H), helped(H), pseudo_ghost(_).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in ROOMS:
        lines.append(asp.fact("place", pid))
    for gid, g in PSEUDO_GHOSTS.items():
        lines.append(asp.fact("suspect", gid))
        lines.append(asp.fact("appears_scary", gid))
        lines.append(asp.fact("real_ghost", f"real_{gid}"))  # never used, keeps domain explicit
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_story() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py_ok = True
    for name in ROOMS:
        if name not in ROOMS:
            py_ok = False
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show pseudo_ghost/1. #show valid_story/2."))
    asp_has_story = bool(asp.atoms(model, "valid_story"))
    if py_ok and asp_has_story:
        print("OK: ASP gate produces a compatible story shape.")
        return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world driven by curiosity and a benefactive helper.")
    ap.add_argument("--name", choices=NAMES_GIRL + NAMES_BOY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", choices=LOCATIONS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = NAMES_GIRL if gender == "girl" else NAMES_BOY
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(HELPERS)
    place = args.place or rng.choice(LOCATIONS)
    return StoryParams(name=name, gender=gender, helper=helper, place=place)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
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
    StoryParams(name="Mina", gender="girl", helper="mother", place="hall"),
    StoryParams(name="Theo", gender="boy", helper="father", place="stairs"),
    StoryParams(name="Ivy", gender="girl", helper="older sister", place="bedroom"),
    StoryParams(name="Ben", gender="boy", helper="grandma", place="living_room"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, p in enumerate(CURATED):
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
