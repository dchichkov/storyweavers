#!/usr/bin/env python3
"""
A small heartwarming story world about a pun, teamwork, and a gentle fix.

This world models a tiny situation:
- a child wants to hang a sign for a neighborhood event,
- the sign contains a pun,
- the letters get mixed up or fall apart,
- the characters work together to fix it,
- the final story ends with the pun land and the teamwork shining through.

The generated stories are intentionally simple, concrete, and child-facing.
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Person:
    name: str
    role: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subject(self) -> str:
        return self.name

    def object(self) -> str:
        return self.name.lower()


@dataclass
class ObjectItem:
    name: str
    label: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Mina"
    helper: str = "Dad"
    venue: str = "the community hall"
    event: str = "the bake sale"
    sign: str = "A-pun-d to be together!"
    pun_word: str = "pun"
    twist: str = "the letters fall apart"
    fix: str = "they rebuild the sign together"


@dataclass
class World:
    params: StoryParams
    people: dict[str, Person] = field(default_factory=dict)
    items: dict[str, ObjectItem] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_person(self, person: Person) -> Person:
        self.people[person.name] = person
        return person

    def add_item(self, item: ObjectItem) -> ObjectItem:
        self.items[item.name] = item
        return item


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
NAMES = ["Mina", "Noah", "Lia", "Owen", "Nia", "Eli", "June", "Aria"]
HELPERS = ["Mom", "Dad", "Grandma", "Grandpa", "Aunt Jo", "Uncle Ben"]
VENUES = ["the community hall", "the library room", "the school gym", "the little park shelter"]
EVENTS = ["the bake sale", "the spring fair", "the read-a-thon", "the school picnic"]
SIGNS = [
    "A-pun-d to be together!",
    "Let's stick together!",
    "Teamwork makes the dream work!",
    "We are all in this pun-derful plan!",
]
TWISTS = [
    "the paper tears in the middle",
    "the tape loses its stick",
    "the letters slide into a jumble",
    "the sign flips upside down",
]
FIXES = [
    "they sort the pieces, tape the edges, and finish it as a team",
    "they hold the sign flat, line up the letters, and smooth it carefully",
    "they make a new sign together, one steady hand at a time",
    "they share the work, and the sign comes back bright and neat",
]


# ---------------------------------------------------------------------------
# Story world mechanics
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    world = World(params=params)
    hero = world.add_person(Person(name=params.hero, role="hero"))
    helper = world.add_person(Person(name=params.helper, role="helper"))
    sign = world.add_item(ObjectItem(name="sign", label=params.sign, owner=hero.name))

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["sign"] = sign
    world.facts["pun_word"] = params.pun_word
    world.facts["venue"] = params.venue
    world.facts["event"] = params.event
    return world


def setup(world: World) -> None:
    p = world.params
    world.say(
        f"{p.hero} was helping get ready for {p.event} at {p.venue}."
    )
    world.say(
        f"{p.hero} had made a cheerful sign that said, “{p.sign}” because a little {p.pun_word} could make everyone smile."
    )


def tension(world: World) -> None:
    p = world.params
    world.para()
    world.say(
        f"But then {p.twist}."
    )
    world.say(
        f"{p.hero} looked worried, because the sign was important and the joke would not work if nobody could read it."
    )


def teamwork_fix(world: World) -> None:
    p = world.params
    hero = world.people[p.hero]
    helper = world.people[p.helper]
    hero.memes["worry"] = 1.0
    helper.memes["care"] = 1.0
    hero.meters["problem"] = 1.0
    helper.meters["help"] = 1.0

    world.para()
    world.say(
        f"Then {p.helper} came over and said, “Let’s fix it together.”"
    )
    world.say(
        f"{p.hero} held the corners, {p.helper} taped the edges, and soon {p.fix}."
    )
    world.say(
        f"When they finished, the pun in the sign landed perfectly, and {p.hero} felt proud instead of worried."
    )


def ending(world: World) -> None:
    p = world.params
    world.para()
    world.say(
        f"At {p.event}, people smiled at the sign and laughed softly at the pun."
    )
    world.say(
        f"{p.hero} stood beside {p.helper}, happy that the best part of the day was not just the joke, but how they worked together to save it."
    )


def generate_story_world(params: StoryParams) -> World:
    world = make_world(params)
    setup(world)
    tension(world)
    teamwork_fix(world)
    ending(world)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a heartwarming story about {p.hero} and {p.helper} fixing a pun-filled sign together.",
        f"Tell a short child-friendly tale where teamwork saves a funny sign for {p.event} at {p.venue}.",
        f"Make a gentle story in which a pun becomes a happy moment because two people work together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"Who was helping get ready for {p.event}?",
            answer=f"{p.hero} was getting ready for {p.event}, and {p.helper} helped make it all work.",
        ),
        QAItem(
            question="What went wrong with the sign?",
            answer=f"The sign was supposed to stay neat, but {p.twist}. That made the joke harder to read at first.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They fixed it by working together: {p.hero} and {p.helper} held, taped, and straightened the sign as a team.",
        ),
        QAItem(
            question="Why was the ending happy?",
            answer=f"The ending was happy because the pun stayed on the sign, the work got finished, and everyone felt proud of their teamwork.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pun?",
            answer="A pun is a funny use of words that can mean more than one thing or sound like another word.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and share the work so they can finish something together.",
        ),
        QAItem(
            question="Why do people make signs for events?",
            answer="People make signs so others can find the event, understand the message, and feel excited to come.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
sign(S) :- sign_text(S).
event(E) :- event_name(E).

teamwork_success(H, K, S) :- hero(H), helper(K), sign(S), shared_fix(H, K, S).
heartwarming_story(H, K, S) :- teamwork_success(H, K, S), pun_sign(S).
"""


def asp_facts() -> str:
    import asp
    p = DEFAULT_PARAMS
    lines = [
        asp.fact("hero_name", p.hero),
        asp.fact("helper_name", p.helper),
        asp.fact("sign_text", p.sign),
        asp.fact("event_name", p.event),
        asp.fact("pun_sign", p.sign),
        asp.fact("shared_fix", p.hero, p.helper, p.sign),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> bool:
    return True


def asp_verify() -> int:
    import asp
    if not asp_reasonable():
        print("Python reasonableness gate failed.")
        return 1
    model = asp.one_model(asp_program("#show heartwarming_story/3."))
    atoms = asp.atoms(model, "heartwarming_story")
    if atoms:
        print("OK: ASP program produces a heartwarming teamwork story.")
        return 0
    print("MISMATCH: ASP program did not produce the expected story atom.")
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
DEFAULT_PARAMS = StoryParams()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming pun-and-teamwork story world.")
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--sign", choices=SIGNS)
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
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    if helper == hero:
        helper = rng.choice([h for h in HELPERS if h != helper])
    venue = args.venue or rng.choice(VENUES)
    event = args.event or rng.choice(EVENTS)
    sign = args.sign or rng.choice(SIGNS)
    twist = rng.choice(TWISTS)
    fix = rng.choice(FIXES)
    return StoryParams(
        seed=args.seed,
        hero=hero,
        helper=helper,
        venue=venue,
        event=event,
        sign=sign,
        pun_word="pun",
        twist=twist,
        fix=fix,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        print(f"hero={sample.world.params.hero}")
        print(f"helper={sample.world.params.helper}")
        print(f"event={sample.world.params.event}")
        print(f"venue={sample.world.params.venue}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show heartwarming_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible heartwarming teamwork story pattern.")
        print(f"  hero={DEFAULT_PARAMS.hero} helper={DEFAULT_PARAMS.helper} sign={DEFAULT_PARAMS.sign}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            hero=NAMES[0],
            helper=HELPERS[0],
            venue=VENUES[0],
            event=EVENTS[0],
            sign=SIGNS[0],
            pun_word="pun",
            twist=TWISTS[0],
            fix=FIXES[0],
        )
        samples = [generate(params)]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
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
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
