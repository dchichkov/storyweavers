#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T021641Z_seed1855084837_n10/tilt_tulip_lesson_learned_quest_transformation_mystery.py
===============================================================================================================================

A standalone storyworld for a tiny mystery about a tilted clue, a tulip, a quest,
and a transformation. The world is small on purpose: one child, one garden mystery,
one hidden path, one small lesson, and one ending image that proves what changed.
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

THEME_WORDS = ("tilt", "tulip")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    name: str
    clue_kind: str
    hidden_kind: str
    transformation: str
    mystery_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    effect: str
    reveals: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    label: str
    phrase: str
    before: str
    after: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    clue: str
    transformation: str
    name: str
    gender: str
    companion: str = "cat"
    seed: Optional[int] = None


PLACES = {
    "garden": Place(
        id="garden",
        name="the little garden",
        clue_kind="tilt",
        hidden_kind="tulip",
        transformation="bloom",
        mystery_hint="a bent stone marker",
        tags={"garden", "mystery", "quest"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        name="the warm greenhouse",
        clue_kind="tilt",
        hidden_kind="tulip",
        transformation="open",
        mystery_hint="a glass shelf",
        tags={"greenhouse", "mystery", "quest"},
    ),
    "path": Place(
        id="path",
        name="the winding path",
        clue_kind="tilt",
        hidden_kind="tulip",
        transformation="reveal",
        mystery_hint="a small signpost",
        tags={"path", "mystery", "quest"},
    ),
}

CLUES = {
    "tilt": Clue(
        id="tilt",
        label="tilted marker",
        phrase="a stone marker that leaned to one side",
        effect="tilt",
        reveals="a hidden pocket of soil",
        tags={"tilt", "mystery"},
    ),
}

TRANSFORMS = {
    "bloom": Transformation(
        id="bloom",
        label="blooming change",
        phrase="a flower waking up",
        before="bare ground",
        after="a tulip lifting its head",
        tags={"tulip", "transformation"},
    ),
    "open": Transformation(
        id="open",
        label="opening change",
        phrase="a closed bud opening",
        before="a tight bud",
        after="a tulip opening wide",
        tags={"tulip", "transformation"},
    ),
    "reveal": Transformation(
        id="reveal",
        label="revealing change",
        phrase="a secret showing itself",
        before="hidden soil",
        after="a tulip rising from the dark",
        tags={"tulip", "transformation"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Maya"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Ben", "Leo"]
COMPANIONS = ["cat", "dog", "mouse", "sparrow"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for cid in CLUES:
            for tid in TRANSFORMS:
                combos.append((pid, cid, tid))
    return combos


def _setup_entity(world: World, name: str, gender: str, companion: str) -> tuple[Entity, Entity]:
    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label=name,
        role="quester",
        attrs={"companion": companion},
        meters={"curiosity": 0.0, "distance": 0.0},
        memes={"wonder": 1.0, "hope": 0.5, "fear": 0.0, "lesson": 0.0, "joy": 0.0},
        tags={"quest", "mystery"},
    ))
    buddy = world.add(Entity(
        id="Companion",
        kind="character",
        type="animal",
        label=companion,
        role="helper",
        meters={"distance": 0.0},
        memes={"trust": 1.0},
        attrs={"watching": True},
        tags={"quest"},
    ))
    return child, buddy


def _narrate_mystery(world: World, child: Entity, buddy: Entity, clue: Clue, trans: Transformation) -> None:
    child.meters["curiosity"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} wandered into {world.place.name} with {buddy.label} at {their(child)} side. "
        f"Something felt odd, like the whole place was holding its breath."
    )
    world.say(
        f"Near a bed of flowers, {child.id} noticed {clue.phrase}. "
        f"The marker's {clue.effect} pointed toward {clue.reveals}."
    )


def their(ent: Entity) -> str:
    return "their" if ent.type not in {"girl", "boy", "mother", "father", "woman", "man"} else ent.pronoun("possessive")


def _quest(world: World, child: Entity, clue: Clue, trans: Transformation) -> None:
    child.meters["distance"] += 1
    world.say(
        f"{child.id} followed the clue and lifted the loose edge of soil. "
        f"Underneath was the answer to the little mystery: {trans.before}."
    )
    world.say(
        f"The search was not about treasure at all. It was a quest to learn why the garden looked strange."
    )


def _transform(world: World, child: Entity, trans: Transformation) -> None:
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"Then the hidden place changed: {trans.after}. "
        f"It was not magic from nowhere; it was a quiet transformation as the day warmed."
    )
    world.say(
        f"{child.id} understood the lesson at once. A small tilt in the world could point to something living, and patient looking could uncover it."
    )


def tell(place: Place, clue: Clue, trans: Transformation, name: str, gender: str, companion: str) -> World:
    world = World(place)
    child, buddy = _setup_entity(world, name, gender, companion)
    world.facts.update(place=place, clue=clue, transformation=trans, child=child, buddy=buddy)

    world.say(
        f"One quiet morning, {child.id} went to {place.name} looking for a strange sign."
    )
    world.say(
        f"{buddy.label.capitalize()} padded along beside {child.id}, because every mystery is easier with a friend."
    )
    world.para()
    _narrate_mystery(world, child, buddy, clue, trans)
    world.para()
    _quest(world, child, clue, trans)
    world.para()
    _transform(world, child, trans)
    world.para()
    world.say(
        f"In the end, {child.id} left the garden smiling. {world.place.mystery_hint} was no longer puzzling, because the tulip had become the clue and the clue had become a lesson learned."
    )
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child that includes the words "tilt" and "tulip".',
        f"Tell a gentle quest story set in {f['place'].name} where a child follows a tilted clue and discovers a tulip.",
        f"Write a simple story with a mystery, a quest, and a transformation, ending with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    place: Place = f["place"]
    clue: Clue = f["clue"]
    trans: Transformation = f["transformation"]
    return [
        QAItem(
            question=f"Why did {child.id} go to {place.name}?",
            answer=(
                f"{child.id} went there to solve a small mystery. {clue.phrase} made them curious, so they followed it to learn what it pointed to."
            ),
        ),
        QAItem(
            question=f"What did the tilted clue help {child.id} find?",
            answer=(
                f"It helped {child.id} find a tulip hidden under the soil. The clue was a way to guide the quest toward the flower."
            ),
        ),
        QAItem(
            question=f"How did the story show a transformation?",
            answer=(
                f"The hidden place changed from {trans.before} to {trans.after}. That change proved the garden was not empty at all; it was becoming something new."
            ),
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer=(
                f"{child.id} learned that small clues can lead to true answers. A careful look at a tilt in the garden can reveal a living thing and a story behind it."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean if something is tilted?",
            answer="If something is tilted, it is leaning a little instead of standing straight. A tilt can be a clue that something unusual happened.",
        ),
        QAItem(
            question="What is a tulip?",
            answer="A tulip is a flower that grows from a bulb and opens in bright colors. It can look like a cup or a little bell.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important or interesting. In a story, it often means following clues to find an answer.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state to another. In stories, it can mean something hidden becomes visible or something plain becomes beautiful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        clue="tilt",
        transformation="bloom",
        name="Mia",
        gender="girl",
        companion="cat",
    ),
    StoryParams(
        place="greenhouse",
        clue="tilt",
        transformation="open",
        name="Eli",
        gender="boy",
        companion="sparrow",
    ),
    StoryParams(
        place="path",
        clue="tilt",
        transformation="reveal",
        name="Nora",
        gender="girl",
        companion="dog",
    ),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this tiny mystery world only supports the tilt clue and tulip transformation.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery about tilt, tulip, quest, and transformation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--transformation", choices=sorted(TRANSFORMS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=sorted(COMPANIONS))
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, transformation = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(
        place=place,
        clue=clue,
        transformation=transformation,
        name=name,
        gender=gender,
        companion=companion,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.transformation not in TRANSFORMS:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], CLUES[params.clue], TRANSFORMS[params.transformation], params.name, params.gender, params.companion)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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


ASP_RULES = r"""
clue(tilt).
transformation(bloom).
transformation(open).
transformation(reveal).
valid(P,C,T) :- place(P), clue(C), transformation(T), C = tilt.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("clue", "tilt"))
    for t in TRANSFORMS:
        lines.append(asp.fact("transformation", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo gates differ.")
        return 1

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("MISMATCH: generated story was empty.")
            return 1
        _ = sample.to_json()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, qa=True, trace=True)
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: smoke test failed: {exc}")
        return 1

    print(f"OK: ASP parity, generation, and emit smoke test passed ({len(valid_combos())} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.transformation}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
