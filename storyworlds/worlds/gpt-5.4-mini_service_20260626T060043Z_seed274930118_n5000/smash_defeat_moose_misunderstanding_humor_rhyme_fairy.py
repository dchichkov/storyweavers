#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a misunderstanding, a humorous rhyme, and
a friendly moose who gets defeated by a clever, nonviolent trick.

Premise:
- A child or small helper tries to solve a problem in a fairy-tale setting.
- They misunderstand a moose's noisy behavior as a threat.
- A funny rhyme reveals the moose was only trying to help.
- The ending proves the change in state: the moose is no longer a problem,
  the misunderstanding is gone, and the characters feel relieved.

This script is standalone and follows the Storyweavers storyworld contract.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "it",
            "object": "it",
            "possessive": "its",
        }
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    moose_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "meadow": Place(
        name="the moonlit meadow",
        detail="The grass shone silver, and the flowers leaned like tiny listeners.",
        affords={"sing", "listen", "run"},
    ),
    "castle_garden": Place(
        name="the castle garden",
        detail="Stone paths curled past rosebushes and a little fountain.",
        affords={"sing", "listen", "run"},
    ),
    "woodland": Place(
        name="the quiet woodland",
        detail="Tall trees made a soft roof, and the moss looked like green cake.",
        affords={"sing", "listen", "run"},
    ),
}

HERO_NAMES = ["Pip", "Lina", "Milo", "Tessa", "Nia", "Gus"]
HELPER_NAMES = ["Bramble", "Penny", "Oren", "Mira", "Fenn", "Wren"]
MOOSE_NAMES = ["Mossy", "Bruno", "Merry", "Thistle", "Hugo", "Nell"]

# Simple Fairy Tale flavor with a small set of valid story shapes.
TALES = {
    "meadow": {
        "mood": "soft and dreamy",
        "problem": "a rustling in the reeds",
        "moose_action": "snorted and bumped a basket of berries",
        "misunderstanding": "looked as if he meant to spoil the picnic",
    },
    "castle_garden": {
        "mood": "bright and royal",
        "problem": "a wobble near the rose arch",
        "moose_action": "stomped by the fountain and shook drops everywhere",
        "misunderstanding": "looked as if he meant to squish the royal cake",
    },
    "woodland": {
        "mood": "quiet and old",
        "problem": "a thump behind the fern wall",
        "moose_action": "nosed a log and sent acorns rolling",
        "misunderstanding": "looked as if he meant to break the lantern path",
    },
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid if it has a place and the moose misunderstanding can be
% resolved by a humorous rhyme.
valid_story(P) :- place(P), misunderstanding(P), humor(P), rhyme(P), defeat(P).

% The moose is defeated only when the rhyme changes the misunderstanding.
defeat(P) :- rhyme(P), misunderstanding(P), fixed(P).

% A fixed misunderstanding becomes harmless and the moose is no longer a threat.
fixed(P) :- rhyme(P), humor(P), place(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("misunderstanding", pid))
        lines.append(asp.fact("humor", pid))
        lines.append(asp.fact("rhyme", pid))
        lines.append(asp.fact("fixed", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((p,) for p in valid_places())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_places() ({len(python_set)} places).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_places() -> list[str]:
    return sorted(PLACES)


def build_story(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    place = PLACES[params.place]
    tale = TALES[params.place]
    world = World(place)

    hero = world.add(Entity(id=params.hero, kind="character", type="child", label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type="helper", label=params.helper))
    moose = world.add(Entity(id=params.moose_name, kind="character", type="moose", label=params.moose_name))
    moose.meters["trouble"] = 1.0
    hero.memes["worry"] = 1.0
    helper.memes["humor"] = 1.0

    world.facts.update(
        hero=hero,
        helper=helper,
        moose=moose,
        place=place,
        tale=tale,
        misunderstanding=True,
        humor=True,
        rhyme=True,
        defeated=True,
    )

    world.say(
        f"Once in {place.name}, there lived a small child named {hero.label} and a kind helper named {helper.label}."
    )
    world.say(place.detail)
    world.say(
        f"One evening, they heard {moose.label} in the brush, and the sound {tale['misunderstanding']}."
    )

    world.para()
    world.say(
        f"{hero.label} gasped. {hero.label} thought the moose wanted to cause trouble, because of {tale['problem']}."
    )
    hero.memes["misunderstanding"] = 1.0
    moose.meters["noticed"] = 1.0

    world.say(
        f"But {helper.label} saw something funny: {moose.label} was only being clumsy, not cruel."
    )
    helper.memes["humor"] = 2.0

    world.para()
    rhyme = (
        f'"If a moose makes a hissy, do not get all hissy; '
        f'listen twice, then smile once, and the meadow turns frisky!" said {helper.label}.'
    )
    world.say(rhyme)
    world.say(
        f"The silly rhyme made {hero.label} blink and laugh. "
        f"{hero.label} finally understood that {moose.label} had only {tale['moose_action']}."
    )

    moose.meters["trouble"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    moose.memes["peace"] = 1.0

    world.para()
    world.say(
        f"After that, {hero.label} patted {moose.label} on the nose, and {moose.label} bowed like a polite giant."
    )
    world.say(
        f"The misunderstanding was gone, the humor remained, and the moose was defeated by the rhyme without anyone getting hurt."
    )
    world.say(
        f"Under the moonlit sky, the three friends shared berries and laughter, and {moose.label} became part of the tale instead of the trouble."
    )
    return world


# ---------------------------------------------------------------------------
# Question / answer generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"].name
    return [
        f"Write a Fairy Tale about a child in {p} who misunderstands a moose, then fixes it with humor and rhyme.",
        f"Tell a short story where a moose seems scary at first but is defeated by a clever rhyme.",
        f"Create a child-friendly fairy tale featuring a misunderstanding, a funny verse, and a peaceful moose.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    moose: Entity = world.facts["moose"]
    place: Place = world.facts["place"]
    tale = world.facts["tale"]

    return [
        QAItem(
            question=f"Who was the story about in {place.name}?",
            answer=f"The story was about {hero.label} and {helper.label}, and it also featured {moose.label} the moose.",
        ),
        QAItem(
            question=f"What did {hero.label} misunderstand at first?",
            answer=f"{hero.label} misunderstood {moose.label}'s noisy behavior and thought it was a threat.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"{helper.label} told a funny rhyme, {hero.label} laughed, and the misunderstanding turned into peace.",
        ),
        QAItem(
            question=f"What did the moose actually do?",
            answer=f"{moose.label} was only clumsy and {tale['moose_action']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with everyone calm, laughing, and sharing berries under the sky.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that makes people smile or laugh.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat.",
        ),
        QAItem(
            question="What is a moose?",
            answer="A moose is a very large deer with long legs and broad antlers.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(sorted(PLACES))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    moose_name = args.moose_name or rng.choice(MOOSE_NAMES)
    if len({hero, helper, moose_name}) < 3:
        raise StoryError("Please choose distinct names for the hero, helper, and moose.")
    return StoryParams(place=place, hero=hero, helper=helper, moose_name=moose_name)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about a moose misunderstanding.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--moose-name")
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


def asp_valid_places() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_places())} valid places:")
        for p in valid_places():
            print(f"  {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in sorted(PLACES):
            params = StoryParams(place=place, hero=HERO_NAMES[0], helper=HELPER_NAMES[0], moose_name=MOOSE_NAMES[0], seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
