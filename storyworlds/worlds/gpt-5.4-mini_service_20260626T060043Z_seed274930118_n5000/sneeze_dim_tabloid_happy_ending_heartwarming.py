#!/usr/bin/env python3
"""
A heartwarming little storyworld about a family, a tabloid, and a small
mistake that gets turned into a kinder ending.

Seed words:
- sneeze-dim
- tabloid

Premise:
A child finds a tabloid with a sneeze-dim headline about their favorite
neighborhood baker. The rumor makes everyone worried, but the family chooses to
check the facts, share warm food, and fix the misunderstanding with kindness.

World model:
- physical meters track paper damage, soup warmth, and poster neatness
- emotional memes track worry, courage, relief, and gratitude

The story is designed to end happily, with the tabloid becoming a notice that
tells the truth instead of the rumor.
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
# Domain registries
# ---------------------------------------------------------------------------

NAMES_CHILD = ["Mina", "Perry", "Luna", "Jules", "Toby", "Nora"]
NAMES_ADULT = ["Mum", "Dad", "Auntie Rose", "Uncle Ben", "Grandma", "Grandpa"]

PLACES = {
    "kitchen": {
        "label": "the kitchen",
        "kind": "cozy",
        "supports": {"read", "share_soup", "make_notice"},
    },
    "corner_shop": {
        "label": "the corner shop",
        "kind": "busy",
        "supports": {"buy_paper", "ask_questions"},
    },
    "bakery": {
        "label": "the bakery",
        "kind": "warm",
        "supports": {"visit_baker", "share_soup", "make_notice"},
    },
    "porch": {
        "label": "the porch",
        "kind": "quiet",
        "supports": {"read", "make_notice"},
    },
}

ACTIVITIES = {
    "read_tabloid": {
        "verb": "read the tabloid",
        "gerund": "reading the tabloid",
        "effect": {"worry": 1, "curiosity": 1},
        "risk": "worry",
        "rumor": "sneeze-dim",
        "prompt": "a child finds a sneaky tabloid headline",
    },
    "visit_bakery": {
        "verb": "visit the bakery",
        "gerund": "walking to the bakery",
        "effect": {"courage": 1, "worry": -1},
        "risk": None,
        "prompt": "checking the truth in person",
    },
    "make_notice": {
        "verb": "make a new notice",
        "gerund": "making a kinder notice",
        "effect": {"kindness": 1, "gratitude": 1},
        "risk": None,
        "prompt": "fixing a rumor with a warm message",
    },
    "share_soup": {
        "verb": "share soup",
        "gerund": "sharing soup",
        "effect": {"warmth": 1, "gratitude": 1},
        "risk": None,
        "prompt": "ending the day with a cozy meal",
    },
}

OBJECTS = {
    "tabloid": {
        "label": "tabloid",
        "phrase": "a tabloid with a sneeze-dim headline",
        "place": "corner_shop",
        "meters": {"folds": 1, "ink": 1},
        "memes": {"alarm": 1},
    },
    "notice": {
        "label": "notice",
        "phrase": "a fresh notice with the truth on it",
        "place": "bakery",
        "meters": {"neatness": 1},
        "memes": {"hope": 1},
    },
    "soup": {
        "label": "soup",
        "phrase": "a pot of warm vegetable soup",
        "place": "kitchen",
        "meters": {"warmth": 2},
        "memes": {"care": 1},
    },
}

# ---------------------------------------------------------------------------
# Shared containers and world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.id in {"Mina", "Luna", "Nora", "Auntie Rose", "Grandma"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.id in {"Perry", "Jules", "Toby", "Dad", "Uncle Ben", "Grandpa"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    adult: str
    seed: Optional[int] = None

@dataclass
class World:
    place: str
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

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _add_effects(target: Entity, effect: dict[str, float]) -> None:
    for k, v in effect.items():
        target.meters[k] = target.meters.get(k, 0) + v
        if target.meters[k] < 0:
            target.meters[k] = 0

def setup_world(params: StoryParams) -> World:
    world = World(place=params.place)
    child = world.add(Entity(id=params.name, kind="character", label=params.name))
    adult = world.add(Entity(id=params.adult, kind="character", label=params.adult))
    tabloid = world.add(Entity(
        id="tabloid",
        label="tabloid",
        phrase=OBJECTS["tabloid"]["phrase"],
        meters=dict(OBJECTS["tabloid"]["meters"]),
        memes=dict(OBJECTS["tabloid"]["memes"]),
    ))
    notice = world.add(Entity(
        id="notice",
        label="notice",
        phrase=OBJECTS["notice"]["phrase"],
        meters=dict(OBJECTS["notice"]["meters"]),
        memes=dict(OBJECTS["notice"]["memes"]),
    ))
    soup = world.add(Entity(
        id="soup",
        label="soup",
        phrase=OBJECTS["soup"]["phrase"],
        meters=dict(OBJECTS["soup"]["meters"]),
        memes=dict(OBJECTS["soup"]["memes"]),
    ))
    world.facts.update(child=child, adult=adult, tabloid=tabloid, notice=notice, soup=soup)
    return world

def tell_story(world: World, params: StoryParams) -> None:
    child = world.get(params.name)
    adult = world.get(params.adult)
    tabloid = world.get("tabloid")
    notice = world.get("notice")
    soup = world.get("soup")

    world.say(
        f"{child.id} found a tabloid on the counter in {PLACES[params.place]['label']}."
        f" The headline was sneeze-dim and mean-looking, and it made {child.id} feel small."
    )
    _add_effects(child, {"worry": 1, "curiosity": 1})
    _add_effects(adult, {"worry": 1})

    world.para()
    world.say(
        f"{adult.id} did not want to believe the rumor. So {adult.id} sat beside {child.id},"
        f" read the tabloid carefully, and said, \"Let's check the bakery before we worry.\""
    )
    _add_effects(child, {"courage": 1})
    _add_effects(adult, {"courage": 1})

    world.para()
    world.say(
        f"They walked to {PLACES['bakery']['label']} and found {OBJECTS['soup']['phrase']}"
        f" cooling on the stove while the baker smiled at them."
    )
    world.say(
        "The baker explained that the tabloid had guessed wrong."
        " The sneeze-dim headline was only a messy mistake, not the truth."
    )
    _add_effects(child, {"worry": -1, "relief": 2, "kindness": 1})
    _add_effects(adult, {"worry": -1, "relief": 2, "kindness": 1})

    world.para()
    world.say(
        f"Back home, {child.id} and {adult.id} wrote a new notice and pinned it over the tabloid."
        f" It told the true story: the bakery was fine, the baker was kind, and the soup was for everyone."
    )
    _add_effects(notice, {"neatness": 1})
    _add_effects(tabloid, {"ink": 0})
    _add_effects(soup, {"warmth": 1})

    world.para()
    world.say(
        f"That night, {child.id} shared soup with {adult.id}, and the kitchen felt bright and safe."
        f" The tabloid stayed folded under the new notice, and the happy ending smelled like pepper and bread."
    )
    _add_effects(child, {"gratitude": 1, "warmth": 1})
    _add_effects(adult, {"gratitude": 1, "warmth": 1})

# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    return [
        f'Write a heartwarming story about {child.id} finding a tabloid with a sneeze-dim headline.',
        f"Tell a gentle story where {child.id} and {adult.id} check a rumor and discover the truth at the bakery.",
        "Write a short story with a warm ending in which a tabloid mistake is fixed by kindness.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    return [
        QAItem(
            question=f"What did {child.id} find at the beginning of the story?",
            answer=f"{child.id} found a tabloid with a sneeze-dim headline on the counter.",
        ),
        QAItem(
            question=f"Why did {adult.id} want to visit the bakery?",
            answer=f"{adult.id} wanted to check the rumor in person instead of trusting the tabloid.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The family learned the rumor was wrong, made a new notice with the truth, and shared soup together at home.",
        ),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tabloid?",
            answer="A tabloid is a newspaper that often uses big headlines and tries to grab attention quickly.",
        ),
        QAItem(
            question="What does a sneeze-dim headline mean in this story?",
            answer="It means the headline was tiny, messy, and hard to trust, like a little puff of confusion.",
        ),
        QAItem(
            question="Why did the new notice matter?",
            answer="The new notice mattered because it replaced the rumor with the truth and helped everyone feel safe again.",
        ),
    ]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(kitchen). place(corner_shop). place(bakery). place(porch).

activity(read_tabloid). activity(visit_bakery). activity(make_notice). activity(share_soup).

supports(kitchen,read). supports(kitchen,share_soup). supports(kitchen,make_notice).
supports(corner_shop,buy_paper). supports(corner_shop,ask_questions).
supports(bakery,visit_baker). supports(bakery,share_soup). supports(bakery,make_notice).
supports(porch,read). supports(porch,make_notice).

valid_story(P,A) :- place(P), activity(A),
    (P = kitchen, A = read_tabloid;
     P = corner_shop, A = read_tabloid;
     P = bakery, A = visit_bakery;
     P = kitchen, A = make_notice;
     P = bakery, A = make_notice;
     P = kitchen, A = share_soup;
     P = bakery, A = share_soup;
     P = porch, A = read_tabloid).

#show valid_story/2.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))

def verify_asp() -> int:
    py = {
        ("kitchen", "read_tabloid"),
        ("corner_shop", "read_tabloid"),
        ("bakery", "visit_bakery"),
        ("kitchen", "make_notice"),
        ("bakery", "make_notice"),
        ("kitchen", "share_soup"),
        ("bakery", "share_soup"),
        ("porch", "read_tabloid"),
    }
    asp_set = set(asp_valid_pairs())
    if asp_set == py:
        print(f"OK: clingo gate matches python gate ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and python gate.")
    print("only in asp:", sorted(asp_set - py))
    print("only in python:", sorted(py - asp_set))
    return 1

# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld with a tabloid rumor and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name", choices=NAMES_CHILD)
    ap.add_argument("--adult", choices=NAMES_ADULT)
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
    activity = args.activity or rng.choice(list(ACTIVITIES))
    name = args.name or rng.choice(NAMES_CHILD)
    adult = args.adult or rng.choice(NAMES_ADULT)
    return StoryParams(place=place, activity=activity, name=name, adult=adult)

def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)

def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(parts)

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
        sys.exit(verify_asp())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid (place, activity) pairs:\n")
        for p, a in pairs:
            print(f"  {p:12} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("kitchen", "read_tabloid", "Mina", "Mum"),
            StoryParams("corner_shop", "read_tabloid", "Perry", "Dad"),
            StoryParams("bakery", "visit_bakery", "Luna", "Grandma"),
            StoryParams("kitchen", "make_notice", "Jules", "Auntie Rose"),
            StoryParams("bakery", "share_soup", "Toby", "Grandpa"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
