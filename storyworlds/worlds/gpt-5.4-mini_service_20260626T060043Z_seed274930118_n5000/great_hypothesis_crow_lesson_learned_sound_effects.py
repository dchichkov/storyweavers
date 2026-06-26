#!/usr/bin/env python3
"""
A small comedy storyworld about a curious crow, a big hypothesis, and some very
loud sound effects.

Premise:
- A crow named Corbin loves making dramatic hypotheses about where sounds come
  from.
- Corbin keeps following sound effects in the town square and guessing wildly.
- Each guess can be right or wrong, and the wrong guesses make a mess of pride.
- The lesson learned is that a great hypothesis needs careful listening first.

The world is intentionally small, constraint-checked, and state-driven.
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
# Shared helpers
# ---------------------------------------------------------------------------

def _slug(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "_" for c in text).strip("_")


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "crow":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Sound:
    id: str
    label: str
    source: str
    effect: str
    volume: str
    clue: str
    truth: str


@dataclass
class Place:
    name: str
    ambience: str
    things: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    sound: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, sound: Sound) -> None:
        self.place = place
        self.sound = sound
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place, self.sound)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "square": Place(
        name="the town square",
        ambience="a wide cobblestone square with a fountain and a snack cart",
        things=["fountain", "snack cart", "bench"],
    ),
    "roof": Place(
        name="the bakery roof",
        ambience="a warm roof above a bakery, with crumbs in every corner",
        things=["chimney", "basket", "railing"],
    ),
    "garden": Place(
        name="the backyard garden",
        ambience="a backyard garden full of flowers, hose loops, and sleepy tomatoes",
        things=["hose", "watering can", "flower bed"],
    ),
}

SOUNDS = {
    "cart": Sound(
        id="cart",
        label="the snack cart whistle",
        source="the snack cart",
        effect="peeeep!",
        volume="sharp",
        clue="a tiny kettle whistle",
        truth="The cart seller was signaling for hot pretzels.",
    ),
    "fountain": Sound(
        id="fountain",
        label="the fountain splatter",
        source="the fountain",
        effect="splish-splash!",
        volume="sprinkly",
        clue="water skipping over stone",
        truth="The fountain was spraying a little extra water after a brave pigeon landed in it.",
    ),
    "roof": Sound(
        id="roof",
        label="the roof drum",
        source="the roof",
        effect="thump-thump!",
        volume="bouncy",
        clue="someone hopping on boards",
        truth="The baker was moving flour sacks across the roof hatch.",
    ),
}

CROW_NAMES = ["Corbin", "Milo", "Nell", "Pip", "Rico", "Tara"]
TRAITS = ["curious", "dramatic", "sly", "cheerful", "mischievous"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(square). place(roof). place(garden).

sound(cart). source(cart,cart). clue(cart,cart). effect(cart,peeeep).
sound(fountain). source(fountain,fountain). clue(fountain,fountain). effect(fountain,splish_splash).
sound(roof). source(roof,roof). clue(roof,roof). effect(roof,thump_thump).

valid(Place,Sound) :- place(Place), sound(Sound).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for thing in place.things:
            lines.append(asp.fact("thing_at", pid, _slug(thing)))
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("source", sid, _slug(sound.source)))
        lines.append(asp.fact("clue", sid, _slug(sound.clue)))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, s) for p in PLACES for s in SOUNDS}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: ASP parity confirmed ({len(cl)} pairs).")
        return 0
    print("Mismatch between ASP and Python:")
    print("  only in python:", sorted(py - cl))
    print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def choose_hypothesis(sound: Sound) -> str:
    if sound.id == "cart":
        return "a tiny dragon was practicing polite squeaks"
    if sound.id == "fountain":
        return "the fountain had learned to sneeze water"
    return "the roof was being thumped by a giant peanut"
    # Comedy is better when the guess is very wrong.


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: a crow, a hypothesis, and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sound", choices=SOUNDS)
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
    sound = args.sound or rng.choice(list(SOUNDS))
    if place not in PLACES or sound not in SOUNDS:
        raise StoryError("Unknown place or sound.")
    return StoryParams(place=place, sound=sound)


def _talk(world: World, text: str) -> None:
    world.say(text)


def generate_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    sound = SOUNDS[params.sound]
    world = World(place, sound)

    crow_name = world.facts.setdefault("crow_name", random.choice(CROW_NAMES))
    crow_trait = world.facts.setdefault("crow_trait", random.choice(TRAITS))
    crow = world.add(Entity(
        id=crow_name,
        kind="character",
        type="crow",
        label=crow_name,
        phrase=f"the {crow_trait} crow {crow_name}",
        location=place.name,
        traits=[crow_trait, "feathered", "noisy"],
        meters={"attention": 0.0, "pride": 0.0, "tired": 0.0},
        memes={"curiosity": 1.0, "confidence": 1.0, "embarrassment": 0.0, "joy": 0.0, "lesson": 0.0},
    ))

    world.facts["place"] = place
    world.facts["sound"] = sound
    world.facts["crow"] = crow

    # Act 1
    world.say(f"In {place.name}, {crow_name} was {crow_trait} and always hunting for the next big mystery.")
    world.say(f"The place had {place.ambience}.")
    world.say(f"Then {crow_name} heard {sound.effect} from {sound.label}.")
    world.say(f'"That is a great hypothesis waiting to happen," {crow_name} squawked.')

    # Act 2
    world.para()
    crow.meters["attention"] += 1
    crow.memes["confidence"] += 1
    guessed = choose_hypothesis(sound)
    world.say(f"{crow_name} flapped toward the noise and announced, \"My hypothesis is that {guessed}.\"")
    world.say(f"He peered behind {sound.source} and made a very serious face, which looked funny on a crow.")
    crow.meters["pride"] += 1

    # Wrong guess or right guess with a comedic twist.
    if guessed not in sound.truth.lower():
        crow.memes["embarrassment"] += 1
        crow.meters["tired"] += 0.5
        world.say(f"That was not right.")
        world.say(f"The real answer was this: {sound.truth}")
        world.say(f"{sound.clue.capitalize()} had been the clue all along, and {crow_name} blinked like he had just met a spoon.")
    else:
        crow.memes["joy"] += 1
        world.say(f"{crow_name} was right, which made him stand taller than a very rude cucumber.")
        world.say(f"Still, he cawed, \"Even a great hypothesis needs a careful ear.\"")

    # Act 3
    world.para()
    crow.memes["lesson"] += 1
    crow.meters["attention"] += 1
    world.say(f"Next time, {crow_name} listened first, then guessed.")
    world.say(f"That turned out to be the lesson learned: a great hypothesis is funny, but a better one is listened to before it leaps.")
    world.say(f"And when {sound.effect} echoed again, {crow_name} only laughed, puffed his feathers, and nodded at the sound like an old friend.")

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    crow = world.get(world.facts["crow_name"])
    sound: Sound = world.facts["sound"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        f'Write a short comedy story for a child that includes the words "great", "hypothesis", and "crow".',
        f"Tell a funny story about {crow.label} the crow in {place.name} who hears {sound.effect} and makes a silly hypothesis.",
        f"Write a gentle lesson-learned story where sound effects lead a crow to guess wrong, then listen better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    crow: Entity = world.facts["crow"]  # type: ignore[assignment]
    sound: Sound = world.facts["sound"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    trait = crow.traits[0] if crow.traits else "curious"
    return [
        QAItem(
            question=f"Who was the story about in {place.name}?",
            answer=f"The story was about {trait} {crow.label}, a crow who loved making guesses about noisy things.",
        ),
        QAItem(
            question=f"What sound effect did {crow.label} hear?",
            answer=f"{crow.label} heard {sound.effect} from {sound.label}. That sound made him start a new hypothesis.",
        ),
        QAItem(
            question="What lesson did the crow learn?",
            answer="He learned that a great hypothesis should come after careful listening, not before it.",
        ),
        QAItem(
            question=f"Was {crow.label}'s first hypothesis correct?",
            answer=f"No. His first hypothesis was funny, but it was wrong, and the real answer was {sound.truth.lower()}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hypothesis?",
            answer="A hypothesis is a smart guess about what might be true, often made before you know the full answer.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises that help tell what is happening, like splashes, whistles, or thumps.",
        ),
        QAItem(
            question="Why do crows seem clever in stories?",
            answer="Crows are often written as clever birds because they watch carefully, remember things, and solve problems.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"facts={list(world.facts.keys())}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid pairs")
        for p, s in pairs:
            print(p, s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in PLACES:
            for sound in SOUNDS:
                params = StoryParams(place=place, sound=sound, seed=base_seed)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
