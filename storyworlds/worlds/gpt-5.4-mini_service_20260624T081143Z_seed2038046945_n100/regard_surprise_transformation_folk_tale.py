#!/usr/bin/env python3
"""
storyworlds/worlds/regard_surprise_transformation_folk_tale.py
==============================================================

A small folk-tale storyworld about regard, surprise, and transformation.

Seed imagination:
- A kind child notices an overlooked creature and treats it with regard.
- The creature surprises the child with a secret truth.
- A humble transformation follows: a plain thing becomes useful, and the
  child's heart changes too.

The domain is kept intentionally small and classical: a path, a cottage, a
small gift, a hidden helper, and a final transformation that proves the change.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the lane"
    rural: bool = True


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    transformed_label: str
    transformed_phrase: str
    reveal: str
    effect: str


@dataclass
class Surprise:
    id: str
    reveal: str
    effect: str
    clue: str


@dataclass
class Transformation:
    id: str
    before: str
    after: str
    benefit: str


class World:
    def __init__(self, setting: Setting) -> None:
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
    "lane": Setting(place="the lane", rural=True),
    "wood": Setting(place="the wood", rural=True),
    "well": Setting(place="the old well", rural=True),
}

GIFTS = {
    "cloak": Gift(
        id="cloak",
        label="cloak",
        phrase="a plain gray cloak",
        transformed_label="bright cloak",
        transformed_phrase="a bright cloak with a gold clasp",
        reveal="the cloak had been woven for a helper nobody had noticed",
        effect="the cloak grew warm and shone like morning light",
    ),
    "cup": Gift(
        id="cup",
        label="cup",
        phrase="a dull tin cup",
        transformed_label="song-cup",
        transformed_phrase="a song-cup that rang like a bell",
        reveal="the cup had a hidden tune sleeping inside",
        effect="the cup sang when the child spoke kindly",
    ),
    "stone": Gift(
        id="stone",
        label="stone",
        phrase="a smooth little stone",
        transformed_label="guiding stone",
        transformed_phrase="a guiding stone with a tiny map mark",
        reveal="the stone was waiting to point the way home",
        effect="the stone turned warm and pointed north",
    ),
}

SURPRISES = {
    "mouse": Surprise(
        id="mouse",
        reveal="a small mouse had been living behind the hearth and listening",
        effect="the mouse knew where the lost bread was hidden",
        clue="the crumbs near the broom were not ordinary crumbs",
    ),
    "bird": Surprise(
        id="bird",
        reveal="a brave bird had been watching from the rafters",
        effect="the bird knew the shortcut to the berry bush",
        clue="the flutter above the door was no accident",
    ),
    "old_woman": Surprise(
        id="old_woman",
        reveal="an old woman in a green shawl had been smiling from the garden gate",
        effect="she knew the spell that wakes useful things",
        clue="the footprints by the gate were tiny and careful",
    ),
}

TRANSFORMATIONS = {
    "heart": Transformation(
        id="heart",
        before="the child's worry",
        after="a kinder, steadier heart",
        benefit="the child could notice help where others saw nothing",
    ),
    "gift": Transformation(
        id="gift",
        before="a plain little thing",
        after="a useful treasure",
        benefit="the family could use it every day",
    ),
    "path": Transformation(
        id="path",
        before="a dark and uncertain path",
        after="a clear bright way home",
        benefit="the child no longer feared the walk",
    ),
}

NAMES = ["Mira", "Anya", "Pavel", "Niko", "Tomas", "Lea", "Sofia", "Ivan"]
KINDS = [("girl", "mother"), ("boy", "father"), ("girl", "grandmother"), ("boy", "grandfather")]


@dataclass
class StoryParams:
    place: str
    gift: str
    surprise: str
    transformation: str
    name: str
    child_type: str
    elder_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for gift in GIFTS:
            for surprise in SURPRISES:
                if gift == "stone" and surprise == "mouse":
                    continue
                combos.append((place, gift, surprise))
    return combos


def explain_rejection(gift: str, surprise: str) -> str:
    return (
        f"(No story: the {gift} and {surprise} pairing does not produce a clean folk-tale turn. "
        f"Try a different surprise or a different gift.)"
    )


ASP_RULES = r"""
gift_pair(P,G,S) :- place(P), gift(G), surprise(S), not bad_pair(G,S).
bad_pair(stone, mouse).
valid(P,G,S) :- gift_pair(P,G,S).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python combo gates.")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about regard, surprise, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.gift and args.surprise and args.gift == "stone" and args.surprise == "mouse":
        raise StoryError(explain_rejection(args.gift, args.surprise))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.gift is None or c[1] == args.gift)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, gift, surprise = rng.choice(sorted(combos))
    trans = args.transformation or rng.choice(list(TRANSFORMATIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    child_type, elder_type = (gender, "mother") if gender == "girl" else (gender, "father")
    return StoryParams(place, gift, surprise, trans, name, child_type, elder_type)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.child_type))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_type))
    gift = world.add(Entity(id="gift", type=params.gift, label=GIFTS[params.gift].label, phrase=GIFTS[params.gift].phrase, owner=child.id))
    surprise = SURPRISES[params.surprise]
    transform = TRANSFORMATIONS[params.transformation]

    world.say(
        f"Once, in {world.setting.place}, {child.id} was a small {child.type} who showed regard for quiet things."
    )
    world.say(
        f"{child.pronoun().capitalize()} carried {child.pronoun('possessive')} {gift.phrase} and kept it close."
    )
    world.para()
    world.say(
        f"At dusk, {child.id} noticed the clue by the door: {surprise.clue}."
    )
    world.say(
        f"That was a surprise, and when {child.id} listened with regard, {surprise.reveal}."
    )
    world.para()
    world.say(
        f"{surprise.effect.capitalize()}. Then {gift.phrase} changed."
    )
    world.say(
        f"It became {GIFTS[params.gift].transformed_phrase}; {GIFTS[params.gift].effect}."
    )
    world.para()
    world.say(
        f"In the end, {transform.before} became {transform.after}, because {transform.benefit}."
    )
    world.say(
        f"{child.id} went home with the transformed gift, and the lane seemed less lonely than before."
    )

    world.facts = {
        "child": child,
        "elder": elder,
        "gift": gift,
        "surprise": surprise,
        "transformation": transform,
        "params": params,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short folk tale about regard, surprise, and transformation set at {p.place}.",
        f"Tell a gentle story where {p.name} treats something small with regard and a surprise changes the day's meaning.",
        f"Write a simple folktale that turns a plain {GIFTS[p.gift].label} into something useful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    g = GIFTS[p.gift]
    s = SURPRISES[p.surprise]
    t = TRANSFORMATIONS[p.transformation]
    return [
        QAItem(
            question=f"Who is the story about in {p.place}?",
            answer=f"The story is about {p.name}, a little {p.child_type}, who shows regard for quiet things.",
        ),
        QAItem(
            question=f"What surprise did {p.name} notice near the door?",
            answer=f"{p.name} noticed that {s.clue}. The surprise was that {s.reveal}.",
        ),
        QAItem(
            question=f"What did the plain {g.label} become by the end?",
            answer=f"It became {g.transformed_phrase}. That was the transformation in the tale.",
        ),
        QAItem(
            question=f"How did regard matter in the story?",
            answer=(
                f"Because {p.name} paid regard to the small clue instead of ignoring it, the hidden helper was revealed "
                f"and the little thing could transform into something useful."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is regard?",
            answer="Regard means paying careful and kind attention to someone or something.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears when you do not know it is coming.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a different form or meaning.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("\n== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}\nA: {item.answer}")
    parts.append("\n== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} owner={e.owner or '-'}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("lane", "cloak", "mouse", "heart", "Mira", "girl", "mother"),
    StoryParams("wood", "cup", "bird", "gift", "Pavel", "boy", "father"),
    StoryParams("well", "stone", "old_woman", "path", "Lea", "girl", "grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
