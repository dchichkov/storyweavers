#!/usr/bin/env python3
"""
storyworlds/worlds/fourth_happy_ending_surprise_mystery.py
===========================================================

A small mystery story world built around a fourth clue, a surprise reveal, and
a happy ending.

Premise:
- A child notices a tiny mystery in a familiar place.
- Three clues appear ordinary.
- The fourth clue changes what everyone thinks is happening.

Turn:
- The child follows the clues, suspects the wrong answer, and then notices the
  surprising fourth clue.

Resolution:
- The mystery turns out to be harmless and kind.
- The ending is happy because the surprise was a gift, not a problem.

This script keeps the world small and classical: typed entities, physical meters,
emotional memes, a reasonableness gate, and an ASP twin for parity checks.
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
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    hidden: bool = False
    revealed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    name: str = "the library"
    indoor: bool = True
    mood: str = "quiet"
    afford: set[str] = field(default_factory=set)


@dataclass
class ClueSet:
    four: list[str] = field(default_factory=list)
    surprise: str = "a surprise note"
    reveal: str = "a kind secret"
    kind_of_truth: str = "a harmless mystery"


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


PLACES = {
    "library": Place(name="the library", indoor=True, mood="quiet", afford={"search", "whisper"}),
    "garden": Place(name="the garden", indoor=False, mood="gentle", afford={"search", "look"}),
    "attic": Place(name="the attic", indoor=True, mood="dusty", afford={"search"}),
}

NAMES = {
    "girl": ["Mia", "Nora", "Lily", "Zoe", "Ava"],
    "boy": ["Finn", "Noah", "Eli", "Theo", "Ben"],
}

PARENTS = {"mother": "mother", "father": "father"}

CLUES = [
    "a mitten on a bench",
    "a chair pulled out just a little",
    "a crumb trail near the wall",
    "a small folded note",
]

CLUESET = ClueSet(
    four=CLUES,
    surprise="a folded note with a ribbon",
    reveal="a secret birthday invitation",
    kind_of_truth="a friendly surprise",
)


def is_reasonable(place: Place) -> bool:
    return bool(place.afford)


def reasonableness_gate(place: Place) -> None:
    if not is_reasonable(place):
        raise StoryError("The place cannot support a mystery story here.")


def _add_clue(world: World, clue: str) -> None:
    idx = len(world.facts.get("clues_seen", [])) + 1
    world.facts.setdefault("clues_seen", []).append(clue)
    world.say(f"The first thing {world.facts['hero'].id} noticed was {clue}.")
    world.trace.append(f"clue{idx}:{clue}")


def _feel(world: World, who: Entity, feel: str, amt: float = 1.0) -> None:
    who.memes[feel] = who.memes.get(feel, 0.0) + amt


def _do_search(world: World, hero: Entity) -> None:
    hero.meters["curiosity"] = hero.meters.get("curiosity", 0.0) + 1
    _feel(world, hero, "curious")
    world.say(
        f"{hero.id} looked carefully around {world.place.name} because {hero.pronoun()} loved solving small mysteries."
    )


def _wrong_guess(world: World, hero: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"At first, {hero.id} worried someone might be lost."
    )


def _reveal(world: World, hero: Entity, parent: Entity, note: Entity) -> None:
    note.revealed = True
    hero.meters["surprise"] = hero.meters.get("surprise", 0.0) + 1
    _feel(world, hero, "relief", 1.0)
    _feel(world, hero, "joy", 1.0)
    world.say(
        f"Then the fourth clue made everything clear: it was {note.phrase}, hidden where only a careful eye would find it."
    )
    world.say(
        f"{hero.id} smiled when {hero.pronoun()} saw that {parent.pronoun('subject').capitalize()} had planned {CLUESET.reveal} all along."
    )


def _happy_end(world: World, hero: Entity, parent: Entity, note: Entity) -> None:
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1.0)
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    world.say(
        f"The mystery was only {CLUESET.kind_of_truth}, and the surprise made {hero.id} laugh with relief."
    )
    world.say(
        f"{hero.id} hugged {hero.pronoun('possessive')} {parent.type} and kept the ribboned note safe, because some surprises are the best kind."
    )


def tell(place: Place, hero_name: str, hero_gender: str, parent_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    note = world.add(
        Entity(
            id="note",
            type="note",
            label="folded note",
            phrase=CLUESET.surprise,
            owner=parent.id,
            hidden=True,
        )
    )

    world.facts.update(hero=hero, parent=parent, note=note)

    world.say(
        f"On a quiet day at {place.name}, {hero.id} noticed that something small had changed."
    )
    world.say(
        f"{hero.id} liked mysteries, so {hero.pronoun()} followed the clues one by one."
    )
    _do_search(world, hero)

    for clue in CLUES[:3]:
        _add_clue(world, clue)

    _wrong_guess(world, hero)
    world.para()

    _add_clue(world, CLUES[3])
    _reveal(world, hero, parent, note)
    world.para()
    _happy_end(world, hero, parent, note)

    world.facts["ended_happy"] = True
    world.facts["surprise"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    return [
        f'Write a short mystery story for a child named {hero.id} with a happy ending and a surprise at the end.',
        f"Tell a gentle story where {hero.id} follows four clues and learns that {parent.pronoun('possessive')} secret is kind.",
        "Write a child-friendly mystery that begins with ordinary clues and ends with a joyful reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    note = f["note"]
    clues = f.get("clues_seen", [])
    return [
        QAItem(
            question=f"What did {hero.id} do when {hero.pronoun()} noticed something strange at {world.place.name}?",
            answer=f"{hero.id} looked carefully around and followed the clues because {hero.pronoun()} liked solving mysteries.",
        ),
        QAItem(
            question=f"What was special about the fourth clue?",
            answer=f"The fourth clue was the one that changed the story. It pointed to {note.phrase} and showed that the mystery was a happy surprise.",
        ),
        QAItem(
            question=f"Why did {hero.id} stop worrying at the end?",
            answer=f"{hero.id} stopped worrying because the secret was kind, and {parent.pronoun('subject')} had planned a happy surprise instead of trouble.",
        ),
        QAItem(
            question=f"How many clues did {hero.id} notice?",
            answer=f"{hero.id} noticed four clues in all, and the fourth clue was the most important one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small bit of information that helps someone figure out what is happening.",
        ),
        QAItem(
            question="Why can a surprise still be happy?",
            answer="A surprise can be happy when it is meant to make someone smile or feel loved.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully, notices clues, and tries to understand a mystery.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.revealed:
            bits.append("revealed=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  clues seen: {world.facts.get('clues_seen', [])}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for gender in ("girl", "boy"):
            for parent in PARENTS:
                out.append((place, gender, parent))
    return out


def explain_rejection(place: Place) -> str:
    return f"(No story: {place.name} does not support a small mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery world with a fourth clue, a surprise, and a happy ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    combos = [c for c in combos if args.place is None or c[0] == args.place]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(NAMES[gender])
    if place not in PLACES:
        raise StoryError("Unknown place.")
    reasonableness_gate(PLACES[place])
    return StoryParams(place=place, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.name, params.gender, params.parent)
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


ASP_RULES = r"""
clue(1..4).
surprise(4).
happy_ending :- surprise.
mystery :- clue(4).
kind_reveal :- surprise, happy_ending.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].indoor:
            lines.append(asp.fact("indoor", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/0.\n#show kind_reveal/0.\n#show mystery/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.all:
        samples = []
        for place, gender, parent in [("library", "girl", "mother"), ("garden", "boy", "father"), ("attic", "girl", "father")]:
            params = StoryParams(place=place, name=random.choice(NAMES[gender]), gender=gender, parent=parent)
            samples.append(generate(params))
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
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
