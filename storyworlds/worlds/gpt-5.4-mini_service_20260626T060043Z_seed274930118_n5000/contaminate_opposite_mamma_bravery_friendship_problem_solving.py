#!/usr/bin/env python3
"""
A small mystery storyworld about a child, a missing clue, a contaminated object,
and the brave, friendly way the puzzle gets solved.

This world keeps the tone close to a gentle mystery: someone notices a strange
problem, follows opposites and clues, asks for help, and uses bravery,
friendship, and problem solving to fix what went wrong.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    contaminated: bool = False
    solved: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"contaminate": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"bravery": 0.0, "friendship": 0.0, "problem_solving": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mamma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    clues: list[str] = field(default_factory=list)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        chunks: list[str] = []
        cur: list[str] = []
        for line in self.lines:
            if line == "":
                if cur:
                    chunks.append(" ".join(cur))
                    cur = []
            else:
                cur.append(line)
        if cur:
            chunks.append(" ".join(cur))
        return "\n\n".join(chunks)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    mamma: str
    clue: str
    seed: Optional[int] = None


PLACES = {
    "attic": Place(id="attic", label="the attic", mood="dusty", clues=["lantern", "footprints", "whisper"]),
    "garden": Place(id="garden", label="the garden shed", mood="quiet", clues=["bucket", "mud", "scratch"]),
    "library": Place(id="library", label="the little library nook", mood="still", clues=["bookmark", "ink", "note"]),
}

HEROES = {
    "Nina": "girl",
    "Toby": "boy",
    "Mira": "girl",
    "Eli": "boy",
}

MAMMAS = ["mamma", "momma", "mother"]

CLUE_WORDS = ["lantern", "footprints", "bookmark", "bucket", "note", "scratch", "ink", "whisper"]

OPPOSITES = [
    ("hot", "cold"),
    ("open", "closed"),
    ("up", "down"),
    ("left", "right"),
    ("inside", "outside"),
    ("light", "dark"),
]

# Inline ASP twin uses these facts.
ASP_RULES = r"""
good_clue(C) :- clue(C).
opposite(A,B) :- opp(A,B).
mystery_possible(P) :- place(P), clue(C), not contaminated(C).
solved(P) :- mystery_possible(P), brave(h), friend(h), solve(h).
#show solved/1.
#show mystery_possible/1.
"""


# ---------------------------------------------------------------------------
# Reasonableness / state helpers
# ---------------------------------------------------------------------------

def contaminate_clue(world: World, clue_id: str) -> None:
    clue = world.get(clue_id)
    clue.contaminated = True
    clue.meters["contaminate"] += 1
    world.say(f"Something had contaminated the {clue.label}, and that made the room feel strange.")


def mark_bravery(hero: Entity) -> None:
    hero.memes["bravery"] += 1


def mark_friendship(hero: Entity) -> None:
    hero.memes["friendship"] += 1


def mark_problem_solving(hero: Entity) -> None:
    hero.memes["problem_solving"] += 1


def can_use_opposite_clue(clue: str) -> bool:
    return clue in CLUE_WORDS


def reasonable(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero not in HEROES:
        raise StoryError("Unknown hero.")
    if params.hero_type != HEROES[params.hero]:
        raise StoryError("Hero type does not match the chosen name.")
    if params.mamma not in MAMMAS:
        raise StoryError("Unknown mamma wording.")
    if not can_use_opposite_clue(params.clue):
        raise StoryError("The chosen clue is not suitable for this mystery.")


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    mamma = world.add(Entity(id="mamma", kind="character", type="mother", label=params.mamma))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=params.clue, phrase=f"the {params.clue} clue"))

    world.facts.update(hero=hero, mamma=mamma, clue=clue, place=place)

    # Setup
    world.say(f"On a quiet day, {hero.label} went to {place.label} with {mamma.label}.")
    world.say(f"The room was {place.mood}, and {hero.label} noticed {clue.phrase} near a shadowed corner.")
    world.say(f"{hero.label} liked mysteries, but this one felt harder because the clue seemed out of place.")

    # Problem
    world.para()
    contaminate_clue(world, "clue")
    hero.memes["fear"] = 1.0
    world.say(f"{hero.label} took one careful step back. {hero.pronoun().capitalize()} wondered who had touched it first.")
    world.say(f"{mamma.label} pointed to the opposite side of the room and said the answer might be there instead.")

    # Bravery + friendship + solving
    world.para()
    mark_bravery(hero)
    mark_friendship(hero)
    mark_problem_solving(hero)
    world.say(f"{hero.label} felt brave enough to look again.")
    world.say(f"{hero.label} and {mamma.label} searched together, one side at a time, until the opposite shelf made sense.")
    world.say(f"There they found the real clue: a small note that matched the scratch and the footprint.")
    world.say(f"The note showed that the contamination was only mud from outside, not anything scary.")
    world.say(f"{hero.label} smiled, because the mystery had a simple answer after all.")

    # Resolution
    world.para()
    clue.solved = True
    world.say(f"{hero.label} cleaned the clue carefully, and {mamma.label} put it back in its place.")
    world.say(f"By the end, bravery had helped {hero.label} stay calm, friendship had helped {hero.label} search, and problem solving had solved the mystery.")
    world.say(f"The room felt ordinary again, which was the best ending of all.")

    world.facts["solved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mamma: Entity = f["mamma"]  # type: ignore[assignment]
    clue: Entity = f["clue"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        f"Write a gentle mystery story about {hero.label}, {mamma.label}, and a contaminated {clue.label} at {place.label}.",
        f"Tell a child-friendly mystery where bravery, friendship, and problem solving help find the opposite clue.",
        f"Write a short story in which a strange clue in {place.label} is cleaned after the family solves the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mamma: Entity = f["mamma"]  # type: ignore[assignment]
    clue: Entity = f["clue"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {hero.label} and {mamma.label} find the strange clue?",
            answer=f"They found it in {place.label}, where the room felt quiet and a little mysterious.",
        ),
        QAItem(
            question=f"What happened to the {clue.label} clue that made the mystery harder?",
            answer=f"It got contaminated, so {hero.label} had to look carefully instead of guessing too fast.",
        ),
        QAItem(
            question=f"How did {hero.label} solve the mystery with {mamma.label}?",
            answer=f"{hero.label} used bravery to keep looking, friendship to work with {mamma.label}, and problem solving to follow the clue on the opposite side of the room.",
        ),
        QAItem(
            question=f"What did {mamma.label} help {hero.label} understand?",
            answer=f"{mamma.label} helped {hero.label} understand that the answer was not scary at all, just ordinary mud and a useful note.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does opposite mean?",
        answer="Opposite means something is on the other side or is a different kind of thing, like hot and cold or left and right.",
    ),
    QAItem(
        question="What is bravery?",
        answer="Bravery is being willing to keep going even when something feels a little scary.",
    ),
    QAItem(
        question="What is friendship?",
        answer="Friendship is when people help, listen, and care about each other.",
    ),
    QAItem(
        question="What is problem solving?",
        answer="Problem solving is thinking step by step to find a good answer.",
    ),
    QAItem(
        question="What does contaminate mean?",
        answer="To contaminate something means to make it dirty or mixed with something it should not have.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        out.append(f"{i}. {prompt}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for clue in place.clues:
            lines.append(asp.fact("clue", clue))
    for a, b in OPPOSITES:
        lines.append(asp.fact("opp", a, b))
        lines.append(asp.fact("opp", b, a))
    lines.append(asp.fact("brave", "h"))
    lines.append(asp.fact("friend", "h"))
    lines.append(asp.fact("solve", "h"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1.\n#show mystery_possible/1."))
    atoms = set((sym.name, tuple(a.number if a.type.name == "Number" else a.string if a.type.name == "String" else a.name for a in sym.arguments)) for sym in model)
    if ("solved", ("h",)) in atoms:
        print("OK: ASP program produces a solved mystery model.")
        return 0
    print("ASP verification failed.")
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery storyworld.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--mamma", choices=MAMMAS)
    ap.add_argument("--clue", choices=CLUE_WORDS)
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
    place = args.place or rng.choice(sorted(PLACES))
    hero = args.hero or rng.choice(sorted(HEROES))
    hero_type = args.hero_type or HEROES[hero]
    mamma = args.mamma or rng.choice(MAMMAS)
    clue = args.clue or rng.choice(CLUE_WORDS)
    params = StoryParams(place=place, hero=hero, hero_type=hero_type, mamma=mamma, clue=clue)
    reasonable(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        pieces = []
        if ent.contaminated:
            pieces.append("contaminated")
        if ent.solved:
            pieces.append("solved")
        if ent.meters.get("contaminate"):
            pieces.append(f"contaminate={ent.meters['contaminate']}")
        memes = {k: v for k, v in ent.memes.items() if v}
        if memes:
            pieces.append(f"memes={memes}")
        lines.append(f"{ent.id}: {ent.label} ({ent.type}) " + " ".join(pieces))
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


CURATED = [
    StoryParams(place="attic", hero="Nina", hero_type="girl", mamma="mamma", clue="footprints"),
    StoryParams(place="garden", hero="Toby", hero_type="boy", mamma="mother", clue="bucket"),
    StoryParams(place="library", hero="Mira", hero_type="girl", mamma="momma", clue="bookmark"),
]


def asp_list() -> list[tuple[str, ...]]:
    import asp
    model = asp.one_model(asp_program("#show solved/1.\n#show mystery_possible/1."))
    return sorted({tuple([sym.name] + [a.name if a.type.name == "Function" else a.string if a.type.name == "String" else str(a.number) if a.type.name == "Number" else a.name for a in sym.arguments]) for sym in model})


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1.\n#show mystery_possible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show solved/1.\n#show mystery_possible/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            reasonable(params)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
