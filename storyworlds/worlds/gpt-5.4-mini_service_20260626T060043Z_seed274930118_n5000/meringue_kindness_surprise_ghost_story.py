#!/usr/bin/env python3
"""
A small storyworld for a gentle ghost story with meringue, kindness, and surprise.

Premise:
A child finds a shy ghost in a quiet kitchen at night. The ghost is lonely and
startles the child at first, but the child chooses kindness and shares a tray of
meringues. The surprise turns warm instead of scary, and the ghost leaves a
little gift of courage.

This file is self-contained except for the shared storyworld results/ASP helpers.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the kitchen"
    quiet: bool = True
    affords: set[str] = field(default_factory=lambda: {"bake_meringue", "offer_meringue"})


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    crumbly: bool = True
    sweet: bool = True


@dataclass
class StoryParams:
    place: str
    treat: str
    name: str
    gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _ask_for_meringue(world: World, child: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(
        f"At the end of a quiet evening, {child.id} noticed a tray on the counter "
        f"and wondered who had baked the pale little meringues."
    )


def _ghost_appears(world: World, ghost: Entity, child: Entity, treat: Treat) -> None:
    ghost.memes["lonely"] = ghost.memes.get("lonely", 0) + 1
    child.memes["fright"] = child.memes.get("fright", 0) + 1
    world.say(
        f"Then a cold shimmer slipped from the dark doorway, and a small ghost "
        f"floated over the floorboards. {child.id} gasped, because the surprise "
        f"felt spooky at first."
    )
    world.say(
        f"The ghost looked at the {treat.label} with wide, hungry eyes, as if "
        f"kindness had been missing from the room for a long time."
    )


def _kind_choice(world: World, child: Entity, ghost: Entity, treat: Treat) -> None:
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    child.memes["courage"] = child.memes.get("courage", 0) + 1
    ghost.memes["hope"] = ghost.memes.get("hope", 0) + 1
    world.say(
        f"Instead of running away, {child.id} took a breath and held up the tray. "
        f'"Would you like to share?" {child.pronoun().capitalize()} asked.'
    )
    world.say(
        f"The ghost blinked, and the cold air softened. The tiny {treat.label} "
        f"turned from a scary surprise into a gentle one."
    )


def _share_meringue(world: World, child: Entity, ghost: Entity, treat: Treat) -> None:
    child.meters["meringue_shared"] = 1
    ghost.meters["meringue_eaten"] = 1
    ghost.memes["joy"] = ghost.memes.get("joy", 0) + 1
    world.say(
        f"{child.id} set one {treat.label} on a saucer, and the ghost nibbled it so "
        f"carefully that not even a crumb fell."
    )
    world.say(
        f"The ghost smiled with a moon-pale glow, because the sweetest thing in the "
        f"room was the kindness."
    )


def _gift_courage(world: World, ghost: Entity, child: Entity) -> None:
    child.memes["peace"] = child.memes.get("peace", 0) + 1
    child.memes["brave"] = child.memes.get("brave", 0) + 1
    world.say(
        f"As the night grew softer, the ghost left a little silver pebble in "
        f"{child.pronoun('possessive')} palm and whispered, 'For bravery when the dark "
        f"looks bigger than it is.'"
    )
    world.say(
        f"After that, {child.id} was no longer afraid of the quiet kitchen. "
        f"The tray was lighter now, and the room felt warm as toast."
    )


def tell(setting: Setting, treat: Treat, hero_name: str, hero_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost"))
    tray = world.add(Entity(id="tray", type="thing", label=treat.label, phrase=treat.phrase))
    world.facts.update(child=child, ghost=ghost, treat=tray, setting=setting)

    _ask_for_meringue(world, child)
    world.para()
    _ghost_appears(world, ghost, child, treat)
    _kind_choice(world, child, ghost, treat)
    world.para()
    _share_meringue(world, child, ghost, treat)
    _gift_courage(world, ghost, child)

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", quiet=True),
    "pantry": Setting(place="the pantry", quiet=True),
    "attic": Setting(place="the attic", quiet=True),
}

TREATS = {
    "meringue": Treat(
        id="meringue",
        label="meringue",
        phrase="a tray of crisp meringues",
    ),
}

NAMES = ["Mia", "Lily", "Nora", "Theo", "Ben", "Ava"]
GENDERS = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, treat) for place in SETTINGS for treat in TREATS]


@dataclass
class StoryParams:
    place: str
    treat: str
    name: str
    gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with kindness and meringue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.treat is None or c[1] == args.treat)]
    if not combos:
        raise StoryError("No valid story combination matches the given options.")
    place, treat = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, treat=treat, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TREATS[params.treat], params.name, params.gender)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    treat = world.facts["treat"]
    return [
        f"Write a gentle ghost story for a young child that includes {treat.label} and kindness.",
        f"Tell a short bedtime story where {child.id} meets a friendly ghost in {world.setting.place}.",
        "Write a small story with a spooky surprise that turns sweet and safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    treat = world.facts["treat"]
    place = world.facts["setting"].place
    return [
        QAItem(
            question=f"Where did {child.id} meet the ghost?",
            answer=f"{child.id} met the ghost in {place}, where the room was quiet and shadowy.",
        ),
        QAItem(
            question=f"What did {child.id} share with the ghost?",
            answer=f"{child.id} shared a {treat.label} from the tray with the ghost.",
        ),
        QAItem(
            question=f"How did the surprise change by the end?",
            answer=(
                f"It started spooky, but kindness made the surprise turn warm and friendly. "
                f"The ghost left feeling less lonely, and {child.id} felt brave."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a meringue?",
            answer=(
                "A meringue is a light, sweet treat made by whipping egg whites and sugar, "
                "then baking it until it is crisp outside and airy inside."
            ),
        ),
        QAItem(
            question="What does kindness do in a scary moment?",
            answer=(
                "Kindness can help a scary moment feel safer, because a gentle choice can "
                "turn fear into trust."
            ),
        ),
        QAItem(
            question="What is a surprise?",
            answer=(
                "A surprise is something unexpected. It can feel startling at first, but "
                "it can also become happy if it is safe and caring."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
place(kitchen).
place(pantry).
place(attic).

treat(meringue).

valid(Place, Treat) :- place(Place), treat(Treat).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TREATS:
        lines.append(asp.fact("treat", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def explain_asp() -> str:
    return asp_program("#show valid/2.")


CURATED = [
    StoryParams(place="kitchen", treat="meringue", name="Mia", gender="girl"),
    StoryParams(place="pantry", treat="meringue", name="Theo", gender="boy"),
    StoryParams(place="attic", treat="meringue", name="Nora", gender="girl"),
]


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
        print(explain_asp())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, t in combos:
            print(f"  {p} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
