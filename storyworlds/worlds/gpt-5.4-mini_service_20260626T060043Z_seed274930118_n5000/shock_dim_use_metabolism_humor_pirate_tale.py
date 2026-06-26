#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/shock_dim_use_metabolism_humor_pirate_tale.py
==============================================================================================================

A compact pirate-tale storyworld about a silly shipboard trick called the
shock-dim, a hungry crew, and the difference a proper meal can make.

The seed words are woven into the world model:
- shock-dim
- use
- metabolism

The prose stays close to a cheerful pirate tale with humor, clear tension,
and a state-driven ending that proves what changed.
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

SHIP_NAMES = [
    "the Wobblefin",
    "the Rum Plum",
    "the Tippy Turtle",
    "the Bright Barnacle",
]

CHARACTER_NAMES = [
    "Pip",
    "Mara",
    "Jory",
    "Nell",
    "Beck",
    "Tomas",
]

ROLE_NAMES = {
    "captain": "captain",
    "cook": "cook",
    "first_mate": "first mate",
    "deckhand": "deckhand",
    "parrot": "parrot",
}

MOODS = ["cheerful", "stubborn", "spry", "sly", "sleepy"]
SNACKS = [
    "oat cakes",
    "banana buns",
    "fish biscuits",
    "raisin porridge",
    "honey crackers",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "cook"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the deck of the Wobblefin"


@dataclass
class StoryParams:
    ship: str
    hero: str
    hero_role: str
    helper: str
    helper_role: str
    snack: str
    mood: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


def pirate_style_opening(hero: Entity, ship: str) -> str:
    return f"On {ship}, little {hero.id} was the sort who grinned at wind, rope, and trouble."


def metabolism_note(hero: Entity) -> str:
    return f"{hero.id}'s metabolism had been running on empty, so {hero.pronoun()} felt wobbly and cross."


def shock_dim_description() -> str:
    return "the shock-dim, a silly little deck trick that made a lantern go snap-spark and then dim as a wink"


def _resolve_hunger(world: World, hero: Entity, snack: Entity) -> None:
    hero.meters["hunger"] = max(0.0, hero.meters.get("hunger", 0.0) - 1.0)
    hero.meters["energy"] = hero.meters.get("energy", 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    world.say(
        f"After a plate of {snack.label}, {hero.id} felt steadier and smiled. "
        f"The old grumbles in {hero.pronoun('possessive')} belly quieted at last."
    )


def tell(params: StoryParams) -> World:
    world = World(Setting(place=f"the deck of {params.ship}"))

    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type="captain",
            label="captain",
            meters={"hunger": 1.0, "energy": 0.0, "balance": 0.0},
            memes={"joy": 0.0, "frustration": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type=params.helper_role,
            label=ROLE_NAMES[params.helper_role],
            meters={"hunger": 0.0, "energy": 1.0},
            memes={"amusement": 1.0},
        )
    )
    snack = world.add(
        Entity(
            id="snack",
            kind="thing",
            type="snack",
            label=params.snack,
            phrase=params.snack,
            owner=helper.id,
        )
    )
    lantern = world.add(
        Entity(
            id="lantern",
            kind="thing",
            type="lantern",
            label="lantern",
            phrase="a brass lantern",
            owner=hero.id,
        )
    )

    world.say(pirate_style_opening(hero, params.ship))
    world.say(
        f"{hero.id} loved to use {shock_dim_description()} when the crew needed to sneak by a sleepy reef."
    )
    world.say(
        f"{helper.id} the {params.helper_role} was always laughing, because the shock-dim sounded like a sneeze in a bucket."
    )

    world.para()
    world.say(
        f"One moonlit night, {hero.id} wanted to use the shock-dim at once and make {lantern.label} go dim."
    )
    world.say(
        f"But {metabolism_note(hero)} {hero.id} tried to march smartly and only managed a zigzag, like a crab on a wet spoon."
    )
    hero.memes["frustration"] += 1.0
    hero.meters["balance"] += 1.0

    world.say(
        f"{helper.id} peeked at the pantry, then at {hero.id}, and snorted, "
        f'"No pirate can do a proper shock-dim on a hollow stomach."'
    )

    world.para()
    world.say(
        f"{hero.id} puffed out {hero.pronoun('possessive')} cheeks and said {hero.pronoun('subject')} could do it anyway."
    )
    world.say(
        f"So {hero.id} reached for the shock-dim handle, but {hero.pronoun('possessive')} knees gave a tiny squeak."
    )
    if hero.meters["hunger"] >= THRESHOLD:
        world.say(
            f"The deck looked extra far away, and even the gulls seemed to giggle at the wobbly captain."
        )

    world.para()
    world.say(
        f"Then {helper.id} held up a warm bowl of {snack.label} and said, "
        f'"First supper, then showtime."'
    )
    _resolve_hunger(world, hero, snack)

    world.say(
        f"{hero.id} took a good bite, took a good breath, and the silly ship stop wobbling under {hero.pronoun('object')}."
    )
    world.say(
        f"At last {hero.id} used the shock-dim, and snap-spark went the lantern before it slipped to a cozy glow."
    )
    hero.meters["balance"] = 0.0
    hero.memes["frustration"] = 0.0
    hero.memes["joy"] += 1.0

    world.say(
        f"{helper.id} clapped like a happy seal, and {hero.id} bowed so hard that {hero.pronoun('possessive')} hat nearly saluted the sea."
    )
    world.say(
        f"After that, the crew crept past the reef in a neat dark hush, and the captain's belly was full enough to sing only one tiny sea shanty."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        snack=snack,
        lantern=lantern,
        params=params,
        ship=params.ship,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    snack = f["snack"]
    return [
        f'Write a short pirate tale for a young child about a captain who wants to use the shock-dim, but first needs a snack.',
        f"Tell a funny story where {hero.id} and {helper.id} share {snack.label} before a deck trick, so the ship can stay quiet.",
        f'Write a cheerful story with the words "shock-dim", "use", and "metabolism" about a pirate crew that solves a wobbly problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    snack = f["snack"]
    ship = f["ship"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel wobbly on {ship} before using the shock-dim?",
            answer=f"{hero.id} felt wobbly because {hero.pronoun('possessive')} metabolism had been running on empty, and {hero.id} was hungry.",
        ),
        QAItem(
            question=f"What did {helper.id} give {hero.id} before the captain used the shock-dim?",
            answer=f"{helper.id} gave {hero.id} {snack.label} so the captain could eat and steady {hero.pronoun('object')} self first.",
        ),
        QAItem(
            question=f"What happened after {hero.id} ate?",
            answer=f"After {hero.id} ate, {hero.pronoun('possessive')} energy came back, the wobble stopped, and {hero.id} could use the shock-dim to dim the lantern.",
        ),
        QAItem(
            question=f"How did the crew feel about the shock-dim in the end?",
            answer=f"The crew thought it was funny, because the shock-dim made a snap-spark sound and the captain ended up bowing like a clownish pirate hero.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is metabolism?",
            answer="Metabolism is the way a body turns food into energy so a person can move, grow, and stay warm.",
        ),
        QAItem(
            question="What does it mean to use something?",
            answer="To use something means to do the thing it was made for, like using a spoon to eat soup or using a lantern to see in the dark.",
        ),
        QAItem(
            question="Why do pirates like lanterns on a ship?",
            answer="Pirates like lanterns because lanterns help them see at night when the deck is dark and the sea is full of shadows.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [("ship", "shock-dim")]


@dataclass
class StoryParamsRegistry:
    ship: str = "the Wobblefin"
    hero: str = "Pip"
    hero_role: str = "captain"
    helper: str = "Mara"
    helper_role: str = "cook"
    snack: str = "oat cakes"
    mood: str = "cheerful"


CURATED = [
    StoryParams(ship="the Wobblefin", hero="Pip", hero_role="captain", helper="Mara", helper_role="cook", snack="oat cakes", mood="cheerful"),
    StoryParams(ship="the Rum Plum", hero="Nell", hero_role="captain", helper="Jory", helper_role="first_mate", snack="banana buns", mood="sly"),
]


ASP_RULES = r"""
% A pirate story is reasonable when the captain wants to use the shock-dim and
% the crew can fix the wobble with food first.
use_plan(S) :- ship(S), wants_use(shock_dim, S).
needs_snack(S) :- use_plan(S), hungry(captain, S), snack_available(S).
good_story(S) :- needs_snack(S), snack_available(S), can_steady(captain, S).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("ship", "the_Wobblefin"),
        asp.fact("wants_use", "shock_dim", "the_Wobblefin"),
        asp.fact("hungry", "captain", "the_Wobblefin"),
        asp.fact("snack_available", "the_Wobblefin"),
        asp.fact("can_steady", "captain", "the_Wobblefin"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show good_story/1."))
    got = set(asp.atoms(model, "good_story"))
    want = {("the_Wobblefin",)}
    if got == want:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", got, want)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a silly shock-dim and a hungry captain.")
    ap.add_argument("--ship", choices=[s.replace("the ", "the ") for s in SHIP_NAMES])
    ap.add_argument("--hero", choices=CHARACTER_NAMES)
    ap.add_argument("--helper", choices=CHARACTER_NAMES)
    ap.add_argument("--hero-role", choices=["captain"])
    ap.add_argument("--helper-role", choices=["cook", "first_mate", "deckhand"])
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--mood", choices=MOODS)
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
    ship = args.ship or rng.choice(SHIP_NAMES)
    hero = args.hero or rng.choice(CHARACTER_NAMES)
    helper = args.helper or rng.choice([n for n in CHARACTER_NAMES if n != hero])
    helper_role = args.helper_role or rng.choice(["cook", "first_mate", "deckhand"])
    snack = args.snack or rng.choice(SNACKS)
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(
        ship=ship,
        hero=hero,
        hero_role="captain",
        helper=helper,
        helper_role=helper_role,
        snack=snack,
        mood=mood,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show good_story/1."))
        print(asp.atoms(model, "good_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
