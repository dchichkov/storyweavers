#!/usr/bin/env python3
"""
A standalone storyworld for a small superhero-style tale:
a piggy hero, a pistol-shaped prop, a parcel, a surprise, humor, and
reconciliation.

This world models a tiny state machine:
- a piggy superhero loves helping in the neighborhood
- a parcel arrives with a surprising gift
- a pistol prop causes a comic misunderstanding
- a hurt feeling turns into reconciliation
- the ending proves what changed in the world state
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"piggy", "hero", "friend"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    friend_name: str
    place: str
    parcel_item: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    description: str


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    humor: bool = False


@dataclass
class ParcelGift:
    label: str
    phrase: str
    surprise: str
    friendly: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "rooftop": Setting("the rooftop", "The rooftop was bright, windy, and perfect for a dramatic landing."),
    "alley": Setting("the alley", "The alley was narrow, with a mailbox, a lamp, and a place to hide a surprise."),
    "square": Setting("the square", "The square was full of neighbors, banners, and enough space for a heroic entrance."),
}

PIGGY_NAMES = ["Pip", "Poppy", "Percy", "Peanut", "Pia"]
FRIEND_NAMES = ["Milo", "Mina", "Toby", "Tia", "Nora"]

GADGET = Prop(
    id="pistol",
    label="pistol",
    phrase="a shiny toy pistol with a springy trigger",
    humor=True,
)

GIFTS = {
    "cookie": ParcelGift("cookie", "a peanut cookie", "sweet surprise"),
    "badge": ParcelGift("badge", "a silver hero badge", "brave surprise"),
    "note": ParcelGift("note", "a folded note with glittery stars", "kind surprise"),
    "scarf": ParcelGift("scarf", "a striped scarf", "cozy surprise"),
}

# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

class Meter:
    JOY = "joy"
    SHOCK = "shock"
    HURT = "hurt"
    HUMOR = "humor"
    TRUST = "trust"
    RECONCILIATION = "reconciliation"
    CURIOSITY = "curiosity"


def _inc(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _set(e: Entity, key: str, value: float) -> None:
    e.meters[key] = value


def _mem_inc(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def _first(words: list[str]) -> str:
    return words[0]


def predict_surprise(world: World, hero: Entity, gift: ParcelGift) -> dict[str, bool]:
    sim = world.copy()
    _inc(sim.get(hero.id), Meter.CURIOSITY, 1.0)
    _inc(sim.get("parcel"), Meter.SHOCK, 1.0)
    _inc(sim.get("parcel"), Meter.JOY, 1.0)
    return {
        "is_kind": gift.friendly,
        "reconcilable": True,
    }


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.parcel_item not in GIFTS:
        raise StoryError("Unknown parcel item.")

    setting = SETTINGS[params.place]
    gift = GIFTS[params.parcel_item]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="piggy",
        label="the piggy hero",
        phrase=f"the piggy hero {params.name}",
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="friend",
        label="the friend",
        phrase=f"the friend {params.friend_name}",
    ))
    parcel = world.add(Entity(
        id="parcel",
        kind="thing",
        type="parcel",
        label="parcel",
        phrase=f"a parcel wrapped in bright paper",
        owner=friend.id,
    ))
    pistol = world.add(Entity(
        id=GADGET.id,
        kind="thing",
        type="pistol",
        label=GADGET.label,
        phrase=GADGET.phrase,
        owner=hero.id,
        worn_by=hero.id,
    ))

    world.facts.update(hero=hero, friend=friend, parcel=parcel, pistol=pistol, gift=gift, setting=setting)

    # Act 1: introduction.
    world.say(
        f"{hero.id} was a piggy superhero who loved helping {world.setting.place} stay cheerful. "
        f"Every day, {hero.pronoun('subject')} wore a cape, checked the sky, and listened for tiny problems."
    )
    world.say(
        f"{hero.id} also carried {pistol.phrase}, because {hero.pronoun('subject')} thought it made a funny pop when the day felt too serious."
    )
    world.para()

    # Act 2: surprise and misunderstanding.
    world.say(
        f"One afternoon, a parcel landed with a soft thump near {hero.id}'s boots."
    )
    _inc(parcel, Meter.CURIOSITY, 1.0)
    _inc(hero, Meter.CURIOSITY, 1.0)
    world.say(
        f"{hero.id} peeked at the parcel and saw bright wrapping, but the shape looked mysterious. "
        f"{hero.pronoun('subject').capitalize()} laughed nervously and pointed the toy pistol at the ribbon."
    )
    _inc(hero, Meter.HUMOR, 1.0)
    _inc(hero, Meter.SHOCK, 1.0)
    world.say(
        f"Pop! The ribbon sprang open, and the parcel flipped wide with a little comic bounce."
    )

    if gift.label == "note":
        world.say(
            f"Inside was {gift.phrase}, which made {hero.id} blink in surprise."
        )
    else:
        world.say(
            f"Inside was {gift.phrase}, and that was a sweet surprise."
        )
    _inc(parcel, Meter.JOY, 1.0)
    _inc(hero, Meter.SHOCK, 1.0)
    _inc(hero, Meter.HUMOR, 1.0)

    # Friend appears; hurt feeling is possible because the parcel was from them.
    world.say(
        f"{friend.id} stepped out from behind a banner and smiled. "
        f'"I sent it for you," {friend.pronoun("subject")} said. "I hoped it would make you grin."'
    )
    _inc(friend, Meter.TRUST, 1.0)

    world.say(
        f"{hero.id}'s ears drooped for a moment. {hero.pronoun('subject').capitalize()} had worried the parcel was a trap, not a present."
    )
    _inc(hero, Meter.HURT, 1.0)
    world.say(
        f"Then {hero.id} looked at {friend.id}, at the opened parcel, and at the wobbling toy pistol still in {hero.pronoun('possessive')} hoof."
    )
    world.para()

    # Act 3: reconciliation.
    world.say(
        f"{hero.id} took a breath, tucked away the pistol, and gave a small sheepish smile."
    )
    world.say(
        f'"I thought the parcel meant trouble," {hero.id} admitted. "{gift.surprise} is much nicer."'
    )
    _inc(hero, Meter.RECONCILIATION, 1.0)
    _inc(friend, Meter.RECONCILIATION, 1.0)
    _inc(hero, Meter.TRUST, 1.0)
    _inc(friend, Meter.TRUST, 1.0)
    _set(hero, Meter.HURT, 0.0)
    world.say(
        f"{friend.id} laughed, and soon both friends were laughing together. "
        f"They shared the gift, and the rooftop alley square felt friendly again."
    )

    world.say(
        f"By the end, the parcel was empty, the toy pistol was safely tucked in {hero.id}'s belt, "
        f"and {hero.id} and {friend.id} were smiling side by side."
    )

    return world


# ---------------------------------------------------------------------------
# Reasonableness / parameter resolution
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero piggy, a pistol prop, and a surprising parcel.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name", choices=PIGGY_NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--parcel-item", choices=GIFTS.keys())
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(PIGGY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != name])
    parcel_item = args.parcel_item or rng.choice(list(GIFTS))
    return StoryParams(name=name, friend_name=friend_name, place=place, parcel_item=parcel_item)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    gift: ParcelGift = f["gift"]  # type: ignore[assignment]
    return [
        f'Write a short superhero story for a young child about {hero.id}, a piggy hero, a parcel, and a funny surprise.',
        f"Tell a gentle story where {hero.id} thinks a parcel is trouble, but {friend.id} sent it as {gift.surprise}.",
        f"Write a story that includes a toy pistol, a parcel, humor, and reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    gift: ParcelGift = f["gift"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the piggy superhero in the story?",
            answer=f"The piggy superhero is {hero.id}. {hero.id} wears a cape and tries to help cheer up the place.",
        ),
        QAItem(
            question=f"Why did {hero.id} point the toy pistol at the parcel?",
            answer=f"{hero.id} thought the parcel looked mysterious, so {hero.pronoun('subject')} used the toy pistol as a funny way to pop the ribbon open.",
        ),
        QAItem(
            question=f"What was inside the parcel?",
            answer=f"The parcel held {gift.phrase}, which was a {gift.surprise}.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {friend.id} stop feeling upset?",
            answer=f"{hero.id} realized the parcel was a present from {friend.id}, so they talked it through and laughed together. That turned the moment into reconciliation instead of worry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parcel?",
            answer="A parcel is a wrapped package that is sent or carried from one person to another.",
        ),
        QAItem(
            question="Why can a toy pistol be funny in a story?",
            answer="A toy pistol can be funny because it looks dramatic, but it does not hurt anyone and can be used for a comic surprise.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means two people stop feeling upset and become friendly again after a misunderstanding.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- piggy_hero(H).
friend(F) :- pal(F).
parcel(P) :- package(P).

surprise(P) :- parcel(P), contains_present(P).
humor(H) :- hero(H), uses_toy_pistol(H).
hurt(H) :- hero(H), misunderstood_parcel(H).
reconciliation(H,F) :- hurt(H), friend(F), gift_from(F, H), surprise(_).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for n in PIGGY_NAMES:
        lines.append(asp.fact("piggy_hero", n))
    for n in FRIEND_NAMES:
        lines.append(asp.fact("pal", n))
    for g in GIFTS.values():
        lines.append(asp.fact("contains_present", g.label))
    lines.append(asp.fact("uses_toy_pistol", "hero"))
    lines.append(asp.fact("misunderstood_parcel", "hero"))
    lines.append(asp.fact("gift_from", "friend", "hero"))
    lines.append(asp.fact("package", "parcel"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Minimal parity check: the ASP program should be solvable and expose core atoms.
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show surprise/1. #show humor/1. #show reconciliation/2."))
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    need = {("surprise", 1), ("humor", 1), ("reconciliation", 2)}
    if need.issubset(atoms):
        print("OK: ASP twin emits the expected core predicates.")
        return 0
    print("MISMATCH: ASP twin did not produce expected predicates.")
    print(sorted(atoms))
    return 1


# ---------------------------------------------------------------------------
# Generation and output
# ---------------------------------------------------------------------------

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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
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
        print(asp_program("#show surprise/1. #show humor/1. #show reconciliation/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show surprise/1. #show humor/1. #show reconciliation/2."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(name="Pip", friend_name="Milo", place="square", parcel_item="badge"),
            StoryParams(name="Poppy", friend_name="Tia", place="rooftop", parcel_item="cookie"),
            StoryParams(name="Percy", friend_name="Nora", place="alley", parcel_item="note"),
        ]
        samples = [generate(p) for p in combos]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
