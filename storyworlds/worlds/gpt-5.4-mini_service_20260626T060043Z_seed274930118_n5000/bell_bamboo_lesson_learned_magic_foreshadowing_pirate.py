#!/usr/bin/env python3
"""
A small pirate tale storyworld with bells, bamboo, magic, foreshadowing,
and a lesson learned at the end.

The tale premise:
- A young pirate crew hears a mysterious bell on an island with bamboo.
- Magic points toward a hidden path.
- Foreshadowing hints that impatience will cause trouble.
- The crew makes a mistake, learns the lesson, and finishes the quest with
  a clearer, kinder choice.

This script is self-contained and follows the shared storyworld contract.
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
# World data
# ---------------------------------------------------------------------------

@dataclass
class Thing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class CrewMember(Thing):
    kind: str = "character"
    type: str = "pirate"
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    has_bamboo: bool = False
    has_bell: bool = False
    has_magic: bool = False
    has_foreshadowing: bool = False
    has_treasure: bool = False


@dataclass
class StoryParams:
    place: str
    hero: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Thing] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, ent: Thing) -> Thing:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Thing:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "bamboo_cove": Place(
        name="Bamboo Cove",
        has_bamboo=True,
        has_bell=True,
        has_magic=True,
        has_foreshadowing=True,
        has_treasure=True,
    ),
    "foggy_jetty": Place(
        name="Foggy Jetty",
        has_bamboo=False,
        has_bell=True,
        has_magic=True,
        has_foreshadowing=True,
        has_treasure=True,
    ),
    "green_isle": Place(
        name="Green Isle",
        has_bamboo=True,
        has_bell=False,
        has_magic=True,
        has_foreshadowing=True,
        has_treasure=True,
    ),
}

TRAITS = ["bold", "curious", "brave", "restless", "clever", "lively"]
HERO_NAMES = ["Mina", "Jory", "Pip", "Nell", "Sailor", "Roo"]

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with bell, bamboo, magic, and lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    hero = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, hero=hero, trait=trait)


def _intro(world: World, hero: CrewMember) -> None:
    place = world.place.name
    world.say(
        f"On {place}, {hero.id} was a {hero.traits[0]} little pirate who loved strange signs at sea."
    )
    world.say(
        f"{hero.id} had heard that a bell could ring without a hand touching it, and that made {hero.pronoun('object')} grin."
    )


def _foreshadow(world: World) -> None:
    if world.place.has_foreshadowing:
        world.say(
            "A bent bamboo stalk creaked in the wind, and the sound felt like a warning to slow down."
        )
        world.facts["foreshadowing"] = True


def _magic_call(world: World) -> None:
    if world.place.has_magic:
        world.say(
            "Then a soft sparkle drifted from the bamboo, and the hidden path seemed to wake up."
        )
        world.facts["magic"] = True


def _bell_ring(world: World) -> None:
    if world.place.has_bell:
        world.say(
            "Far ahead, an old bell gave one clear ring, as if it were calling the crew to listen."
        )
        world.facts["bell"] = True


def _mistake(world: World, hero: CrewMember) -> None:
    hero.memes["impatience"] = hero.memes.get("impatience", 0.0) + 1.0
    world.say(
        f"{hero.id} wanted treasure right away and rushed toward the bell."
    )
    world.say(
        "But the fast step snapped a thin bamboo bridge, and the treasure path vanished into the reeds."
    )
    world.facts["mistake"] = "rushed"


def _lesson_learned(world: World, hero: CrewMember) -> None:
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 1.0
    hero.memes["impatience"] = 0.0
    world.say(
        f"{hero.id} stopped, took a breath, and finally understood the lesson: magic works best when a pirate listens first."
    )
    world.say(
        "So the crew used the bamboo as a bridge rail, followed the bell's echo slowly, and found the hidden chest without breaking anything else."
    )
    world.facts["lesson"] = "listen_first"
    world.facts["resolved"] = True


def tell(place_key: str, hero_name: str, trait: str) -> World:
    place = PLACES[place_key]
    world = World(place)
    hero = world.add(CrewMember(id=hero_name, label="pirate", traits=[trait, "little"]))

    world.say(
        f"{hero.id} sailed into {place.name} with {hero.pronoun('possessive')} eyes wide and {hero.pronoun('possessive')} hat askew."
    )
    _intro(world, hero)
    world.para()
    _foreshadow(world)
    _bell_ring(world)
    _magic_call(world)
    world.para()
    _mistake(world, hero)
    world.para()
    _lesson_learned(world, hero)

    world.facts.update(hero=hero, place=place, theme="pirate_tale")
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: CrewMember = world.facts["hero"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        f"Write a short pirate tale for a child about {hero.id} at {place.name} with a bell and bamboo.",
        "Tell a magical pirate story that foreshadows a mistake and ends with a lesson learned.",
        f"Write a gentle sea adventure where a pirate listens to a bell, notices bamboo, and chooses a wiser path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: CrewMember = world.facts["hero"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the pirate story about at {place.name}?",
            answer=f"It is about {hero.id}, a {hero.traits[0]} little pirate at {place.name}.",
        ),
        QAItem(
            question="What warned the crew before the mistake?",
            answer="The creaking bamboo and the bell's strange echo warned the crew to slow down.",
        ),
        QAItem(
            question="What lesson did the pirate learn?",
            answer="The pirate learned to listen first, because magic works better when nobody rushes.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bell?",
            answer="A bell is a metal object that rings loudly when struck or shaken.",
        ),
        QAItem(
            question="What is bamboo?",
            answer="Bamboo is a tall, hollow plant that grows in strong green stalks.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints something important may happen later.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something wonderful or impossible that can happen in a story world.",
        ),
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place={world.place.name}")
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} traits={getattr(e, 'traits', [])} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_name(P).
feature(P, bell) :- has_bell(P).
feature(P, bamboo) :- has_bamboo(P).
feature(P, magic) :- has_magic(P).
feature(P, foreshadowing) :- has_foreshadowing(P).

story_ok(P) :- place(P), feature(P, bell), feature(P, bamboo), feature(P, magic), feature(P, foreshadowing).
#show story_ok/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for key, pl in PLACES.items():
        lines.append(asp.fact("place_name", key))
        if pl.has_bell:
            lines.append(asp.fact("has_bell", key))
        if pl.has_bamboo:
            lines.append(asp.fact("has_bamboo", key))
        if pl.has_magic:
            lines.append(asp.fact("has_magic", key))
        if pl.has_foreshadowing:
            lines.append(asp.fact("has_foreshadowing", key))
    return "\n".join(lines)


def asp_program(show: str = "#show story_ok/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show story_ok/1.")
    model = asp.one_model(program)
    atoms = asp.atoms(model, "story_ok")
    py_ok = sorted([k for k, p in PLACES.items() if p.has_bell and p.has_bamboo and p.has_magic and p.has_foreshadowing])
    asp_ok = sorted([a[0] for a in atoms])
    if py_ok == asp_ok:
        print(f"OK: ASP parity matches Python ({len(py_ok)} places).")
        return 0
    print("MISMATCH between Python and ASP")
    print("python:", py_ok)
    print("asp:", asp_ok)
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.hero, params.trait)
    hero: CrewMember = world.facts["hero"]  # type: ignore[assignment]
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Main / CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="bamboo_cove", hero="Mina", trait="curious"),
    StoryParams(place="foggy_jetty", hero="Pip", trait="clever"),
    StoryParams(place="green_isle", hero="Nell", trait="brave"),
]


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        ok = sorted(set(asp.atoms(model, "story_ok")))
        print(f"{len(ok)} compatible place(s):")
        for (p,) in ok:
            print(f"  {p}")
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
            header = f"### {p.hero} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
