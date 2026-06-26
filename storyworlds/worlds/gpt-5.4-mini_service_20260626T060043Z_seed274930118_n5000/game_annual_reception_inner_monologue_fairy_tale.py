#!/usr/bin/env python3
"""
storyworlds/worlds/game_annual_reception_inner_monologue_fairy_tale.py
======================================================================

A small fairy-tale story world about an annual reception where a child longs
to play a game, worries in secret, and finds a kinder way to join the feast of
the evening.

Seed image:
---
Every year, the king and queen held an annual reception in the lantern hall.
A young page named Mira loved the reception game, a quiet game of cards played
after supper. But when the trumpeter lost the silver deck, Mira's inner
monologue turned to worry: without the cards, the game could not begin. She
searched the hall, followed her thoughts, and found the deck tucked inside a
harp case. The game began, and Mira felt brave enough to smile at the bright
hall at last.

Design notes:
---
- Physical state tracks small items, rooms, and hidden objects in meters.
- Emotional state tracks worry, hope, pride, and delight in memes.
- The story is generated from a causal simulation, not a frozen template.
- Inner monologue is rendered as private thoughts that change as the world
  changes.
- The story remains child-facing and fairy-tale flavored.
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
    hidden_in: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman"}
        male = {"boy", "prince", "king", "father", "man", "trumpeter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Hall:
    name: str
    reception_kind: str = "annual reception"
    game_kind: str = "cards"
    rooms: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str = "lantern hall"
    hero_name: str = "Mira"
    hero_type: str = "girl"
    host_name: str = "the queen"
    helper_name: str = "the trumpeter"
    seed: Optional[int] = None


class World:
    def __init__(self, hall: Hall) -> None:
        self.hall = hall
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.hall)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = [[]]
        w.facts = dict(self.facts)
        return w


def thought(entity: Entity, text: str) -> str:
    return f'“{text},” thought {entity.id}.'


def result_text(entity: Entity) -> str:
    return f"{entity.id} could feel {entity.pronoun('possessive')} heart grow lighter."


def setup_world(params: StoryParams) -> World:
    hall = Hall(name=params.place, rooms=["court table", "music alcove", "curtain nook"])
    world = World(hall)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    host = world.add(Entity(id="Host", kind="character", type="queen", label=params.host_name))
    helper = world.add(Entity(id="Helper", kind="character", type="trumpeter", label=params.helper_name))
    deck = world.add(Entity(
        id="Deck",
        type="thing",
        label="silver deck of cards",
        phrase="a silver deck of cards",
        owner=hero.id,
        held_by=helper.id,
        meters={"hidden": 0.0, "found": 0.0, "ready": 0.0},
        memes={"worry": 0.0},
    ))
    world.add(Entity(
        id="Lantern",
        type="thing",
        label="lantern",
        phrase="a round lantern",
        meters={"lit": 1.0},
    ))
    world.add(Entity(
        id="HarpCase",
        type="thing",
        label="harp case",
        phrase="a tall harp case",
        meters={"closed": 1.0},
    ))
    world.facts.update(hero=hero, host=host, helper=helper, deck=deck)
    return world


def _r_loss(world: World) -> list[str]:
    out = []
    deck = world.get("Deck")
    if deck.held_by == "Helper" and world.facts.get("reception_began") and deck.hidden_in is None:
        sig = ("loss",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        deck.held_by = None
        deck.hidden_in = "HarpCase"
        deck.meters["hidden"] = 1.0
        out.append("The silver deck was nowhere to be seen.")
    return out


def _r_discovery(world: World) -> list[str]:
    out = []
    deck = world.get("Deck")
    hero = world.get(world.facts["hero"].id)
    if hero.memes.get("resolve", 0.0) < THRESHOLD:
        return []
    if deck.hidden_in == "HarpCase" and deck.meters.get("found", 0.0) < THRESHOLD:
        sig = ("found",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        deck.meters["found"] = 1.0
        deck.hidden_in = None
        deck.held_by = hero.id
        hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
        out.append("Inside the harp case, the deck glittered like moonlight.")
    return out


def _r_ready(world: World) -> list[str]:
    out = []
    deck = world.get("Deck")
    hero = world.get(world.facts["hero"].id)
    if deck.held_by != hero.id:
        return []
    if deck.meters.get("ready", 0.0) >= THRESHOLD:
        return []
    sig = ("ready",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    deck.meters["ready"] = 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    out.append("The cards were ready for the game at last.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_loss, _r_discovery, _r_ready):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def introduce(world: World) -> None:
    hero = world.facts["hero"]
    world.say(f"{hero.id} lived in the lantern hall and loved the annual reception game.")
    world.say(f"Every year, the hall shimmered with candles, ribbons, and careful laughter.")
    world.say(thought(hero, "If the cards come out tonight, the room will feel like a storybook"))


def beginning(world: World) -> None:
    hero = world.facts["hero"]
    host = world.facts["host"]
    helper = world.facts["helper"]
    deck = world.facts["deck"]
    world.say(f"On the night of the reception, {host.label} welcomed every guest with a smile.")
    world.say(f"{helper.label} had promised to bring {deck.phrase}, the heart of the game.")
    world.say(f"{hero.id} sat straight as a candle flame and waited.")
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1


def tension(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    deck = world.facts["deck"]
    world.facts["reception_began"] = True
    deck.held_by = helper.id
    propagate(world, narrate=False)
    world.say(f"Then the music paused, and {helper.label} looked under the table, then by the stairs.")
    world.say(f"{helper.label} whispered that the silver deck was gone.")
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    world.say(thought(hero, "Oh dear, if the game cannot begin, the evening will go flat as old bread"))
    world.say(f"{hero.id} stood very still, listening to {hero.pronoun('possessive')} own thoughts.")
    world.say(thought(hero, "I can look quietly. A kind search is still a brave search"))


def search(world: World) -> None:
    hero = world.facts["hero"]
    deck = world.facts["deck"]
    world.say(f"{hero.id} crept from the court table to the music alcove and peered behind the curtain nook.")
    if deck.hidden_in == "HarpCase":
        world.say(f"A narrow shape showed behind the harp case, as if it wanted to be found by a gentle hand.")
    propagate(world)
    if deck.held_by == hero.id:
        world.say(thought(hero, "There you are, little shining secret"))
        world.say(f"{hero.id} carried the deck back to the lantern table with both hands.")


def resolution(world: World) -> None:
    hero = world.facts["hero"]
    host = world.facts["host"]
    deck = world.facts["deck"]
    world.say(f"The {world.hall.game_kind} began at once, and the guests leaned in with bright eyes.")
    world.say(f"{host.label} praised {hero.id} for finding what was lost without making a fuss.")
    world.say(f"{hero.id} dealt the cards, and the room turned warm with the soft tap of play.")
    if deck.meters.get("ready", 0.0) >= THRESHOLD:
        world.say(result_text(hero))
    world.say(f"By the end, the annual reception felt like a spell that had chosen {hero.id} for its helper.")


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    world.para()
    beginning(world)
    world.para()
    tension(world)
    world.para()
    search(world)
    world.para()
    resolution(world)
    world.facts["resolved"] = True
    return world


def validate_params(params: StoryParams) -> None:
    if not params.place:
        raise StoryError("The reception needs a place.")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError("The hero must be a girl or a boy in this world.")
    if not params.hero_name:
        raise StoryError("The hero needs a name.")


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    host = world.facts["host"]
    return [
        f"Write a fairy tale about an annual reception where {hero.id} helps a game begin.",
        f"Tell a child-sized story with inner monologue, a lost deck of cards, and {host.label}.",
        f"Create a gentle fairy tale set at a lantern hall reception with a search and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    host = world.facts["host"]
    helper = world.facts["helper"]
    deck = world.facts["deck"]
    return [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"The story is mostly about {hero.id}, who loves the annual reception game.",
        ),
        QAItem(
            question=f"What was missing when the game was about to start?",
            answer=f"The silver deck of cards was missing, and that made the reception feel shaky for a moment.",
        ),
        QAItem(
            question=f"Who praised {hero.id} at the end?",
            answer=f"{host.label} praised {hero.id} for finding the deck and helping the game begin.",
        ),
        QAItem(
            question=f"Where was the deck found?",
            answer=f"It was found inside the harp case in the lantern hall.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the cards were ready?",
            answer=f"{hero.id} felt proud and happy, because the game could finally begin.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an annual event?",
            answer="An annual event is something that happens once every year.",
        ),
        QAItem(
            question="What is a reception?",
            answer="A reception is a welcoming gathering where guests come together to meet, talk, or celebrate.",
        ),
        QAItem(
            question="What is a game?",
            answer="A game is a playful activity with rules that people do for fun.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the quiet voice of thoughts a character has in their mind.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "lantern hall": "lantern hall",
}

GENDERS = ["girl", "boy"]
GIRL_NAMES = ["Mira", "Nina", "Lena", "Tessa", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Jules", "Arlo"]


ASP_RULES = r"""
% A deck is missing when it has been hidden away.
missing(D) :- deck(D), hidden_in(D, _).

% A hero can restore the game once the deck is found and held by the hero.
ready_for_game(H, D) :- hero(H), deck(D), held_by(D, H), found(D).

% The reception becomes joyful when the game is ready.
joyful_reception(H) :- ready_for_game(H, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "lantern_hall"))
    lines.append(asp.fact("place_name", "lantern_hall", "lantern hall"))
    lines.append(asp.fact("game_kind", "cards"))
    lines.append(asp.fact("reception_kind", "annual reception"))
    lines.append(asp.fact("hero_type", "girl"))
    lines.append(asp.fact("hero_type", "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about an annual reception and a lost game.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    place = args.place or "lantern hall"
    return StoryParams(place=place, hero_name=name, hero_type=gender, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(params)
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show joyful_reception/1."))
    if asp.atoms(model, "joyful_reception"):
        print("OK: ASP twin accepts the reception becoming joyful.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected joyful reception.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show joyful_reception/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show joyful_reception/1."))
        vals = asp.atoms(model, "joyful_reception")
        print(f"{len(vals)} joyful reception result(s).")
        for v in vals:
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="lantern hall", hero_name="Mira", hero_type="girl"),
            StoryParams(place="lantern hall", hero_name="Owen", hero_type="boy"),
            StoryParams(place="lantern hall", hero_name="Lena", hero_type="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
