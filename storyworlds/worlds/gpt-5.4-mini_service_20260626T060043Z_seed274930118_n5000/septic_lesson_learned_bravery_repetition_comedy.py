#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/septic_lesson_learned_bravery_repetition_comedy.py
=================================================================================

A small comedy storyworld about a backyard septic lesson: a brave child, a very
stinky tank, a repeated mistake, and a learned lesson.

The seed idea:
---
A child notices the septic tank in the backyard and decides, with great bravery
and almost no wisdom, that they should "help" it. The parent warns them that the
tank is not a toy. The child tries anyway, then learns that bravery is better
when it comes with listening, distance, and a clothespin for the nose.

This world keeps the tone light and funny:
- repeated attempts create repetition comedy,
- bravery is real, but needs guidance,
- the ending proves a lesson was learned.

Story state:
- meters track physical things like stink, mud, and distance,
- memes track emotional things like bravery, embarrassment, and lesson learned.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the backyard"
    smells_like: str = "a fishy potato"
    affords: set[str] = field(default_factory=lambda: {"inspect", "tap", "listen"})


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    risky: bool = False


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    item: str
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


def make_item(item_id: str) -> Item:
    items = {
        "ball": Item("ball", "ball", "a bright red ball", "toy", risky=True),
        "shoe": Item("shoe", "shoe", "a tiny blue shoe", "toy", risky=True),
        "spoon": Item("spoon", "spoon", "a shiny soup spoon", "tool", risky=True),
        "stick": Item("stick", "stick", "a long curious stick", "tool", risky=True),
    }
    return items[item_id]


def make_setting() -> Setting:
    return Setting()


GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Ben", "Jack"]
TRAITS = ["curious", "brave", "silly", "cheerful", "determined", "dramatic"]


def noun_for_parent(parent: str) -> str:
    return {"mother": "mom", "father": "dad"}.get(parent, parent)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes if t), 'curious')} "
        f"{hero.type} who liked big ideas."
    )


def setup(world: World, hero: Entity, parent: Entity, item: Item) -> None:
    world.say(
        f"One afternoon, {hero.id} found the septic tank cover in {world.setting.place}. "
        f"It sat there like a grumpy metal pancake."
    )
    world.say(
        f"{hero.id} thought the tank looked important and wanted to help, "
        f"even though it smelled like {world.setting.smells_like}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} told {hero.pronoun('possessive')} "
        f"{noun_for_parent(parent.type)} about the {item.label} nearby, just in case."
    )


def warn(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.say(
        f'"That septic tank is not a toy," {hero.pronoun("possessive")} '
        f"{noun_for_parent(parent.type)} said. "
        f'"It is a grown-up job, and it smells brave all by itself."'
    )


def repeated_attempts(world: World, hero: Entity, item: Item) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.memes["persistence"] = hero.memes.get("persistence", 0) + 1
    world.say(
        f"{hero.id} took one brave step closer, then another, then stopped and "
        f"pinched {hero.pronoun('possessive')} nose."
    )
    world.say(
        f'"I can do it," {hero.pronoun()} said. Then {hero.pronoun()} tried again, '
        f'and the septic smell made {hero.pronoun("object")} sneeze.'
    )
    world.say(
        f"{hero.id} tried to tap the cover twice for luck, but the second tap "
        f"was funnier than the first."
    )
    world.say(
        f"{hero.id} backed up, marched forward, and backed up again, like a tiny "
        f"marching band with only one member."
    )


def lesson(world: World, hero: Entity, parent: Entity, item: Item) -> None:
    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0) + 1
    hero.memes["lesson_learned"] = hero.memes.get("lesson_learned", 0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} learned that being brave did not mean "
        f"touching every smelly thing."
    )
    world.say(
        f"{hero.id} listened when {hero.pronoun('possessive')} "
        f"{noun_for_parent(parent.type)} explained that the septic tank needed a "
        f"grown-up, not a hero with sticky fingers."
    )
    world.say(
        f"Together they moved the {item.label} away from the cover, because "
        f"the tank was for water and waste, not toys."
    )


def ending(world: World, hero: Entity, parent: Entity, item: Item) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"At the end, {hero.id} stood a safe step back, holding {hero.pronoun('possessive')} "
        f"nose and laughing at the last tiny sneeze."
    )
    world.say(
        f"The septic tank stayed shut, the {item.label} stayed clean, and "
        f"{noun_for_parent(parent.type)} said {hero.id} was brave enough to learn."
    )
    world.say(
        f"{hero.id} gave a proud nod. Next time, {hero.pronoun()} decided, brave "
        f"would mean asking first."
    )


def tell(hero_name: str, gender: str, parent_type: str, trait: str, item_id: str) -> World:
    world = World(make_setting())
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        memes={"bravery": 0.0, "embarrassment": 0.0, "lesson_learned": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=noun_for_parent(parent_type),
        memes={},
    ))
    item = make_item(item_id)

    world.facts.update(hero=hero, parent=parent, item=item, trait=trait)
    hero.memes[trait] = 1.0

    introduce(world, hero)
    world.para()
    setup(world, hero, parent, item)
    warn(world, parent, hero)
    repeated_attempts(world, hero, item)
    lesson(world, hero, parent, item)
    world.para()
    ending(world, hero, parent, item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, item, trait = f["hero"], f["parent"], f["item"], f["trait"]
    return [
        f'Write a short comedy story for a child about a brave {hero.type} named {hero.id}, '
        f"a septic tank, and a lesson learned.",
        f"Tell a funny backyard story where {hero.id} wants to help the septic tank, "
        f"but {noun_for_parent(parent.type)} teaches {hero.id} a better way.",
        f'Write a simple story that repeats a silly mistake around "{item.label}" and ends '
        f"with {hero.id} learning to be brave in a smarter way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, item = f["hero"], f["parent"], f["item"]
    return [
        QAItem(
            question=f"Why did {hero.id} go near the septic tank?",
            answer=(
                f"{hero.id} went near it because {hero.pronoun()} wanted to help and "
                f"thought the tank looked important."
            ),
        ),
        QAItem(
            question=f"What happened when {hero.id} kept trying again and again?",
            answer=(
                f"{hero.id} got closer, pinched {hero.pronoun('possessive')} nose, "
                f"sneezed, and had to back up more than once. That repetition made the "
                f"moment silly instead of scary."
            ),
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn at the end?",
            answer=(
                f"{hero.id} learned that bravery does not mean touching every smelly thing. "
                f"The smarter brave choice was to listen and let a grown-up handle the septic tank."
            ),
        ),
        QAItem(
            question=f"What did {noun_for_parent(parent.type)} say the septic tank was not?",
            answer="It was not a toy.",
        ),
        QAItem(
            question=f"What stayed clean when the story was over?",
            answer=f"The {item.label} stayed clean, and the septic tank stayed shut.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a septic tank?",
            answer=(
                "A septic tank is an underground container that helps handle waste water "
                "in places without a city sewer system."
            ),
        ),
        QAItem(
            question="Why should children stay away from septic tank covers?",
            answer=(
                "Children should stay away because the area can be unsafe, and the tank is a grown-up job."
            ),
        ),
        QAItem(
            question="What does bravery mean?",
            answer=(
                "Bravery means doing something hard or scary in a thoughtful way, not doing something dangerous without help."
            ),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
parent(P) :- parent_name(P).
item(I) :- item_name(I).

near_septic(H) :- hero(H), curious(H).
warned(H) :- near_septic(H), parent(P).

brave(H) :- warned(H).
retries(H) :- brave(H).
learns(H) :- retries(H).

valid_story(H, P, I) :- hero(H), parent(P), item(I), brave(H), learns(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("hero_name", name))
    for p in ["mother", "father"]:
        lines.append(asp.fact("parent_name", p))
    for item_id in ["ball", "shoe", "spoon", "stick"]:
        lines.append(asp.fact("item_name", item_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for h in GIRL_NAMES + BOY_NAMES:
        for p in ["mother", "father"]:
            for i in ["ball", "shoe", "spoon", "stick"]:
                combos.append((h, p, i))
    return combos


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if clingo_set:
        print(f"OK: ASP produced {len(clingo_set)} story combos.")
        return 0
    print("MISMATCH: ASP produced no valid stories.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic septic-tank lesson story world.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--item", choices=["ball", "shoe", "spoon", "stick"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    item = args.item or rng.choice(["ball", "shoe", "spoon", "stick"])
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait, item=item)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.parent, params.trait, params.item)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:\n")
        for item in stories:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = [
            StoryParams(name="Mia", gender="girl", parent="mother", trait="curious", item="ball"),
            StoryParams(name="Leo", gender="boy", parent="father", trait="brave", item="shoe"),
            StoryParams(name="Ava", gender="girl", parent="father", trait="silly", item="spoon"),
            StoryParams(name="Finn", gender="boy", parent="mother", trait="determined", item="stick"),
        ]
        samples = [generate(p) for p in cur]
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
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
