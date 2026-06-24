#!/usr/bin/env python3
"""
spaz_exuberant_misunderstanding_comedy.py
=========================================

A tiny comedy storyworld about a cheerful mix-up: someone exuberant hears
instructions wrong, makes a harmless mess, and then the misunderstanding is
cleared up with a funny fix.

The domain is intentionally small:
- one playful character who is exuberant
- one careful helper who worries about the mix-up
- one small object or task that can be misunderstood
- one comic turn, then a cheerful resolution

The world model keeps track of:
- physical meters: bits like tidy, mixed_up, and ready
- emotional memes: things like exuberance, confusion, embarrassment, and relief
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: str


@dataclass
class Task:
    id: str
    verb: str
    mistaken_action: str
    object_name: str
    effect: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    task: str
    prop: str
    name: str
    helper_name: str
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", afford="mixing"),
    "classroom": Setting(place="the classroom", afford="sorting"),
    "garden": Setting(place="the garden table", afford="watering"),
}

TASKS = {
    "mixing": Task(
        id="mixing",
        verb="mix the batter",
        mistaken_action="mix up the letters",
        object_name="bowl",
        effect="swirled and spilled",
        keyword="mix",
        tags={"mix", "batter", "funny"},
    ),
    "sorting": Task(
        id="sorting",
        verb="sort the cards",
        mistaken_action="sort the snacks",
        object_name="box",
        effect="all jumbled",
        keyword="sort",
        tags={"sort", "cards", "funny"},
    ),
    "watering": Task(
        id="watering",
        verb="water the plants",
        mistaken_action="water the drawing",
        object_name="pitcher",
        effect="splashed and smeared",
        keyword="water",
        tags={"water", "plants", "funny"},
    ),
}

PROPS = {
    "bowl": Prop(id="bowl", label="a bright bowl", phrase="a bright blue bowl", type="bowl"),
    "cards": Prop(id="cards", label="picture cards", phrase="some picture cards", type="cards", plural=True),
    "plants": Prop(id="plants", label="little plants", phrase="some little green plants", type="plants", plural=True),
}

NAMES = ["Spaz", "Milo", "Tess", "Ruby", "Nico", "Luna", "Pip", "June"]
HELPERS = ["Aunt Bea", "Dad", "Mom", "Mr. Lane", "Ms. Reed"]
TRAITS = ["exuberant", "cheerful", "bouncy", "silly", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        task = TASKS[setting.afford]
        for pid in PROPS:
            out.append((place, task.id, pid))
    return out


def reasonableness_gate(task: Task, prop: Prop) -> bool:
    if task.id == "mixing" and prop.id != "bowl":
        return False
    if task.id == "sorting" and prop.id != "cards":
        return False
    if task.id == "watering" and prop.id != "plants":
        return False
    return True


def explain_rejection(task: Task, prop: Prop) -> str:
    return (
        f"(No story: the task '{task.verb}' does not honestly fit with {prop.label}. "
        f"The comedy needs a real misunderstanding, not a random object swap.)"
    )


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was an {hero.memes.get('trait_word', 'exuberant')} child who could "
        f"turn even a small job into a big adventure."
    )


def setup(world: World, hero: Entity, helper: Entity, prop: Entity, task: Task) -> None:
    hero.memes["exuberance"] = hero.memes.get("exuberance", 0.0) + 1
    world.say(
        f"One day, {hero.id} and {helper.noun()} were in {world.setting.place}, where "
        f"they were supposed to {task.verb} with {prop.phrase}."
    )
    world.say(
        f"{helper.noun()} gave a simple instruction, but {hero.id} heard it in a very "
        f"different way."
    )


def misunderstanding(world: World, hero: Entity, helper: Entity, prop: Entity, task: Task) -> None:
    hero.memes["confusion"] = hero.memes.get("confusion", 0.0) + 1
    hero.memes["exuberance"] = hero.memes.get("exuberance", 0.0) + 1
    world.say(
        f"{hero.id} thought {helper.noun()} meant to {task.mistaken_action} instead."
    )
    world.say(
        f"So {hero.id} hurried off with {prop.obj()} and did the wrong thing in the "
        f"silliest possible way."
    )


def comic_mess(world: World, hero: Entity, prop: Entity, task: Task) -> None:
    hero.meters["mixed_up"] = hero.meters.get("mixed_up", 0.0) + 1
    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0.0) + 1
    world.say(
        f"Soon everything was {task.effect}, and {hero.id} froze with a tiny gulp."
    )


def clarify(world: World, helper: Entity, hero: Entity, task: Task) -> None:
    helper.memes["amused"] = helper.memes.get("amused", 0.0) + 1
    world.say(
        f"{helper.noun()} blinked, then laughed and said, "
        f'"Oh dear, I meant {task.verb}, not {task.mistaken_action}!"'
    )


def resolution(world: World, hero: Entity, helper: Entity, prop: Entity, task: Task) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["confusion"] = 0.0
    hero.meters["ready"] = hero.meters.get("ready", 0.0) + 1
    world.say(
        f"{hero.id} grinned, and together they fixed the mix-up."
    )
    world.say(
        f"In the end, they really did {task.verb}, and {prop.label} stayed part of a "
        f"funny story instead of a disaster."
    )


def tell(setting: Setting, task: Task, prop_cfg: Prop, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="child",
        memes={"trait_word": "exuberant"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="adult",
        label=helper_name,
    ))
    prop = world.add(Entity(
        id=prop_cfg.id,
        type=prop_cfg.type,
        label=prop_cfg.label,
        phrase=prop_cfg.phrase,
        plural=prop_cfg.plural,
        caretaker=helper.id,
    ))

    introduce(world, hero)
    world.para()
    setup(world, hero, helper, prop, task)
    misunderstanding(world, hero, helper, prop, task)
    comic_mess(world, hero, prop, task)
    world.para()
    clarify(world, helper, hero, task)
    resolution(world, hero, helper, prop, task)

    world.facts = {
        "hero": hero,
        "helper": helper,
        "prop": prop,
        "task": task,
        "setting": setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    prop = f["prop"]
    return [
        f'Write a short comedy story for a child named {hero.id} who is exuberant and '
        f'misunderstands a simple instruction.',
        f"Tell a funny story where {helper.noun()} asks {hero.id} to {task.verb}, "
        f"but {hero.id} hears it wrong.",
        f'Write a child-friendly misunderstanding comedy using the word "{task.keyword}" '
        f"and ending with a cheerful fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    prop = f["prop"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, an exuberant child who made a funny mistake.",
        ),
        QAItem(
            question=f"What did {helper.noun()} want {hero.id} to do?",
            answer=f"{helper.noun()} wanted {hero.id} to {task.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} think {helper.noun()} meant?",
            answer=f"{hero.id} thought {helper.noun()} meant to {task.mistaken_action}.",
        ),
        QAItem(
            question=f"What helped fix the misunderstanding?",
            answer=f"They talked it through, laughed, and then did the right job with {prop.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks something the wrong way.",
        ),
        QAItem(
            question="Why can comedy be funny?",
            answer="Comedy can be funny because people do silly things, mix things up, and then laugh together.",
        ),
        QAItem(
            question="What does exuberant mean?",
            answer="Exuberant means full of happy energy and excitement.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("affords", sid, setting.afford))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("verb", tid, task.verb))
        lines.append(asp.fact("mistaken", tid, task.mistaken_action))
        lines.append(asp.fact("keyword", tid, task.keyword))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("matches", pid, pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Task, Prop) :- affords(Place, Task), matches(Prop, Prop).
story(Place, Task, Prop) :- valid(Place, Task, Prop).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with a funny misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.prop:
        combos = [c for c in combos if c[2] == args.prop]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, prop = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper = args.helper_name or rng.choice(HELPERS)
    return StoryParams(place=place, task=task, prop=prop, name=name, helper_name=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], PROPS[params.prop], params.name, params.helper_name)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task, prop) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, task, prop in valid_combos():
            samples.append(generate(StoryParams(place=place, task=task, prop=prop, name="Spaz", helper_name="Mom")))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
