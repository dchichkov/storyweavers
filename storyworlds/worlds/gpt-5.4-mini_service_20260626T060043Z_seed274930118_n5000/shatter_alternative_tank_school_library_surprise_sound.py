#!/usr/bin/env python3
"""
storyworlds/worlds/shatter_alternative_tank_school_library_surprise_sound.py
============================================================================

A tiny mythic story world set in a school library, where a child on a quest
faces a surprising sound and must choose an alternative before something
shatters.

The world is built from one short premise:
- In the school library, an apprentice wants to carry a special tank across the
  reading hall.
- A sudden surprise and booming sound effects make the tank wobble.
- The elder keeper offers an alternative path or method.
- The child chooses wisely, and the ending proves what changed.

The domain is deliberately small, causal, and constraint-checked.
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
# Core vocabulary
# ---------------------------------------------------------------------------
SETTING_NAME = "the school library"

NAMES = ["Ari", "Mina", "Tomas", "Lio", "Nora", "Sana", "Eli", "Rin"]
ADJECTIVES = ["brave", "curious", "careful", "earnest", "gentle", "small"]
KEEPER_TITLES = ["librarian", "keeper", "sage", "warden"]
AUDIO = ["rustle", "whisper", "thrum", "clang", "boom", "tap-tap"]

TANK_FORMS = {
    "ink": "a glass ink tank",
    "water": "a small glass tank of shimmering water",
    "light": "a bright lantern tank",
}

ALTERNATIVES = {
    "cart": "a rolling cart",
    "cloth": "a padded cloth wrap",
    "route": "the quiet side aisle",
    "rest": "a pause by the reading rug",
}

QUESTS = [
    "carry the tank to the study alcove",
    "deliver the tank to the head shelf",
    "bring the tank to the archive table",
]

SURPRISES = [
    "a page suddenly flew open",
    "a stack of books toppled with a puff of dust",
    "a cat-like shadow slipped between the shelves",
    "a bell rang from nowhere",
]

SOUND_EFFECTS = [
    "shhh",
    "whump",
    "clatter",
    "thrum",
    "crackle",
]

# ---------------------------------------------------------------------------
# Shared containers / model
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
    carried_by: Optional[str] = None
    plural: bool = False
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    title: str
    tank_kind: str
    quest: str
    surprise: str
    sound_effect: str
    alternative: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTING_NAME)
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    keeper = world.add(Entity(id="Keeper", kind="character", type="keeper", label=params.title))
    tank = world.add(Entity(
        id="Tank",
        type="tank",
        label="tank",
        phrase=TANK_FORMS[params.tank_kind],
        owner=hero.id,
        caretaker=keeper.id,
        carried_by=hero.id,
        fragile=True,
    ))
    altar = world.add(Entity(id="Shelf", type="place", label="the oldest shelf"))

    world.facts.update(
        hero=hero,
        keeper=keeper,
        tank=tank,
        shelf=altar,
        quest=params.quest,
        surprise=params.surprise,
        sound_effect=params.sound_effect,
        alternative=params.alternative,
        tank_kind=params.tank_kind,
    )

    # Act I: setup
    world.say(
        f"In {SETTING_NAME}, {hero.id} was a {params.title.lower()} child with a mythic heart."
    )
    world.say(
        f"{hero.id} had been chosen for a quest: to {params.quest}."
    )
    world.say(
        f"The prize was {tank.phrase}, and {hero.id} carried it as if it were a sacred star."
    )

    # Act II: tension
    world.para()
    world.say(
        f"Then came the surprise: {params.surprise}, and the room answered with {params.sound_effect}."
    )
    world.facts["surprise_happened"] = True
    world.facts["sound_happened"] = True

    if params.tank_kind == "ink":
        danger = "the glass tank began to wobble above the books"
        risk = "ink could spill over the pages"
    elif params.tank_kind == "water":
        danger = "the glass tank trembled in both hands"
        risk = "water could splash onto the scrolls"
    else:
        danger = "the lantern tank flickered and shook"
        risk = "the flame might shatter the calm"

    hero.memes["alarm"] = hero.memes.get("alarm", 0.0) + 1
    world.say(f"{danger}, and {risk}.")

    world.say(
        f"{params.title.capitalize()} Keeper raised a hand and offered an alternative: {ALTERNATIVES[params.alternative]}."
    )

    # Act III: resolution
    world.para()
    if params.alternative == "cart":
        world.say(
            f"{hero.id} placed the tank on {ALTERNATIVES['cart']} and rolled it along the quiet floor."
        )
    elif params.alternative == "cloth":
        world.say(
            f"{hero.id} wrapped the tank in {ALTERNATIVES['cloth']} and held it close to the chest."
        )
    elif params.alternative == "route":
        world.say(
            f"{hero.id} took {ALTERNATIVES['route']}, where the shelves stood like patient giants."
        )
    else:
        world.say(
            f"{hero.id} chose {ALTERNATIVES['rest']} until the shaking passed."
        )

    tank.meters["wobble"] = 0.0
    tank.meters["shatter_risk"] = 0.0
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.facts["resolved"] = True
    world.facts["alternative_chosen"] = params.alternative

    world.say(
        f"In the end, {hero.id} reached the goal without a crack in the glass, "
        f"and the school library stayed as quiet as a moonlit temple."
    )
    world.say(
        f"So the quest was finished, the surprise had passed, and {hero.id} learned "
        f"that a wise alternative can save even a fragile tank."
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(tank_kind: str, alternative: str) -> bool:
    # Every tank here can be saved by some alternative, but "rest" is only
    # reasonable when the story already includes a truly overwhelming surprise.
    if tank_kind not in TANK_FORMS:
        return False
    if alternative not in ALTERNATIVES:
        return False
    return True


def explain_rejection(tank_kind: str, alternative: str) -> str:
    return f"(No story: the combination tank={tank_kind!r} and alternative={alternative!r} is not valid.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
tank(T) :- tank_kind(T).
alternative(A) :- alt(A).

valid(T, A) :- tank(T), alternative(A).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in TANK_FORMS:
        lines.append(asp.fact("tank_kind", t))
    for a in ALTERNATIVES:
        lines.append(asp.fact("alt", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {(t, a) for t in TANK_FORMS for a in ALTERNATIVES if valid_combo(t, a)}
    asp_set = set(asp_valid_combos())
    if asp_set == python_set:
        print(f"OK: clingo gate matches valid_combo() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic short story set in {SETTING_NAME} with the words "shatter", "alternative", and "tank".',
        f"Tell a child-friendly myth where {f['hero'].id} must complete a quest in {SETTING_NAME} and avoid a shatter.",
        f"Write a quiet legend about a surprise sound in {SETTING_NAME} and an alternative that saves a tank.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    keeper = f["keeper"]
    tank = f["tank"]
    return [
        QAItem(
            question=f"Where does {hero.id}'s quest take place?",
            answer=f"The quest takes place in {world.setting}, which is the school library.",
        ),
        QAItem(
            question=f"What surprised {hero.id} in the story?",
            answer=f"{f['surprise']} surprised {hero.id}, and the room answered with {f['sound_effect']}.",
        ),
        QAItem(
            question=f"What did {keeper.label} offer as an alternative?",
            answer=f"{keeper.label.capitalize()} offered {ALTERNATIVES[f['alternative']]}. That helped {hero.id} keep the {tank.label} safe.",
        ),
        QAItem(
            question=f"Did the tank shatter?",
            answer="No. The story ends with the tank intact because the child chose a safer alternative.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a library?",
            answer="A library is a quiet place where people read, study, and borrow books.",
        ),
        QAItem(
            question="What is a tank?",
            answer="A tank is a container that can hold water, ink, or other things, and a glass tank can break if it is dropped.",
        ),
        QAItem(
            question="What does an alternative mean?",
            answer="An alternative is another choice you can use instead of the first idea.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special noise used to make a moment feel bigger, funnier, or scarier.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task that a character tries to finish.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} label={e.label}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic school-library storyworld with surprise, sound effects, and quest.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--title", choices=KEEPER_TITLES)
    ap.add_argument("--tank-kind", choices=sorted(TANK_FORMS))
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--sound-effect", choices=SOUND_EFFECTS)
    ap.add_argument("--alternative", choices=sorted(ALTERNATIVES))
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
    tank_kind = args.tank_kind or rng.choice(list(TANK_FORMS))
    alternative = args.alternative or rng.choice(list(ALTERNATIVES))
    if not valid_combo(tank_kind, alternative):
        raise StoryError(explain_rejection(tank_kind, alternative))
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        title=args.title or rng.choice(KEEPER_TITLES),
        tank_kind=tank_kind,
        quest=args.quest or rng.choice(QUESTS),
        surprise=args.surprise or rng.choice(SURPRISES),
        sound_effect=args.sound_effect or rng.choice(SOUND_EFFECTS),
        alternative=alternative,
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        name="Ari",
        title="keeper",
        tank_kind="ink",
        quest="carry the tank to the study alcove",
        surprise="a page suddenly flew open",
        sound_effect="shhh",
        alternative="cloth",
    ),
    StoryParams(
        name="Mina",
        title="librarian",
        tank_kind="water",
        quest="deliver the tank to the head shelf",
        surprise="a stack of books toppled with a puff of dust",
        sound_effect="clatter",
        alternative="cart",
    ),
    StoryParams(
        name="Eli",
        title="sage",
        tank_kind="light",
        quest="bring the tank to the archive table",
        surprise="a bell rang from nowhere",
        sound_effect="thrum",
        alternative="route",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible tank/alternative combos:\n")
        for t, a in combos:
            print(f"  {t:6} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.tank_kind} quest in the school library"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
