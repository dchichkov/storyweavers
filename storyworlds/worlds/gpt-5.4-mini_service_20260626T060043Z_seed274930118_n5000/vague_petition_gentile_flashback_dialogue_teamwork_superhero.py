#!/usr/bin/env python3
"""
A standalone storyworld for a small superhero-style domain.

Premise:
- A young hero wants to help the city in a big, noisy way.
- The city is facing a small problem that can only be solved by teamwork.
- A vague petition and a flashback reveal why the hero is careful.
- Dialogue carries the turn from solo action to cooperative action.
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
# Core data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "heroine", "mother"}
        male = {"boy", "man", "hero", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class City:
    name: str = "Bright Harbor"
    place: str = "the city square"
    weather: str = "windy"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str
    sidekick: str
    hero_type: str
    sidekick_type: str
    city: str
    problem: str
    petition: str
    seed: Optional[int] = None


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
HEROES = {
    "Nova": {"type": "girl", "trait": "brave"},
    "Bolt": {"type": "boy", "trait": "quick"},
    "Spark": {"type": "girl", "trait": "gentle"},
    "Comet": {"type": "boy", "trait": "kind"},
}

SIDEKICKS = {
    "Pip": {"type": "boy"},
    "Mira": {"type": "girl"},
    "Juno": {"type": "girl"},
    "Ace": {"type": "boy"},
}

PROBLEMS = {
    "bridge": {
        "label": "broken bridge",
        "need": "pull the metal beams together",
        "risk": "the cars could not cross",
        "flashback": "the last time a rescue went too fast, a beam slipped and made a loud crash",
    },
    "balloons": {
        "label": "runaway balloons",
        "need": "catch the strings before they drifted over the river",
        "risk": "the party would lose all its decorations",
        "flashback": "she remembered a birthday when she had rushed alone and missed the knot",
    },
    "lights": {
        "label": "dark street lights",
        "need": "carry the battery box to the top of the tower",
        "risk": "the block would stay dim and lonely",
        "flashback": "he remembered being afraid of the dark lane when the lights had gone out",
    },
}

PETITIONS = {
    "park": "a vague petition to keep the park safe",
    "tower": "a petition for a better lookout tower",
    "market": "a petition to fix the market path",
}


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if params.hero not in HEROES:
        raise StoryError(f"Unknown hero {params.hero!r}.")
    if params.sidekick not in SIDEKICKS:
        raise StoryError(f"Unknown sidekick {params.sidekick!r}.")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem {params.problem!r}.")
    if params.petition not in PETITIONS:
        raise StoryError(f"Unknown petition {params.petition!r}.")

    city = City(name=params.city, place="the city square")
    world = World(city)

    hero_cfg = HEROES[params.hero]
    side_cfg = SIDEKICKS[params.sidekick]

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=hero_cfg["type"],
        label="hero",
        meters={"energy": 3.0, "resolve": 2.0, "stamina": 2.0},
        memes={"caution": 1.0, "hope": 2.0},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick,
        kind="character",
        type=side_cfg["type"],
        label="sidekick",
        meters={"energy": 2.0, "stamina": 2.0},
        memes={"loyalty": 2.0, "curiosity": 1.0},
    ))
    petition = world.add(Entity(
        id="petition",
        type="thing",
        label="petition",
        phrase=PETITIONS[params.petition],
        meters={"pages": 4.0},
        memes={"vague": 2.0},
    ))
    problem = world.add(Entity(
        id="problem",
        type="thing",
        label=PROBLEMS[params.problem]["label"],
        phrase=PROBLEMS[params.problem]["need"],
        meters={"danger": 2.0, "difficulty": 2.0},
        memes={"fear": 1.0},
    ))

    # Setup
    world.say(
        f"In {city.name}, {hero.id} was known as a {hero_cfg['trait']} hero who liked to help."
    )
    world.say(
        f"{sidekick.id} stayed close, because {hero.id} and {sidekick.id} were a team."
    )
    world.say(
        f"At the city square, they found {petition.phrase}, and the words felt vague on purpose."
    )

    # Flashback
    world.para()
    world.say(
        f"Flashback: {PROBLEMS[params.problem]['flashback']}."
    )
    world.say(
        f"That memory made {hero.id} gentile and careful instead of fast and loud."
    )

    # Conflict
    world.para()
    world.say(
        f"{hero.id} wanted to fix the {problem.label} alone."
    )
    world.say(
        f'"We can do it in one leap," {hero.id} said.'
    )
    world.say(
        f'"Maybe," {sidekick.id} said, "but the petition is asking for help, not a show."'
    )
    world.say(
        f"The {problem.label} still blocked the way, and {problem.phrase} was too heavy for one pair of hands."
    )
    hero.memes["doubt"] = 1.0
    hero.memes["listening"] = 1.0

    # Turn to teamwork
    world.para()
    world.say(
        f"{hero.id} looked at {sidekick.id} and nodded."
    )
    world.say(
        f'"You take the left side," {hero.id} said, "and I will take the right."'
    )
    world.say(
        f'"Deal," {sidekick.id} said. "Teamwork first."'
    )
    problem.meters["danger"] = 0.0
    problem.meters["difficulty"] = 0.0
    hero.meters["energy"] -= 1.0
    sidekick.meters["energy"] -= 1.0
    hero.memes["hope"] += 1.0
    sidekick.memes["loyalty"] += 1.0

    # Resolution
    world.para()
    world.say(
        f"Together they lifted, balanced, and guided the broken pieces into place."
    )
    world.say(
        f"The {problem.label} was fixed, and the city could breathe again."
    )
    world.say(
        f"{hero.id} smiled at the {petition.label} and said it was no longer vague, because now the answer was clear."
    )
    world.say(
        f"In the end, {hero.id}, {sidekick.id}, and the whole city had a small bright victory."
    )

    world.facts.update(hero=hero, sidekick=sidekick, petition=petition, problem=problem, city=city)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    problem: Entity = f["problem"]  # type: ignore[assignment]
    petition: Entity = f["petition"]  # type: ignore[assignment]
    return [
        f'Write a superhero story with a vague petition, a flashback, and teamwork in {world.city.name}.',
        f"Tell a child-friendly story where {hero.id} and {sidekick.id} solve {problem.label} after reading {petition.phrase}.",
        f'Write a gentle superhero tale that uses the words "vague", "petition", and "gentile".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    problem: Entity = f["problem"]  # type: ignore[assignment]
    petition: Entity = f["petition"]  # type: ignore[assignment]
    hero_trait = HEROES[hero.id]["trait"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero_trait} hero, and {sidekick.id}, who worked with {hero.id} as a teammate.",
        ),
        QAItem(
            question=f"What made the heroes stop and think before acting?",
            answer=f"They found {petition.phrase}, which was a vague petition, and then a flashback reminded {hero.id} to be careful.",
        ),
        QAItem(
            question=f"How did they fix the {problem.label}?",
            answer=f"They fixed it with teamwork: {sidekick.id} held one side while {hero.id} held the other, and together they finished the job.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a petition?",
            answer="A petition is a request that people sign to ask for help or change."
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people share the work and help each other reach a goal."
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a scene that briefly shows something that happened before the main moment."
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
sidekick(S) :- sidekick_name(S).
problem(P) :- problem_name(P).
petition(T) :- petition_name(T).

needs_teamwork(P) :- problem_name(P), teamwork_required(P).
has_flashback(P) :- problem_name(P), flashback_marker(P).
gentle_hero(H) :- hero_name(H), trait(H, gentle).

compatible(H,S,P,T) :- hero_name(H), sidekick_name(S), problem_name(P), petition_name(T),
                       needs_teamwork(P), has_flashback(P), petition_type(T, vague).

#show compatible/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for h, cfg in HEROES.items():
        lines.append(asp.fact("hero_name", h))
        lines.append(asp.fact("trait", h, cfg["trait"]))
    for s in SIDEKICKS:
        lines.append(asp.fact("sidekick_name", s))
    for p, cfg in PROBLEMS.items():
        lines.append(asp.fact("problem_name", p))
        lines.append(asp.fact("teamwork_required", p))
        lines.append(asp.fact("flashback_marker", p))
    for pet in PETITIONS:
        lines.append(asp.fact("petition_name", pet))
    lines.append(asp.fact("petition_type", "park", "vague"))
    lines.append(asp.fact("petition_type", "tower", "vague"))
    lines.append(asp.fact("petition_type", "market", "vague"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {
        (h, s, p, t)
        for h in HEROES
        for s in SIDEKICKS
        for p in PROBLEMS
        for t in PETITIONS
    }
    asp_set = set(asp_compatible())
    if asp_set == py:
        print(f"OK: clingo gate matches Python grid ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(asp_set - py))
    print("only in python:", sorted(py - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with flashback, dialogue, and teamwork.")
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--sidekick", choices=sorted(SIDEKICKS))
    ap.add_argument("--city", default="Bright Harbor")
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--petition", choices=sorted(PETITIONS))
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
    hero = args.hero or rng.choice(sorted(HEROES))
    sidekick = args.sidekick or rng.choice(sorted(SIDEKICKS))
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    petition = args.petition or rng.choice(sorted(PETITIONS))
    return StoryParams(
        hero=hero,
        sidekick=sidekick,
        hero_type=HEROES[hero]["type"],
        sidekick_type=SIDEKICKS[sidekick]["type"],
        city=args.city,
        problem=problem,
        petition=petition,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"  city: {world.city.name} at {world.city.place}")
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
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_compatible()
        print(f"{len(combos)} compatible story combos:\n")
        for h, s, p, t in combos:
            print(f"  {h:8} {s:8} {p:8} {t:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for h in sorted(HEROES):
            for s in sorted(SIDEKICKS):
                for p in sorted(PROBLEMS):
                    for t in sorted(PETITIONS):
                        params = StoryParams(
                            hero=h,
                            sidekick=s,
                            hero_type=HEROES[h]["type"],
                            sidekick_type=SIDEKICKS[s]["type"],
                            city=args.city,
                            problem=p,
                            petition=t,
                        )
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
