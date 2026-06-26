#!/usr/bin/env python3
"""
Standalone story world: Raspberry Flashback Mystery

A small, classical simulation about a child detective, a missing raspberry
treat, and the flashback that reveals where it went.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    phrase: str
    reveal: str
    hint: str


@dataclass
class Mystery:
    id: str
    missing_label: str
    missing_phrase: str
    reason: str
    search_zone: str
    flashback_detail: str
    ending_image: str
    clue: Clue


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
SETTINGS = {
    "kitchen": Setting("the kitchen", indoor=True),
    "garden": Setting("the garden"),
    "market": Setting("the market"),
    "porch": Setting("the porch"),
}

MYSTERIES = {
    "basket": Mystery(
        id="basket",
        missing_label="raspberry basket",
        missing_phrase="a little basket full of raspberries",
        reason="someone needed the berries for a tart",
        search_zone="windowsill",
        flashback_detail="the basket had been set near the bright window while the tart cooled",
        ending_image="the tart sat safe and pink on the table",
        clue=Clue(
            id="note",
            label="sticky note",
            kind="note",
            phrase="a sticky note with one raspberry stain",
            reveal="the note mentioned the tart",
            hint="It pointed toward the kitchen table.",
        ),
    ),
    "jam": Mystery(
        id="jam",
        missing_label="raspberry jam",
        missing_phrase="a small jar of raspberry jam",
        reason="someone had used it on toast",
        search_zone="pantry shelf",
        flashback_detail="the jar had been left open beside the bread",
        ending_image="the jam jar was back beside the loaf, with one red drip on the lid",
        clue=Clue(
            id="spoon",
            label="spoon",
            kind="spoon",
            phrase="a spoon with a pink smear",
            reveal="the spoon had raspberry on it",
            hint="It pointed toward breakfast.",
        ),
    ),
    "pie": Mystery(
        id="pie",
        missing_label="raspberry pie",
        missing_phrase="one raspberry pie with a golden crust",
        reason="someone had sliced it for a surprise snack",
        search_zone="cooling rack",
        flashback_detail="the pie had rested by the oven after baking",
        ending_image="the last pie slice waited on a blue plate, smelling sweet",
        clue=Clue(
            id="crumb",
            label="crumb trail",
            kind="crumbs",
            phrase="a few pink crumbs on the floor",
            reveal="the crumbs showed the pie had been carried away",
            hint="They led back to the kitchen.",
        ),
    ),
}

HEROES = [
    ("Mina", "girl", "curious"),
    ("Leo", "boy", "careful"),
    ("Nora", "girl", "patient"),
    ("Theo", "boy", "brave"),
]

HELPERS = [
    ("Grandma", "grandmother"),
    ("Dad", "father"),
    ("Mom", "mother"),
]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    hero_type: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.hero_type,
        meters={"curiosity": 1.0, "search": 0.0},
        memes={"curiosity": 2.0, "worry": 0.0, "joy": 0.0, "understanding": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=next(t for n, t in HELPERS if n == params.helper),
        meters={"care": 1.0},
        memes={"calm": 1.0, "memory": 1.0},
    ))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=mystery.missing_label,
        label=mystery.missing_label,
        phrase=mystery.missing_phrase,
        meters={"lost": 1.0},
    ))
    clue = world.add(Entity(
        id=mystery.clue.id,
        kind="thing",
        type=mystery.clue.kind,
        label=mystery.clue.label,
        phrase=mystery.clue.phrase,
        meters={"noticed": 1.0},
    ))

    # Act 1
    world.say(
        f"{hero.id} was a {params.trait} little {params.hero_type} who loved looking for patterns, "
        f"especially when the room smelled sweet."
    )
    world.say(
        f"One morning at {setting.place}, {hero.id} noticed {missing.phrase} was gone."
    )
    world.say(
        f"{hero.id} felt worried, because {mystery.reason}."
    )

    # Act 2: search and flashback
    world.para()
    hero.meters["search"] += 1
    hero.memes["worry"] += 1.5
    world.say(
        f"{hero.id} searched the {mystery.search_zone}, then peeked under bowls and behind cups."
    )
    world.say(
        f"{helper.id} bent down beside {hero.id} and said, "
        f"'{mystery.clue.hint}'"
    )

    # Flashback
    world.say(
        f"Then {hero.id} remembered something from before: {mystery.flashback_detail}."
    )
    world.say(
        f"In the flashback, {hero.id} had seen the clue {clue.phrase} near the missing treat."
    )
    hero.memes["understanding"] += 2.0
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)

    # Resolution
    world.para()
    world.say(
        f"{hero.id} followed the memory back to the right spot and found that {missing.phrase} was not stolen at all."
    )
    if mystery.id == "jam":
        world.say("It had simply been moved for breakfast, and the toast had been waiting patiently.")
    elif mystery.id == "pie":
        world.say("It had been cut into a careful slice for sharing.")
    else:
        world.say("It had been brought aside so the tart could cool before anyone touched it.")

    hero.memes["joy"] += 2.0
    helper.memes["calm"] += 1.0
    world.say(
        f"{hero.id} smiled, because the mystery was solved and the sweet treat was safe again."
    )
    world.say(mystery.ending_image)

    world.facts.update(
        hero=hero,
        helper=helper,
        mystery=mystery,
        missing=missing,
        clue=clue,
        setting=setting,
        solved=True,
        flashback=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        f'Write a child-friendly mystery story set at {setting.place} about {hero.id} and {mystery.missing_label}.',
        f'Tell a short story that includes a flashback and the word "raspberry" while a child solves a missing-treat mystery.',
        f'Write a gentle detective story where a child notices something missing, remembers an earlier clue, and finds {mystery.missing_label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What was missing at {setting.place}?",
            answer=f"{mystery.missing_phrase} was missing at {setting.place}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} think about the clue?",
            answer=f"{helper.id} helped {hero.id} think about the clue and stay calm.",
        ),
        QAItem(
            question="What made this story a flashback mystery?",
            answer=(
                f"It was a flashback mystery because {hero.id} remembered an earlier moment "
                f"that showed where the missing {mystery.missing_label} had been."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the mystery solved and {mystery.ending_image}.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a raspberry?",
        answer="A raspberry is a small red fruit that tastes sweet and a little tart.",
    ),
    QAItem(
        question="What is a flashback in a story?",
        answer="A flashback is when a story briefly remembers something that happened earlier.",
    ),
    QAItem(
        question="Why do clues matter in a mystery?",
        answer="Clues matter because they help the detective figure out what happened.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(kitchen). setting(garden). setting(market). setting(porch).
indoor(kitchen).

mystery(basket). mystery(jam). mystery(pie).

has_flashback(M) :- mystery(M).
has_raspberry(M) :- mystery(M).

valid(Setting, Mystery) :- setting(Setting), mystery(Mystery), has_flashback(Mystery), has_raspberry(Mystery).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if SETTINGS[sid].indoor:
            lines.append(asp.fact("indoor", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("has_flashback", mid))
        lines.append(asp.fact("has_raspberry", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    return sorted((s, m) for s in SETTINGS for m in MYSTERIES)


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(python_valid())
    if a == p:
        print(f"OK: ASP parity verified for {len(a)} combinations.")
        return 0
    print("MISMATCH between ASP and Python:")
    if a - p:
        print("  only in ASP:", sorted(a - p))
    if p - a:
        print("  only in Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Raspberry flashback mystery storyworld.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=[n for n, _ in HELPERS])
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    name, hero_type, trait = rng.choice(HEROES)
    if args.gender:
        choices = [x for x in HEROES if x[1] == args.gender]
        if not choices:
            raise StoryError("No hero matches that gender.")
        name, hero_type, trait = rng.choice(choices)
    helper = args.helper or rng.choice([n for n, _ in HELPERS])
    if args.name:
        name = args.name
    return StoryParams(
        setting=setting,
        mystery=mystery,
        name=name,
        hero_type=hero_type,
        helper=helper,
        trait=trait,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible settings/mysteries:")
        for s, m in combos:
            print(f"  {s:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in sorted(SETTINGS):
            for m in sorted(MYSTERIES):
                params = StoryParams(
                    setting=s,
                    mystery=m,
                    name=HEROES[0][0],
                    hero_type=HEROES[0][1],
                    helper=HELPERS[0][0],
                    trait=HEROES[0][2],
                    seed=base_seed,
                )
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) > 1:
            p = sample.params
            print(f"### {idx + 1}. {p.name} at {p.setting} ({p.mystery})")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
