#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T034914Z_seed1855084837_n10/occupy_tennis_friendship_happy_ending_fable.py
=========================================================================================================================

A small fable-style story world about a place, a tennis court, and a friendship
that learns how to share an occupied space. The world keeps physical state in
meters and emotional state in memes, then renders a complete child-facing story
from that state.

The seed request asks for:
- words: occupy, tennis
- features: Friendship, Happy Ending
- style: Fable

This world models a simple problem: two friends want to use the same tennis court
at the same time. One may occupy it first, but a kind compromise can turn the
situation into a shared game and a happy ending.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    partner: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fox"}
        male = {"boy", "father", "dad", "man", "rabbit"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Court:
    id: str
    label: str
    phrase: str
    occupies: str
    can_share: bool = True
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
class Game:
    id: str
    label: str
    phrase: str
    action: str
    return_phrase: str
    gear: str
    risk: str
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
class Compromise:
    id: str
    label: str
    phrase: str
    method: str
    ending: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    court: str
    game: str
    compromise: str
    hero: str
    friend: str
    hero_type: str
    friend_type: str
    narrator: str
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


COURTS = {
    "park_court": Court(
        id="park_court",
        label="the little tennis court",
        phrase="a sunny tennis court behind the park",
        occupies="the whole court",
        can_share=True,
        tags={"tennis", "court", "share"},
    ),
    "school_court": Court(
        id="school_court",
        label="the school tennis court",
        phrase="a bright tennis court near the school",
        occupies="the court",
        can_share=True,
        tags={"tennis", "court", "school"},
    ),
}

GAMES = {
    "tennis": Game(
        id="tennis",
        label="tennis",
        phrase="play tennis",
        action="serve the ball and run for the next shot",
        return_phrase="the ball bounced back and forth",
        gear="rackets",
        risk="one friend might feel left out",
        tags={"tennis", "ball", "racket"},
    ),
}

COMPROMISES = {
    "switch": Compromise(
        id="switch",
        label="take turns",
        phrase="take turns on the court",
        method="one friend serves while the other returns, then they switch",
        ending="they both got a fair chance to play",
        tags={"share", "turns", "friendship"},
    ),
    "doubles": Compromise(
        id="doubles",
        label="play doubles",
        phrase="play doubles together",
        method="they each guarded one side and traded the returns like a team",
        ending="the game felt more like friendship than competition",
        tags={"share", "friendship", "team"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Zoe", "Ivy"]
BOY_NAMES = ["Leo", "Noah", "Eli", "Sam", "Max", "Toby"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for court in COURTS:
        for game in GAMES:
            for compromise in COMPROMISES:
                combos.append((court, game, compromise))
    return combos


def select_names(rng: random.Random) -> tuple[str, str, str, str]:
    hero_type = rng.choice(["girl", "boy"])
    friend_type = rng.choice(["girl", "boy"])
    hero_pool = GIRL_NAMES if hero_type == "girl" else BOY_NAMES
    friend_pool = GIRL_NAMES if friend_type == "girl" else BOY_NAMES
    hero = rng.choice(hero_pool)
    friend = rng.choice([n for n in friend_pool if n != hero] or friend_pool)
    return hero, friend, hero_type, friend_type


def explain_rejection(court: Court, game: Game) -> str:
    return f"(No story: {game.label} does not fit this court as a meaningful shared fable.)"


def tell(court: Court, game: Game, compromise: Compromise, hero: str, friend: str,
         hero_type: str, friend_type: str, narrator: str) -> World:
    world = World()
    a = world.add(Entity(
        id=hero,
        kind="character",
        type=hero_type,
        role="hero",
        traits=["kind", "curious"],
    ))
    b = world.add(Entity(
        id=friend,
        kind="character",
        type=friend_type,
        role="friend",
        traits=["kind", "patient"],
    ))
    place = world.add(Entity(
        id=court.id,
        kind="place",
        type="place",
        label=court.label,
        phrase=court.phrase,
        owner="none",
        attrs={"occupies": court.occupies, "can_share": court.can_share},
    ))
    ball = world.add(Entity(
        id="ball",
        kind="thing",
        type="ball",
        label="the tennis ball",
        phrase="a tennis ball",
        plural=False,
    ))
    rackets = world.add(Entity(
        id="rackets",
        kind="thing",
        type="gear",
        label="their rackets",
        phrase="two small rackets",
        plural=True,
        owner=hero,
        partner=friend,
    ))

    a.memes["wish"] += 1
    b.memes["wish"] += 1
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    place.meters["occupied"] += 1

    world.say(f"Once there was a little court that could fit a gentle game of tennis.")
    world.say(f"On a bright morning, {hero} and {friend} came to {place.label} with {rackets.phrase}.")
    world.say(f"{hero} loved to {game.phrase}, and {friend} loved it too.")
    world.say(f"But the court was already occupied, and that made the day feel tight.")

    world.para()
    a.memes["want"] += 1
    b.memes["worry"] += 1
    world.say(f"{hero} wanted to claim {court.occupies} at once, but {friend} did not want a quarrel.")
    world.say(f"{game.label.capitalize()} can be a fine game, yet it is kinder when two friends share it.")
    world.say(f"{hero} looked at the ball, then at {friend}, and the first wish grew softer.")

    world.para()
    place.meters["shared"] += 1
    a.memes["warmth"] += 1
    b.memes["warmth"] += 1
    world.say(f'Then {friend} smiled and said, "Let us {compromise.label}."')
    world.say(f'They chose to {compromise.phrase}, and {compromise.method}.')
    world.say(f"The ball flew one way and then the other, and both friends laughed as if the court had opened its arms.")

    world.para()
    place.meters["occupied"] = 0
    place.meters["shared"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(f"By the end, the court was no longer a place to fight over.")
    world.say(f"It was a place where friendship lived, and {game.label} became part of the happy ending.")
    world.say(f"{hero} and {friend} left together, carrying their rackets and a cheerful promise to return.")

    world.facts.update(
        hero=a,
        friend=b,
        court=place,
        court_cfg=court,
        game=game,
        compromise=compromise,
        ball=ball,
        rackets=rackets,
        narrator=narrator,
        shared=place.meters["shared"] >= THRESHOLD,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    court: Court = f["court_cfg"]
    game: Game = f["game"]
    comp: Compromise = f["compromise"]
    return [
        f"Write a fable about {hero.id} and {friend.id} at {court.label} where they want to {game.phrase} and learn to share.",
        f"Tell a gentle friendship story using the words occupy and tennis, and end with {comp.label}.",
        f"Write a happy-ending fable where two children are kind on {court.label} and {game.label} becomes a shared game.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    court: Entity = f["court"]
    game: Game = f["game"]
    comp: Compromise = f["compromise"]
    return [
        QAItem(
            question=f"Who were the story's two friends at {court.label}?",
            answer=f"The story was about {hero.id} and {friend.id}. They both wanted to enjoy {game.label} and found a kinder way to share the court.",
        ),
        QAItem(
            question=f"Why did the word occupy matter at the tennis court?",
            answer=f"It mattered because one friend was taking up the court first. That made the other friend pause, and the pause opened the door to a shared plan.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} keep the tennis day friendly?",
            answer=f"They used {comp.label} and chose to share the game instead of arguing. That turned the crowded court into a cheerful place for both of them.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tennis?",
            answer="Tennis is a game where players hit a ball back and forth with rackets. It is fun to play with a friend because turns matter.",
        ),
        QAItem(
            question="What does it mean to occupy a place?",
            answer="To occupy a place means to be using it or taking up space there. If a place is occupied, someone may need to wait or share.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other and act kindly. Friends listen, share, and try to make things fair.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.kind == "place":
            bits.append(f"attrs={e.attrs}")
        lines.append(f"{e.id}: {e.kind} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in COURTS:
        lines.append(asp.fact("court", cid))
        lines.append(asp.fact("can_share", cid))
    for gid in GAMES:
        lines.append(asp.fact("game", gid))
    for pid in COMPROMISES:
        lines.append(asp.fact("compromise", pid))
        lines.append(asp.fact("friendship", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(C,G,P) :- court(C), game(G), compromise(P).
shared(C) :- court(C), can_share(C).
happy_end(C,G,P) :- valid(C,G,P), shared(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    sample = generate(resolve_params(argparse.Namespace(court=None, game=None, compromise=None, hero=None, friend=None, hero_type=None, friend_type=None, narrator=None), random.Random(7)))
    _ = sample.story
    if ok:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        print("OK: generation smoke test succeeded.")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about occupy, tennis, friendship, and a happy ending.")
    ap.add_argument("--court", choices=COURTS)
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--compromise", choices=COMPROMISES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = [c for c in valid_combos()
              if (args.court is None or c[0] == args.court)
              and (args.game is None or c[1] == args.game)
              and (args.compromise is None or c[2] == args.compromise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    court, game, compromise = rng.choice(sorted(combos))
    hero, friend, hero_type, friend_type = select_names(rng)
    if args.hero:
        hero = args.hero
    if args.friend:
        friend = args.friend
    if args.hero_type:
        hero_type = args.hero_type
    if args.friend_type:
        friend_type = args.friend_type
    narrator = rng.choice(["owl", "mole", "sparrow"])
    return StoryParams(
        court=court,
        game=game,
        compromise=compromise,
        hero=hero,
        friend=friend,
        hero_type=hero_type,
        friend_type=friend_type,
        narrator=narrator,
    )


def generate(params: StoryParams) -> StorySample:
    if params.court not in COURTS or params.game not in GAMES or params.compromise not in COMPROMISES:
        raise StoryError("Invalid params.")
    world = tell(COURTS[params.court], GAMES[params.game], COMPROMISES[params.compromise],
                 params.hero, params.friend, params.hero_type, params.friend_type, params.narrator)
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


CURATED = [
    StoryParams(court="park_court", game="tennis", compromise="switch", hero="Mia", friend="Leo", hero_type="girl", friend_type="boy", narrator="owl"),
    StoryParams(court="school_court", game="tennis", compromise="doubles", hero="Ava", friend="Nora", hero_type="girl", friend_type="girl", narrator="sparrow"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(t) for t in asp_valid_combos()))
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
