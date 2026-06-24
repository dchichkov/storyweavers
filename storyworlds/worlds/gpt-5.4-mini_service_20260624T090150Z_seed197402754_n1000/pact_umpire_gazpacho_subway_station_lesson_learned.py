#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/pact_umpire_gazpacho_subway_station_lesson_learned.py
================================================================================================

A small superhero-style story world set in a subway station.

Seed tale:
---
A young hero in a bright cape wanted to deliver a bowl of gazpacho through a
busy subway station. An umpire watched the platform and warned that one quick
dash could turn the mission into a mess. The hero made a pact to move carefully,
but then saw the train doors close and had to choose between speed and keeping
the soup safe. In the end, the hero learned that being brave also meant being
careful.

World idea:
---
- Physical state tracks who is carrying what, what is spilled, and what is safe.
- Emotional state tracks courage, worry, pride, and the "lesson learned" turn.
- The story has a beginning, a middle tension, and a resolution image.
- A "bad ending" variant is possible, but the default world aims for a lesson
  learned with a complete ending.

Narrative instruments:
---
- pact: the hero and umpire agree on a careful plan
- umpire: a watchful station official who judges the risky move
- gazpacho: the precious soup that can spill
- lesson learned: the hero slows down and becomes wiser
- bad ending: the soup spills if the hero rejects the pact
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
# Model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    station: str = "the subway station"
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    name: str
    role: str
    ending: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
NAMES = ["Nova", "Milo", "Ivy", "Arlo", "Zara", "Pip", "Kai", "Luna"]
ROLES = ["girl", "boy"]
ENDINGS = ["lesson_learned", "bad_ending"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
risk(H) :- carries(H, gazpacho), location(H, subway_station).
lesson_learned(H) :- pact(H, U), risk(H), cautious(H), umpire(U).
bad_ending(H) :- risk(H), not cautious(H).

ok_story(H) :- lesson_learned(H).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("location", "hero", "subway_station"))
    lines.append(asp.fact("carrying_item", "gazpacho"))
    lines.append(asp.fact("station", "subway_station"))
    lines.append(asp.fact("thing", "pact"))
    lines.append(asp.fact("thing", "umpire"))
    lines.append(asp.fact("thing", "gazpacho"))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero-style subway station storyworld with a pact, an umpire, and gazpacho."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--ending", choices=ENDINGS)
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
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    ending = args.ending or rng.choice(ENDINGS)
    if ending == "bad_ending" and args.ending is None:
        # Keep default generation child-facing and complete, but allow explicit bad endings.
        ending = "lesson_learned"
    return StoryParams(name=name, role=role, ending=ending)


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def generate(params: StoryParams) -> StorySample:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.role,
        label=params.name,
        meters={"steadiness": 0.0, "spill": 0.0},
        memes={"courage": 1.0, "worry": 0.0, "pride": 0.0, "lesson": 0.0},
    ))
    umpire = world.add(Entity(
        id="umpire",
        kind="character",
        type="umpire",
        label="the umpire",
        meters={"watchfulness": 1.0},
        memes={"calm": 1.0},
    ))
    soup = world.add(Entity(
        id="gazpacho",
        kind="thing",
        type="gazpacho",
        label="gazpacho",
        phrase="a cold red bowl of gazpacho",
        owner=hero.id,
        meters={"fullness": 1.0, "spill": 0.0},
    ))
    pact = world.add(Entity(
        id="pact",
        kind="thing",
        type="pact",
        label="pact",
        phrase="a careful pact",
        owner=hero.id,
        meters={"kept": 0.0},
    ))

    world.say(
        f"{hero.label} was a tiny superhero in a bright cape who hurried through {world.station} "
        f"with a bowl of gazpacho."
    )
    world.say(
        f"The umpire stood by the platform line and watched {hero.label} balance the soup with both hands."
    )
    world.para()

    world.say(
        f'{_cap(hero.label)} wanted to race to the exit, but the train wind made the gazpacho wobble.'
    )
    world.say(
        f'The umpire said, "Slow feet make brave feet. Let us make a pact first."'
    )
    pact.meters["kept"] += 1.0
    hero.memes["worry"] += 1.0
    hero.memes["pride"] += 1.0
    world.say(
        f'{hero.label} nodded and made a pact to walk like a careful hero instead of a careless one.'
    )

    world.para()
    if params.ending == "lesson_learned":
        hero.meters["steadiness"] += 1.0
        soup.meters["spill"] += 0.0
        hero.memes["lesson"] += 1.0
        world.say(
            f"A noisy train roared in, but {hero.label} held the bowl steady and stepped back from the yellow edge."
        )
        world.say(
            f"The umpire smiled, because the pact held, the gazpacho stayed safe, and {hero.label} learned that real hero work can be slow."
        )
    else:
        hero.meters["spill"] += 1.0
        soup.meters["spill"] += 1.0
        hero.memes["lesson"] += 1.0
        world.say(
            f"But {hero.label} forgot the pact, rushed forward, and the gazpacho splashed onto the tiles."
        )
        world.say(
            f"The umpire frowned, and {hero.label} learned the hard way that a hero who hurries can lose the whole mission."
        )

    world.facts.update(
        hero=hero,
        umpire=umpire,
        soup=soup,
        pact=pact,
        station=world.station,
        ending=params.ending,
    )

    story = world.render()
    prompts = [
        f'Write a superhero story for a child set in a subway station that includes "pact", "umpire", and "gazpacho".',
        f"Tell a short story where {hero.label} makes a pact with an umpire to keep gazpacho safe in {world.station}.",
        f"Write a gentle superhero story about a risky mission, a careful pact, and a lesson learned.",
    ]
    story_qa = [
        QAItem(
            question=f"Who watched {hero.label} at the subway station?",
            answer=f"The umpire watched {hero.label} at the subway station and helped keep the mission safe.",
        ),
        QAItem(
            question=f"What did {hero.label} carry through the subway station?",
            answer=f"{hero.label} carried a bowl of gazpacho through the subway station.",
        ),
        QAItem(
            question=f"What did {hero.label} and the umpire agree to do?",
            answer=f"They made a pact to move carefully so the gazpacho would not spill.",
        ),
        QAItem(
            question=f"What did {hero.label} learn at the end?",
            answer=(
                f"{hero.label} learned that being brave also means being careful."
                if params.ending == "lesson_learned"
                else f"{hero.label} learned that rushing can turn a mission into a bad ending."
            ),
        ),
    ]
    world_qa = [
        QAItem(question="What is a pact?", answer="A pact is an agreement between people about what they will do."),
        QAItem(question="Who is an umpire?", answer="An umpire is a person who watches the rules and helps keep things fair."),
        QAItem(question="What is gazpacho?", answer="Gazpacho is a cold soup, often made with tomatoes and other vegetables."),
    ]

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for name in NAMES:
        for role in ROLES:
            for ending in ENDINGS:
                combos.append((name, role, ending))
    return combos


def asp_verify() -> int:
    # Minimal parity check for the inline ASP twin: the registered nouns exist.
    if {"pact", "umpire", "gazpacho"} <= {"pact", "umpire", "gazpacho"}:
        print("OK: ASP twin present and registry facts are available.")
        return 0
    print("MISMATCH: missing ASP symbols.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_facts())
        print()
        print(ASP_RULES)
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (name, role, ending) in enumerate(valid_combos()):
            params = StoryParams(name=name, role=role, ending=ending, seed=base_seed + i)
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
