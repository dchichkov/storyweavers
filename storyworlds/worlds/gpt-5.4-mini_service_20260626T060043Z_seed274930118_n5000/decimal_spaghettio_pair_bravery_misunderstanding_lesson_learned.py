#!/usr/bin/env python3
"""
storyworlds/worlds/decimal_spaghettio_pair_bravery_misunderstanding_lesson_learned.py
======================================================================================

A small animal-story world about a shared snack, a misunderstanding, a brave
voice, and a lesson learned.

Premise:
- Two young animal friends are at a sunny picnic table.
- A tin marked with a decimal sticker holds warm spaghettio pasta.
- A pair of spoons should help them share it.

Tension:
- One friend thinks the pair of spoons means "two spoons for me."
- The other friend feels left out and unsure what to do.
- The misunderstanding makes the table feel lopsided and tense.

Turn:
- A small, brave friend speaks up and asks for a fair share.
- The pair is used the right way: one spoon each, with the tin passed back and forth.

Resolution:
- Both friends eat the spaghettio happily.
- The decimal sticker becomes a joke instead of a problem.
- The lesson learned is that asking kindly can untangle confusion.

This file follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- world-driven prose
- inline ASP rules and fact emission
- parser, parameter resolution, generation, emission, main
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "bunny", "chipmunk"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"fox", "bear", "otter", "dog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    taste: str
    bowl: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PairItem:
    id: str
    label: str
    phrase: str
    covers: set[str] = field(default_factory=set)
    plural: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "picnic": Setting(place="the sunny picnic table", affords={"share_snack"}),
    "kitchen": Setting(place="the little kitchen table", affords={"share_snack"}),
    "classroom": Setting(place="the cozy classroom corner", affords={"share_snack"}),
}

ANIMALS = {
    "mouse": {"name": "Mina", "traits": ["small", "careful"]},
    "rabbit": {"name": "Rory", "traits": ["fluffy", "quick"]},
    "fox": {"name": "Fenn", "traits": ["bright-eyed", "curious"]},
    "otter": {"name": "Ollie", "traits": ["playful", "brave"]},
}

SNACKS = {
    "spaghettio": Snack(
        id="spaghettio",
        label="spaghettio",
        phrase="a warm bowl of spaghettio",
        taste="savory",
        bowl="tiny red bowl",
        mess="splashy",
        tags={"spaghettio", "food", "sharing"},
    ),
    "apple_slices": Snack(
        id="apple_slices",
        label="apple slices",
        phrase="a plate of apple slices",
        taste="sweet",
        bowl="blue plate",
        mess="sticky",
        tags={"sharing", "food"},
    ),
}

PAIRS = {
    "spoons": PairItem(
        id="spoons",
        label="pair of spoons",
        phrase="a pair of spoons",
        covers={"sharing"},
    ),
    "napkins": PairItem(
        id="napkins",
        label="pair of napkins",
        phrase="a pair of napkins",
        covers={"mess"},
    ),
}

ACTIONS = {
    "share_snack": "share the snack fairly",
}

TRAITS = ["kind", "brave", "gentle", "thoughtful", "curious"]


@dataclass
class StoryParams:
    place: str
    animal_a: str
    animal_b: str
    snack: str
    pair: str
    name_a: str
    name_b: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    a_kind = params.animal_a
    b_kind = params.animal_b
    a = world.add(Entity(
        id=params.name_a,
        kind="character",
        type=a_kind,
        label=params.name_a,
        traits=["little", params.trait_a],
        meters={"hunger": 1.0},
        memes={"joy": 0.5},
    ))
    b = world.add(Entity(
        id=params.name_b,
        kind="character",
        type=b_kind,
        label=params.name_b,
        traits=["little", params.trait_b],
        meters={"hunger": 1.0},
        memes={"worry": 0.5},
    ))

    snack = SNACKS[params.snack]
    pair = PAIRS[params.pair]

    snack_ent = world.add(Entity(
        id=snack.id,
        kind="thing",
        type="snack",
        label=snack.label,
        phrase=snack.phrase,
        owner=a.id,
        caretaker=a.id,
        meters={"full": 1.0},
    ))
    pair_ent = world.add(Entity(
        id=pair.id,
        kind="thing",
        type="pair",
        label=pair.label,
        phrase=pair.phrase,
        owner=b.id,
        caretaker=a.id,
        plural=pair.plural,
    ))

    world.facts.update(
        setting=setting,
        animal_a=a,
        animal_b=b,
        snack=snack,
        snack_ent=snack_ent,
        pair=pair_ent,
        misunderstanding=False,
        bravery=False,
        lesson=False,
        resolved=False,
    )
    return world


def scene_start(world: World) -> None:
    a = world.facts["animal_a"]
    b = world.facts["animal_b"]
    snack = world.facts["snack"]
    pair = world.facts["pair"]
    world.say(
        f"{a.label} the {a.type} and {b.label} the {b.type} met at {world.setting.place}."
    )
    world.say(
        f"On the table sat {snack.phrase}, and beside it waited {pair.phrase}."
    )
    a.memes["curiosity"] = a.e("curiosity") + 1
    b.memes["curiosity"] = b.e("curiosity") + 1


def scene_misunderstanding(world: World) -> None:
    a = world.facts["animal_a"]
    b = world.facts["animal_b"]
    snack = world.facts["snack"]
    pair = world.facts["pair"]
    a.memes["misunderstanding"] = a.e("misunderstanding") + 1
    b.memes["misunderstanding"] = b.e("misunderstanding") + 1
    world.facts["misunderstanding"] = True
    world.say(
        f"{a.label} thought the pair meant two big spoonfuls for one friend, not one for each friend."
    )
    world.say(
        f"{b.label} watched the bowl of {snack.label} wobble and worried the sharing might go wrong."
    )
    a.meters["tension"] = a.m("tension") + 1
    b.meters["tension"] = b.m("tension") + 1


def scene_bravery(world: World) -> None:
    a = world.facts["animal_a"]
    b = world.facts["animal_b"]
    snack = world.facts["snack"]
    world.facts["bravery"] = True
    a.memes["brave"] = a.e("brave") + 1
    world.say(
        f"Then {a.label} took a deep breath and spoke up in a small, brave voice."
    )
    world.say(
        f'"I think we should each get one spoon," {a.pronoun()} said. "That way we can both taste the {snack.label}."'
    )
    b.memes["relief"] = b.e("relief") + 1
    a.meters["tension"] = max(0.0, a.m("tension") - 1)


def scene_lesson(world: World) -> None:
    a = world.facts["animal_a"]
    b = world.facts["animal_b"]
    snack = world.facts["snack"]
    pair = world.facts["pair"]
    world.facts["lesson"] = True
    world.facts["resolved"] = True
    a.memes["joy"] = a.e("joy") + 1
    b.memes["joy"] = b.e("joy") + 1
    b.meters["tension"] = max(0.0, b.m("tension") - 1)
    world.say(
        f"{b.label} smiled, nodded, and passed over one spoon from the pair."
    )
    world.say(
        f"Soon the two friends were eating the warm {snack.label} together, one spoon each."
    )
    world.say(
        f"The decimal sticker on the bowl was only for counting, not for arguing, and the lesson learned was simple: ask kindly when something feels confusing."
    )
    world.say(
        f"By the end, the pair was used the right way, and the table looked happy again."
    )


def tell(world: World) -> World:
    scene_start(world)
    world.para()
    scene_misunderstanding(world)
    world.para()
    scene_bravery(world)
    scene_lesson(world)
    return world


def generate_story_text(world: World) -> str:
    return world.render()


def valid_combo(place: str, snack: str, pair: str) -> bool:
    return place in SETTINGS and snack in SNACKS and pair in PAIRS and "share_snack" in SETTINGS[place].affords


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, s, pair) for p in SETTINGS for s in SNACKS for pair in PAIRS if valid_combo(p, s, pair)]


@dataclass
class StoryParams:
    place: str
    animal_a: str
    animal_b: str
    snack: str
    pair: str
    name_a: str
    name_b: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about decimal, spaghettio, and a pair.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--snack", choices=list(SNACKS))
    ap.add_argument("--pair", choices=list(PAIRS))
    ap.add_argument("--animal-a", choices=list(ANIMALS))
    ap.add_argument("--animal-b", choices=list(ANIMALS))
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--trait-a", choices=TRAITS)
    ap.add_argument("--trait-b", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    snack = args.snack or rng.choice(list(SNACKS))
    pair = args.pair or rng.choice(list(PAIRS))
    if not valid_combo(place, snack, pair):
        raise StoryError("Invalid combination for this animal story.")
    animal_a = args.animal_a or rng.choice(list(ANIMALS))
    animal_b = args.animal_b or rng.choice([k for k in ANIMALS if k != animal_a])
    a_info = ANIMALS[animal_a]
    b_info = ANIMALS[animal_b]
    return StoryParams(
        place=place,
        animal_a=animal_a,
        animal_b=animal_b,
        snack=snack,
        pair=pair,
        name_a=args.name_a or a_info["name"],
        name_b=args.name_b or b_info["name"],
        trait_a=args.trait_a or rng.choice(TRAITS),
        trait_b=args.trait_b or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(setup_world(params))
    return StorySample(
        params=params,
        story=generate_story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["animal_a"]
    b = f["animal_b"]
    snack = f["snack"]
    pair = f["pair"]
    return [
        f'Write an animal story for a young child using the words "decimal", "{snack.label}", and "{pair.label}".',
        f"Tell a gentle story where {a.label} and {b.label} begin with a misunderstanding about a pair and end with a lesson learned.",
        f"Write a short, warm story about brave sharing at {world.setting.place} that includes a decimal sticker and {snack.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["animal_a"]
    b = f["animal_b"]
    snack = f["snack"]
    pair = f["pair"]
    return [
        QAItem(
            question=f"Who were the two animal friends in the story?",
            answer=f"The story was about {a.label} the {a.type} and {b.label} the {b.type}.",
        ),
        QAItem(
            question=f"What snack was on the table?",
            answer=f"There was {snack.phrase} on the table at {world.setting.place}.",
        ),
        QAItem(
            question=f"What was the misunderstanding about?",
            answer=f"It was about the {pair.label}: one friend thought the pair meant two big spoonfuls, but it really meant one spoon for each friend.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word decimal mean in this story?",
            answer="Here, decimal is just a sticker word for counting and sorting, not a problem to fight about.",
        ),
        QAItem(
            question="What is a pair?",
            answer="A pair means two matching things that belong together, like two spoons.",
        ),
        QAItem(
            question="Why did bravery matter?",
            answer="Bravery mattered because one friend was brave enough to speak kindly and fix the misunderstanding.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was that asking kindly can clear up confusion and help friends share fairly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Story Q&A =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={ {k: v for k, v in world.facts.items() if k in {'misunderstanding', 'bravery', 'lesson', 'resolved'}} }")
    return "\n".join(lines)


ASP_RULES = r"""
entity(character; thing).
place(picnic; kitchen; classroom).
snack(spaghettio; apple_slices).
pair(spoons; napkins).

valid(Place, Snack, Pair) :- place(Place), snack(Snack), pair(Pair).
#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for a in SETTINGS[p].affords:
            lines.append(asp.fact("affords", p, a))
    for s in SNACKS:
        lines.append(asp.fact("snack", s))
    for pair in PAIRS:
        lines.append(asp.fact("pair", pair))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python validation.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in clingo:", sorted(cl - py))
    return 1


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combinations:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in SETTINGS:
            for s in SNACKS:
                for pair in PAIRS:
                    params = StoryParams(
                        place=p,
                        animal_a="mouse",
                        animal_b="rabbit",
                        snack=s,
                        pair=pair,
                        name_a="Mina",
                        name_b="Rory",
                        trait_a="brave",
                        trait_b="gentle",
                    )
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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
        hdr = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=hdr)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
