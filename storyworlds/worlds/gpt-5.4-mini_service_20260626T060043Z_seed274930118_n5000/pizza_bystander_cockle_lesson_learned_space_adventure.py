#!/usr/bin/env python3
"""
A tiny storyworld about a space adventure, a pizza problem, a bystander,
and a cockle lesson learned.

Premise:
A child on a small spaceship really wants to eat a floating pizza in zero-g.
A bystander worries because the pizza will drift into a vent, and a cockle shell
artifact will clatter loose during the scramble.
The child learns that slowing down and using a tray makes the trip safer.

The simulated world tracks:
- meters: position, drift, mess, damage, clean
- memes: excitement, worry, embarrassment, relief, lesson_learned
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

# -----------------------------------------------------------------------------
# Small world model
# -----------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"position": 0.0, "drift": 0.0, "mess": 0.0, "damage": 0.0, "clean": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"excitement": 0.0, "worry": 0.0, "embarrassment": 0.0, "relief": 0.0, "lesson_learned": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    spacey: bool = True


@dataclass
class SceneItem:
    id: str
    label: str
    phrase: str
    risky: bool = False


@dataclass
class Lesson:
    id: str
    offer: str
    result: str
    prevents: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


# -----------------------------------------------------------------------------
# Story content
# -----------------------------------------------------------------------------

SETTINGS = {
    "orbital_kitchen": Setting(place="the orbital kitchen", spacey=True),
    "moon_habitat": Setting(place="the moon habitat", spacey=True),
    "cargo_bay": Setting(place="the cargo bay", spacey=True),
}

HEROES = [
    ("Nova", "girl"),
    ("Rex", "boy"),
    ("Mika", "girl"),
    ("Timo", "boy"),
]

BYSTANDERS = [
    ("Captain Sera", "woman"),
    ("Engineer Pio", "man"),
    ("Aunt Juno", "woman"),
]

ITEMS = {
    "pizza": SceneItem(
        id="pizza",
        label="pizza",
        phrase="a hot cheese pizza in a shiny magnetic box",
        risky=True,
    ),
    "cockle": SceneItem(
        id="cockle",
        label="cockle shell",
        phrase="a little cockle shell kept in a display pouch",
        risky=True,
    ),
}


LESSONS = [
    Lesson(
        id="slow_down",
        offer="use a tray with magnetic edges",
        result="the pizza stayed in its box",
        prevents="it drifting into a vent",
    ),
    Lesson(
        id="hold_on",
        offer="clip the cockle pouch to the wall first",
        result="the shell stopped clacking around",
        prevents="a noisy spill",
    ),
]


# -----------------------------------------------------------------------------
# ASP twin and fact emission
# -----------------------------------------------------------------------------

ASP_RULES = r"""
risky(item) :- item(item), risky_item(item).
need_care(item) :- risky(item).

safe(item) :- chosen_fix(item, fix), helps(fix, item).

lesson_learned(hero) :- hero(hero), safe(pizza), safe(cockle).

valid_story(hero, bystander, lesson) :-
    hero(hero), bystander(bystander), lesson(lesson),
    can_warn(bystander, hero), can_fix(lesson, pizza), can_fix(lesson, cockle).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, _ in HEROES:
        lines.append(asp.fact("hero", hid))
    for bid, _ in BYSTANDERS:
        lines.append(asp.fact("bystander", bid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.risky:
            lines.append(asp.fact("risky_item", iid))
    for lesson in LESSONS:
        lines.append(asp.fact("lesson", lesson.id))
        lines.append(asp.fact("can_fix", lesson.id, "pizza"))
        lines.append(asp.fact("can_fix", lesson.id, "cockle"))
    for hid, _ in HEROES:
        for bid, _ in BYSTANDERS:
            lines.append(asp.fact("can_warn", bid, hid))
    for lesson in LESSONS:
        lines.append(asp.fact("helps", lesson.id, "pizza"))
        lines.append(asp.fact("helps", lesson.id, "cockle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# -----------------------------------------------------------------------------
# Reasonableness gate
# -----------------------------------------------------------------------------

def lesson_for(item: SceneItem) -> Lesson:
    return LESSONS[0] if item.id == "pizza" else LESSONS[1]


def validate_choice(item: SceneItem, lesson: Lesson) -> None:
    if item.id == "pizza" and lesson.id != "slow_down":
        raise StoryError("Pizza stories need the tray lesson so the pizza can stay safely boxed.")
    if item.id == "cockle" and lesson.id != "hold_on":
        raise StoryError("Cockle stories need the wall-clip lesson so the shell can stop clattering.")


# -----------------------------------------------------------------------------
# Story engine
# -----------------------------------------------------------------------------

def predict(world: World, hero: Entity, item: SceneItem, lesson: Lesson) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.memes["excitement"] += 1
    if item.id == "pizza":
        sim.facts["risk"] = "vent"
        return {"mess": True, "lesson_needed": True}
    return {"mess": True, "lesson_needed": True}


def setup(world: World, hero: Entity, bystander: Entity, item: SceneItem) -> None:
    world.say(
        f"On a bright day above the stars, {hero.id} explored {world.setting.place} "
        f"with {hero.pronoun('possessive')} eyes on {item.phrase}."
    )
    world.say(
        f"{hero.id} loved space adventures and wanted to take {item.phrase} to the viewing window."
    )
    world.say(
        f"{bystander.id} was nearby, watching carefully like a calm guide on the ship."
    )


def tension(world: World, hero: Entity, bystander: Entity, item: SceneItem) -> None:
    hero.memes["excitement"] += 1
    bystander.memes["worry"] += 1
    if item.id == "pizza":
        world.say(
            f"{hero.id} reached for the pizza, but the box started to slide in the low gravity."
        )
        world.say(
            f'"Careful," {bystander.id} said. "If that pizza drifts, it could bump the vent and make a mess."'
        )
    else:
        world.say(
            f"{hero.id} reached for the cockle shell, and the tiny pouch began to swing in the ship's hum."
        )
        world.say(
            f'"Careful," {bystander.id} said. "That cockle shell could clatter loose and turn the cabin noisy."'
        )
    hero.memes["embarrassment"] += 1


def lesson_turn(world: World, hero: Entity, bystander: Entity, item: SceneItem, lesson: Lesson) -> None:
    hero.memes["lesson_learned"] += 1
    bystander.memes["relief"] += 1
    world.say(
        f"{hero.id} stopped, listened, and learned a small lesson: {lesson.offer}."
    )
    world.say(
        f"Together, {hero.id} and {bystander.id} tried it, and soon {lesson.result}."
    )


def resolution(world: World, hero: Entity, bystander: Entity, item: SceneItem, lesson: Lesson) -> None:
    hero.memes["relief"] += 1
    world.say(
        f"After that, {hero.id} could enjoy the {item.label} without worry, because {lesson.prevents}."
    )
    if item.id == "pizza":
        world.say(
            f"The pizza stayed warm and round while the stars glowed outside the window."
        )
    else:
        world.say(
            f"The cockle shell rested quietly again, and the ship felt peaceful and tidy."
        )


def tell(setting: Setting, hero_name: str, hero_type: str, bystander_name: str, bystander_type: str, item: SceneItem) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    bystander = world.add(Entity(id=bystander_name, kind="character", type=bystander_type))
    lesson = lesson_for(item)
    validate_choice(item, lesson)

    world.facts.update(hero=hero, bystander=bystander, item=item, lesson=lesson)

    setup(world, hero, bystander, item)
    world.para()
    tension(world, hero, bystander, item)
    world.para()
    lesson_turn(world, hero, bystander, item, lesson)
    resolution(world, hero, bystander, item, lesson)
    return world


# -----------------------------------------------------------------------------
# Registries and params
# -----------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    item: str
    hero_name: str
    hero_type: str
    bystander_name: str
    bystander_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [("orbital_kitchen", "pizza"), ("cargo_bay", "cockle"), ("moon_habitat", "pizza"), ("moon_habitat", "cockle")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld with pizza, a bystander, and a cockle lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--bystander")
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
    combos = valid_combos()
    if args.setting and args.item and (args.setting, args.item) not in combos:
        raise StoryError("That setting/item pair does not make a reasonable space-adventure story.")

    choices = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.item is None or c[1] == args.item)]
    if not choices:
        raise StoryError("No valid choices match the given options.")

    setting, item = rng.choice(sorted(choices))
    hero_name, hero_type = rng.choice(HEROES)
    if args.name:
        hero_name = args.name
    bystander_name, bystander_type = rng.choice(BYSTANDERS)
    if args.bystander:
        bystander_name = args.bystander
    return StoryParams(setting=setting, item=item, hero_name=hero_name, hero_type=hero_type, bystander_name=bystander_name, bystander_type=bystander_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    lesson = f["lesson"]
    return [
        f'Write a short space-adventure story for a child about {hero.id}, a bystander, and {item.label}.',
        f'Tell a gentle story where {hero.id} almost causes trouble with {item.label}, but a bystander helps them learn a lesson.',
        f'Write a tiny story that ends with the lesson "{lesson.offer}" in a spaceship setting.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    bystander: Entity = f["bystander"]
    item: SceneItem = f["item"]
    lesson: Lesson = f["lesson"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {item.label}?",
            answer=f"{hero.id} wanted to explore with the {item.label} at the viewing window.",
        ),
        QAItem(
            question=f"Why did {bystander.id} warn {hero.id}?",
            answer=f"{bystander.id} warned {hero.id} because the {item.label} could drift, spill, or make a mess in the ship.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned to {lesson.offer}, which kept the {item.label} safe and the trip calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bystander?",
            answer="A bystander is someone who is nearby and sees what is happening, even if they are not the main person acting.",
        ),
        QAItem(
            question="What is a cockle shell?",
            answer="A cockle shell is a hard shell from a sea animal, often with a curved shape and ridges.",
        ),
        QAItem(
            question="Why is pizza fun to eat on a trip?",
            answer="Pizza is fun to eat on a trip because it is warm, tasty, and easy to share with friends.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        params.hero_name,
        params.hero_type,
        params.bystander_name,
        params.bystander_type,
        ITEMS[params.item],
    )
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


# -----------------------------------------------------------------------------
# ASP helpers
# -----------------------------------------------------------------------------

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set((s, i) for s, i in valid_combos())
    cl = set((a, b) for a, b, _ in asp_valid_stories())
    if py == cl:
        print(f"OK: ASP gate matches Python gate ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python gates.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

CURATED = [
    StoryParams("orbital_kitchen", "pizza", "Nova", "girl", "Captain Sera", "woman"),
    StoryParams("cargo_bay", "cockle", "Rex", "boy", "Engineer Pio", "man"),
    StoryParams("moon_habitat", "pizza", "Mika", "girl", "Aunt Juno", "woman"),
    StoryParams("moon_habitat", "cockle", "Timo", "boy", "Captain Sera", "woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_stories():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.item} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
