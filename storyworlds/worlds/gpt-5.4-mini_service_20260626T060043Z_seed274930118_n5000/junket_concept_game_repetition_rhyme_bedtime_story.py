#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/junket_concept_game_repetition_rhyme_bedtime_story.py
===============================================================================================================================

A small bedtime-story world about a child who wants to play a "concept game"
during a sleepy junket, where repetition and rhyme help the evening settle
into a happy ending.

Seed premise:
- The child and caretaker are on a short junket away from home.
- The child invents a concept game: name things that rhyme.
- The child repeats the same eager request again and again.
- The caretaker worries the game will keep bedtime awake.
- A gentler version of the game becomes a lullaby-like rhythm, and the child
  grows sleepy instead of wound up.

World model:
- Physical meters: energy, sleepiness, distance, tidiness, moonlight
- Emotional memes: excitement, worry, calm, closeness, frustration

The prose is driven by simulation:
- Eager repetition increases excitement and frustration.
- Rhyme, when accepted as a bedtime version of the game, lowers excitement and
  increases calm and sleepiness.
- If the child pushes too hard, the caretaker redirects the game into a soft,
  repeatable rhyme that fits bedtime.

The story always resolves with a proof image: the child asleep, the rhyme
quiet, and the junket ending peacefully.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core domain model
# ---------------------------------------------------------------------------

def _meme_default() -> dict[str, float]:
    return {
        "excitement": 0.0,
        "worry": 0.0,
        "calm": 0.0,
        "closeness": 0.0,
        "frustration": 0.0,
        "delight": 0.0,
    }


def _meter_default() -> dict[str, float]:
    return {
        "energy": 0.0,
        "sleepiness": 0.0,
        "distance": 0.0,
        "tidiness": 0.0,
        "moonlight": 0.0,
    }


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=_meter_default)
    memes: dict[str, float] = field(default_factory=_meme_default)
    plural: bool = False
    asleep: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = True
    moonlit: bool = True


@dataclass
class Game:
    id: str
    concept: str
    repeated_phrase: str
    rhyme_word: str
    soft_phrase: str
    bedtime_phrase: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    game: str
    child_name: str
    child_gender: str
    caretaker_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

PLACES = {
    "cabin": Place("the cabin", indoors=True, moonlit=True),
    "train": Place("the train car", indoors=True, moonlit=False),
    "inn": Place("the little inn", indoors=True, moonlit=True),
    "tent": Place("the cozy tent", indoors=True, moonlit=True),
}

GAMES = {
    "rhyme": Game(
        id="rhyme",
        concept="rhyme words",
        repeated_phrase="say a word and find a word that sounds the same at the end",
        rhyme_word="moon",
        soft_phrase="moon, spoon, tune",
        bedtime_phrase="moon, tune, soon",
        risk="keep the child too awake",
        tags={"rhyme", "bedtime", "repetition"},
    ),
    "concept": Game(
        id="concept",
        concept="make a simple concept game",
        repeated_phrase="name a thing and tell what kind of thing it is",
        rhyme_word="nest",
        soft_phrase="nest, rest, best",
        bedtime_phrase="nest, rest, best",
        risk="make bedtime feel like homework",
        tags={"concept", "repetition", "bedtime"},
    ),
    "junket": Game(
        id="junket",
        concept="play a junket game about the trip",
        repeated_phrase="name the things they saw on the trip",
        rhyme_word="ride",
        soft_phrase="ride, slide, glide",
        bedtime_phrase="ride, slide, glide",
        risk="turn the journey into a noisy game",
        tags={"junket", "repetition", "bedtime"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Theo", "Luna", "Ava", "Finn", "Owen"]
TRAITS = ["curious", "gentle", "playful", "quiet", "bright", "restless"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _repeat_request(world: World, child: Entity, game: Game) -> None:
    child.memes["excitement"] += 1
    child.meters["energy"] += 1
    world.say(
        f'{child.id} kept saying, "{game.repeated_phrase}!" '
        f'Then {child.pronoun().capitalize()} said it again, with even rounder eyes.'
    )


def _caretaker_worries(world: World, caretaker: Entity, child: Entity, game: Game) -> None:
    caretaker.memes["worry"] += 1
    child.memes["frustration"] += 0.5
    world.say(
        f'{caretaker.pronoun().capitalize()} smiled, but {caretaker.pronoun("possessive")} '
        f"heart grew thoughtful. That kind of {game.concept} might {game.risk}."
    )


def _soften_game(world: World, child: Entity, caretaker: Entity, game: Game) -> None:
    child.memes["calm"] += 1.5
    child.meters["sleepiness"] += 1.5
    child.memes["excitement"] = max(0.0, child.memes["excitement"] - 1.0)
    caretaker.memes["calm"] += 1.0
    caretaker.memes["closeness"] += 1.0
    world.say(
        f'Then {caretaker.pronoun().capitalize()} offered a softer version: '
        f'"We can {game.concept}, but we will keep it slow and low."'
    )
    world.say(
        f'They chose a gentle rhyme: "{game.soft_phrase}." '
        f'Again and again, the words came back like tiny soft bells.'
    )


def _repeat_rhyme(world: World, child: Entity, game: Game) -> None:
    child.memes["delight"] += 1.5
    child.memes["calm"] += 1.0
    child.meters["sleepiness"] += 2.0
    child.meters["energy"] = max(0.0, child.meters["energy"] - 1.0)
    world.say(
        f'{child.id} whispered the rhyme back: "{game.bedtime_phrase}." '
        f"Then once more, because bedtime games feel nicest when they come back the same way."
    )


def _sleep(world: World, child: Entity, caretaker: Entity) -> None:
    child.asleep = True
    child.memes["calm"] += 1.0
    caretaker.memes["closeness"] += 1.0
    world.say(
        f'{child.id} yawned, tucked {child.pronoun("possessive")} hands under {child.pronoun("possessive")} cheek, '
        f"and fell asleep while the moon watched quietly."
    )
    world.say(
        f'{caretaker.pronoun().capitalize()} sat near the pillow and listened to the last tiny breath.'
    )


def tell(place: Place, game: Game, child_name: str = "Mia", child_gender: str = "girl",
         caretaker_type: str = "mother", trait: str = "curious") -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=caretaker_type, label="caretaker"))
    child.memes["curiosity"] = 1.0
    child.memes["trait"] = 1.0
    caretaker.meters["moonlight"] = 1.0 if place.moonlit else 0.0

    world.say(
        f"At {place.name}, little {trait} {child.type} {child.id} was getting sleepy, "
        f"but {child.pronoun('possessive')} mind still sparkled with one more game."
    )
    world.say(
        f"{child.id} loved a concept game, especially one that used repetition and rhyme."
    )

    world.para()
    world.say(
        f'On the bunk and by the window, {child.id} asked for the {game.id} game.'
    )
    _repeat_request(world, child, game)
    _repeat_request(world, child, game)
    _caretaker_worries(world, caretaker, child, game)

    world.para()
    world.say(
        f"The room stayed still. Outside, the night was kind, and the moonlight felt like a blanket."
    )
    _soften_game(world, child, caretaker, game)
    _repeat_rhyme(world, child, game)

    world.para()
    _sleep(world, child, caretaker)

    world.facts.update(
        child=child,
        caretaker=caretaker,
        game=game,
        trait=trait,
        place=place,
        asleep=child.asleep,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    game = f["game"]
    place = f["place"]
    return [
        f'Write a bedtime story about {child.id} at {place.name} who keeps asking for a {game.id} game.',
        f"Tell a gentle story where repetition and rhyme help turn a noisy {game.concept} into sleep.",
        f'Write a short bedtime tale that uses the words "junket", "concept", and "game".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    caretaker: Entity = f["caretaker"]
    game: Game = f["game"]
    place: Place = f["place"]
    trait: str = f["trait"]
    qa: list[QAItem] = [
        QAItem(
            question=f"What did {child.id} want to play at {place.name}?",
            answer=(
                f"{child.id} wanted to play the {game.id} game, a little concept game "
                f"with repetition and rhyme."
            ),
        ),
        QAItem(
            question=f"Why did {caretaker.label} worry about the game?",
            answer=(
                f"{caretaker.pronoun().capitalize()} worried because that kind of game could "
                f"{game.risk} instead of helping bedtime get sleepy."
            ),
        ),
        QAItem(
            question=f"How did the grown-up change the game?",
            answer=(
                f"{caretaker.pronoun().capitalize()} made it slower and softer, so the child could "
                f"keep the rhyme while the room stayed calm."
            ),
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=(
                f"{trait.capitalize()} {child.id} felt calm and sleepy, and then {child.pronoun()} fell asleep."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is repetition?",
            answer="Repetition means saying or doing the same thing again. In stories and songs, repetition can make words easy to remember.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme means two words sound alike at the end, like moon and spoon. Rhymes can make a story feel musical.",
        ),
        QAItem(
            question="What is a bedtime story?",
            answer="A bedtime story is a gentle story told before sleep. It is usually calm, cozy, and comforting.",
        ),
        QAItem(
            question="What is a junket?",
            answer="A junket is a little trip or outing. It can be a short journey with special stops or treats.",
        ),
        QAItem(
            question="What is a concept game?",
            answer="A concept game is a game that plays with an idea, like naming things, sorting things, or finding rhyming words.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the requested game exists and the bedtime resolution is possible.
valid_game(G) :- game(G).
valid_story(P, G) :- place(P), valid_game(G), calm_fix(G).

% A game has a calm fix when it includes repetition and rhyme, because both can be
% softened into a sleep-friendly ritual.
calm_fix(G) :- game(G), repeats(G), rhymes(G).

% No story should be generated for a game that lacks either repetition or rhyme.
unsafe(G) :- game(G), not repeats(G).
unsafe(G) :- game(G), not rhymes(G).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for gid, game in GAMES.items():
        lines.append(asp.fact("game", gid))
        if "repetition" in game.tags:
            lines.append(asp.fact("repeats", gid))
        if "rhyme" in game.tags:
            lines.append(asp.fact("rhymes", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid() -> list[tuple]:
    return sorted((p, g) for p in PLACES for g in GAMES if "repetition" in GAMES[g].tags and "rhyme" in GAMES[g].tags)


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} stories).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: junket, concept, game; repetition and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    game = args.game or rng.choice(list(GAMES))
    gender = args.gender or rng.choice(["girl", "boy"])
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, game=game, child_name=name, child_gender=gender, caretaker_type=caretaker)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], GAMES[params.game], params.child_name, params.child_gender, params.caretaker_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.asleep:
            bits.append("asleep=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid stories:")
        for p, g in vals:
            print(f"  {p:8} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for game in GAMES:
                p = StoryParams(place=place, game=game, child_name="Mia", child_gender="girl", caretaker_type="mother")
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
