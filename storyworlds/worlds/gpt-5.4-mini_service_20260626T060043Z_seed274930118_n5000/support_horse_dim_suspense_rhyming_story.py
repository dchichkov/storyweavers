#!/usr/bin/env python3
"""
Storyworld: support / horse-dim suspense rhyming story.

A tiny, child-facing story world where a small horse-dim friend needs support
to cross a wobbly place, and the scene resolves with a calm, rhyming turn.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    supports: bool = False
    suspense: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


@dataclass
class StoryConfig:
    place: str
    title: str
    trouble: str
    turn: str


PLACES = {
    "barn_path": Place("the barn path", supports=True, suspense=True),
    "hill_bridge": Place("the little bridge", supports=True, suspense=True),
    "moon_dock": Place("the moonlit dock", supports=True, suspense=True),
}

CONFIGS = {
    "barn_path": StoryConfig(
        place="barn_path",
        title="a barn path with a wobble",
        trouble="a plank that made a creak",
        turn="a sturdy prop that made the path keep neat",
    ),
    "hill_bridge": StoryConfig(
        place="hill_bridge",
        title="a bridge that swayed in the breeze",
        trouble="a board that shivered and leaned to one side",
        turn="a firm support that held the sway just right",
    ),
    "moon_dock": StoryConfig(
        place="moon_dock",
        title="a dock that whispered at night",
        trouble="a step that trembled under moonlight",
        turn="a strong support block tucked underneath with care",
    ),
}

GIRL_NAMES = ["Lily", "Mina", "Rose", "Nora", "Ava"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Leo", "Max"]


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="adult"))
    support = world.add(Entity(id="support", type="support", label="support block"))
    horse = world.add(Entity(id="horse", type="horse", label="horse-dim pony", phrase="a horse-dim pony"))
    plank = world.add(Entity(id="plank", type="thing", label="plank", phrase="a wobbly plank"))

    hero.memes["curious"] = 1
    hero.memes["hope"] = 1
    horse.meters["wobble"] = 1
    plank.meters["wobble"] = 1

    world.say(
        f"On {place.name}, where the wind could moan, "
        f"there stood a path with a hush of its own."
    )
    world.say(
        f"{hero.id} saw {horse.phrase}, small and light, "
        f"and wanted to help it move just right."
    )
    world.say(
        f"But {CONFIGS[params.place].trouble}, and the night felt thin, "
        f"so the little one paused with a nervous grin."
    )

    world.para()
    hero.memes["suspense"] = 1
    horse.memes["fear"] = 1
    world.say(
        f"\"Don't step so fast,\" said {helper.id}, low and slow, "
        f"\"this place needs support, as you well know.\""
    )
    world.say(
        f"The board gave a creak, the rail gave a shake, "
        f"and even the lantern seemed ready to quake."
    )

    if place.supports:
        support.meters["steady"] = 1
        support.owner = helper.id
        world.say(
            f"{helper.id} slid in the {support.label}, firm and neat, "
            f"so the path could stay safe for four small feet."
        )
        horse.meters["wobble"] = 0
        plank.meters["wobble"] = 0
        hero.memes["suspense"] = 0
        horse.memes["fear"] = 0
        hero.memes["joy"] = 2
        world.say(
            f"Then {horse.label} went clip and clop, "
            f"and the scary little shiver had to stop."
        )
        world.say(
            f"{hero.id} laughed, because the danger had flown, "
            f"and the moonlit path felt safe as a stone."
        )
        world.say(
            f"With support in place, the brave pair passed, "
            f"and the night turned soft, and sweet, and last."
        )
    else:
        raise StoryError("This story needs a place where support can actually help.")

    world.facts = {
        "hero": hero,
        "helper": helper,
        "horse": horse,
        "support": support,
        "place": place,
        "config": CONFIGS[params.place],
        "resolved": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story about {f["hero"].id}, a horse-dim friend, and a support that ends a suspenseful wobble.',
        f"Tell a gentle suspense story in rhyme where {f['helper'].id} brings support to keep the little path safe.",
        f"Write a child-friendly story with the words 'support' and 'horse-dim' and a calm ending after a scare.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    horse = f["horse"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was trying to help the horse-dim pony on {place.name}?",
            answer=f"{hero.id} was trying to help the horse-dim pony, and {helper.id} joined in with calm support.",
        ),
        QAItem(
            question="What made the story feel suspenseful at first?",
            answer=f"The path wobbled, a plank creaked, and everything felt shaky until support was added.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the support holding firm, the pony going safely across, and everyone feeling glad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does support mean?",
            answer="Support is something that helps hold another thing steady so it does not tip or fall.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the nervous feeling you get when you wonder what will happen next.",
        ),
        QAItem(
            question="What does a horse-dim thing mean here?",
            answer="It means something that is as small and pony-like as a little horse, easy to imagine and gentle to picture.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for key, place in PLACES.items():
        lines.append(asp.fact("place", key))
        if place.supports:
            lines.append(asp.fact("supports", key))
        if place.suspense:
            lines.append(asp.fact("suspense", key))
    return "\n".join(lines)


ASP_RULES = r"""
ok(P) :- place(P), supports(P), suspense(P).
#show ok/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show ok/1."))
    asp_set = set(asp.atoms(model, "ok"))
    py_set = {(k,) for k, p in PLACES.items() if p.supports and p.suspense}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} places).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("only in clingo:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Support and horse-dim suspense rhyming story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"], default="girl")
    ap.add_argument("--helper-name")
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
    place = args.place or rng.choice(list(PLACES))
    if place not in PLACES:
        raise StoryError("Unknown place.")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if args.hero_type == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(["Mara", "Pip", "June", "Otto"])
    return StoryParams(place=place, hero_name=hero_name, hero_type=args.hero_type, helper_name=helper_name)


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
    StoryParams(place="barn_path", hero_name="Lily", hero_type="girl", helper_name="Mara"),
    StoryParams(place="hill_bridge", hero_name="Theo", hero_type="boy", helper_name="Pip"),
    StoryParams(place="moon_dock", hero_name="Nora", hero_type="girl", helper_name="June"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show ok/1."))
        print(sorted(set(asp.atoms(model, "ok"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
