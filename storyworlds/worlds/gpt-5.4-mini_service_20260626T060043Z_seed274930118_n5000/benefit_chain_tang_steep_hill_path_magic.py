#!/usr/bin/env python3
"""
A small storyworld about a steep hill path where a mysterious chain of favors,
a tricky tang of magic, and a suspenseful problem lead to a happy ending.

The seed imagery is simple:
- A child walks a steep hill path.
- A helpful charm and a chain of linked actions create both benefit and trouble.
- A tangy snag threatens the plan.
- The story resolves with a magical fix and a clear happy ending.

This script keeps a live world model with physical meters and emotional memes,
and emits a child-facing story plus grounded QA.
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
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "steep_hill_path": {
        "label": "the steep hill path",
        "detail": "The path climbed high and curved around a quiet stand of pines.",
    }
}

CHARACTER_TYPES = {
    "child": {"subject": "they", "object": "them", "possessive": "their"},
    "girl": {"subject": "she", "object": "her", "possessive": "her"},
    "boy": {"subject": "he", "object": "him", "possessive": "his"},
}

NAMES = {
    "girl": ["Mina", "Lena", "Tess", "Nora", "Ivy"],
    "boy": ["Finn", "Owen", "Eli", "Milo", "Theo"],
    "child": ["Robin", "Pip", "Sage", "Ari", "Rowan"],
}

MYSTERY_WORDS = ["tang", "chain", "benefit", "magic"]


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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        table = CHARACTER_TYPES.get(self.type, CHARACTER_TYPES["child"])
        return table[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper logic
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def character_title(gender: str) -> str:
    return {"girl": "girl", "boy": "boy", "child": "child"}[gender]


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES[gender])


def choose_gender(rng: random.Random) -> str:
    return rng.choice(["girl", "boy", "child"])


def emotion_line(world: World, hero: Entity) -> str:
    if hero.memes.get("suspense", 0.0) >= THRESHOLD:
        return f"{hero.id} felt a hush of suspense as the hill grew steeper."
    return f"{hero.id} kept going, curious about what the path would reveal."


def benefit_chain_line(world: World, hero: Entity) -> str:
    chain = world.facts["chain"]
    benefit = world.facts["benefit"]
    tang = world.facts["tang"]
    return (
        f"First came the {chain}, then the {benefit}, and after that the odd little {tang} "
        f"that made the path feel like a riddle."
    )


def prediction(world: World, hero: Entity) -> dict:
    sim = world.copy()
    _walk(sim, sim.get(hero.id), narrate=False)
    return {
        "stuck": sim.facts.get("stuck", False),
        "helped": sim.facts.get("helped", False),
    }


def _walk(world: World, hero: Entity, narrate: bool = True) -> None:
    hero.meters["progress"] = hero.meters.get("progress", 0.0) + 1.0
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1.0
    world.facts["stuck"] = world.facts.get("stuck", False) or world.facts.get("tang_trouble", False)
    if narrate:
        world.say(
            f"{hero.id} climbed the steep hill path with careful steps."
        )


def reveal_tang(world: World, hero: Entity) -> None:
    world.facts["tang_trouble"] = True
    hero.meters["tang"] = hero.meters.get("tang", 0.0) + 1.0
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1.0
    world.say(
        f"Halfway up, {hero.id} spotted a strange tang in the air, like orange peel and rain."
    )


def mystery_hint(world: World, hero: Entity) -> None:
    world.say(
        f"The hint seemed small, but it mattered; the hill kept its secret a little longer."
    )


def magic_help(world: World, hero: Entity) -> None:
    world.facts["helped"] = True
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    hero.memes["suspense"] = 0.0
    world.say(
        f"Then a tiny bit of magic glittered in {hero.pronoun('possessive')} palm, and the tang lifted away."
    )


def happy_ending(world: World, hero: Entity) -> None:
    world.say(
        f"By the top of the hill, the path felt friendly again, and {hero.id} smiled at the bright view."
    )
    world.say(
        f"It was the sort of ending that made the whole mystery feel kind."
    )


def tell_story(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    world = World(params.place)
    gender = params.gender
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=gender,
            meters={"progress": 0.0},
            memes={"suspense": 0.0},
        )
    )

    world.facts.update(
        place=params.place,
        chain="chain of favors",
        benefit="small benefit",
        tang="tangy magic clue",
        magic="tiny magic",
        style="mystery",
    )

    world.say(
        f"{hero.id} went along {PLACES[params.place]['label']} and noticed the quiet trees watching from above."
    )
    world.say(PLACES[params.place]["detail"])
    world.say(
        f"{hero.id} had heard a story about a {world.facts['chain']}, where one good turn led to another."
    )
    world.say(
        f"The first part was a {world.facts['benefit']} because it helped {hero.id} keep going."
    )

    _walk(world, hero)
    reveal_tang(world, hero)
    mystery_hint(world, hero)

    pred = prediction(world, hero)
    if pred["stuck"]:
        world.say(
            f"For a moment, it seemed the climb might end in a tangle."
        )
    hero.memes["suspense"] += 1.0
    world.para()
    magic_help(world, hero)
    happy_ending(world, hero)

    world.facts["resolved"] = True
    world.facts["hero"] = hero
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    return [
        'Write a short mystery-style story for a young child set on a steep hill path with a tiny bit of magic.',
        f"Tell a suspenseful story about {hero.id} walking a steep hill path, finding a tang, and getting help from magic.",
        "Write a gentle story where a chain of helpful actions leads to a happy ending on a hill.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    return [
        QAItem(
            question=f"What kind of path did {hero.id} walk on?",
            answer=f"{hero.id} walked on the steep hill path, which climbed up high and made the trip feel careful and quiet.",
        ),
        QAItem(
            question=f"What strange thing did {hero.id} notice on the hill?",
            answer=f"{hero.id} noticed a tangy clue in the air, and it made the story feel mysterious for a moment.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended happily: a little magic cleared the trouble, and {hero.id} reached the top smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chain?",
            answer="A chain is a line of linked pieces or linked events, where one thing connects to the next.",
        ),
        QAItem(
            question="What does benefit mean?",
            answer="A benefit is something helpful that makes a situation better.",
        ),
        QAItem(
            question="What is tang?",
            answer="Tang can mean a sharp, lively taste or smell that stands out and feels a little surprising.",
        ),
        QAItem(
            question="What does magic often mean in a story?",
            answer="Magic in a story is a special kind of power that can do surprising things and help solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(steep_hill_path).
word(chain).
word(benefit).
word(tang).
feature(magic).
feature(happy_ending).
feature(suspense).

valid_story(P) :- place(P).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "steep_hill_path"),
        asp.fact("word", "chain"),
        asp.fact("word", "benefit"),
        asp.fact("word", "tang"),
        asp.fact("feature", "magic"),
        asp.fact("feature", "happy_ending"),
        asp.fact("feature", "suspense"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("steep_hill_path",)}
    if atoms == py:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld on a steep hill path with magic, suspense, and a happy ending.")
    ap.add_argument("--place", choices=list(PLACES), default="steep_hill_path")
    ap.add_argument("--gender", choices=["girl", "boy", "child"])
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
    gender = args.gender or choose_gender(rng)
    if gender not in NAMES:
        raise StoryError("Unsupported gender.")
    name = args.name or choose_name(rng, gender)
    return StoryParams(place=args.place, name=name, gender=gender)


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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"facts={dict(world.facts)}")
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        genders = ["girl", "boy", "child"]
        for i, g in enumerate(genders):
            params = StoryParams(place="steep_hill_path", name=NAMES[g][0], gender=g, seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
